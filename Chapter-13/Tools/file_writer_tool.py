# Tools/file_writer_tool.py
import os
from datetime import datetime
from agents import function_tool
from slugify import slugify

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')

@function_tool
def save_report(topic: str, content: str) -> str:
    """
    Saves a report to a file with a standardized, timestamped name in the 'output' directory.
    The filename is automatically generated from the report's topic.
    """
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        topic_slug = slugify(topic)
        filename = f"{timestamp}_{topic_slug}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)

        print(f"🛠️  [Tool Call] Saving report to: '{filepath}'...")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully saved report to the 'output' directory as '{filename}'."
    except Exception as e:
        return f"Error: Failed to save the report. Reason: {e}"