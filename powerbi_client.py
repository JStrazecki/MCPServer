# utils/powerbi_client.py - MCP Server Power BI API Client
"""
Power BI API client for syncing metadata
"""

import os
import logging
import aiohttp
from typing import Dict, List, Any, Optional
from datetime import datetime
from msal import ConfidentialClientApplication

logger = logging.getLogger(__name__)

class PowerBIAPIClient:
    """Client for interacting with Power BI REST API"""
    
    def __init__(self):
        self.tenant_id = os.environ.get("POWERBI_TENANT_ID")
        self.client_id = os.environ.get("POWERBI_CLIENT_ID")
        self.client_secret = os.environ.get("POWERBI_CLIENT_SECRET")
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.scope = ["https://analysis.windows.net/powerbi/api/.default"]
        
        if all([self.tenant_id, self.client_id, self.client_secret]):
            self.msal_app = ConfidentialClientApplication(
                self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                client_credential=self.client_secret
            )
        else:
            logger.warning("Power BI credentials not configured")
            self.msal_app = None
        
        self.token_cache = {}
    
    def get_access_token(self) -> Optional[str]:
        """Get access token for Power BI API"""
        if not self.msal_app:
            return None
        
        # Check cache
        if 'token' in self.token_cache:
            token_data = self.token_cache['token']
            if token_data['expires_at'] > datetime.utcnow():
                return token_data['access_token']
        
        try:
            result = self.msal_app.acquire_token_for_client(scopes=self.scope)
            
            if "access_token" in result:
                # Cache the token
                from datetime import timedelta
                self.token_cache['token'] = {
                    'access_token': result['access_token'],
                    'expires_at': datetime.utcnow() + timedelta(seconds=result.get('expires_in', 3600))
                }
                return result['access_token']
            else:
                logger.error(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
                return None
                
        except Exception as e:
            logger.error(f"Exception getting access token: {e}")
            return None
    
    def get_workspace(self, workspace_id: str) -> Optional[Dict]:
        """Get workspace details"""
        token = self.get_access_token()
        if not token:
            return None
        
        try:
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{self.base_url}/groups/{workspace_id}", headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get workspace: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting workspace: {e}")
            return None
    
    def get_workspace_datasets(self, workspace_id: str) -> List[Dict]:
        """Get datasets in a workspace"""
        token = self.get_access_token()
        if not token:
            return []
        
        try:
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{self.base_url}/groups/{workspace_id}/datasets", headers=headers)
            
            if response.status_code == 200:
                return response.json().get('value', [])
            else:
                logger.error(f"Failed to get datasets: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting datasets: {e}")
            return []
    
    def get_dataset_metadata(self, dataset_id: str) -> Optional[Dict]:
        """Get detailed dataset metadata including tables and measures"""
        token = self.get_access_token()
        if not token:
            return None
        
        try:
            # Note: Power BI REST API has limited metadata access
            # For full metadata, you might need to use XMLA endpoint or Tabular Object Model
            # This is a simplified version
            
            metadata = {
                'tables': [],
                'measures': [],
                'relationships': []
            }
            
            # Get dataset details
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            
            # Get dataset info
            response = requests.get(f"{self.base_url}/datasets/{dataset_id}", headers=headers)
            if response.status_code == 200:
                dataset_info = response.json()
                metadata['model_version'] = dataset_info.get('targetStorageMode')
                
            # Note: To get tables, measures, and relationships, you would typically need to:
            # 1. Use XMLA endpoint with MDSCHEMA_MEASURES, MDSCHEMA_HIERARCHIES queries
            # 2. Or use Analysis Services client libraries
            # 3. Or execute DAX queries to discover metadata
            
            # For now, return basic structure
            logger.info(f"Dataset metadata retrieval limited - consider using XMLA endpoint for full metadata")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error getting dataset metadata: {e}")
            return None
    
    def get_dataset_refresh_history(self, dataset_id: str) -> Optional[Dict]:
        """Get dataset refresh history"""
        token = self.get_access_token()
        if not token:
            return None
        
        try:
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{self.base_url}/datasets/{dataset_id}/refreshes?$top=1",
                headers=headers
            )
            
            if response.status_code == 200:
                refreshes = response.json().get('value', [])
                if refreshes:
                    latest = refreshes[0]
                    return {
                        'last_refresh_date': latest.get('endTime'),
                        'last_refresh_status': latest.get('status'),
                        'duration': latest.get('duration')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting refresh history: {e}")
            return None
    
    def discover_dataset_schema(self, dataset_id: str, workspace_id: str) -> Dict[str, List]:
        """
        Discover dataset schema using DAX queries
        This is a workaround for limited REST API metadata access
        """
        token = self.get_access_token()
        if not token:
            return {'tables': [], 'measures': []}
        
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # DAX query to discover tables and columns
            discover_tables_query = """
            EVALUATE
                SELECTCOLUMNS(
                    INFO.TABLES(),
                    "TableName", [Name],
                    "IsHidden", [IsHidden],
                    "Description", [Description]
                )
            """
            
            # DAX query to discover measures
            discover_measures_query = """
            EVALUATE
                SELECTCOLUMNS(
                    INFO.MEASURES(),
                    "MeasureName", [Name],
                    "TableName", [TableName],
                    "Expression", [Expression],
                    "FormatString", [FormatString],
                    "IsHidden", [IsHidden],
                    "Description", [Description]
                )
            """
            
            schema = {'tables': [], 'measures': []}
            
            # Execute queries
            endpoint = f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
            
            for query_type, dax_query in [('tables', discover_tables_query), ('measures', discover_measures_query)]:
                payload = {
                    "queries": [{"query": dax_query}],
                    "serializerSettings": {"includeNulls": True}
                }
                
                response = requests.post(endpoint, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'results' in result and result['results']:
                        tables = result['results'][0].get('tables', [])
                        if tables:
                            rows = tables[0].get('rows', [])
                            schema[query_type] = rows
                
            return schema
            
        except Exception as e:
            logger.error(f"Error discovering schema: {e}")
            return {'tables': [], 'measures': []}

# utils/validators.py - MCP Server Validators
"""
Data validators for MCP Server
"""

def validate_measure_expression(expression: str) -> bool:
    """Validate DAX measure expression"""
    if not expression:
        return False
    
    # Basic validation - check for common DAX functions
    dax_functions = ['CALCULATE', 'SUM', 'AVERAGE', 'COUNT', 'DISTINCTCOUNT', 
                     'MAX', 'MIN', 'DIVIDE', 'IF', 'SWITCH', 'VAR', 'RETURN']
    
    expression_upper = expression.upper()
    return any(func in expression_upper for func in dax_functions)

def validate_table_name(name: str) -> bool:
    """Validate table name"""
    if not name:
        return False
    
    # Table names should not contain certain characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    return not any(char in name for char in invalid_chars)

def validate_dataset_id(dataset_id: str) -> bool:
    """Validate Power BI dataset ID format"""
    import re
    # Power BI IDs are GUIDs
    guid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    return bool(re.match(guid_pattern, dataset_id))

# utils/helpers.py - MCP Server Helper Functions
"""
Helper functions for MCP Server
"""

from typing import List, Dict, Any

def extract_measure_dependencies(expression: str) -> Dict[str, List[str]]:
    """Extract measure and column dependencies from DAX expression"""
    import re
    
    dependencies = {
        'measures': [],
        'columns': []
    }
    
    if not expression:
        return dependencies
    
    # Find measure references [MeasureName]
    measure_pattern = r'\[([^\]]+)\]'
    potential_measures = re.findall(measure_pattern, expression)
    
    # Find column references 'TableName'[ColumnName]
    column_pattern = r"'([^']+)'\[([^\]]+)\]"
    columns = re.findall(column_pattern, expression)
    
    dependencies['measures'] = list(set(potential_measures))
    dependencies['columns'] = [f"{table}.{col}" for table, col in columns]
    
    return dependencies

def categorize_measure_by_name(measure_name: str) -> Dict[str, str]:
    """Categorize measure based on naming patterns"""
    name_lower = measure_name.lower()
    
    # Determine measure type
    if any(pattern in name_lower for pattern in ['ytd', 'mtd', 'yoy', 'mom']):
        measure_type = 'Time Intelligence'
    elif any(pattern in name_lower for pattern in ['%', 'percent', 'ratio']):
        measure_type = 'Ratio'
    elif any(pattern in name_lower for pattern in ['avg', 'average']):
        measure_type = 'Average'
    elif any(pattern in name_lower for pattern in ['sum', 'total']):
        measure_type = 'Sum'
    elif any(pattern in name_lower for pattern in ['count', 'distinct']):
        measure_type = 'Count'
    else:
        measure_type = 'Calculated'
    
    # Determine business area
    if any(pattern in name_lower for pattern in ['revenue', 'sales', 'income']):
        business_area = 'Sales'
    elif any(pattern in name_lower for pattern in ['cost', 'expense']):
        business_area = 'Finance'
    elif any(pattern in name_lower for pattern in ['profit', 'margin']):
        business_area = 'Finance'
    elif any(pattern in name_lower for pattern in ['customer', 'client']):
        business_area = 'Customer'
    elif any(pattern in name_lower for pattern in ['inventory', 'stock']):
        business_area = 'Operations'
    else:
        business_area = 'General'
    
    return {
        'measure_type': measure_type,
        'business_area': business_area
    }

def format_dax_expression(expression: str) -> str:
    """Format DAX expression for readability"""
    if not expression:
        return expression
    
    # Basic formatting - add newlines after certain keywords
    keywords = ['CALCULATE', 'RETURN', 'VAR', 'FILTER', 'ALL', 'VALUES']
    
    formatted = expression
    for keyword in keywords:
        formatted = formatted.replace(f'{keyword}(', f'\n{keyword}(')
        formatted = formatted.replace(f'{keyword} (', f'\n{keyword} (')
    
    # Clean up extra newlines
    formatted = '\n'.join(line.strip() for line in formatted.split('\n') if line.strip())
    
    return formatted