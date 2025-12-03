"""
ChromaDB vector schemas and helper functions
Defines the structure for vector embeddings used in semantic search
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import uuid


@dataclass
class MemeTemplateDocument:
    """
    Schema for meme template documents in ChromaDB
    Used for semantic matching between trends and templates
    """
    id: str
    name: str
    description: str
    tags: List[str]
    scene_types: List[str]
    mood: str  # funny, serious, sarcastic, wholesome, etc.
    format_type: str  # single_image, multi_panel, reaction, etc.
    
    # Metadata for filtering
    popularity_score: float = 0.0
    usage_count: int = 0
    
    def to_chroma_document(self) -> Dict[str, Any]:
        """Convert to ChromaDB document format"""
        # Combine all text fields for embedding
        text_content = f"{self.name}. {self.description}. Tags: {', '.join(self.tags)}. " \
                       f"Scenes: {', '.join(self.scene_types)}. Mood: {self.mood}."
        
        return {
            'id': self.id,
            'document': text_content,
            'metadata': {
                'name': self.name,
                'description': self.description,
                'tags': ','.join(self.tags),
                'scene_types': ','.join(self.scene_types),
                'mood': self.mood,
                'format_type': self.format_type,
                'popularity_score': self.popularity_score,
                'usage_count': self.usage_count
            }
        }
    
    @staticmethod
    def from_chroma_result(result: Dict[str, Any]) -> 'MemeTemplateDocument':
        """Create from ChromaDB query result"""
        metadata = result.get('metadata', {})
        return MemeTemplateDocument(
            id=result.get('id', ''),
            name=metadata.get('name', ''),
            description=metadata.get('description', ''),
            tags=metadata.get('tags', '').split(',') if metadata.get('tags') else [],
            scene_types=metadata.get('scene_types', '').split(',') if metadata.get('scene_types') else [],
            mood=metadata.get('mood', ''),
            format_type=metadata.get('format_type', ''),
            popularity_score=metadata.get('popularity_score', 0.0),
            usage_count=metadata.get('usage_count', 0)
        )


@dataclass
class TrendingContextDocument:
    """
    Schema for trending context documents in ChromaDB
    Used for tracking and matching trending topics
    """
    id: str
    title: str
    description: str
    category: str  # memes, news, pop_culture, music, gaming
    reason: str  # Why it's trending
    scene_ideas: List[str]
    
    # Timestamps as strings for metadata
    fetched_at: str = ""
    expires_at: str = ""
    
    # Source information
    source: str = "gemini"  # gemini, manual, external
    confidence_score: float = 1.0
    
    def to_chroma_document(self) -> Dict[str, Any]:
        """Convert to ChromaDB document format"""
        text_content = f"{self.title}. {self.description}. Category: {self.category}. " \
                       f"Why trending: {self.reason}. Scene ideas: {', '.join(self.scene_ideas)}."
        
        return {
            'id': self.id,
            'document': text_content,
            'metadata': {
                'title': self.title,
                'description': self.description,
                'category': self.category,
                'reason': self.reason,
                'scene_ideas': ','.join(self.scene_ideas),
                'fetched_at': self.fetched_at,
                'expires_at': self.expires_at,
                'source': self.source,
                'confidence_score': self.confidence_score
            }
        }
    
    @staticmethod
    def from_chroma_result(result: Dict[str, Any]) -> 'TrendingContextDocument':
        """Create from ChromaDB query result"""
        metadata = result.get('metadata', {})
        return TrendingContextDocument(
            id=result.get('id', ''),
            title=metadata.get('title', ''),
            description=metadata.get('description', ''),
            category=metadata.get('category', ''),
            reason=metadata.get('reason', ''),
            scene_ideas=metadata.get('scene_ideas', '').split(',') if metadata.get('scene_ideas') else [],
            fetched_at=metadata.get('fetched_at', ''),
            expires_at=metadata.get('expires_at', ''),
            source=metadata.get('source', 'gemini'),
            confidence_score=metadata.get('confidence_score', 1.0)
        )


def generate_template_id() -> str:
    """Generate unique ID for meme template"""
    return f"template_{uuid.uuid4().hex[:12]}"


def generate_trending_id() -> str:
    """Generate unique ID for trending context"""
    return f"trend_{uuid.uuid4().hex[:12]}"


# Default meme templates for seeding the database
DEFAULT_MEME_TEMPLATES = [
    MemeTemplateDocument(
        id=generate_template_id(),
        name="Drake Approving/Disapproving",
        description="Two-panel meme showing Drake rejecting one thing and approving another",
        tags=["drake", "approval", "disapproval", "comparison", "choice"],
        scene_types=["office", "studio", "indoor"],
        mood="funny",
        format_type="multi_panel",
        popularity_score=0.95
    ),
    MemeTemplateDocument(
        id=generate_template_id(),
        name="Distracted Boyfriend",
        description="Man looking at another woman while his girlfriend looks on disapprovingly",
        tags=["distracted", "boyfriend", "jealousy", "temptation", "relationship"],
        scene_types=["street", "outdoor", "urban"],
        mood="funny",
        format_type="single_image",
        popularity_score=0.92
    ),
    MemeTemplateDocument(
        id=generate_template_id(),
        name="Woman Yelling at Cat",
        description="Split image of woman yelling and confused cat at dinner table",
        tags=["cat", "yelling", "dinner", "confusion", "argument"],
        scene_types=["dining", "indoor", "home"],
        mood="funny",
        format_type="multi_panel",
        popularity_score=0.90
    ),
    MemeTemplateDocument(
        id=generate_template_id(),
        name="Expanding Brain",
        description="Multi-panel showing progressively 'enlightened' brain states",
        tags=["brain", "intelligence", "evolution", "levels", "progression"],
        scene_types=["abstract", "cosmic", "mental"],
        mood="sarcastic",
        format_type="multi_panel",
        popularity_score=0.85
    ),
    MemeTemplateDocument(
        id=generate_template_id(),
        name="Stonks",
        description="Businessman with stonks arrow going up, representing poor financial decisions",
        tags=["stonks", "stocks", "money", "finance", "business"],
        scene_types=["office", "market", "business"],
        mood="sarcastic",
        format_type="single_image",
        popularity_score=0.88
    ),
    MemeTemplateDocument(
        id=generate_template_id(),
        name="This is Fine",
        description="Dog sitting in burning room saying 'This is fine'",
        tags=["fire", "dog", "denial", "disaster", "calm"],
        scene_types=["indoor", "disaster", "home"],
        mood="sarcastic",
        format_type="single_image",
        popularity_score=0.87
    ),
    MemeTemplateDocument(
        id=generate_template_id(),
        name="Success Kid",
        description="Toddler with fist pump celebrating small victories",
        tags=["success", "victory", "celebration", "kid", "achievement"],
        scene_types=["beach", "outdoor", "casual"],
        mood="wholesome",
        format_type="single_image",
        popularity_score=0.80
    ),
    MemeTemplateDocument(
        id=generate_template_id(),
        name="Two Buttons",
        description="Person sweating while choosing between two buttons",
        tags=["choice", "decision", "anxiety", "dilemma", "buttons"],
        scene_types=["abstract", "indoor", "office"],
        mood="funny",
        format_type="single_image",
        popularity_score=0.82
    ),
]


def seed_meme_templates(collection):
    """Seed the meme templates collection with default templates"""
    for template in DEFAULT_MEME_TEMPLATES:
        doc = template.to_chroma_document()
        try:
            collection.add(
                ids=[doc['id']],
                documents=[doc['document']],
                metadatas=[doc['metadata']]
            )
        except Exception as e:
            # Document might already exist
            pass
    
    print(f"[OK] Seeded {len(DEFAULT_MEME_TEMPLATES)} meme templates")
