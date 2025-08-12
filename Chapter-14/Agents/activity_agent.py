# agents/activity_agent.py
from agents import Agent
from Tools.github_tool import get_commit_activity, ActivityAnalysis

activity_agent = Agent(
    name="ActivityAgent",
    instructions=(
        "You are an analyst specializing in software development velocity. Your sole purpose is to "
        "check a project's recent commit history and produce a structured analysis."
    ),
    tools=[get_commit_activity],

    # CORRECTED: The agent formally declares its output contract.
    output_type=ActivityAnalysis,
)