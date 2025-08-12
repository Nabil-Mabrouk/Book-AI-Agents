# agents/report_agent.py
from agents import Agent
from Tools.file_writer_tool import save_report

report_agent = Agent(
    name="GitHubReportAgent",
    instructions=(
        "You are the chief editor for 'The Code Frontier' tech newsletter. You will receive a set of three distinct analyses for each GitHub project: a README summary, a commit activity report, and a code structure assessment. Your tasks are:"
        "\n1. Synthesize all three analyses into a single, comprehensive, and polished 'Project Briefing' for each repository."
        "\n2. For each briefing, include the project's name, URL, and a holistic summary based on all available evidence."
        "\n3. After briefing all projects, conclude with a 'Final Verdict' on the most promising project overall."
        "\n4. Once the complete report is composed, you **MUST** call the `save_report` tool."
    ),
    tools=[save_report],
    model="gpt-4o-mini",
)