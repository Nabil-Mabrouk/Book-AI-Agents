# Chapter-07/tracing_filter_example.py

"""
Demonstrates how to create a **custom trace processor** to filter or
scrub sensitive data from traces before they are exported.

This is a critical pattern for security and compliance (e.g., GDPR, HIPAA)
to prevent sensitive information like PII, API keys, or proprietary data
from being logged or sent to third-party observability platforms.

This script shows how to:
1. Define a tool that notionally handles sensitive data.
2. Create a `DataScrubbingProcessor` by subclassing `BatchTraceProcessor`.
3. Override the `on_span_end` method to implement custom filtering logic.
4. Verify that the final exported trace contains only redacted data.
"""

import asyncio
from agents import Agent, Runner, trace, function_tool
from agents.tracing import (set_trace_processors, Span, SpanData, FunctionSpanData)
from agents.tracing.processors import (BatchTraceProcessor, ConsoleSpanExporter)

# ------------------------------------------------------------------
# 1. The Tool with Sensitive Data
#    This tool simulates an operation that handles sensitive values.
# ------------------------------------------------------------------
@function_tool
def get_user_secret(user_id: str) -> str:
    """A tool that simulates returning a sensitive value for a user."""
    print(f"    🛠️  [Tool] Executing get_user_secret for {user_id}")
    return f"secret-for-{user_id}"

# ------------------------------------------------------------------
# 2. Custom Filtering Processor
#    This class inherits from the standard processor to add custom logic.
# ------------------------------------------------------------------
class DataScrubbingProcessor(BatchTraceProcessor):
    """
    A custom trace processor that scrubs sensitive data from function spans
    before they are exported.
    """
    def on_span_end(self, span: Span[SpanData]) -> None:
        """
        This method is a hook that runs automatically every time a trace
        span is completed. We override it to inspect and modify the span.
        """
        # Check if the completed span is a function call to our sensitive tool.
        if isinstance(span.span_data, FunctionSpanData):
            if span.span_data.name == "get_user_secret":
                print("🛡️  [Scrubber] Detected sensitive function call. Redacting data...")
                # Overwrite the sensitive data on the span object itself.
                # This ensures the original values are never queued for export.
                span.span_data.input = '{"user_id": "REDACTED"}'
                span.span_data.output = "REDACTED"

        # IMPORTANT: Call the parent method to continue the normal processing
        # pipeline with the (now potentially scrubbed) span.
        super().on_span_end(span)

# ------------------------------------------------------------------
# 3. Setup the Custom Tracing Pipeline
# ------------------------------------------------------------------

# 1. Create an exporter to see the final, processed output.
console_exporter = ConsoleSpanExporter()

# 2. Instantiate our custom scrubbing processor, passing it the exporter.
scrubbing_processor = DataScrubbingProcessor(exporter=console_exporter)

# 3. Replace the default processors with our custom one.
set_trace_processors([scrubbing_processor])


# ------------------------------------------------------------------
# 4. Agent and Workflow
# ------------------------------------------------------------------
secret_agent = Agent(
    name="SecretAgent",
    tools=[get_user_secret],
    instructions="Call the get_user_secret tool.",
    model="gpt-4o-mini",
)

async def main():
    """
    Run the agent workflow to demonstrate the data scrubbing in action.
    """
    # Note: Ensure your OPENAI_API_KEY is set in your environment,
    # as the agent's LLM call will still be traced.
    with trace("Data Filtering Example"):
        print("⚙️  Running agent with a tool that returns sensitive data...")
        await Runner.run(secret_agent, "Get the secret for user-123.")

    # Reliably flush the processor to see the final, scrubbed output
    # printed to the console by the ConsoleSpanExporter.
    print("\n⚙️  Flushing traces...")
    scrubbing_processor.force_flush()
    print("🏁 Done.")
    print("\n✅ Notice the final span output in your console is redacted,")
    print("   even though the tool itself ran with the original data.")

# ------------------------------------------------------------------
# 5. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())