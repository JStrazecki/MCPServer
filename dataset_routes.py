# api/dataset_routes.py - MCP Server Dataset Routes
"""
Dataset-related API routes
"""

from flask import Blueprint, jsonify, request
from config.database import db
from models.dataset import Dataset
from models.measure import Measure
from models.table import Table
from services.metadata_service import MetadataService
import logging

logger = logging.getLogger(__name__)

dataset_bp = Blueprint('datasets', __name__)
metadata_service = MetadataService()

@dataset_bp.route('/', methods=['GET'])
def list_datasets():
    """List all datasets with optional filtering"""
    try:
        query = Dataset.query
        
        # Filter by workspace
        workspace_id = request.args.get('workspace_id')
        if workspace_id:
            query = query.filter_by(workspace_id=workspace_id)
        
        # Filter by business area
        business_area = request.args.get('business_area')
        if business_area:
            query = query.filter_by(business_area=business_area)
        
        datasets = query.all()
        return jsonify({
            'datasets': [d.to_dict() for d in datasets],
            'count': len(datasets)
        })
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        return jsonify({'error': str(e)}), 500

@dataset_bp.route('/<dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """Get specific dataset with full details"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        include_details = request.args.get('include_details', 'true').lower() == 'true'
        return jsonify(dataset.to_dict(include_details=include_details))
    except Exception as e:
        logger.error(f"Error getting dataset: {e}")
        return jsonify({'error': str(e)}), 500

@dataset_bp.route('/<dataset_id>/metadata', methods=['GET'])
def get_dataset_metadata(dataset_id):
    """Get complete metadata for a dataset"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Get all related data
        measures = Measure.query.filter_by(dataset_id=dataset_id).all()
        tables = Table.query.filter_by(dataset_id=dataset_id).all()
        
        # Build metadata response
        metadata = {
            'dataset': dataset.to_dict(include_details=True),
            'measures': {
                'count': len(measures),
                'by_type': {},
                'by_area': {},
                'items': [m.to_dict() for m in measures]
            },
            'tables': {
                'count': len(tables),
                'by_type': {},
                'items': []
            }
        }
        
        # Group measures by type and area
        for measure in measures:
            # By type
            m_type = measure.measure_type or 'Other'
            if m_type not in metadata['measures']['by_type']:
                metadata['measures']['by_type'][m_type] = []
            metadata['measures']['by_type'][m_type].append(measure.name)
            
            # By area
            m_area = measure.business_area or 'General'
            if m_area not in metadata['measures']['by_area']:
                metadata['measures']['by_area'][m_area] = []
            metadata['measures']['by_area'][m_area].append(measure.name)
        
        # Process tables
        for table in tables:
            table_data = table.to_dict()
            table_data['columns'] = [c.to_dict() for c in table.columns]
            metadata['tables']['items'].append(table_data)
            
            # By type
            t_type = table.table_type or 'Other'
            if t_type not in metadata['tables']['by_type']:
                metadata['tables']['by_type'][t_type] = []
            metadata['tables']['by_type'][t_type].append(table.name)
        
        return jsonify(metadata)
        
    except Exception as e:
        logger.error(f"Error getting dataset metadata: {e}")
        return jsonify({'error': str(e)}), 500

@dataset_bp.route('/<dataset_id>/measures', methods=['GET'])
def get_dataset_measures(dataset_id):
    """Get measures for a dataset"""
    try:
        measures = Measure.query.filter_by(dataset_id=dataset_id).all()
        
        # Group by folder
        by_folder = {}
        for measure in measures:
            folder = measure.folder or 'Uncategorized'
            if folder not in by_folder:
                by_folder[folder] = []
            by_folder[folder].append(measure.to_dict())
        
        return jsonify({
            'dataset_id': dataset_id,
            'count': len(measures),
            'by_folder': by_folder,
            'measures': [m.to_dict() for m in measures]
        })
        
    except Exception as e:
        logger.error(f"Error getting measures: {e}")
        return jsonify({'error': str(e)}), 500

@dataset_bp.route('/<dataset_id>/tables', methods=['GET'])
def get_dataset_tables(dataset_id):
    """Get tables for a dataset"""
    try:
        tables = Table.query.filter_by(dataset_id=dataset_id).all()
        
        return jsonify({
            'dataset_id': dataset_id,
            'count': len(tables),
            'tables': [t.to_dict() for t in tables]
        })
        
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return jsonify({'error': str(e)}), 500

@dataset_bp.route('/<dataset_id>/sync', methods=['POST'])
def sync_dataset(dataset_id):
    """Sync dataset metadata from Power BI"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Call metadata service to sync
        result = metadata_service.sync_dataset(dataset_id)
        
        if result['success']:
            dataset.last_synced = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Dataset synced successfully',
                'details': result
            })
        else:
            return jsonify({
                'status': 'error',
                'error': result['error']
            }), 500
            
    except Exception as e:
        logger.error(f"Error syncing dataset: {e}")
        return jsonify({'error': str(e)}), 500

# api/context_routes.py - MCP Server Context Routes
"""
Context generation API routes
"""

from flask import Blueprint, jsonify, request
from services.context_service import ContextService
import logging

logger = logging.getLogger(__name__)

context_bp = Blueprint('context', __name__)
context_service = ContextService()

@context_bp.route('/generate', methods=['POST'])
def generate_context():
    """Generate context for a query"""
    try:
        data = request.json
        dataset_id = data.get('dataset_id')
        query = data.get('query')
        query_type = data.get('query_type', 'general')
        
        if not dataset_id or not query:
            return jsonify({'error': 'dataset_id and query are required'}), 400
        
        # Generate context
        context = context_service.generate_context(
            dataset_id=dataset_id,
            query=query,
            query_type=query_type
        )
        
        return jsonify(context)
        
    except Exception as e:
        logger.error(f"Error generating context: {e}")
        return jsonify({'error': str(e)}), 500

@context_bp.route('/dataset/<dataset_id>', methods=['GET'])
def get_dataset_context(dataset_id):
    """Get pre-generated context for a dataset"""
    try:
        context = context_service.get_dataset_context(dataset_id)
        return jsonify(context)
        
    except Exception as e:
        logger.error(f"Error getting dataset context: {e}")
        return jsonify({'error': str(e)}), 500

@context_bp.route('/measure/<dataset_id>/<measure_name>', methods=['GET'])
def get_measure_context(dataset_id, measure_name):
    """Get context for a specific measure"""
    try:
        context = context_service.get_measure_context(dataset_id, measure_name)
        return jsonify(context)
        
    except Exception as e:
        logger.error(f"Error getting measure context: {e}")
        return jsonify({'error': str(e)}), 500

@context_bp.route('/business-rules/<dataset_id>', methods=['GET'])
def get_business_rules(dataset_id):
    """Get business rules for a dataset"""
    try:
        from models.business_rule import BusinessRule
        
        rules = BusinessRule.query.filter_by(
            dataset_id=dataset_id,
            is_active=True
        ).all()
        
        # Group by category
        by_category = {}
        for rule in rules:
            category = rule.category or 'General'
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(rule.to_dict())
        
        return jsonify({
            'dataset_id': dataset_id,
            'count': len(rules),
            'by_category': by_category,
            'rules': [r.to_dict() for r in rules]
        })
        
    except Exception as e:
        logger.error(f"Error getting business rules: {e}")
        return jsonify({'error': str(e)}), 500