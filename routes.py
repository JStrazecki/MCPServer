# api/routes.py - MCP Server Main API Routes
"""
Main API routes for MCP Server
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def api_index():
    """API root endpoint"""
    return jsonify({
        'name': 'MCP Power BI API',
        'version': '1.0.0',
        'endpoints': {
            'workspaces': {
                'list': 'GET /api/workspaces',
                'get': 'GET /api/workspaces/{id}',
                'create': 'POST /api/workspaces',
                'update': 'PUT /api/workspaces/{id}',
                'sync': 'POST /api/workspaces/{id}/sync'
            },
            'datasets': {
                'list': 'GET /api/datasets',
                'get': 'GET /api/datasets/{id}',
                'metadata': 'GET /api/datasets/{id}/metadata',
                'measures': 'GET /api/datasets/{id}/measures',
                'tables': 'GET /api/datasets/{id}/tables',
                'sync': 'POST /api/datasets/{id}/sync'
            },
            'context': {
                'generate': 'POST /api/context/generate',
                'dataset': 'GET /api/context/dataset/{id}',
                'measure': 'GET /api/context/measure/{dataset_id}/{measure_name}'
            },
            'queries': {
                'history': 'GET /api/queries/history',
                'record': 'POST /api/queries/record',
                'analytics': 'GET /api/queries/analytics'
            }
        }
    })

@api_bp.route('/status')
def api_status():
    """API status endpoint"""
    from config.database import db
    from models.workspace import Workspace
    from models.dataset import Dataset
    from models.measure import Measure
    from models.table import Table
    from models.query_history import QueryHistory
    
    try:
        # Get counts
        workspace_count = Workspace.query.count()
        dataset_count = Dataset.query.count()
        measure_count = Measure.query.count()
        table_count = Table.query.count()
        query_count = QueryHistory.query.count()
        
        # Get last sync times
        last_workspace_sync = db.session.query(db.func.max(Workspace.last_synced)).scalar()
        last_dataset_sync = db.session.query(db.func.max(Dataset.last_synced)).scalar()
        
        return jsonify({
            'status': 'operational',
            'timestamp': datetime.utcnow().isoformat(),
            'statistics': {
                'workspaces': workspace_count,
                'datasets': dataset_count,
                'measures': measure_count,
                'tables': table_count,
                'query_history': query_count
            },
            'last_sync': {
                'workspaces': last_workspace_sync.isoformat() if last_workspace_sync else None,
                'datasets': last_dataset_sync.isoformat() if last_dataset_sync else None
            }
        })
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# api/workspace_routes.py - MCP Server Workspace Routes
"""
Workspace-related API routes
"""

from flask import Blueprint, jsonify, request
from config.database import db
from models.workspace import Workspace
from services.metadata_service import MetadataService
import logging

logger = logging.getLogger(__name__)

workspace_bp = Blueprint('workspaces', __name__)
metadata_service = MetadataService()

@workspace_bp.route('/', methods=['GET'])
def list_workspaces():
    """List all workspaces"""
    try:
        workspaces = Workspace.query.all()
        return jsonify({
            'workspaces': [w.to_dict() for w in workspaces],
            'count': len(workspaces)
        })
    except Exception as e:
        logger.error(f"Error listing workspaces: {e}")
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/<workspace_id>', methods=['GET'])
def get_workspace(workspace_id):
    """Get specific workspace"""
    try:
        workspace = Workspace.query.get_or_404(workspace_id)
        return jsonify(workspace.to_dict())
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/', methods=['POST'])
def create_workspace():
    """Create or update workspace"""
    try:
        data = request.json
        workspace = Workspace.query.get(data['id'])
        
        if workspace:
            # Update existing
            for key, value in data.items():
                if hasattr(workspace, key):
                    setattr(workspace, key, value)
        else:
            # Create new
            workspace = Workspace(**data)
            db.session.add(workspace)
        
        db.session.commit()
        return jsonify(workspace.to_dict()), 201 if not workspace else 200
        
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@workspace_bp.route('/<workspace_id>/sync', methods=['POST'])
def sync_workspace(workspace_id):
    """Sync workspace metadata from Power BI"""
    try:
        workspace = Workspace.query.get_or_404(workspace_id)
        
        # Call metadata service to sync
        result = metadata_service.sync_workspace(workspace_id)
        
        if result['success']:
            workspace.last_synced = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f"Synced {result['datasets_synced']} datasets",
                'details': result
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error syncing workspace: {e}")
        return jsonify({'error': str(e)}), 500