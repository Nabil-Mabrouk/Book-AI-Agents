# tools/file_writer_tool.py
import os
from datetime import datetime
from agents import function_tool
from slugify import slugify # Import the slugify function

# Define the output directory relative to this file's location
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'output')

@function_tool
def save_report(topic: str, content: str) -> str:
    """
    Saves a report to a file with a standardized, timestamped name in the 'output' directory.
    The filename is automatically generated from the topic.

    Args:
        topic: The main topic or title of the report. This will be used to create the filename.
        content: The full markdown content of the report to be saved.
    """
    try:
        # 1. Ensure the output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # 2. Generate the dynamic filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        topic_slug = slugify(topic)
        filename = f"{timestamp}_{topic_slug}.md"
        
        # 3. Define the full path
        filepath = os.path.join(OUTPUT_DIR, filename)

        print(f"🛠️  [Tool Call] Saving report to: '{filepath}'...")
        
        # 4. Write the content to the file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"Successfully saved report to the 'output' directory as '{filename}'."
    except Exception as e:
        return f"Error: Failed to save the report. Reason: {e}"