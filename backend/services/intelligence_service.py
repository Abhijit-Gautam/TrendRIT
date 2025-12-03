"""
Intelligence Service for ChromaDB trending logic
Uses sentence-transformers for semantic search and matching
"""

from sentence_transformers import SentenceTransformer
from database import get_meme_templates_collection, get_trending_context_collection
from models.vector_schemas import (
    MemeTemplateDocument, 
    TrendingContextDocument,
    generate_trending_id,
    seed_meme_templates
)
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np


class IntelligenceService:
    """
    Service for semantic search and trending topic management using ChromaDB
    """
    
    def __init__(self, model_name='all-MiniLM-L6-v2', chroma_path='./data/chroma_db'):
        """
        Initialize the intelligence service
        
        Args:
            model_name: Sentence transformer model for embeddings
            chroma_path: Path to ChromaDB persistent storage
        """
        self.model = SentenceTransformer(model_name)
        self.chroma_path = chroma_path
        
        # Initialize collections
        self._templates_collection = None
        self._trending_collection = None
        
        print(f"[OK] IntelligenceService initialized with model: {model_name}")
    
    @property
    def templates_collection(self):
        """Lazy load templates collection"""
        if self._templates_collection is None:
            self._templates_collection = get_meme_templates_collection(self.chroma_path)
        return self._templates_collection
    
    @property
    def trending_collection(self):
        """Lazy load trending collection"""
        if self._trending_collection is None:
            self._trending_collection = get_trending_context_collection(self.chroma_path)
        return self._trending_collection
    
    def initialize_templates(self):
        """Initialize and seed meme templates if empty"""
        count = self.templates_collection.count()
        if count == 0:
            seed_meme_templates(self.templates_collection)
            print(f"[OK] Meme templates seeded")
        else:
            print(f"[OK] Found {count} existing meme templates")
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using sentence-transformers"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def add_trend(self, trend_data: Dict[str, Any], ttl_hours: int = 6) -> str:
        """
        Add a trending topic to ChromaDB
        
        Args:
            trend_data: Dictionary with title, description, category, reason, scene_ideas
            ttl_hours: Time-to-live in hours
            
        Returns:
            Trend ID
        """
        trend_id = generate_trending_id()
        now = datetime.utcnow()
        
        doc = TrendingContextDocument(
            id=trend_id,
            title=trend_data.get('title', ''),
            description=trend_data.get('description', ''),
            category=trend_data.get('category', 'memes'),
            reason=trend_data.get('reason', ''),
            scene_ideas=trend_data.get('scene_ideas', []),
            fetched_at=now.isoformat(),
            expires_at=(now + timedelta(hours=ttl_hours)).isoformat(),
            source=trend_data.get('source', 'gemini'),
            confidence_score=trend_data.get('confidence_score', 1.0)
        )
        
        chroma_doc = doc.to_chroma_document()
        
        # Generate embedding
        embedding = self.get_embedding(chroma_doc['document'])
        
        self.trending_collection.add(
            ids=[chroma_doc['id']],
            documents=[chroma_doc['document']],
            metadatas=[chroma_doc['metadata']],
            embeddings=[embedding]
        )
        
        return trend_id
    
    def add_trends_batch(self, trends: List[Dict[str, Any]], ttl_hours: int = 6) -> List[str]:
        """Add multiple trending topics at once"""
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        now = datetime.utcnow()
        
        for trend_data in trends:
            trend_id = generate_trending_id()
            
            doc = TrendingContextDocument(
                id=trend_id,
                title=trend_data.get('title', ''),
                description=trend_data.get('description', ''),
                category=trend_data.get('category', 'memes'),
                reason=trend_data.get('reason', ''),
                scene_ideas=trend_data.get('scene_ideas', []),
                fetched_at=now.isoformat(),
                expires_at=(now + timedelta(hours=ttl_hours)).isoformat(),
                source=trend_data.get('source', 'gemini')
            )
            
            chroma_doc = doc.to_chroma_document()
            
            ids.append(chroma_doc['id'])
            documents.append(chroma_doc['document'])
            metadatas.append(chroma_doc['metadata'])
            embeddings.append(self.get_embedding(chroma_doc['document']))
        
        if ids:
            self.trending_collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
        
        return ids
    
    def search_trends(self, query: str, category: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Semantic search for trending topics
        
        Args:
            query: Search query
            category: Optional category filter
            limit: Maximum results
            
        Returns:
            List of matching trends with similarity scores
        """
        query_embedding = self.get_embedding(query)
        
        where_filter = None
        if category:
            where_filter = {"category": category}
        
        results = self.trending_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter
        )
        
        trends = []
        if results and results['ids'] and results['ids'][0]:
            for i, trend_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0
                
                trends.append({
                    'id': trend_id,
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', ''),
                    'category': metadata.get('category', ''),
                    'reason': metadata.get('reason', ''),
                    'scene_ideas': metadata.get('scene_ideas', '').split(',') if metadata.get('scene_ideas') else [],
                    'similarity_score': 1 - distance,  # Convert distance to similarity
                    'source': metadata.get('source', '')
                })
        
        return trends
    
    def match_trend_to_templates(self, trend_query: str, limit: int = 5) -> List[Dict]:
        """
        Match a trending topic to suitable meme templates
        
        Args:
            trend_query: Trend description or keywords
            limit: Maximum templates to return
            
        Returns:
            List of matching meme templates with scores
        """
        query_embedding = self.get_embedding(trend_query)
        
        results = self.templates_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        templates = []
        if results and results['ids'] and results['ids'][0]:
            for i, template_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0
                
                templates.append({
                    'id': template_id,
                    'name': metadata.get('name', ''),
                    'description': metadata.get('description', ''),
                    'tags': metadata.get('tags', '').split(',') if metadata.get('tags') else [],
                    'scene_types': metadata.get('scene_types', '').split(',') if metadata.get('scene_types') else [],
                    'mood': metadata.get('mood', ''),
                    'format_type': metadata.get('format_type', ''),
                    'match_score': 1 - distance
                })
        
        return templates
    
    def get_trending_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """
        Get trending topics by category
        
        Args:
            category: Category to filter by
            limit: Maximum results
            
        Returns:
            List of trending topics
        """
        results = self.trending_collection.get(
            where={"category": category},
            limit=limit
        )
        
        trends = []
        if results and results['ids']:
            for i, trend_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                
                # Check if not expired
                expires_at = metadata.get('expires_at', '')
                if expires_at:
                    try:
                        expire_time = datetime.fromisoformat(expires_at)
                        if expire_time < datetime.utcnow():
                            continue  # Skip expired
                    except:
                        pass
                
                trends.append({
                    'id': trend_id,
                    'title': metadata.get('title', ''),
                    'description': metadata.get('description', ''),
                    'category': metadata.get('category', ''),
                    'reason': metadata.get('reason', ''),
                    'scene_ideas': metadata.get('scene_ideas', '').split(',') if metadata.get('scene_ideas') else []
                })
        
        return trends
    
    def add_meme_template(self, template_data: Dict[str, Any]) -> str:
        """
        Add a new meme template to the collection
        
        Args:
            template_data: Template information
            
        Returns:
            Template ID
        """
        from models.vector_schemas import generate_template_id
        
        template = MemeTemplateDocument(
            id=generate_template_id(),
            name=template_data.get('name', ''),
            description=template_data.get('description', ''),
            tags=template_data.get('tags', []),
            scene_types=template_data.get('scene_types', []),
            mood=template_data.get('mood', 'funny'),
            format_type=template_data.get('format_type', 'single_image'),
            popularity_score=template_data.get('popularity_score', 0.5)
        )
        
        chroma_doc = template.to_chroma_document()
        embedding = self.get_embedding(chroma_doc['document'])
        
        self.templates_collection.add(
            ids=[chroma_doc['id']],
            documents=[chroma_doc['document']],
            metadatas=[chroma_doc['metadata']],
            embeddings=[embedding]
        )
        
        return template.id
    
    def get_all_templates(self, limit: int = 100) -> List[Dict]:
        """Get all meme templates"""
        results = self.templates_collection.get(limit=limit)
        
        templates = []
        if results and results['ids']:
            for i, template_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                templates.append({
                    'id': template_id,
                    'name': metadata.get('name', ''),
                    'description': metadata.get('description', ''),
                    'tags': metadata.get('tags', '').split(',') if metadata.get('tags') else [],
                    'scene_types': metadata.get('scene_types', '').split(',') if metadata.get('scene_types') else [],
                    'mood': metadata.get('mood', ''),
                    'format_type': metadata.get('format_type', ''),
                    'popularity_score': metadata.get('popularity_score', 0)
                })
        
        return templates
    
    def clear_expired_trends(self):
        """Remove expired trending topics"""
        now = datetime.utcnow().isoformat()
        
        # Get all trends and filter expired ones
        results = self.trending_collection.get()
        
        expired_ids = []
        if results and results['ids']:
            for i, trend_id in enumerate(results['ids']):
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                expires_at = metadata.get('expires_at', '')
                
                if expires_at and expires_at < now:
                    expired_ids.append(trend_id)
        
        if expired_ids:
            self.trending_collection.delete(ids=expired_ids)
            print(f"[OK] Cleared {len(expired_ids)} expired trends")
        
        return len(expired_ids)
    
    def get_recommended_templates_for_image(self, image_description: str, mood: str = None) -> List[Dict]:
        """
        Get recommended meme templates based on image content
        
        Args:
            image_description: Description of the uploaded image
            mood: Optional mood filter
            
        Returns:
            List of recommended templates
        """
        query = f"Image showing: {image_description}"
        if mood:
            query += f" with {mood} mood"
        
        return self.match_trend_to_templates(query, limit=5)
