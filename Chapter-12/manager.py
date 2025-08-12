# manager.py
import asyncio
from agents import Runner
from rich.console import Console

# Import the agents this manager will orchestrate
from Agents.research_agent import research_agent
from Agents.writer_agent import writer_agent

class ResearchManager:
    def __init__(self):
        self.console = Console()
        self.researcher = research_agent
        self.writer = writer_agent

    async def run(self, query: str):
        """
        Orchestrates the two-step research and writing process.
        """
        self.console.rule("[bold green]Step 1: Research Phase[/bold green]")
        
        research_result = await Runner.run(self.researcher, query)
        research_summary = str(research_result.final_output)
        self.console.print(f"Research summary gathered.")

        self.console.rule("[bold green]Step 2: Writing & Saving Phase[/bold green]")

        # The prompt guides the writer, but its instructions now command it
        # to use the file writing tool as its final step.
        writing_prompt = (
            f"Based on the following research summary, please write a final, "
            f"polished report that answers the original query: '{query}'\n\n"
            f"Research Summary:\n{research_summary}"
        )
        writer_result = await Runner.run(self.writer, writing_prompt)
        
        # The result from the writer is now a confirmation message, not the report itself.
        agent_confirmation_message = str(writer_result.final_output)
        
        self.console.rule("[bold magenta]Workflow Complete[/bold magenta]")
        self.console.print(f"✅ Agent confirmation: {agent_confirmation_message}")
        self.console.print("\n[bold]You can now find the generated report in your project directory.[/bold]")