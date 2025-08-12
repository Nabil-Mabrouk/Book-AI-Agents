#
# agents/search_agent.py
#
# This file defines the SearchAgent. Its sole responsibility is to take a
# user's topic and use the appropriate tool to find trending repositories.
# It does not perform any analysis; it is a pure data-gathering agent.
#
# agents/search_agent.py
from agents import Agent
from Tools.github_tool import search_github_for_trending_repos, GitHubSearchResult

search_agent = Agent(
    name="GitHubSearchAgent",
    instructions=(
        "Your only job is to call the `search_github_for_trending_repos` tool "
        "using the user's provided topic and return its structured result."
    ),
    tools=[search_github_for_trending_repos],
    
    output_type=GitHubSearchResult,
)