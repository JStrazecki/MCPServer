"""
Minimal Power BI MCP Server - Version 1: List Workspaces
"""

#region Imports
import json
import requests
import os
from fastmcp import FastMCP
#endregion


#region Configuration
# Create server
mcp = FastMCP("powerbi-server")

# API endpoints
POWERBI_API = "https://api.powerbi.com/v1.0/myorg"

# Authentication
TOKEN = os.environ.get("POWERBI_TOKEN", "")
#endregion


#region Helper Functions
## Simple HTTP request helper
## Returns JSON response or error dict
def make_request(url, method="GET", data=None):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, headers=headers, json=data)
        
        if response.ok:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}
#endregion


#region MCP Tool Functions
@mcp.tool()
def list_workspaces() -> str:
    """List all Power BI workspaces you have access to.
    Returns formatted list of workspace names and IDs.
    Examples: 'show my workspaces', 'what Power BI workspaces do I have?', 'list all workspaces'
    """
    result = make_request(f"{POWERBI_API}/groups")
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    workspaces = result.get("value", [])
    if not workspaces:
        return "No workspaces found"
    
    output = f"Found {len(workspaces)} workspaces:\n\n"
    for ws in workspaces:
        output += f"• {ws['name']} (ID: {ws['id']})\n"
    
    return output
#endregion


#region Main Entry Point
if __name__ == "__main__":
    mcp.run()
#endregion