# projects/my_first_project/graph_definition.py
"""
This file defines the actual workflow for your project by creating
node actions and connecting them into a graph.
"""
from system.graph import GraphNode, WorkflowState
from agents import Runner, Agent

# --- NODE ACTIONS ---
# These functions are now "factories" that take the agent registry
# and return the actual async action function. This pattern cleanly
# gives the actions access to the agents they need without globals.

def create_triage_action(agents: dict[str, Agent]):
    async def triage_action(state: WorkflowState) -> WorkflowState:
        """Uses the TriageAgent to classify the user's intent."""
        result = await Runner.run(agents["TriageAgent"], state.initial_input)
        state.next_node = result.final_output.strip().upper()
        return state
    return triage_action

def create_weather_action(agents: dict[str, Agent]):
    async def weather_action(state: WorkflowState) -> WorkflowState:
        """This node is activated for weather-related queries."""
        result = await Runner.run(agents["WeatherAgent"], state.initial_input)
        state.final_answer = result.final_output
        return state
    return weather_action

def create_math_action(agents: dict[str, Agent]):
    async def math_action(state: WorkflowState) -> WorkflowState:
        """This node is activated for math-related queries."""
        result = await Runner.run(agents["MathAgent"], state.initial_input)
        state.final_answer = result.final_output
        return state
    return math_action

def create_general_action(agents: dict[str, Agent]):
    async def general_action(state: WorkflowState) -> WorkflowState:
        """A fallback node for general conversation."""
        # This node doesn't need an agent, but we keep the pattern consistent.
        state.final_answer = "I can only help with math or weather questions right now."
        return state
    return general_action


# --- GRAPH ASSEMBLY ---
# This function now ACCEPTS the agents registry and wires everything up.
def define_graph(graph_runner, agents: dict[str, Agent]):
    """Assembles the complete workflow graph using the provided agents."""
    
    # 1. Create all nodes by calling the action factories
    nodes = [
        GraphNode(name="Triage", action=create_triage_action(agents)),
        GraphNode(name="GetWeather", action=create_weather_action(agents)),
        GraphNode(name="DoMath", action=create_math_action(agents)),
        GraphNode(name="GeneralResponse", action=create_general_action(agents)),
    ]
    for node in nodes:
        graph_runner.add_node(node)

    # 2. Define all edges
    graph_runner.set_entry_point("Triage")
    graph_runner.add_conditional_edge(
        start_node="Triage",
        path_map={
            "WEATHER": "GetWeather",
            "MATH": "DoMath",
            "GENERAL": "GeneralResponse"
        }
    )