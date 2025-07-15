# models/relationship.py - MCP Server Relationship Model
"""
Relationship model for storing Power BI table relationships
"""

from datetime import datetime
from config.database import db

class Relationship(db.Model):
    """Power BI Relationship between tables"""
    __tablename__ = 'relationships'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.String(100), db.ForeignKey('datasets.id'), nullable=False)
    name = db.Column(db.String(255))
    
    # Relationship definition
    from_table = db.Column(db.String(255), nullable=False)
    from_column = db.Column(db.String(255), nullable=False)
    to_table = db.Column(db.String(255), nullable=False)
    to_column = db.Column(db.String(255), nullable=False)
    
    # Relationship properties
    cardinality = db.Column(db.String(50))  # One-to-Many, Many-to-One, etc.
    cross_filter_direction = db.Column(db.String(50))  # Single, Both
    is_active = db.Column(db.Boolean, default=True)
    
    # Business context
    business_description = db.Column(db.Text)
    relationship_type = db.Column(db.String(100))  # Fact-Dimension, etc.
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dataset = db.relationship('Dataset', back_populates='relationships')
    
    def to_dict(self):
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'name': self.name,
            'from_table': self.from_table,
            'from_column': self.from_column,
            'to_table': self.to_table,
            'to_column': self.to_column,
            'cardinality': self.cardinality,
            'cross_filter_direction': self.cross_filter_direction,
            'is_active': self.is_active,
            'business_description': self.business_description,
            'relationship_type': self.relationship_type
        }

# models/query_history.py - MCP Server Query History Model
"""
Query History model for tracking queries and their results
"""

class QueryHistory(db.Model):
    """Query execution history"""
    __tablename__ = 'query_history'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.String(100), db.ForeignKey('datasets.id'), nullable=False)
    session_id = db.Column(db.String(100))
    user_identifier = db.Column(db.String(255))  # Could be email, session, etc.
    
    # Query information
    natural_language_query = db.Column(db.Text, nullable=False)
    dax_query = db.Column(db.Text)
    query_type = db.Column(db.String(50))  # analysis, error, discovery, etc.
    
    # Execution details
    execution_time_ms = db.Column(db.Integer)
    row_count = db.Column(db.Integer)
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    
    # Results summary
    result_summary = db.Column(db.JSON)  # Key metrics from results
    insights_generated = db.Column(db.JSON)  # List of insights
    recommendations = db.Column(db.JSON)  # List of recommendations
    
    # Analysis metadata
    confidence_score = db.Column(db.Float)
    measures_used = db.Column(db.JSON)  # List of measure names
    tables_accessed = db.Column(db.JSON)  # List of table names
    
    # User feedback
    user_rating = db.Column(db.Integer)  # 1-5 rating
    user_feedback = db.Column(db.Text)
    was_helpful = db.Column(db.Boolean)
    
    # Follow-up
    follow_up_queries = db.Column(db.JSON)  # Suggested follow-ups
    led_to_query_id = db.Column(db.Integer, db.ForeignKey('query_history.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    dataset = db.relationship('Dataset', back_populates='query_history')
    follow_up_from = db.relationship('QueryHistory', remote_side=[id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'dataset_name': self.dataset.name if self.dataset else None,
            'session_id': self.session_id,
            'natural_language_query': self.natural_language_query,
            'query_type': self.query_type,
            'execution_time_ms': self.execution_time_ms,
            'row_count': self.row_count,
            'success': self.success,
            'error_message': self.error_message,
            'confidence_score': self.confidence_score,
            'measures_used': self.measures_used,
            'tables_accessed': self.tables_accessed,
            'user_rating': self.user_rating,
            'was_helpful': self.was_helpful,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# models/business_rule.py - MCP Server Business Rule Model
"""
Business Rule model for storing business logic and calculations
"""

class BusinessRule(db.Model):
    """Business rules and calculation logic"""
    __tablename__ = 'business_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.String(100), db.ForeignKey('datasets.id'))
    
    # Rule definition
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))  # Calculation, Validation, Transformation
    business_area = db.Column(db.String(100))
    
    # Rule content
    description = db.Column(db.Text, nullable=False)
    rule_logic = db.Column(db.Text)  # Plain English explanation
    dax_implementation = db.Column(db.Text)  # DAX code if applicable
    
    # Applicability
    applies_to_measures = db.Column(db.JSON)  # List of measure names
    applies_to_tables = db.Column(db.JSON)  # List of table names
    conditions = db.Column(db.JSON)  # When this rule applies
    
    # Examples
    examples = db.Column(db.JSON)  # List of examples
    
    # Metadata
    version = db.Column(db.String(50), default='1.0')
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(255))
    approved_by = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'name': self.name,
            'category': self.category,
            'business_area': self.business_area,
            'description': self.description,
            'rule_logic': self.rule_logic,
            'applies_to_measures': self.applies_to_measures,
            'applies_to_tables': self.applies_to_tables,
            'conditions': self.conditions,
            'examples': self.examples,
            'version': self.version,
            'is_active': self.is_active
        }