"""
Minimal Hello World MCP Server Example

To test this server, use prompts like:
- "test MCP"
- "say hello"
- "are you working?"
"""

#region imports
import asyncio  # For async/await functionality

# Required imports for MCP server functionality
import mcp.server.stdio
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
#endregion


#region variables
# Create a new MCP server instance with a name
server = Server("helloworld_server")
#endregion

#region MCP functions
## Define what tools are available to the LLM
@server.list_tools()
async def list_tools():
    # Return a list of available tools
    return [
        Tool(
            # Tool identifier; what it does. This is used by the LLM to find/call the tool.
            name="say_hello",
            description=(
                "Says hello to demonstrate MCP is working."
                "Use when user wants to test the connection or asks for a greeting."
                "Example: 'test MCP', 'say hello', 'are you working?'"
            ),
            # Define expected input parameters
            inputSchema={
                "type": "object",  # No properties needed
                "properties": {},
                "required": [],  # No required parameters
            },
        )
    ]

## Handle tool execution requests from the LLM
@server.call_tool()
async def call_tool(name, arguments):
    # Check which tool was requested
    if name == "say_hello":
        # Return the hello world message
        return [TextContent(type="text", text="Hello World! MCP server is working!")]
    # Return error if unknown tool requested
    return [TextContent(type="text", text=f"Unknown tool: {name}")]
#endregion

#region functions
## Main entry point
async def main():
    # Use the stdio_server context manager to get read/write streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # Run the server with streams and initialization options as positional arguments
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="helloworld_server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            ),
        )

# Run the server when script is executed directly
if __name__ == "__main__":
    asyncio.run(main())
#endregion