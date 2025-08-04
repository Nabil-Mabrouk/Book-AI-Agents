# Chapter-03/order_agent.py
"""
An advanced agent example demonstrating the use of tools.

This script defines a tool `get_order_status` that an AI agent can use
to answer user questions about e-commerce orders. It showcases how to:
1.  Define a structured output for a tool using Pydantic.
2.  Create a tool using a decorator (`@function_tool`).
3.  Equip an agent with the tool to solve a specific task.
"""
import asyncio
import os
import random
from datetime import date, timedelta

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agents import Agent, Runner, function_tool, trace


# 1. Define the Tool's Output Structure with Pydantic
# By defining a Pydantic model, we tell the agent exactly what kind of
# structured data to expect from the tool. This improves reliability.
class OrderStatus(BaseModel):
    """A data structure to hold the details of an order's status."""

    order_number: str = Field(
        description="The unique identifier for the order."
    )
    status: str = Field(
        description="The current status of the order (e.g., 'Processing', 'Shipped')."
    )
    estimated_delivery_date: date = Field(
        description="The estimated date of arrival."
    )


# 2. Define the Tool with the @function_tool Decorator
# The decorator automatically converts this Python function into a format
# that the AI model can understand and decide to use.
@function_tool
def get_order_status(order_number: str) -> OrderStatus:
    """
    Looks up and returns the status of a specific e-commerce order.

    The agent will use this function when a user asks for the status
    of their order and provides an order number.

    Args:
        order_number: The unique number of the order to look up.

    Returns:
        An object containing the order status and delivery details.
    """
    # This log is for us, the developers, to see when the tool is
    # actually executed by the agent during its run.
    print(f"🛠️ [Tool Call] Looking up order status for {order_number}...")

    # In a real application, this section would contain logic to call a
    # database or an external API. Here, we simulate that process by
    # returning random, plausible data for demonstration purposes.
    statuses = ["Processing", "Shipped", "Out for Delivery", "Delivered"]
    simulated_status = random.choice(statuses)
    delivery_date = date.today() + timedelta(days=random.randint(1, 7))

    return OrderStatus(
        order_number=order_number,
        status=simulated_status,
        estimated_delivery_date=delivery_date
    )


# 3. Define the Agent and Give It the Tool
# The key step is passing the `get_order_status` function in the `tools` list.
# This makes the agent "aware" of the tool and capable of using it.
order_assistant_agent = Agent(
    name="OrderAssistant",
    instructions=(
        "You are a friendly customer service assistant. Use the "
        "get_order_status tool to help users with their order inquiries. "
        "Be sure to provide the status and the estimated delivery date."
    ),
    tools=[get_order_status],
    model="gpt-4o-mini",
)


async def main():
    """
    The main function to run our order assistant agent.
    """
    # Load the OPENAI_API_KEY from the .env file for secure key management.
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set. Please add it to your .env file.")
        return

    # This is the user's request that will trigger the agent's tool use.
    user_query = "Hi, where is my order? The number is GHI-456-789."
    print(f"👤 User: {user_query}")

    # Using a `trace` block is a helpful debugging and visualization feature.
    # It allows us to see the agent's entire thought process, including
    # its decision to call a tool and the data it received back.
    with trace("Order Agent Workflow"):
        result = await Runner.run(order_assistant_agent, user_query)

    # The final output is a user-friendly summary crafted by the agent
    # after it has successfully used the tool and analyzed the results.
    print(f"🤖 Assistant: {result.final_output}")


if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())