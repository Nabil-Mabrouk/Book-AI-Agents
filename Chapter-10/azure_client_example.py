# Chapter-10/azure_client_example.py
"""
Demonstrates how to configure an agent to use an **Azure OpenAI Service**
deployment instead of the default public OpenAI API.

This is the standard pattern for enterprise use cases or for developers who
host their models on Microsoft Azure.

This script shows how to:
1. Import and instantiate the `AzureOpenAI` client from the `openai` library.
2. Configure the client with Azure-specific credentials (endpoint, API key, version).
3. Pass the pre-configured client to an `OpenAIModel` instance.
4. Specify the Azure "deployment name" for the model.
"""

import asyncio
import os
from dotenv import load_dotenv
from openai import AzureOpenAI  # Import the AzureOpenAI client
from agents import Agent, Runner
from agents.models import OpenAIModel

# ------------------------------------------------------------------
# 1. Azure Client Configuration and Agent Execution
# ------------------------------------------------------------------
async def main():
    """
    Defines and runs an agent that uses a custom-configured Azure
    OpenAI client.
    """
    load_dotenv()

    # --- 1. Load Azure-specific credentials from your .env file ---
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = "2024-02-01"  # Use the API version required by your deployment

    if not all([azure_endpoint, api_key]):
        print("❌  Error: AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY must be set in .env file.")
        return

    # --- 2. Create a pre-configured AzureOpenAI client instance ---
    # This client object is tailored to communicate with your specific
    # Azure OpenAI resource.
    print(f"🔄  Initializing Azure client for endpoint: {azure_endpoint}")
    azure_client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    # --- 3. Define the Model with the Custom Client ---
    # When defining the model for the agent, we pass our custom client.
    # Crucially, the `model` parameter must match your Azure "deployment name".
    azure_model = OpenAIModel(
        model="your-azure-deployment-name",  # e.g., "gpt-4o", "gpt-35-turbo"
        client=azure_client,
    )

    # --- 4. Define the Agent ---
    azure_agent = Agent(
        name="AzureAgent",
        instructions="You are an assistant running on Azure.",
        model=azure_model,
    )

    # --- 5. Run the Agent ---
    print("⚙️  Running agent on Azure...")
    result = await Runner.run(azure_agent, "How are you running?")
    print(f"🤖 Assistant: {result.output}")


# ------------------------------------------------------------------
# 2. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())