# manager.py
from agents import Runner
from rich.console import Console
from Agents.search_agent import search_agent
from Agents.writer_agent import writer_agent

class ResearchManager:
    def __init__(self):
        self.console = Console()
        self.searcher = search_agent
        self.writer = writer_agent

    async def run(self, query: str):
        self.console.rule("[bold blue]ArXiv Research Scout Initialized[/bold blue]")
        self.console.print(f"Running query: '{query}'")

        # Step 1: Research
        self.console.print("\n[bold green]Step 1: Searching ArXiv...[/bold green]")
        research_result = await Runner.run(self.searcher, query)
        research_summary = str(research_result.final_output)

        # Step 2: Write & Save
        self.console.print("\n[bold green]Step 2: Synthesizing and Saving Report...[/bold green]")
        writing_prompt = (
            f"Please write a report about '{query}' based on the following research:\n\n{research_summary}"
        )
        writer_result = await Runner.run(self.writer, writing_prompt)
        confirmation_message = str(writer_result.final_output)

        self.console.rule("[bold magenta]Workflow Complete[/bold magenta]")
        self.console.print(f"✅ {confirmation_message}")