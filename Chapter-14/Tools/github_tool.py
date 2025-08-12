# tools/github_tool.py
import os
import requests
import base64
from datetime import datetime, timedelta
from agents import function_tool
from pydantic import BaseModel, Field
from typing import List

class GitHubRepo(BaseModel):
    """A data structure for a single GitHub repository."""
    name: str
    html_url: str
    description: str | None
    stargazers_count: int
    language: str | None
    # NEW FIELD: This will hold the direct URL to the README's content API endpoint.
    readme_url: str | None = Field(description="The direct API URL to fetch the README content.")


class GitHubSearchResult(BaseModel):
    repositories: List[GitHubRepo]

class ReadmeAnalysis(BaseModel):
    """An analysis of the quality of a project's README file."""
    clarity_score: int = Field(description="Score (1-10) for how clear and understandable the README is.")
    completeness_score: int = Field(description="Score (1-10) for how complete the README is (e.g., has installation, usage).")
    overall_impression: str = Field(description="A one-paragraph summary of the README's quality and its effectiveness.")

class ActivityAnalysis(BaseModel):
    activity_level: str = Field(description="A qualitative assessment (e.g., 'High', 'Moderate', 'Low').")
    recent_commit_count: int = Field(description="The number of commits in the last 14 days.")
    comment: str = Field(description="A brief comment on the activity level.")

class StructureAnalysis(BaseModel):
    maturity_score: int = Field(description="A score (1-10) for code maturity based on file structure.")
    has_tests: bool = Field(description="Indicates if test files were found.")
    comment: str = Field(description="A brief comment on the project's structure.")


# --- Tool Functions ---
@function_tool
def search_github_for_trending_repos(topic: str) -> GitHubSearchResult:
    """
    Finds trending repositories on GitHub and also discovers the direct API
    URL for each repository's README file.
    """
    token = os.getenv("GITHUB_API_TOKEN")
    headers = {"Authorization": f"token {token}"}
    if not token:
        raise ValueError("GITHUB_API_TOKEN environment variable not set.")
    
    print(f"🛠️  [Tool Call] Searching GitHub for actively trending repos on: '{topic}'")
    one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    query = f"{topic} in:name,description,topics created:>{one_week_ago} stars:>10"
    params = {"q": query, "sort": "stars", "order": "desc"}
    
    try:
        response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        repo_list = []
        for item in data.get("items", [])[:5]:
            repo_name = item["full_name"]
            readme_url = None
            try:
                readme_info_res = requests.get(f"https://api.github.com/repos/{repo_name}/readme", headers=headers)
                if readme_info_res.status_code == 200:
                    readme_url = readme_info_res.json().get("url")
            except requests.RequestException:
                print(f"Warning: Could not fetch README info for {repo_name}.")
            
            repo_list.append(GitHubRepo(
                name=item["full_name"],
                html_url=item["html_url"],
                description=item["description"],
                stargazers_count=item["stargazers_count"],
                language=item["language"],
                readme_url=readme_url
            ))
            
        return GitHubSearchResult(repositories=repo_list)
        
    except requests.RequestException as e:
        print(f"Error connecting to GitHub API for search: {e}")
        return GitHubSearchResult(repositories=[])

@function_tool
def read_readme_from_url(readme_api_url: str) -> str:
    """
    Fetches the content of a README file from its direct content API URL.
    This tool takes a URL, not a repository name.
    """
    token = os.getenv("GITHUB_API_TOKEN")
    if not token:
        return "Error: GITHUB_API_TOKEN not set."
    
    print(f"🛠️  [Tool Call] Fetching README from direct URL: {readme_api_url}")
    headers = {"Authorization": f"token {token}"}
    try:
        response = requests.get(readme_api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        readme_content_encoded = data['content']
        readme_content_decoded = base64.b64decode(readme_content_encoded).decode('utf-8')
        return readme_content_decoded
    except requests.RequestException as e:
        return f"Error: Could not fetch README content from URL. Reason: {e}"
    
@function_tool
def get_commit_activity(repo_full_name: str) -> str:
    """Fetches the number of commits in the last 14 days to gauge recent activity."""
    token = os.getenv("GITHUB_API_TOKEN"); headers = {"Authorization": f"token {token}"}
    if not token: return "Error: GITHUB_API_TOKEN not set."
    print(f"🛠️  [Tool Call] Fetching commit activity for: '{repo_full_name}'")
    since_date = (datetime.now() - timedelta(days=14)).isoformat()
    try:
        response = requests.get(f"https://api.github.com/repos/{repo_full_name}/commits", headers=headers, params={"since": since_date})
        response.raise_for_status(); commits = response.json()
        return f"Found {len(commits)} commits in the last 14 days."
    except requests.RequestException: return "Could not fetch commit activity."

@function_tool
def get_project_structure(repo_full_name: str) -> str:
    """Fetches the file and directory structure of a repository to assess its maturity."""
    token = os.getenv("GITHUB_API_TOKEN"); headers = {"Authorization": f"token {token}"}
    if not token: return "Error: GITHUB_API_TOKEN not set."
    print(f"🛠️  [Tool Call] Fetching project structure for: '{repo_full_name}'")
    try:
        response = requests.get(f"https://api.github.com/repos/{repo_full_name}/git/trees/main?recursive=1", headers=headers)
        if response.status_code == 404: # Fallback for 'master'
             response = requests.get(f"https://api.github.com/repos/{repo_full_name}/git/trees/master?recursive=1", headers=headers)
        response.raise_for_status(); data = response.json()
        if data.get("truncated"): return "Project is too large to fully list, a sign of high maturity."
        paths = [item['path'] for item in data.get('tree', [])]; return f"Found {len(paths)} files and directories." if paths else "Project appears empty."
    except requests.RequestException: return "Could not determine project structure."