# Chapter-07/tracing_console_example.py

"""
Demonstrates how to configure a **custom tracing pipeline** to view agent
traces directly in your console.

This is useful for local development and debugging, as it allows you to
inspect the full lifecycle of an agent run (LLM calls, tool executions, etc.)
without needing to set up an external observability dashboard.

This script shows how to:
1. Create a `ConsoleSpanExporter` to direct trace data to the console.
2. Use a `BatchTraceProcessor` to efficiently handle trace data.
3. Replace the default tracing setup using `set_trace_processors`.
"""

import asyncio
from agents import Agent, Runner, trace
from agents.tracing import (
    set_trace_processors,
)
from agents.tracing.processors import (
    ConsoleSpanExporter,
    BatchTraceProcessor,
)

# ------------------------------------------------------------------
# 1. Setup the Custom Tracing Pipeline
#    This must be done once, at the start of your application,
#    *before* any agent work begins.
# ------------------------------------------------------------------

# The exporter is the final destination for trace data. In this case, it's
# simply the standard console output.
console_exporter = ConsoleSpanExporter()

# The processor receives trace data (spans) from the application, batches
# them together for efficiency, and sends them to the configured exporter.
console_processor = BatchTraceProcessor(console_exporter)

# By default, the framework may have other trace processors enabled (e.g.,
# for sending data to an external dashboard). This call replaces them all
# with our custom console-only setup.
set_trace_processors([console_processor])


# ------------------------------------------------------------------
# 2. Agent Definition
#    This can be any agent; the tracing setup is independent of the
#    agent's specific logic.
# ------------------------------------------------------------------
math_agent = Agent(
    name="MathAgent",
    instructions="You are a math expert.",
    model="gpt-4o-mini",
)


# ------------------------------------------------------------------
# 3. Orchestration + Flushing
# ------------------------------------------------------------------
async def main():
    """
    Run a simple agent workflow to generate trace data and ensure it's
    flushed to the console for inspection.
    """
    # Now, any code executed within a `trace()` block will have its
    # trace data captured by the console processor we configured.
    with trace("Console Trace Example"):
        print("⚙️  Running agent to generate trace data...")
        result = await Runner.run(math_agent, "What is 2 + 2?")
        print(f"✨ Agent Result: {result.final_output}")

    # The BatchTraceProcessor sends data in the background. For a short-lived
    # script like this one, we must explicitly tell it to send any pending
    # traces before the program exits. In a long-running server application,
    # this would happen automatically.
    print("\n⚙️  Flushing traces to console...")
    console_processor.force_flush()
    print("🏁 Done. Trace details should be visible above.")


# ------------------------------------------------------------------
# 4. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())