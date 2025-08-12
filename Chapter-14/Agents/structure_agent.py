# agents/structure_agent.py
from agents import Agent
from Tools.github_tool import get_project_structure, StructureAnalysis

structure_agent = Agent(
    name="StructureAgent",
    instructions=(
        "You are an analyst specializing in software architecture. Your sole purpose is to "
        "examine a project's file structure and produce a structured analysis of its maturity."
    ),
    tools=[get_project_structure],

    # CORRECTED: The agent formally declares its output contract.
    output_type=StructureAnalysis,
)