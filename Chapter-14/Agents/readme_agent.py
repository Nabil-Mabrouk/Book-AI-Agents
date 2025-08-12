# agents/readme_agent.py
# agents/readme_agent.py
from agents import Agent
from Tools.github_tool import read_readme_from_url, ReadmeAnalysis

readme_agent = Agent(
    name="ReadmeAgent",
    instructions=(
        "You are a senior technical writer and documentation expert. You will be given a direct API URL to a README file's content. Your jobs are:"
        "\n1. Call the `read_readme_from_url` tool to get the text content."
        "\n2. Based on the content, critically evaluate the README's quality. Score it on clarity and completeness."
        "\n3. Provide a final, structured `ReadmeAnalysis` object."
    ),
    tools=[read_readme_from_url],
    output_type=ReadmeAnalysis,
)