# main.py
import asyncio
import os
from dotenv import load_dotenv
from rich.console import Console

from agents import Runner, trace

# --- Import the AGENTS registry from the chosen project's config ---
# To switch projects, you only need to change this one line.
from projects.my_first_project.config import AGENTS

# ------------------------------------------------------------------
# THE WORKFLOW MANAGER
# ------------------------------------------------------------------
class WorkflowManager:
    def __init__(self):
        self.console = Console()
        # The entry point is now retrieved from the standard AGENTS dictionary.
        self.entry_agent = AGENTS.get("triage")
        if not self.entry_agent:
            raise ValueError("Configuration error: AGENTS dictionary must have a 'triage' key.")

    async def run(self, user_query: str):
        """The main orchestration method."""
        self.console.print("\n[bold blue]🚀 Kicking off agent workflow...[/bold blue]")

        try:
            with trace("HandoffWorkflow"):
                # We run the entry agent defined in the config.
                result = await Runner.run(
                    agent=self.entry_agent,
                    user_input=user_query,
                )
                self.console.print("\n[bold green]✅ Workflow Complete![/bold green]")
                self.console.print(f"[grey50](Handled by: {result.last_agent.name})[/grey50]")
                self.console.print("[bold yellow]📤 Final Output:[/bold yellow]")
                self.console.print(result.final_output)
        except Exception as e:
            self.console.print(f"\n[bold red]🔥 An unexpected error occurred:[/bold red] {e}")


# ------------------------------------------------------------------
# THE MAIN ENTRYPOINT
# ------------------------------------------------------------------
async def main() -> None:
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set.")
        return

    manager = WorkflowManager()
    user_query = Console().input("[bold yellow]Ask your agent: [/bold yellow]").strip()
    if user_query:
        await manager.run(user_query)

if __name__ == "__main__":
    asyncio.run(main())