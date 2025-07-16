"""
Minimal Hello World MCP Server Example (FastMCP)

To test this server, use prompts like:
- "test MCP"
- "say hello"
- "are you working?"
"""


from fastmcp import FastMCP

# Server instance
mcp = FastMCP("hello-world")

## Tool registry
@mcp.tool()
def say_hello(name: str = "World") -> str:
    """Says hello to demonstrate MCP is working"""
    return f"Hello, {name}! MCP server is working!"

## Runner
if __name__ == "__main__":
    mcp.run()