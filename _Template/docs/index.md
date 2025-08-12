# The Definitive Blueprint for Professional Agentic Systems**

You have mastered the fundamental patterns of agentic design. Now, we will forge them into a single, unified architecture. This is not just a template; it is a professional, scalable **engine** for building any agentic system you can imagine.

The core philosophy of this blueprint is the **separation of concerns**. We strategically divide our system into three parts: the **Core Engine**, the project-specific **Configuration and Workflow**, and a lean **Main Entrypoint**.

This chapter will present the complete blueprint, fully annotated, and demonstrate how it elegantly handles local context, conversational memory, tool use, and complex multi-agent orchestration.

---

## Blueprint File Structure

This is the recommended directory structure for any new agentic project. It is designed for clarity, reusability, and scalability.

```
your_agentic_project/
├── .env
├── main.py                     # The main entrypoint to run a specific project
|
├── system/                     # The Core Engine (Stable & Reusable)
│   ├── __init__.py
│   └── graph.py                # The graph-based workflow execution engine
|
├── projects/                   # Contains all your project implementations
│   ├── __init__.py
│   └── my_first_project/
│       ├── __init__.py
│       ├── config.py           # Defines agents, tools, and context for this project
│       └── graph_definition.py # Defines the NODES and EDGES of the workflow
|
└── tools/                      # A shared library of all available, reusable tools
    └── __init__.py
    └── shared_tools.py
```

---

## Part 1: The Core Engine (`system/`)

This is the heart of the blueprint. You will copy this `system` directory into every new repository, but you will rarely need to modify its code. It provides the generic machinery for running any workflow you design.

**File: `system/graph.py`**
```python
# system/graph.py
"""
Contains the generic, reusable engine for executing workflows defined as
a graph of nodes and edges.
"""
import asyncio
from typing import Any, Dict, Callable, Coroutine
from rich.console import Console

from agents import Agent, Runner, BaseSession

class WorkflowState(dict):
    """
    A dictionary-like object that holds the current state of the workflow.
    It's passed between nodes, allowing agents to share information.
    The use of __dict__ allows for attribute-style access (e.g., state.result).
    """
    def __init__(self, *args, **kwargs):
        super(WorkflowState, self).__init__(*args, **kwargs)
        self.__dict__ = self

class GraphNode:
    """Represents a single agent or function as a node in the workflow graph."""
    def __init__(self, name: str, action: Callable[[WorkflowState], Coroutine]):
        self.name = name
        self.action = action

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Executes the node's action with the current state."""
        return await self.action(state)

class GraphRunner:
    """Executes a workflow defined as a graph of nodes and conditional edges."""
    def __init__(self, console: Console):
        self.console = console
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, Callable[[WorkflowState], str]] = {}
        self.entry_point: str | None = None
        self.finish_point = "FINISH" # A special node name to end the workflow

    def add_node(self, node: GraphNode):
        """Adds a processing step (e.g., an agent) to the graph."""
        self.nodes[node.name] = node

    def set_entry_point(self, node_name: str):
        """Sets the starting node of the graph."""
        self.entry_point = node_name

    def add_edge(self, start_node: str, end_node: str):
        """Adds a direct, unconditional link from one node to another."""
        self.edges[start_node] = lambda state: end_node

    def add_conditional_edge(self, start_node: str, path_map: Dict[str, str]):
        """

        Adds a conditional handoff based on the workflow state.
        A router function reads `state.next_node` (which must be set by the
        `start_node`'s action) and uses `path_map` to determine the next step.
        """
        def router(state: WorkflowState) -> str:
            next_node_key = state.get("next_node", self.finish_point)
            return path_map.get(next_node_key, self.finish_point)
        self.edges[start_node] = router

    async def run(self, initial_input: Any, session: BaseSession | None = None, context: Any | None = None) -> WorkflowState:
        """Runs the graph from the entry point until a terminal node is reached."""
        if not self.entry_point:
            raise ValueError("Graph entry point not set.")

        state = WorkflowState(initial_input=initial_input, history=[], session=session, context=context)
        current_node_name = self.entry_point

        while current_node_name != self.finish_point:
            self.console.print(f"\n[bold magenta]Entering Node:[/bold magenta] {current_node_name}")
            node = self.nodes.get(current_node_name)
            if not node:
                raise ValueError(f"Node '{current_node_name}' not found in graph.")

            state.history.append(current_node_name)
            state = await node.execute(state) # Execute the node's logic

            if current_node_name not in self.edges:
                break # Reached a terminal node

            router = self.edges[current_node_name]
            current_node_name = router(state)

        self.console.print("\n[bold green]✅ Workflow Finished.[/bold green]")
        return state
```

---

## Part 2: A Project Implementation (`projects/my_first_project/`)

This is where you define the specific "what" of your application. Notice how local context and session management are now first-class citizens of the configuration.

