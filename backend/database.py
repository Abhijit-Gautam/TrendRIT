"""
Database setup for SQLite (SQLAlchemy) and ChromaDB (Vector Search)
Handles both transactional data and semantic search functionality
"""

import os
from flask_sqlalchemy import SQLAlchemy
import chromadb
from chromadb.config import Settings

# Initialize SQLAlchemy
db = SQLAlchemy()

# ChromaDB client (initialized lazily)
_chroma_client = None
_meme_templates_collection = None
_trending_context_collection = None


def init_db(app):
    """Initialize SQLite database with Flask app"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        print("[OK] SQLite database initialized successfully!")


def get_chroma_client(persist_directory='./data/chroma_db'):
    """Get or create ChromaDB client with persistent storage"""
    global _chroma_client
    
    if _chroma_client is None:
        os.makedirs(persist_directory, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        print(f"[OK] ChromaDB initialized at {persist_directory}")
    
    return _chroma_client


def get_meme_templates_collection(chroma_path='./data/chroma_db'):
    """Get or create the meme templates collection for semantic search"""
    global _meme_templates_collection
    
    if _meme_templates_collection is None:
        client = get_chroma_client(chroma_path)
        _meme_templates_collection = client.get_or_create_collection(
            name="meme_templates",
            metadata={
                "description": "Meme templates with semantic embeddings for matching",
                "hnsw:space": "cosine"  # Use cosine similarity
            }
        )
        print("[OK] Meme templates collection ready")
    
    return _meme_templates_collection


def get_trending_context_collection(chroma_path='./data/chroma_db'):
    """Get or create the trending context collection"""
    global _trending_context_collection
    
    if _trending_context_collection is None:
        client = get_chroma_client(chroma_path)
        _trending_context_collection = client.get_or_create_collection(
            name="trending_context",
            metadata={
                "description": "Trending topics and their semantic embeddings",
                "hnsw:space": "cosine"
            }
        )
        print("[OK] Trending context collection ready")
    
    return _trending_context_collection


def reset_chroma_collections(chroma_path='./data/chroma_db'):
    """Reset all ChromaDB collections (for development/testing)"""
    global _meme_templates_collection, _trending_context_collection
    
    client = get_chroma_client(chroma_path)
    
    # Delete existing collections
    try:
        client.delete_collection("meme_templates")
    except:
        pass
    
    try:
        client.delete_collection("trending_context")
    except:
        pass
    
    # Reset cached references
    _meme_templates_collection = None
    _trending_context_collection = None
    
    # Recreate collections
    get_meme_templates_collection(chroma_path)
    get_trending_context_collection(chroma_path)
    
    print("[OK] ChromaDB collections reset")


def init_all_databases(app):
    """Initialize all database connections"""
    # Initialize SQLite
    init_db(app)
    
    # Initialize ChromaDB collections
    chroma_path = app.config.get('CHROMADB_PATH', './data/chroma_db')
    get_meme_templates_collection(chroma_path)
    get_trending_context_collection(chroma_path)
    
    print("[OK] All databases initialized successfully!")
