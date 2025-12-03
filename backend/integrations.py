"""
Integrations module for external services
Handles Gemini API and trending data integrations
"""

import google.generativeai as genai
from datetime import datetime
import json
from typing import List, Dict, Any, Optional
import requests


class GeminiIntegration:
    """
    Integration with Google Gemini API for trending content and caption generation
    """
    
    def __init__(self, api_key: str, model_name: str = 'gemini-pro'):
        """
        Initialize Gemini integration
        
        Args:
            api_key: Google API key for Gemini
            model_name: Gemini model to use
        """
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.enabled = True
            print(f"[OK] Gemini integration enabled with model: {model_name}")
        else:
            self.model = None
            self.enabled = False
            print("[WARNING] Gemini integration disabled (no API key)")
    
    def fetch_trending_topics(self, category: str = 'memes', count: int = 10) -> List[Dict]:
        """
        Fetch trending topics using Gemini
        
        Args:
            category: Category to fetch (memes, news, pop_culture, etc.)
            count: Number of trends to fetch
            
        Returns:
            List of trending topics
        """
        if not self.enabled:
            return self._get_mock_trends(category)
        
        prompt = f"""
        List the top {count} trending {category} as of {datetime.now().strftime('%B %Y')}.
        For each item, provide:
        1. Title/Name
        2. Brief description (one sentence)
        3. Why it's trending
        4. Suggested 3D scene ideas for meme creation (list of 3-4 ideas)
        
        Return ONLY valid JSON array with keys: title, description, reason, scene_ideas
        No additional text or markdown formatting.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            print(f"[ERROR] Gemini trending fetch failed: {e}")
            return self._get_mock_trends(category)
    
    def generate_meme_caption(
        self, 
        image_description: str, 
        meme_template: str = None,
        mood: str = 'funny'
    ) -> Dict[str, Any]:
        """
        Generate meme caption based on image and context
        
        Args:
            image_description: Description of the image content
            meme_template: Optional meme template being used
            mood: Desired mood (funny, sarcastic, wholesome, etc.)
            
        Returns:
            Dictionary with caption suggestions
        """
        if not self.enabled:
            return self._get_mock_captions()
        
        template_context = f" using the '{meme_template}' meme format" if meme_template else ""
        
        prompt = f"""
        Generate 5 creative meme captions for an image showing: {image_description}
        The tone should be {mood}{template_context}.
        
        Return ONLY valid JSON with structure:
        {{
            "captions": [
                {{"text": "caption text", "placement": "top/bottom/both"}}
            ],
            "recommended_font": "suggested font style",
            "estimated_virality": "low/medium/high"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_json_response(response.text)
        except Exception as e:
            print(f"[ERROR] Gemini caption generation failed: {e}")
            return self._get_mock_captions()
    
    def generate_scene_suggestions(
        self, 
        meme_type: str, 
        user_context: str = None
    ) -> Dict[str, Any]:
        """
        Generate 3D scene suggestions for a meme
        
        Args:
            meme_type: Type of meme being created
            user_context: Additional context from user
            
        Returns:
            Dictionary with scene suggestions
        """
        if not self.enabled:
            return self._get_mock_scenes(meme_type)
        
        context = f"\nUser context: {user_context}" if user_context else ""
        
        prompt = f"""
        Generate 5 creative 3D scene ideas for a "{meme_type}" meme.{context}
        
        For each scene, provide:
        - Scene name
        - Description (2-3 sentences)
        - Camera angles (list of 3-4 angles)
        - Lighting style
        - Props/background elements
        
        Return ONLY valid JSON array with scene objects.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            return {'meme_type': meme_type, 'scenes': result}
        except Exception as e:
            print(f"[ERROR] Gemini scene suggestions failed: {e}")
            return self._get_mock_scenes(meme_type)
    
    def analyze_image_content(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze image content for meme suggestions
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Analysis results with meme suggestions
        """
        if not self.enabled:
            return {'description': 'Image analysis unavailable', 'suggestions': []}
        
        try:
            import PIL.Image
            img = PIL.Image.open(image_path)
            
            prompt = """
            Analyze this image and provide:
            1. Brief description of the content
            2. Detected subjects/objects
            3. Mood/tone of the image
            4. Suggested meme formats that would work well
            5. Potential caption ideas
            
            Return as JSON with keys: description, subjects, mood, suggested_formats, caption_ideas
            """
            
            response = self.model.generate_content([prompt, img])
            return self._parse_json_response(response.text)
        except Exception as e:
            print(f"[ERROR] Image analysis failed: {e}")
            return {'description': 'Analysis failed', 'suggestions': [], 'error': str(e)}
    
    def _parse_json_response(self, response_text: str) -> Any:
        """Parse JSON from Gemini response"""
        # Clean up response
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'[\[\{].*[\]\}]', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
    
    def _get_mock_trends(self, category: str) -> List[Dict]:
        """Return mock trending data"""
        return [
            {
                'title': 'Drake Approving Meme',
                'description': 'Two-panel format showing rejection and approval',
                'reason': 'Versatile and timeless format',
                'scene_ideas': ['Office', 'Studio', 'Casual indoor']
            },
            {
                'title': 'Distracted Boyfriend',
                'description': 'Man looking at another woman while girlfriend disapproves',
                'reason': 'Highly relatable for comparisons',
                'scene_ideas': ['Street', 'Mall', 'Party']
            },
            {
                'title': 'This is Fine',
                'description': 'Dog in burning room maintaining composure',
                'reason': 'Perfect for 2024 mood',
                'scene_ideas': ['Office on fire', 'Disaster scene', 'Chaotic room']
            }
        ]
    
    def _get_mock_captions(self) -> Dict[str, Any]:
        """Return mock caption data"""
        return {
            'captions': [
                {'text': 'When the code works on the first try', 'placement': 'top'},
                {'text': 'Nobody: / Me at 3am:', 'placement': 'both'},
                {'text': 'POV: You just discovered a new bug', 'placement': 'top'}
            ],
            'recommended_font': 'Impact',
            'estimated_virality': 'medium'
        }
    
    def _get_mock_scenes(self, meme_type: str) -> Dict[str, Any]:
        """Return mock scene suggestions"""
        return {
            'meme_type': meme_type,
            'scenes': [
                {
                    'name': 'Office Environment',
                    'description': 'Corporate setting with cubicles and computers',
                    'camera_angles': ['Front view', 'Over shoulder', '45 degree'],
                    'lighting': 'Fluorescent office lighting',
                    'props': ['Computer', 'Desk', 'Coffee mug', 'Stack of papers']
                },
                {
                    'name': 'Living Room',
                    'description': 'Cozy home setting with couch and TV',
                    'camera_angles': ['Wide shot', 'Close up', 'Side profile'],
                    'lighting': 'Warm ambient lighting',
                    'props': ['Couch', 'TV', 'Remote', 'Snacks']
                }
            ]
        }


class TrendingDataFetcher:
    """
    Fetches trending data from various sources
    Can be extended to support multiple data providers
    """
    
    def __init__(self):
        self.sources = []
    
    def add_source(self, name: str, fetch_func):
        """Add a data source"""
        self.sources.append({'name': name, 'fetch': fetch_func})
    
    def fetch_all(self, category: str = 'memes') -> List[Dict]:
        """Fetch from all sources and combine"""
        all_trends = []
        
        for source in self.sources:
            try:
                trends = source['fetch'](category)
                for trend in trends:
                    trend['source'] = source['name']
                all_trends.extend(trends)
            except Exception as e:
                print(f"[ERROR] Failed to fetch from {source['name']}: {e}")
        
        return all_trends
    
    @staticmethod
    def fetch_from_reddit(category: str, limit: int = 10) -> List[Dict]:
        """
        Fetch trending from Reddit (example implementation)
        Note: Requires Reddit API credentials for production use
        """
        # This is a placeholder - in production, use PRAW library
        return []
    
    @staticmethod
    def fetch_from_twitter(category: str, limit: int = 10) -> List[Dict]:
        """
        Fetch trending from Twitter/X (example implementation)
        Note: Requires Twitter API credentials for production use
        """
        # This is a placeholder - in production, use Twitter API
        return []
