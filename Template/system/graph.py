# system/graph.py
"""
Contains the generic, reusable engine for executing workflows defined as
a graph of nodes and edges.
"""
import asyncio
from typing import Any, Dict, Callable, Coroutine
from rich.console import Console

from agents import Agent, Runner

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

    async def run(self, initial_input: Any) -> WorkflowState:
        """Runs the graph from the entry point until a terminal node is reached."""
        if not self.entry_point:
            raise ValueError("Graph entry point not set.")

        state = WorkflowState(initial_input=initial_input, history=[])
        current_node_name = self.entry_point

        while current_node_name != self.finish_point:
            self.console.print(f"\n[bold magenta]Entering Node:[/bold magenta] {current_node_name}")
            node = self.nodes.get(current_node_name)
            if not node:
                raise ValueError(f"Node '{current_node_name}' not found in graph.")

            state.history.append(current_node_name)
            state = await node.execute(state) # Execute the node's logic

            if current_node_name not in self.edges:
                break # Reached a terminal node with no defined exit path

            router = self.edges[current_node_name]
            current_node_name = router(state)

        self.console.print("\n[bold green]✅ Workflow Finished.[/bold green]")
        return state