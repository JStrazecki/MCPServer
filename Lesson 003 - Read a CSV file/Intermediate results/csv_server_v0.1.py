"""
Minimal CSV Reader MCP Server (FastMCP)

Example prompts to test this server:
/read_csv file_path="/path/to/your/data.csv"
/read_csv file_path="sales_data.csv"
read the CSV file at "data/sales.csv"
read the sample.csv file
"""

# For reading and analyzing CSV files
import pandas as pd
# For file path handling
from pathlib import Path
# FastMCP for simplified MCP server creation
from fastmcp import FastMCP

# Create a new FastMCP server instance
mcp = FastMCP("csv-reader-server")

@mcp.tool()
def read_csv(file_path: str) -> str:
    """
    Reads a CSV file and returns its contents and basic info.
    
    Use when: analyzing data files, checking CSV structure, or viewing data samples.
    Examples: 'read sales.csv', 'analyze the data file', 'show me what's in the CSV'
    
    Args:
        file_path: Path to the CSV file to read. Can be absolute or relative.
    
    Returns:
        String containing file info and preview of the data.
    """
    try:
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return f"Error: File not found at {file_path_obj}"
        
        # Read the CSV file into a dataframe
        df = pd.read_csv(file_path_obj)
        
        # Build result message with file info
        result = f"Successfully read CSV: {file_path_obj}\n"
        result += f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n"
        result += f"Columns: {', '.join(df.columns)}\n\n"
        
        # Add first 5 rows as preview
        result += "First 5 rows:\n"
        result += df.head().to_string()
        
        return result
        
    except Exception as e:
        return f"Error reading CSV: {str(e)}"

# Run the server when script is executed directly
if __name__ == "__main__":
    mcp.run()
