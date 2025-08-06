# Chapter-11/mcp_filesystem_example.py
"""
Demonstrates an agent connecting to a **language-agnostic tool server** using
MCP.

This script showcases the power of MCP to connect Python agents to tools
written in any language. It uses `npx` to run a pre-built, Node.js-based
filesystem server, and the agent automatically discovers and uses the tools
(like `readFile`, `listFiles`) that the server exposes.

This script shows how to:
1.  Run a non-Python tool server (Node.js) as a managed subprocess.
2.  Use the `async with` pattern for robust server lifecycle management.
3.  Pass the server connection directly into an agent's `tools` list to
    trigger automatic tool discovery.

Prerequisites:
- Requires Node.js and npx to be installed and available in your system's PATH.
"""

import asyncio
import os
import shutil

from agents import Agent, Runner
from agents.mcp import MCPServerStdio


# ------------------------------------------------------------------
# 1. Main Orchestration Logic
# ------------------------------------------------------------------
async def main():
    """
    Launches a Node.js filesystem server and runs an agent that interacts
    with it to answer questions about local files.
    """
    # As a prerequisite, we check that `npx` is available on the system PATH.
    if not shutil.which("npx"):
        raise RuntimeError("❌ npx is not installed. Please install Node.js and npx first.")

    # For security, we define a specific directory that the tool server will
    # have access to. The server will not be able to read or write files
    # outside of this "sandbox".
    current_dir = os.path.dirname(os.path.abspath(__file__))
    samples_dir = os.path.join(current_dir, "sample_files")

    os.makedirs(samples_dir, exist_ok=True)
    # Let's add a sample file for the agent to find.
    with open(os.path.join(samples_dir, "my_favorite_book.txt"), "w") as f:
        f.write("My #1 favorite book is 'Project Hail Mary'.")

    print(f"📦 Server will have access to directory: {samples_dir}")

    # 1. Instantiate and configure the MCPServerStdio.
    #    The `async with` block ensures the server process is started
    #    before the agent uses it and is cleaned up properly afterward.
    print("\n🔌 Starting MCP Filesystem server via npx...")
    async with MCPServerStdio(
        name="FilesystemServer",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", samples_dir],
        },
        client_session_timeout_seconds=30,
    ) as fs_server:
        print("✅ Server started successfully.")

        # 2. Pass the server instance to the agent.
        #    By including the `fs_server` object in the `tools` list, we tell
        #    the agent to connect to it and automatically discover and register
        #    all the tools it provides.
        agent = Agent(
            name="FileSystemAgent",
            instructions=(
                "You are a helpful assistant with access to a file system. "
                "Use the tools provided to read files and answer the "
                "user's questions about their contents."
            ),
            mcp_servers=[fs_server],
        )

        # 3. Run the agent.
        #    The agent will now see tools like `readFile` and `listFiles` from
        #    the server and can decide to use them to fulfill the user's request.
        print("\n⚙️  Running agent workflow...")
        user_query = "What files are available?"
        print(f"👤 User: {user_query}")

        result = await Runner.run(
            starting_agent=agent,
            input=user_query,
        )

        print("\n🤖 Assistant:")
        print(result.final_output)

# ------------------------------------------------------------------
# 2. Entry point
# ------------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(main())