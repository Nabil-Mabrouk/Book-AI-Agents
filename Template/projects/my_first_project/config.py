# projects/my_first_project/config.py
"""
This is the "control panel" for your project. It defines your team of
specialist agents and the main TriageAgent that orchestrates them.
It exports a single AGENTS dictionary that the main application can use.
"""
from agents import Agent, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from tools.local_tools import get_weather

# --- 1. DEFINE SPECIALIST AGENTS ---
math_agent = Agent(
    name="MathAgent",
    handoff_description="An expert in mathematics for calculations and concepts.",
    instructions="You are a math genius. Answer the user's question clearly.",
    model="gpt-4-turbo",
)

weather_agent = Agent(
    name="WeatherAgent",
    handoff_description="Can provide up-to-date weather forecasts for any city.",
    instructions="You are a weather specialist. Use the get_weather tool.",
    tools=[get_weather],
    model="gpt-4o-mini",
)

# <-- TODO: Add your other specialist agents here.

# --- 2. DEFINE THE TRIAGE (ORCHESTRATOR) AGENT ---
triage_agent = Agent(
    name="TriageAgent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a master triage agent. Analyze the user's request and delegate
    it to the most appropriate specialist from your team. Do not answer yourself.
    """,
    handoffs=[
        handoff(math_agent),
        handoff(weather_agent),
        # <-- TODO: Add other specialists to the handoff list.
    ],
    model="gpt-4o-mini",
)

# --- 3. EXPORT THE AGENT REGISTRY ---
# This is the single, consistent entry point for the main application.
# The 'triage' key should point to the primary agent that starts the workflow.
AGENTS = {
    "triage": triage_agent,
    # You can also add other agents here if the orchestrator needs to
    # access them by name for more complex workflows.
    "math": math_agent,
    "weather": weather_agent,
}