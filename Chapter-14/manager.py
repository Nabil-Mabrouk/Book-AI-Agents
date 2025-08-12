# manager.py
import asyncio
from agents import Runner
from rich.console import Console
from Agents.search_agent import search_agent
from Agents.readme_agent import readme_agent
from Agents.activity_agent import activity_agent
from Agents.structure_agent import structure_agent
from Agents.report_agent import report_agent
from Tools.github_tool import GitHubSearchResult, GitHubRepo, ReadmeAnalysis, ActivityAnalysis, StructureAnalysis

class GitHubTrendManager:
    def __init__(self):
        self.console = Console()
        self.searcher = search_agent
        self.readme_analyzer = readme_agent
        self.activity_analyzer = activity_agent
        self.structure_analyzer = structure_agent
        self.reporter = report_agent

    async def _investigate_one_repo(self, repo: GitHubRepo) -> tuple:
        """Helper to run the three analysis agents in parallel for one repo."""
        repo_name = repo.name
        
        # CORRECTED: The ReadmeAgent now gets the direct URL found by the SearchAgent.
        # If no README was found, we pass a message indicating that.
        readme_prompt = repo.readme_url if repo.readme_url else "No README file found for this repository."
        
        activity_prompt = f"repo_full_name: {repo_name}"
        structure_prompt = f"repo_full_name: {repo_name}"
        
        readme_task = Runner.run(self.readme_analyzer, readme_prompt)
        activity_task = Runner.run(self.activity_analyzer, activity_prompt)
        structure_task = Runner.run(self.structure_analyzer, structure_prompt)
        
        results = await asyncio.gather(readme_task, activity_task, structure_task)
        return repo, results[0].final_output, results[1].final_output, results[2].final_output
    
    async def run(self, topic: str):
        self.console.rule("[bold blue]GitHub Trend Scout Initialized[/bold blue]")
        
        # Step 1: Search
        self.console.print(f"\n[bold green]Step 1: Searching for trending repositories on '{topic}'...[/bold green]")
        search_run = await Runner.run(self.searcher, topic)
        search_result = search_run.final_output

        if not isinstance(search_result, GitHubSearchResult) or not search_result.repositories:
            self.console.print("[yellow]No relevant trending repositories found. Halting.[/yellow]")
            return
        
        self.console.print(f"Found {len(search_result.repositories)} candidate repositories.")

        # Step 2: Investigate in Parallel
        self.console.print("\n[bold green]Step 2: Forking to investigate repositories in parallel...[/bold green]")
        investigation_tasks = [self._investigate_one_repo(repo) for repo in search_result.repositories]
        investigation_results = await asyncio.gather(*investigation_tasks)
        self.console.print("Investigation complete. Joining results.")

        # Step 3: Format data for the final report
        report_details = []
        for repo, readme, activity, structure in investigation_results:
            readme_impression = readme.overall_impression if isinstance(readme, ReadmeAnalysis) else "README analysis failed."
            activity_comment = activity.comment if isinstance(activity, ActivityAnalysis) else "Activity analysis failed."
            structure_comment = structure.comment if isinstance(structure, StructureAnalysis) else "Structure analysis failed."
            details = (
                f"### {repo.name}\n"
                f"- **URL**: {repo.html_url} | **Stars**: {repo.stargazers_count}\n"
                f"- **README Quality**: {readme_impression}\n"
                f"- **Recent Activity**: {activity_comment}\n"
                f"- **Code Maturity**: {structure_comment}\n\n"
            )
            report_details.append(details)
        
        report_prompt = (
            "Synthesize ALL of the following briefings into ONE SINGLE, cohesive report. "
            "After composing the final report, call the `save_report` tool exactly ONCE "
            f"to save it. The topic is: '{topic}'.\n\n"
            "---BEGIN PROJECT BRIEFINGS---\n"
            f"{''.join(report_details)}"
            "\n---END PROJECT BRIEFINGS---"
        )

        # Step 4: Write & Save
        self.console.print("\n[bold green]Step 3: Writing final intelligence report...[/bold green]")
        report_run = await Runner.run(self.reporter, report_prompt)
        confirmation_message = str(report_run.final_output)

        self.console.rule("[bold magenta]Workflow Complete[/bold magenta]")
        self.console.print(f"✅ {confirmation_message}")