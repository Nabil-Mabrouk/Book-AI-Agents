# Agents/writer_agent.py
from agents import Agent
from Tools.file_writer_tool import save_report

writer_agent = Agent(
    name="WriterAgent",
    instructions=(
        "You are an expert technical writer. You will be given a user's original query and a block of text containing summaries of research papers. "
        "Each paper summary will include a title, a summary, and its publication date."
        "\n\n"
        "**CRITICAL INSTRUCTIONS:**"
        "\n1. Synthesize the provided information into a single, coherent report in markdown format."
        "\n2. For each paper you discuss, you **MUST** mention its publication date in your summary."
        "\n3. Once the report is composed, call the `save_report` tool to save it."
        "\n4. Use the original user query as the `topic` for the report."
        "\n5. Your final response should be the confirmation message returned by the tool."
    ),
    tools=[save_report],
    model="gpt-4o-mini",
)