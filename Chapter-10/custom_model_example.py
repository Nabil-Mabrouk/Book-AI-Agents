# Chapter-10/custom_model_example.py
"""
Demonstrates how to configure and use a **custom LLM** from a provider
other than the default (OpenAI), using the `LitellmModel` adapter.

This pattern provides immense flexibility, allowing developers to choose the
best model for their task based on cost, performance, or specific capabilities,
leveraging the vast ecosystem supported by the LiteLLM library.

This script shows how to:
1. Import the `LitellmModel` class.
2. Instantiate `LitellmModel` to configure a specific model (Anthropic's Claude 3 Haiku).
3. Pass the custom model instance to an `Agent` during its definition.
4. Use the appropriate API key for the chosen model provider.
"""

import asyncio
import os
from dotenv import load_dotenv
from agents import Agent, Runner
from agents.models import LitellmModel # Import the LitellmModel class

# ------------------------------------------------------------------
# 1. Custom Model Configuration and Agent Execution
# ------------------------------------------------------------------
async def main():
    """
    Defines and runs an agent that uses a custom-configured model
    (Anthropic's Claude 3 Haiku) instead of the default.
    """
    load_dotenv()
    # Note: We check for the API key corresponding to the model provider
    # we intend to use. For Claude, this is `ANTHROPIC_API_KEY`.
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌  Error: ANTHROPIC_API_KEY not set in .env file.")
        return

    # --- 1. Configure the Custom Model ---
    # Instead of letting the agent use the default, we instantiate LitellmModel.
    # This class acts as a bridge to the hundreds of models supported by the
    # LiteLLM library. We just need to provide the model string.
    claude_model = LitellmModel(model="claude-3-haiku-20240307")
    print(f"🔄  Model configured: {claude_model.model}")

    # --- 2. Define the Agent with the Custom Model ---
    # We then pass this model instance to our agent during definition using
    # the `model` parameter.
    custom_model_agent = Agent(
        name="CustomModelAgent",
        instructions=(
            "You are a helpful assistant powered by a custom model. "
            "Please introduce yourself as such."
        ),
        # The agent will now use our specified Claude model for all its LLM calls.
        model=claude_model,
    )

    # --- 3. Run the Agent ---
    user_query = "Who are you?"
    print(f"👤 User: {user_query}")

    result = await Runner.run(agent=custom_model_agent, input=user_query)

    # Note: The result object's structure can vary. While many examples use
    # `result.final_output`, the correct attribute might be `result.output` or
    # another field. Always inspect the result object to find the agent's response.
    print(f"🤖 Assistant: {result.output}")

# ------------------------------------------------------------------
# 2. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())