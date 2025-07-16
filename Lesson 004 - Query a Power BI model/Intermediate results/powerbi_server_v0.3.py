"""
Minimal Power BI MCP Server - Version 3: Full Model Discovery
"""

#region Imports
import json
import requests
import os
import time
import base64
from fastmcp import FastMCP
#endregion


#region Configuration
# Create server
mcp = FastMCP("powerbi-server")

# API endpoints
POWERBI_API = "https://api.powerbi.com/v1.0/myorg"
FABRIC_API = "https://api.fabric.microsoft.com/v1"

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


## Wait for a long-running operation to complete
## Polls the operation status until success or failure
def wait_for_operation(location_url, retry_seconds=30):
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    while True:
        time.sleep(retry_seconds)
        response = requests.get(location_url, headers=headers)
        
        if response.ok:
            data = response.json()
            status = data.get('status', '')
            
            if status == 'Succeeded':
                # Get the final result
                result_response = requests.get(f"{location_url}/result", headers=headers)
                return result_response.json() if result_response.ok else {"error": "Failed to get result"}
            elif status == 'Failed':
                return {"error": data.get('error', 'Operation failed')}
            # Keep waiting if still running
        else:
            return {"error": f"Failed to check status: {response.status_code}"}
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


@mcp.tool()
def list_datasets(workspace_id: str) -> str:
    """List all datasets in a specific workspace.
    Returns formatted list of dataset names and IDs.
    Examples: 'show datasets in workspace X', 'what datasets are available?', 'list all semantic models'
    """
    result = make_request(f"{POWERBI_API}/groups/{workspace_id}/datasets")
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    datasets = result.get("value", [])
    if not datasets:
        return "No datasets found in this workspace"
    
    output = f"Found {len(datasets)} datasets:\n\n"
    for ds in datasets:
        output += f"• {ds['name']} (ID: {ds['id']})\n"
    
    return output


@mcp.tool()
def get_model_definition(workspace_id: str, dataset_id: str) -> str:
    """Get the complete TMDL definition of a dataset including tables, columns, measures, and relationships.
    Returns full model structure in TMDL format with all DAX expressions.
    Examples: 'show me the data model', 'what tables are in this dataset?', 'get all measures and their DAX'
    """
    # Call Fabric API
    url = f"{FABRIC_API}/workspaces/{workspace_id}/semanticModels/{dataset_id}/getDefinition"
    response = requests.post(url, headers={"Authorization": f"Bearer {TOKEN}"})
    
    # Handle long-running operation
    if response.status_code == 202:
        location = response.headers.get('Location')
        retry_after = int(response.headers.get('Retry-After', 30))
        result = wait_for_operation(location, retry_after)
    elif response.ok:
        result = response.json()
    else:
        return f"Error: HTTP {response.status_code}"
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    # Extract and decode TMDL parts
    parts = result.get("definition", {}).get("parts", [])
    if not parts:
        return "No model definition found"
    
    output = f"Dataset Model Definition (TMDL Format)\n{'='*40}\n\n"
    
    for part in parts:
        path = part.get("path", "")
        payload = part.get("payload", "")
        
        # Skip non-TMDL files
        if not path.endswith('.tmdl'):
            continue
            
        try:
            # Decode content
            content = base64.b64decode(payload).decode('utf-8')
            
            # Add section header
            output += f"\n{'─'*40}\n"
            output += f"File: {path}\n"
            output += f"{'─'*40}\n"
            output += content
            output += "\n"
            
        except Exception as e:
            output += f"\nError decoding {path}: {str(e)}\n"
    
    return output
#endregion


#region Main Entry Point
if __name__ == "__main__":
    mcp.run()
#endregion