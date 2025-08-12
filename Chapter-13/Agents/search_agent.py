# Agents/search_agent.py
from agents import Agent
from Tools.arxiv_tool import search_arxiv

search_agent = Agent(
    name="SearchAgent",
    instructions="You are a helpful research assistant. Your sole purpose is to call the `search_arxiv` tool with the user's query.",
    tools=[search_arxiv],
)