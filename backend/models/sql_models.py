"""
SQLAlchemy models for SQLite database
Handles project and scene data with tracking statuses and file paths
"""

from database import db
from datetime import datetime
import uuid


class Project(db.Model):
    """Project model for storing meme project data"""
    __tablename__ = 'projects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(100), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    
    # Image paths (local storage)
    original_image_path = db.Column(db.String(500), nullable=True)
    depth_map_path = db.Column(db.String(500), nullable=True)
    
    # Processing status
    status = db.Column(db.String(50), default='created', index=True)
    # Status values: created, uploading, processing_depth, processing_3d, completed, failed
    
    error_message = db.Column(db.Text, nullable=True)
    
    # Metadata
    metadata_json = db.Column(db.Text, nullable=True)  # JSON string for flexible metadata
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    scenes = db.relationship('Scene', backref='project', lazy=True, cascade='all, delete-orphan')
    exports = db.relationship('Export', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'original_image_path': self.original_image_path,
            'depth_map_path': self.depth_map_path,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def create(user_id, name=None, description=None):
        """Create a new project"""
        project = Project(
            user_id=user_id,
            name=name,
            description=description
        )
        db.session.add(project)
        db.session.commit()
        return project
    
    @staticmethod
    def get(project_id):
        """Get project by ID"""
        return Project.query.get(project_id)
    
    @staticmethod
    def get_by_user(user_id, limit=50):
        """Get all projects by user"""
        return Project.query.filter_by(user_id=user_id)\
            .order_by(Project.created_at.desc())\
            .limit(limit).all()
    
    def update_status(self, status, error_message=None):
        """Update project status"""
        self.status = status
        if error_message:
            self.error_message = error_message
        db.session.commit()
    
    def update_paths(self, original_image_path=None, depth_map_path=None):
        """Update file paths"""
        if original_image_path:
            self.original_image_path = original_image_path
        if depth_map_path:
            self.depth_map_path = depth_map_path
        db.session.commit()


class Scene(db.Model):
    """Scene model for 3D mesh data extracted from projects"""
    __tablename__ = 'scenes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False, index=True)
    
    # Scene properties
    scene_index = db.Column(db.Integer, default=0)
    name = db.Column(db.String(255), nullable=True)
    
    # File paths (local storage)
    mesh_path = db.Column(db.String(500), nullable=True)  # .glb, .obj, .ply
    point_cloud_path = db.Column(db.String(500), nullable=True)  # .ply
    texture_path = db.Column(db.String(500), nullable=True)
    
    # Segmentation data
    segmentation_data_json = db.Column(db.Text, nullable=True)  # JSON string
    bbox_json = db.Column(db.Text, nullable=True)  # Bounding box as JSON
    
    # Processing status
    status = db.Column(db.String(50), default='created')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        import json
        return {
            'id': self.id,
            'project_id': self.project_id,
            'scene_index': self.scene_index,
            'name': self.name,
            'mesh_path': self.mesh_path,
            'point_cloud_path': self.point_cloud_path,
            'texture_path': self.texture_path,
            'bbox': json.loads(self.bbox_json) if self.bbox_json else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def create(project_id, scene_index=0, name=None):
        """Create a new scene"""
        scene = Scene(
            project_id=project_id,
            scene_index=scene_index,
            name=name
        )
        db.session.add(scene)
        db.session.commit()
        return scene
    
    @staticmethod
    def get(scene_id):
        """Get scene by ID"""
        return Scene.query.get(scene_id)
    
    @staticmethod
    def get_by_project(project_id):
        """Get all scenes for a project"""
        return Scene.query.filter_by(project_id=project_id)\
            .order_by(Scene.scene_index).all()
    
    def update_paths(self, mesh_path=None, point_cloud_path=None, texture_path=None):
        """Update file paths"""
        if mesh_path:
            self.mesh_path = mesh_path
        if point_cloud_path:
            self.point_cloud_path = point_cloud_path
        if texture_path:
            self.texture_path = texture_path
        db.session.commit()


class Export(db.Model):
    """Export model for GIF/video exports"""
    __tablename__ = 'exports'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False, index=True)
    
    # Export type: gif, mp4, webm
    export_type = db.Column(db.String(20), nullable=False)
    
    # File path (local storage)
    export_path = db.Column(db.String(500), nullable=True)
    
    # Export settings
    settings_json = db.Column(db.Text, nullable=True)  # JSON string for settings
    
    # Metadata
    metadata_json = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        import json
        return {
            'id': self.id,
            'project_id': self.project_id,
            'export_type': self.export_type,
            'export_path': self.export_path,
            'settings': json.loads(self.settings_json) if self.settings_json else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def create(project_id, export_type, export_path=None, settings=None):
        """Create a new export record"""
        import json
        export = Export(
            project_id=project_id,
            export_type=export_type,
            export_path=export_path,
            settings_json=json.dumps(settings) if settings else None
        )
        db.session.add(export)
        db.session.commit()
        return export
    
    @staticmethod
    def get_by_project(project_id):
        """Get all exports for a project"""
        return Export.query.filter_by(project_id=project_id)\
            .order_by(Export.created_at.desc()).all()


class MemeTemplate(db.Model):
    """Meme template model for storing template metadata"""
    __tablename__ = 'meme_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Template file path
    template_path = db.Column(db.String(500), nullable=True)
    thumbnail_path = db.Column(db.String(500), nullable=True)
    
    # Semantic tags for matching
    tags_json = db.Column(db.Text, nullable=True)  # JSON array of tags
    
    # Usage stats
    usage_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_path': self.template_path,
            'thumbnail_path': self.thumbnail_path,
            'tags': json.loads(self.tags_json) if self.tags_json else [],
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TrendingTopic(db.Model):
    """Trending topic model for caching trending data"""
    __tablename__ = 'trending_topics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category = db.Column(db.String(100), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    reason = db.Column(db.Text, nullable=True)
    
    # Scene ideas as JSON array
    scene_ideas_json = db.Column(db.Text, nullable=True)
    
    # Timestamps
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        import json
        return {
            'id': self.id,
            'category': self.category,
            'title': self.title,
            'description': self.description,
            'reason': self.reason,
            'scene_ideas': json.loads(self.scene_ideas_json) if self.scene_ideas_json else [],
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None
        }
    
    @staticmethod
    def get_by_category(category, limit=10):
        """Get trending topics by category"""
        return TrendingTopic.query.filter_by(category=category)\
            .filter(TrendingTopic.expires_at > datetime.utcnow())\
            .order_by(TrendingTopic.fetched_at.desc())\
            .limit(limit).all()
    
    @staticmethod
    def clear_expired():
        """Clear expired trending topics"""
        TrendingTopic.query.filter(TrendingTopic.expires_at <= datetime.utcnow()).delete()
        db.session.commit()
