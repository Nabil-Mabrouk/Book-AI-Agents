# agents/writer_agent.py
from agents import Agent
from Tools.file_writer_tool import save_report # Import our new, smarter tool

writer_agent = Agent(
    name="WriterAgent",
    
    instructions=(
        "You are an expert report writer. Your primary goal is to synthesize the "
        "provided research findings into a clear, concise, and well-structured "
        "report in markdown format. The user's original query will serve as the topic."
        "\n\n"
        "**CRITICAL INSTRUCTIONS:**"
        "\n1. First, formulate the complete markdown content of the report."
        "\n2. Once the report is composed, you **MUST** call the `save_report` tool."
        "\n3. You must pass the **original query topic** to the `topic` parameter and the **full markdown report** to the `content` parameter of the tool."
        "\n4. Your final output to the user should be the confirmation message returned by the tool."
    ),
    
    # Give the writer the new tool.
    tools=[save_report],
    
    model="gpt-4o-mini",
)