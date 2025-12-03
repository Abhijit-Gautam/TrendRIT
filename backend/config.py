"""
Configuration for TrendRIT Backend
Local/self-hosted environment with SQLite and ChromaDB
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration for local/self-hosted deployment"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    
    # File Storage Paths (Local)
    BASE_DATA_DIR = os.environ.get('BASE_DATA_DIR', './data')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './data/uploads')
    MODELS_FOLDER = os.environ.get('MODELS_FOLDER', './data/3d_models')
    EXPORTS_FOLDER = os.environ.get('EXPORTS_FOLDER', './data/exports')
    OUTPUT_FOLDER = MODELS_FOLDER  # Alias for backward compatibility
    
    # SQLite Database (via SQLAlchemy)
    SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', 'sqlite:///data/meme3d.db')
    SQLALCHEMY_DATABASE_URI = SQLITE_DB_PATH
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ChromaDB Configuration (Local Vector Database)
    CHROMADB_PATH = os.environ.get('CHROMADB_PATH', './data/chroma_db')
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    
    # Model Configuration
    DEPTH_MODEL_NAME = os.environ.get('DEPTH_MODEL_NAME', 'Intel/dpt-hybrid-midas')
    SENTENCE_TRANSFORMER_MODEL = os.environ.get('SENTENCE_TRANSFORMER_MODEL', 'all-MiniLM-L6-v2')
    
    # Legacy model paths (for backward compatibility)
    SAM3_MODEL_PATH = os.environ.get('SAM3_MODEL_PATH', 'models/sam3_checkpoint.pth')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 50)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    OUTPUT_FORMATS = ['gif', 'mp4', 'webm', 'glb', 'obj', 'ply']
    
    # Processing Configuration
    MAX_IMAGE_DIMENSION = int(os.environ.get('MAX_IMAGE_DIMENSION', 2048))
    DEFAULT_GIF_FRAMES = int(os.environ.get('DEFAULT_GIF_FRAMES', 36))
    DEFAULT_GIF_DURATION = float(os.environ.get('DEFAULT_GIF_DURATION', 0.1))
    
    # Trending Cache Configuration
    TRENDING_CACHE_TTL_HOURS = int(os.environ.get('TRENDING_CACHE_TTL_HOURS', 6))
    
    @staticmethod
    def init_directories():
        """Create necessary directories if they don't exist"""
        directories = [
            Config.UPLOAD_FOLDER,
            Config.MODELS_FOLDER,
            Config.EXPORTS_FOLDER,
            Config.CHROMADB_PATH,
            os.path.dirname(Config.SQLITE_DB_PATH.replace('sqlite:///', ''))
        ]
        
        for directory in directories:
            if directory and not directory.startswith('sqlite'):
                os.makedirs(directory, exist_ok=True)
        
        print("[OK] Data directories initialized")
    
    @staticmethod
    def get_upload_path(filename: str) -> str:
        """Get full path for uploaded file"""
        return os.path.join(Config.UPLOAD_FOLDER, filename)
    
    @staticmethod
    def get_model_path(filename: str) -> str:
        """Get full path for 3D model file"""
        return os.path.join(Config.MODELS_FOLDER, filename)
    
    @staticmethod
    def get_export_path(filename: str) -> str:
        """Get full path for export file"""
        return os.path.join(Config.EXPORTS_FOLDER, filename)


class DevelopmentConfig(Config):
    """Development-specific configuration"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production-specific configuration"""
    DEBUG = False
    FLASK_ENV = 'production'


class TestingConfig(Config):
    """Testing-specific configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CHROMADB_PATH = './data/test_chroma_db'


# Configuration mapping
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
