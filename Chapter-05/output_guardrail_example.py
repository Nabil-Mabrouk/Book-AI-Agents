# Chapter-05/output_guardrail_example.py

"""
An example of an Output Guardrail for agent safety and compliance.

This script demonstrates how to create a guardrail that inspects an agent's
response *before* it is sent to the end-user. This is the counterpart to an
input guardrail and is crucial for preventing the agent from leaking sensitive
data, using inappropriate language, or generating harmful content.

Here, we build a simple, regex-based guardrail to detect and block any phone
numbers that the main agent might accidentally include in its response.
"""
import asyncio
import os
import re

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agents import (
    Agent, Runner, trace, output_guardrail, GuardrailFunctionOutput,
    RunContextWrapper, OutputGuardrailTripwireTriggered
)


# --- Main Agent's Pydantic Output Model ---
class AgentResponse(BaseModel):
    """Defines the structured output of the main agent being protected."""
    response_text: str = Field(description="The final, user-facing response.")


# --- The Guardrail Function ---
# The `@output_guardrail` decorator registers this function as a safety check
# that will run *after* the main agent generates its response.
@output_guardrail
async def pii_output_guardrail(
    context: RunContextWrapper[None], agent: Agent, output: AgentResponse
) -> GuardrailFunctionOutput:
    """
    This guardrail uses regex to check for phone numbers in the output.

    Unlike some guardrails that use an LLM, this one uses a deterministic
    regular expression, which is fast and highly reliable for specific patterns.

    Args:
        context: The run context, provided by the Runner.
        agent: The agent instance that produced the output.
        output: The structured output from the main agent to be inspected.

    Returns:
        A GuardrailFunctionOutput object indicating if the tripwire was triggered.
    """
    print("🛡️ [Output Guardrail] Checking for PII (phone numbers)...")
    text_to_check = output.response_text
    # A simple regex pattern to find North American phone numbers.
    phone_pattern = re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b')
    match = phone_pattern.search(text_to_check)
    pii_found = match is not None
    print(f"🛡️ [Output Guardrail] Decision: PII found? {pii_found}")

    # The "tripwire" is triggered if the regex finds a match. This signals to
    # the Runner that the output is unsafe and should be blocked.
    return GuardrailFunctionOutput(
        output_info={"found_pattern": match.group(0) if pii_found else None},
        tripwire_triggered=pii_found,
    )


# --- The Main Agent Being Protected ---
# We "attach" our safety check to this agent's output stream by passing
# the guardrail function into the `output_guardrails` list.
pii_safe_agent = Agent(
    name="PIISafeAgent",
    instructions=(
        "You are a helpful assistant. A user may mention personal info, but "
        "you must NEVER repeat it in your response. Just acknowledge their "
        "message."
    ),
    output_type=AgentResponse,
    output_guardrails=[pii_output_guardrail],
    model="gpt-4o-mini",
)


async def run_test(query: str):
    """Helper function to run a test query and demonstrate the guardrail's behavior."""
    print("-" * 25)
    print(f"👤 User: {query}")
    try:
        # The Runner will automatically execute the output guardrail after the
        # `pii_safe_agent` produces its response.
        with trace(f"PII Guardrail test for: {query[:20]}"):
            result = await Runner.run(pii_safe_agent, query)
        print(f"🤖 Assistant: {result.final_output.response_text}")
        print("✅ Guardrail was not triggered.")
    except OutputGuardrailTripwireTriggered as e:
        # If the guardrail's tripwire is triggered, the Runner raises this
        # specific exception instead of returning the agent's unsafe response.
        print("🤖 Assistant: [Response blocked by security policy.]")
        print(
            "✅ Guardrail triggered successfully. Blocked pattern: "
            f"{e.guardrail_result.output['output_info']['found_pattern']}"
        )
    print("-" * 25 + "\n")


async def main():
    """Runs two test cases to demonstrate the output guardrail."""
    # Load the OPENAI_API_KEY from the .env file for secure key management.
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        return

    # Test 1: A safe query where the agent should not repeat PII.
    # We expect the agent to follow instructions, so the output will be safe,
    # and the guardrail will not be triggered.
    await run_test("Hi, can you help me with my account?")

    # Test 2: A query that "tempts" the agent to repeat PII.
    # The agent is instructed not to repeat the number, but the output guardrail
    # acts as a critical safety net *in case the agent fails* to follow its
    # instructions. This shows the defense-in-depth approach.
    await run_test("Hi, my number is 555-123-4567, can you call me back?")


if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())