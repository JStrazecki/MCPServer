# api/query_routes.py - MCP Server Query History Routes
"""
Query history and analytics API routes
"""

from flask import Blueprint, jsonify, request
from config.database import db
from models.query_history import QueryHistory
from models.dataset import Dataset
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

query_bp = Blueprint('queries', __name__)

@query_bp.route('/history', methods=['GET'])
def get_query_history():
    """Get query history with filtering options"""
    try:
        query = QueryHistory.query
        
        # Filter by dataset
        dataset_id = request.args.get('dataset_id')
        if dataset_id:
            query = query.filter_by(dataset_id=dataset_id)
        
        # Filter by user
        user_identifier = request.args.get('user_identifier')
        if user_identifier:
            query = query.filter_by(user_identifier=user_identifier)
        
        # Filter by session
        session_id = request.args.get('session_id')
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        # Filter by date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date:
            query = query.filter(QueryHistory.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(QueryHistory.created_at <= datetime.fromisoformat(end_date))
        
        # Filter by success
        success_only = request.args.get('success_only', 'false').lower() == 'true'
        if success_only:
            query = query.filter_by(success=True)
        
        # Pagination
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        
        # Order by recency
        query = query.order_by(desc(QueryHistory.created_at))
        
        # Execute query
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'queries': [q.to_dict() for q in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        
    except Exception as e:
        logger.error(f"Error getting query history: {e}")
        return jsonify({'error': str(e)}), 500

@query_bp.route('/record', methods=['POST'])
def record_query():
    """Record a new query execution"""
    try:
        data = request.json
        
        # Create query history entry
        query_history = QueryHistory(
            dataset_id=data['dataset_id'],
            session_id=data.get('session_id'),
            user_identifier=data.get('user_identifier'),
            natural_language_query=data['natural_language_query'],
            dax_query=data.get('dax_query'),
            query_type=data.get('query_type', 'analysis'),
            execution_time_ms=data.get('execution_time_ms'),
            row_count=data.get('row_count'),
            success=data.get('success', True),
            error_message=data.get('error_message'),
            result_summary=data.get('result_summary'),
            insights_generated=data.get('insights_generated'),
            recommendations=data.get('recommendations'),
            confidence_score=data.get('confidence_score'),
            measures_used=data.get('measures_used'),
            tables_accessed=data.get('tables_accessed'),
            follow_up_queries=data.get('follow_up_queries'),
            led_to_query_id=data.get('led_to_query_id')
        )
        
        db.session.add(query_history)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'query_id': query_history.id,
            'query': query_history.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error recording query: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@query_bp.route('/analytics', methods=['GET'])
def get_query_analytics():
    """Get analytics about query usage"""
    try:
        # Time range
        days = int(request.args.get('days', 30))
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query
        base_query = QueryHistory.query.filter(QueryHistory.created_at >= start_date)
        
        # Total queries
        total_queries = base_query.count()
        successful_queries = base_query.filter_by(success=True).count()
        
        # Queries by dataset
        queries_by_dataset = db.session.query(
            Dataset.name,
            func.count(QueryHistory.id).label('count')
        ).join(
            QueryHistory, Dataset.id == QueryHistory.dataset_id
        ).filter(
            QueryHistory.created_at >= start_date
        ).group_by(Dataset.name).all()
        
        # Most used measures
        all_measures = []
        for query in base_query.all():
            if query.measures_used:
                all_measures.extend(query.measures_used)
        
        measure_counts = {}
        for measure in all_measures:
            measure_counts[measure] = measure_counts.get(measure, 0) + 1
        
        top_measures = sorted(measure_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Query types
        query_types = db.session.query(
            QueryHistory.query_type,
            func.count(QueryHistory.id).label('count')
        ).filter(
            QueryHistory.created_at >= start_date
        ).group_by(QueryHistory.query_type).all()
        
        # Average execution time
        avg_execution_time = db.session.query(
            func.avg(QueryHistory.execution_time_ms)
        ).filter(
            QueryHistory.created_at >= start_date,
            QueryHistory.execution_time_ms.isnot(None)
        ).scalar()
        
        # User satisfaction (based on ratings)
        rated_queries = base_query.filter(QueryHistory.user_rating.isnot(None))
        avg_rating = db.session.query(func.avg(QueryHistory.user_rating)).filter(
            QueryHistory.created_at >= start_date,
            QueryHistory.user_rating.isnot(None)
        ).scalar()
        
        helpful_count = base_query.filter_by(was_helpful=True).count()
        
        return jsonify({
            'time_range_days': days,
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'success_rate': (successful_queries / total_queries * 100) if total_queries > 0 else 0,
            'queries_by_dataset': [
                {'dataset': name, 'count': count} for name, count in queries_by_dataset
            ],
            'top_measures': [
                {'measure': name, 'count': count} for name, count in top_measures
            ],
            'query_types': [
                {'type': type_name or 'unknown', 'count': count} 
                for type_name, count in query_types
            ],
            'average_execution_time_ms': float(avg_execution_time) if avg_execution_time else 0,
            'user_satisfaction': {
                'average_rating': float(avg_rating) if avg_rating else None,
                'rated_queries': rated_queries.count(),
                'helpful_count': helpful_count
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting query analytics: {e}")
        return jsonify({'error': str(e)}), 500

@query_bp.route('/<int:query_id>/feedback', methods=['POST'])
def update_query_feedback(query_id):
    """Update feedback for a query"""
    try:
        query = QueryHistory.query.get_or_404(query_id)
        data = request.json
        
        # Update feedback
        if 'user_rating' in data:
            query.user_rating = data['user_rating']
        if 'user_feedback' in data:
            query.user_feedback = data['user_feedback']
        if 'was_helpful' in data:
            query.was_helpful = data['was_helpful']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'query': query.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating query feedback: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@query_bp.route('/popular-questions/<dataset_id>', methods=['GET'])
def get_popular_questions(dataset_id):
    """Get popular questions for a dataset"""
    try:
        # Get successful queries with high ratings
        popular_queries = QueryHistory.query.filter_by(
            dataset_id=dataset_id,
            success=True
        ).filter(
            QueryHistory.user_rating >= 4
        ).order_by(
            desc(QueryHistory.user_rating),
            desc(QueryHistory.created_at)
        ).limit(20).all()
        
        # Deduplicate similar questions
        seen_questions = set()
        unique_questions = []
        
        for query in popular_queries:
            # Simple deduplication - in production, use more sophisticated similarity
            question_lower = query.natural_language_query.lower().strip()
            if question_lower not in seen_questions:
                seen_questions.add(question_lower)
                unique_questions.append({
                    'question': query.natural_language_query,
                    'rating': query.user_rating,
                    'asked_count': 1  # Would need to implement proper counting
                })
        
        return jsonify({
            'dataset_id': dataset_id,
            'popular_questions': unique_questions[:10]
        })
        
    except Exception as e:
        logger.error(f"Error getting popular questions: {e}")
        return jsonify({'error': str(e)}), 500