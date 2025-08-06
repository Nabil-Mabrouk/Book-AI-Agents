# Chapter-12/blueprint.py
"""
TODO: A one-line description of the agentic workflow's purpose.
e.g., "An agent that uses local and external tools to answer questions."

NOTE: This blueprint uses the 'rich' library for pretty console output.
You can install it with: pip install rich
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from rich.console import Console

from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    trace,
    function_tool,
    RunConfig,
    input_guardrail,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    MCPServer,
    MCPServerSse,
)

# ------------------------------------------------------------------
# 1. PYDANTIC MODELS (Data Contracts)
# ------------------------------------------------------------------

class UserInput(BaseModel):
    """Defines the expected structure for a tool's input."""
    # <-- TODO: Define the parameters for your tool(s).
    query: str = Field(..., description="The primary text input from the user.")

class LocalContext(BaseModel):
    """
    Private data for the agent's internal use. This is never seen by the LLM.
    """
    # <-- TODO: Add secrets, DB handles, feature flags, etc.
    user_id: str
    session_id: str

# ------------------------------------------------------------------
# 2. LOCAL TOOLS (The Agent's Built-in Capabilities)
# ------------------------------------------------------------------

@function_tool(param_model=UserInput)
async def get_user_info(query: str, wrapper: RunContextWrapper[LocalContext]) -> Dict[str, Any]:
    """
    TODO: A one-sentence description of what this tool does.
    Gets internal information about the current user, such as their ID or session.
    """
    user_ctx = wrapper.context
    print(f"🛠️  [Local Tool] Running for user: {user_ctx.user_id}")
    # <-- TODO: Implement the tool's actual business logic here.
    return {
        "user_id": user_ctx.user_id,
        "session_id": user_ctx.session_id,
        "note": f"Request was: '{query}'"
    }

# ------------------------------------------------------------------
# 3. GUARDRAILS (The Safety Net)
# ------------------------------------------------------------------

@input_guardrail
async def block_short_prompts_guardrail(
    ctx, agent, raw_input: str
) -> GuardrailFunctionOutput:
    """
    TODO: A plain-English description of the rule this guardrail enforces.
    Example: Blocks any user prompt that is fewer than 10 characters long.
    """
    if len(raw_input) < 10:
        return GuardrailFunctionOutput(
            output_info=f"Input is too short ({len(raw_input)} chars). Must be 10+.",
            tripwire_triggered=True,
        )
    return GuardrailFunctionOutput(tripwire_triggered=False)

# ------------------------------------------------------------------
# 4. MCP SERVER CONNECTIONS (External Tools)
# ------------------------------------------------------------------

def get_mcp_servers() -> List[MCPServer]:
    """
    Initializes and returns a list of MCP server connections.
    This function isolates the configuration of external tool servers.
    """
    # <-- TODO: Configure your MCP servers here.
    # This example connects to the custom SSE server built in Chapter 11.
    # To use this, that server must be running in a separate terminal.
    sse_server = MCPServerSse(
        params={"url": "http://localhost:8000/sse"},
        name="CustomCalculationServer"
    )
    return [sse_server]
    # return [] # Return an empty list if no MCP servers are needed.

# ------------------------------------------------------------------
# 5. AGENT DEFINITIONS (The Actors)
# ------------------------------------------------------------------

primary_agent = Agent(
    name="PrimaryAgent",
    instructions="""
    TODO: Define the agent's persona and primary goal.
    You are a powerful assistant with access to both internal user information
    and external calculation tools.
    - For questions about the user, use the 'get_user_info' tool.
    - For math problems, use the external 'add' tool from the MCP server.
    """,
    tools=[get_user_info], # <-- Local tools are listed here.
    input_guardrails=[block_short_prompts_guardrail],
    model="gpt-4-turbo",
)

# ------------------------------------------------------------------
# 6. THE WORKFLOW MANAGER (Orchestration Logic)
# ------------------------------------------------------------------

class WorkflowManager:
    def __init__(self):
        self.console = Console()
        self.mcp_servers = get_mcp_servers()

    async def _connect_mcp_servers(self):
        """Connects to all configured MCP servers."""
        if not self.mcp_servers:
            return
        self.console.print("[grey50]Connecting to MCP servers...[/grey50]")
        await asyncio.gather(*(server.connect() for server in self.mcp_servers))
        self.console.print("[green]MCP servers connected.[/green]")

    async def _cleanup_mcp_servers(self):
        """Cleans up all MCP server connections."""
        if not self.mcp_servers:
            return
        self.console.print("\n[grey50]Cleaning up MCP server connections...[/grey50]")
        await asyncio.gather(*(server.cleanup() for server in self.mcp_servers))

    async def run(self, user_query: str):
        """The main orchestration method."""
        self.console.print("\n[bold blue]🚀 Kicking off agent workflow...[/bold blue]")
        await self._connect_mcp_servers()

        # Initialize context for this specific run
        ctx = LocalContext(user_id="dev-user-123", session_id="session-abc-456")

        try:
            with trace("MyAgentWorkflow"):
                result = await Runner.run(
                    agent=primary_agent,
                    user_input=user_query,
                    context=ctx,
                    mcp_servers=self.mcp_servers,
                    run_config=RunConfig(trace_metadata={"user": ctx.user_id}),
                )
                self.console.print("\n[bold green]✅ Workflow Complete![/bold green]")
                self.console.print("[bold yellow]📤 Final Output:[/bold yellow]")
                self.console.print(result.final_output)

        except InputGuardrailTripwireTriggered as e:
            self.console.print(f"\n[bold red]⚠️ Request Blocked by Guardrail:[/bold red] {e.output_info}")
        except Exception as e:
            self.console.print(f"\n[bold red]🔥 An unexpected error occurred:[/bold red] {e}")
        finally:
            await self._cleanup_mcp_servers()

# ------------------------------------------------------------------
# 7. THE MAIN ENTRYPOINT
# ------------------------------------------------------------------

async def main() -> None:
    """The main function to run the agentic workflow."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set. Please set it and try again.")
        return

    console = Console()
    user_query = console.input("[bold yellow]Ask your agent: [/bold yellow]").strip()
    if not user_query:
        return

    manager = WorkflowManager()
    await manager.run(user_query)

if __name__ == "__main__":
    asyncio.run(main())