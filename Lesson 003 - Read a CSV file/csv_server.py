"""
Enhanced CSV Reader MCP Server with Aggregation (FastMCP)

Example prompts to test this server:
what are the total units sold by product in the sample CSV?
/read_csv file_path="/path/to/your/data.csv"
/aggregate_csv file_path="sample.csv" group_by="Category" agg_column="Sales_Amount" agg_function="sum"
/aggregate_csv file_path="sample.csv" group_by="Region,Customer_Type" agg_column="Units_Sold" agg_function="mean"
"""

# For reading and analyzing CSV files
import pandas as pd
# For file path handling
from pathlib import Path
# FastMCP for simplified MCP server creation
from fastmcp import FastMCP

# Create a new FastMCP server instance
mcp = FastMCP("csv-reader-server-enhanced")

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

@mcp.tool()
def aggregate_csv(file_path: str, group_by: str, agg_column: str, agg_function: str) -> str:
    """
    Aggregates data in a CSV file by grouping columns and applying aggregation functions.
    
    Use when: calculating totals, averages, counts, or other statistics by category.
    Examples: 'sum sales by region', 'average units sold by category', 'count products by type'.
    
    Args:
        file_path: Path to the CSV file to aggregate
        group_by: Column name(s) to group by. Use comma-separated for multiple columns (e.g., 'Category,Region')
        agg_column: Column name to aggregate
        agg_function: Aggregation function to apply: sum, mean, count, min, max, std
    
    Returns:
        String containing aggregation results and summary statistics.
    """
    try:
        file_path_obj = Path(file_path)
        agg_function = agg_function.lower()
        
        if not file_path_obj.exists():
            return f"Error: File not found at {file_path_obj}"
        
        # Read the CSV file
        df = pd.read_csv(file_path_obj)
        
        # Parse group_by columns (handle comma-separated values)
        group_columns = [col.strip() for col in group_by.split(',')]
    
        # Validate aggregation function
        valid_functions = ['sum', 'mean', 'count', 'min', 'max', 'std']
        if agg_function not in valid_functions:
            return f"Error: Invalid function '{agg_function}'. Valid options: {valid_functions}"
        
        # Perform aggregation
        if agg_function == 'count':
            # For count, we don't need to specify the column
            agg_result = df.groupby(group_columns).size().reset_index(name='count')
            agg_col_name = 'count'
        else:
            # Apply the aggregation function
            agg_result = df.groupby(group_columns)[agg_column].agg(agg_function).reset_index()
            agg_col_name = agg_column
        
        # Build result message
        result = f"Aggregation Results:\n"
        result += f"File: {file_path_obj}\n"
        result += f"Grouped by: {', '.join(group_columns)}\n"
        result += f"Aggregation: {agg_function}({agg_column if agg_function != 'count' else 'rows'})\n\n"
        
        # Format the results
        result += agg_result.to_string(index=False)
        
        # Add summary stats
        if agg_function != 'count':
            total = agg_result[agg_col_name].sum() if agg_function in ['sum', 'mean'] else None
            if total is not None:
                result += f"\n\nTotal {agg_function}: {total:,.2f}"
        
        return result
        
    except Exception as e:
        return f"Error aggregating CSV: {str(e)}"

# Run the server when script is executed directly
if __name__ == "__main__":
    mcp.run()
