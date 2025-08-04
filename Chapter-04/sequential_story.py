# Chapter-04/sequential_story.py
"""
An example of a sequential multi-agent workflow.

This script demonstrates how to chain two agents together to perform a
multi-step task. The first agent creates a plot outline, and its
structured output becomes the direct input for the second agent, which
writes a full story. This pattern is powerful for breaking down complex
problems into a series of specialized tasks.
"""
import asyncio
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agents import Agent, Runner, trace


# --- Pydantic Models for Structured I/O ---
# By defining the output for each agent, we create a reliable "contract"
# between them. This ensures the data passed from one agent to the next
# is always in the expected format.

class StoryOutline(BaseModel):
    """Defines the structured output for the OutlineAgent."""
    outline: str = Field(
        description="A single-sentence plot outline for a story."
    )

class FinalStory(BaseModel):
    """Defines the structured output for the WriterAgent."""
    story: str = Field(
        description="The full text of the short story."
    )


# --- Agent Definitions ---

# Agent 1: The specialist for creating outlines.
# This agent's only job is to generate a creative, high-level plot idea.
# We enforce its output structure by setting `output_type=StoryOutline`.
outline_agent = Agent(
    name="OutlineAgent",
    instructions=(
        "You are a creative expert in plot development. Generate a concise, "
        "one-sentence story outline based on the user's topic."
    ),
    output_type=StoryOutline,
    model="gpt-4o-mini",
)

# Agent 2: The specialist for writing stories.
# This agent takes the outline from the first agent and expands it into a
# full narrative. Its focus is on prose and storytelling, not idea generation.
writer_agent = Agent(
    name="WriterAgent",
    instructions=(
        "You are a talented author. Write a short, engaging story based on "
        "the provided plot outline. The story should be no more than "
        "three paragraphs."
    ),
    output_type=FinalStory,
    model="gpt-4o-mini",
)


async def main():
    """Orchestrates the two-step sequential agent workflow."""
    # Load the OPENAI_API_KEY from the .env file for secure key management.
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set.")
        return

    user_topic = "A detective who is afraid of the dark."
    print(f"👤 User Topic: {user_topic}\n")

    # The trace block provides a visual log of the entire multi-agent
    # process, making it easy to see how data flows from one agent to the next.
    with trace("Sequential Story Workflow"):
        # --- Step 1: Run the Outline Agent ---
        # The first stage of our pipeline is to generate the plot outline.
        print("Step 1: Generating plot outline...")
        outline_result = await Runner.run(outline_agent, user_topic)

        # Extract the structured output. Using `.final_output_as(StoryOutline)`
        # is crucial because it validates the AI's output and parses it
        # directly into the Pydantic model we defined.
        generated_outline = outline_result.final_output_as(StoryOutline)
        print(f"✅ Generated Outline: '{generated_outline.outline}'\n")

        # --- Step 2: Run the Writer Agent ---
        # The second stage of the pipeline begins here.
        print("Step 2: Writing the story based on the outline...")

        # The output of the first agent (`generated_outline.outline`) becomes
        # the direct input for the second. This handoff is the core of the
        # sequential pattern, creating a chain of specialized work.
        story_result = await Runner.run(writer_agent, generated_outline.outline)

        # We extract the final structured output from the writer agent.
        final_story = story_result.final_output_as(FinalStory)
        print("\n--- 📖 Final Story ---")
        print(final_story.story)


if __name__ == "__main__":
    # Standard entry point to run the async main function of the script.
    asyncio.run(main())