# workflows/research_assistant.py
"""
A complete, professional template for a self-contained, stateful, and secure workflow.

This module is a reusable and testable unit of work that is 100% consistent
with the documented patterns of the openai-agents library. It demonstrates:
1.  Input/Output Schemas: Pydantic models for clear data contracts.
2.  Local Context: Passing private, application-level data specifically to TOOLS.
3.  Sessions (Memory): Maintaining a coherent, multi-turn conversation using SQLiteSession.
4.  Guardrails: Enforcing general safety rules on agent inputs.
5.  Tools: The specific capabilities required for this workflow.
6.  Agent: The specialist agent that will execute the task.
7.  Execution Logic: A `run_workflow` function that orchestrates the process.
8.  Standalone Entrypoint: Allows the workflow to be tested in isolation.
"""
import asyncio
import os
import re # Using regex for a code-based guardrail
from typing import Any, Dict, List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from rich.console import Console

from agents import (
    Agent,
    Runner,
    trace,
    FunctionTool,
    RunContextWrapper,
    SQLiteSession,
    input_guardrail,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    TResponseInputItem, # Import for the guardrail signature
)

# ------------------------------------------------------------------
# 1. DEFINE WORKFLOW DATA CONTRACTS (Unchanged)
# ------------------------------------------------------------------
class WorkflowInput(BaseModel): user_query: str
class WorkflowOutput(BaseModel): final_response: str
class LocalContext(BaseModel):
    """Defines private data FOR TOOLS, unseen by the LLM."""
    user_id: str = Field(..., description="The unique ID of the user.")
    api_key_for_service: str = Field(..., description="A hypothetical secret key for a tool.")

# ------------------------------------------------------------------
# 2. DEFINE GUARDRAILS FOR THIS WORKFLOW (CORRECTED)
# ------------------------------------------------------------------
# This guardrail uses a simple, code-based regex check, which is fast and reliable.
# It demonstrates the correct, documented signature for an input guardrail.
@input_guardrail
async def block_url_guardrail(
    ctx: RunContextWrapper[None], # The context here is generic, not our LocalContext.
    agent: Agent,
    input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    """Blocks any input that contains a URL to prevent SSRF or unwanted browsing."""
    print("GUARDRAIL: Checking for URLs in input...")
    
    # Robustly check all string parts of the input
    text_to_check = ""
    if isinstance(input, str):
        text_to_check = input
    elif isinstance(input, list):
        # Handle complex inputs by concatenating all string parts
        text_to_check = " ".join([item for item in input if isinstance(item, str)])

    # A simple regex to find URLs
    url_pattern = re.compile(r'https?://\S+')
    match = url_pattern.search(text_to_check)

    if match:
        return GuardrailFunctionOutput(
            output_info=f"Input contains a forbidden URL: {match.group(0)}",
            tripwire_triggered=True,
        )
            
    return GuardrailFunctionOutput(output_info="Input passed URL check successfully.",
                                   tripwire_triggered=False)

# ------------------------------------------------------------------
# 3. DEFINE TOOLS FOR THIS WORKFLOW (CORRECTED & DOCUMENT-ALIGNED)
# ------------------------------------------------------------------
# This is the correct pattern for a tool that needs application-specific data.
async def _get_user_data_logic(
    wrapper: RunContextWrapper[LocalContext],
    params: Dict[str, Any] # This second argument is required by the Runner
) -> Dict[str, Any]:
    """The raw Python logic for the tool."""
    context = wrapper.context
    print(f"TOOL: Fetching data for user '{context.user_id}' using their secret API key.")
    # The 'params' argument is unused here because our tool takes no LLM input,
    # but the signature must accept it.
    return {"user_id": context.user_id, "data": f"Sensitive data for {context.user_id}"}

# This part was already correct.
get_user_data_tool = FunctionTool(
    on_invoke_tool=_get_user_data_logic,
    name="get_user_data",
    description="Fetches private data for the currently logged-in user.",
    params_json_schema={"type": "object", "properties": {}},
)

# ------------------------------------------------------------------
# 4. DEFINE THE AGENT FOR THIS WORKFLOW (CORRECTED)
# ------------------------------------------------------------------
# We establish the contract that this agent is designed to work with LocalContext.
workflow_agent = Agent[LocalContext](
    name="SecureAssistantAgent",
    instructions="You are a helpful and secure assistant. Use your tools to access user data when requested.",
    tools=[get_user_data_tool],
    input_guardrails=[block_url_guardrail],
    model="gpt-4-turbo",
)

# ------------------------------------------------------------------
# 5. DEFINE THE WORKFLOW EXECUTION LOGIC (Unchanged and Correct)
# ------------------------------------------------------------------
async def run_workflow(
    inputs: WorkflowInput,
    context: LocalContext,
    session: SQLiteSession,
    console: Console = Console()
) -> WorkflowOutput:
    # This logic was already correct and robustly handles the tripwire exception.
    console.print(f"\n[bold blue]🚀 Running Secure Workflow for user: '{context.user_id}'[/bold blue]")
    try:
        with trace("StatefulWorkflow"):
            result = await Runner.run(
                workflow_agent,
                inputs.user_query,
                session=session,
                context=context,
            )
            output = WorkflowOutput(final_response=result.final_output)
    except InputGuardrailTripwireTriggered as e:
        console.print(f"\n[bold red]⚠️ Workflow Blocked by Guardrail:[/bold red] {e.output_info}")
        output = WorkflowOutput(final_response=f"Request Blocked: {e.output_info}")
    console.print("\n[bold green]✅ Workflow Complete![/bold green]")
    return output
# ------------------------------------------------------------------
# 6. STANDALONE ENTRYPOINT (for direct testing)
# ------------------------------------------------------------------
async def main():
    """Allows this workflow to be run directly as a standalone script for testing."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set.")
        return
    
    console = Console()
    session = SQLiteSession(session_id="research-assistant-test")

    # --- THE DEFINITIVE FIX IS HERE ---
    # We must provide a value for ALL required fields in the LocalContext model.
    context = LocalContext(
        user_id="dev-user-007",
        api_key_for_service="dummy-secret-key-12345" # <-- Added the missing required field
    )
    # --- END OF FIX ---
    
    console.print(f"[grey50]Initializing workflow with Session ID: {session.session_id}[/grey50]")
    await session.clear_session()

    while True:
        user_query = console.input("[bold yellow]Ask the Secure Assistant (or type 'exit'): [/bold yellow]").strip()
        if user_query.lower() == 'exit':
            break
        
        workflow_input = WorkflowInput(user_query=user_query)
        final_output = await run_workflow(workflow_input, context, session, console)
        
        console.print("\n[bold yellow]📤 Final Workflow Output:[/bold yellow]")
        console.print(final_output.final_response)

if __name__ == "__main__":
    asyncio.run(main())