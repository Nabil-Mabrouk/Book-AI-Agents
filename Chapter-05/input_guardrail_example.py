# Chapter-05/input_guardrail_example.py

"""
An example of an Input Guardrail for agent safety.

This script demonstrates how to create and use an input guardrail to prevent
an agent from processing undesirable input. A guardrail is a safety mechanism
that inspects data before the main agent runs.

Here, we build a guardrail to detect Personally Identifiable Information (PII)
and block the request if any is found, thus preventing the main agent from
ever seeing or processing sensitive user data.
"""
import asyncio
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

# 1. Define the Guardrail's Output Structure
# This Pydantic model ensures the guardrail's analysis is returned in a
# predictable, structured format that the system can reliably act upon.
class PIICheckOutput(BaseModel):
    """Defines the structured output for the PII detection agent."""
    contains_pii: bool
    reasoning: str

# 2. Create the specialized Guardrail Agent
# This is a highly specialized "micro-agent" whose only job is to perform
# the security check. It's the "brain" of our guardrail.
pii_guardrail_agent = Agent(
    name="PII Detection Guardrail",
    instructions=(
        "You are a security agent. Your only job is to check if the user's "
        "input contains any PII like email addresses, full names, or phone "
        "numbers. Your output must indicate if PII is present and why."
    ),
    output_type=PIICheckOutput,
)

# 3. Create the Input Guardrail Function
# The `@input_guardrail` decorator registers this async function as a
# safety check that will run before the main agent.
@input_guardrail
async def pii_detection_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    """
    This guardrail function runs a specialist agent to check for PII.

    It returns a special output object that tells the Runner whether to
    "trip the wire" and block the main agent's execution.
    """
    print("--- Running PII Detection Guardrail ---")
    # We run our specialist agent to analyze the input.
    result = await Runner.run(pii_guardrail_agent, input, context=ctx.context)

    # The `GuardrailFunctionOutput` is the formal response from the guardrail.
    # The `tripwire_triggered` flag is the critical signal. If it's True,
    # the Runner will raise an exception and stop the process.
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.contains_pii,
    )

# 4. Define the Main Agent with the Guardrail enabled
# This is the agent we want to protect. We "attach" our safety mechanism
# to it by passing the guardrail function into the `input_guardrails` list.
feedback_agent = Agent(
    name="Product Feedback Collector",
    instructions="You are a friendly agent designed to collect feedback about our new product. Summarize the user's feedback.",
    input_guardrails=[pii_detection_guardrail],
)

# 5. Demonstrate the Guardrail in action
async def main():
    """Runs two test cases to show the guardrail passing and tripping."""
    # --- Case 1: Input with NO PII (Guardrail should NOT trip) ---
    # In this case, the guardrail runs, finds no PII, and allows the
    # `feedback_agent` to execute normally.
    safe_feedback = "I really like the new user interface. It feels much more intuitive than the old one. The dark mode is a great addition!"
    print(f"Submitting safe feedback: '{safe_feedback}'\n")
    try:
        result = await Runner.run(feedback_agent, safe_feedback)
        print("\n--- Guardrail Passed ---")
        print(f"Feedback Agent successfully processed the input:\n{result.final_output}")
    except InputGuardrailTripwireTriggered:
        # This block should not be reached in this case.
        print("Guardrail tripped unexpectedly - this should not happen.")

    print("\n" + "="*50 + "\n")

    # --- Case 2: Input WITH PII (Guardrail SHOULD trip) ---
    # Here, the guardrail detects PII and sets its tripwire to True.
    # This causes the Runner to raise an `InputGuardrailTripwireTriggered`
    # exception, PREVENTING the `feedback_agent` from ever running.
    unsafe_feedback = "The app keeps crashing. Please contact me at john.doe@email.com or call me on 555-123-4567 to resolve this."
    print(f"Submitting unsafe feedback: '{unsafe_feedback}'\n")
    try:
        await Runner.run(feedback_agent, unsafe_feedback)
        # This line should not be reached.
        print("Guardrail didn't trip - this is unexpected")
    except InputGuardrailTripwireTriggered as e:
        # Catching the specific exception is the correct way to handle a tripwire.
        print("\n--- PII Guardrail Tripped as Expected! ---")
        print("The main agent was prevented from processing the input.")
        # We can inspect the exception object to get details from the guardrail.
        if e.guardrail_result and e.guardrail_result.output:
            print(f"Reasoning from guardrail: {e.guardrail_result.output.output_info}")

if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())