**File: `tools/shared_tools.py`**
```python
# tools/shared_tools.py
from agents import function_tool, RunContextWrapper
from pydantic import BaseModel, Field

# --- Define Pydantic models for context and tool inputs ---
class LocalContext(BaseModel):
    """Private data for your Python code, unseen by the LLM."""
    user_id: str
    permissions_level: str

class DashboardParams(BaseModel):
    """Input model for the get_user_dashboard tool."""
    reason_for_request: str = Field(description="The user's stated reason for needing the dashboard link.")

# --- Define a reusable tool that requires local context ---
@function_tool(param_model=DashboardParams)
def get_user_dashboard(wrapper: RunContextWrapper[LocalContext], reason_for_request: str) -> str:
    """Fetches a dashboard URL, behavior changes based on user permissions in local context."""
    user_id = wrapper.context.user_id
    permissions = wrapper.context.permissions_level
    print(f"🛠️  [Tool Call] Fetching dashboard for user '{user_id}' (Permissions: {permissions})")
    
    if permissions == "admin":
        return f"Admin Dashboard: https://company.com/admin?user={user_id}"
    else:
        return f"User Dashboard: https://company.com/user?user={user_id}"

```

**File: `projects/my_first_project/config.py`**

```python
# projects/my_first_project/config.py
"""
This is the "control panel" for your project. It defines all the
component parts (agents, tools, context) that your workflow can use.
"""
from agents import Agent, SQLiteSession
from tools.shared_tools import get_user_dashboard, LocalContext

# --- CONTEXT & SESSION CONFIGURATION ---
# Define the structure and initial values for your private local context.
# This data will be passed to tools that need it.
CONTEXT = LocalContext(user_id="u-admin-777", permissions_level="admin")

# Define the session for conversational memory.
# The session ID determines which conversation history to load.
SESSION = SQLiteSession(session_id="project-1-conversation")

# --- AGENT REGISTRY ---
# Define all the specialist agents your system might need.
AGENTS = {
    "DashboardAgent": Agent(
        name="DashboardAgent",
        instructions="You are a helpful assistant. If the user asks for their dashboard, use the get_user_dashboard tool.",
        tools=[get_user_dashboard],
        model="gpt-4o-mini",
    ),
    # Add other agents here for more complex workflows
}
```

**File: `projects/my_first_project/graph_definition.py`**
```python
# projects/my_first_project/graph_definition.py
"""
This file defines the workflow graph for your project.
"""
from system.graph import GraphNode, WorkflowState
from agents import Runner, Agent

# --- NODE ACTIONS ---
def create_primary_action(agents: dict[str, Agent]):
    async def primary_action(state: WorkflowState) -> WorkflowState:
        """The main action for this simple workflow."""
        result = await Runner.run(
            agent=agents["DashboardAgent"],
            user_input=state.initial_input,
            session=state.session, # Pass the session for memory
            context=state.context, # Pass the local context for tools
        )
        state.final_answer = result.final_output
        return state
    return primary_action

# --- GRAPH ASSEMBLY ---
def define_graph(graph_runner, agents: dict[str, Agent]):
    """Assembles the complete workflow graph."""
    
    # 1. Create all nodes
    graph_runner.add_node(GraphNode(name="PrimaryAction", action=create_primary_action(agents)))

    # 2. Define the entry point. This is a simple, single-step graph.
    graph_runner.set_entry_point("PrimaryAction")
```

---

### **Part 3: The Main Entrypoint (`main.py`)**

The main script remains lean. It loads the configuration and tells the graph engine to run, now passing in the session and context objects.

**File: `main.py`**
```python
# main.py
import asyncio
import os
from dotenv import load_dotenv
from rich.console import Console

from system.graph import GraphRunner

# --- SELECT THE PROJECT TO RUN ---
from projects.my_first_project.config import AGENTS, SESSION, CONTEXT
from projects.my_first_project.graph_definition import define_graph

async def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set.")
        return

    console = Console()
    
    # 1. Create the Graph Runner engine
    graph_runner = GraphRunner(console)

    # 2. Let the project-specific file define the graph structure
    define_graph(graph_runner, AGENTS)
        
    # 3. Get user input and run the graph, passing in the configured session and context
    console.print(f"[grey50]Using Session ID: {SESSION.session_id}[/grey50]")
    console.print(f"[grey50]Running as User: {CONTEXT.user_id} (Permissions: {CONTEXT.permissions_level})[/grey50]")
    
    user_query = console.input("[bold yellow]Ask your agent (e.g., 'what is my dashboard link?'): [/bold yellow]").strip()
    if user_query:
        final_state = await graph_runner.run(
            initial_input=user_query,
            session=SESSION,
            context=CONTEXT,
        )
        console.print("\n[bold cyan]Final Answer:[/bold cyan]")
        console.print(final_state.get("final_answer", "No final answer was produced."))

if __name__ == "__main__":
    asyncio.run(main())
```

### **How This Blueprint Handles State and Memory**

This architecture seamlessly integrates context and memory management:

1.  **Centralized Configuration:** The `config.py` file is the single source of truth. It defines not just the agents and tools, but also the session ID for conversational memory and the data for local context. This makes it easy to see and manage the state of your application.
2.  **Explicit Passing:** The `main.py` explicitly loads `SESSION` and `CONTEXT` from the config and passes them to the `GraphRunner`.
3.  **State Propagation:** The `GraphRunner` adds the session and context objects to the `WorkflowState`. This makes them available to *every single node* in the graph automatically.
4.  **Clean Node Actions:** The node action functions (`primary_action`) have a clean signature. They receive the state object, which contains everything they need (`state.session`, `state.context`), and they pass it directly to the `Runner.run` call, which in turn makes the context available to the tools.

This design is incredibly robust. You can now build complex, multi-step, multi-agent workflows that have both long-term conversational memory and access to secure, private application data, all within a clean, maintainable, and scalable architecture.