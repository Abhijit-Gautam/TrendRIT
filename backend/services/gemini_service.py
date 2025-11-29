import google.generativeai as genai
from datetime import datetime
import json

class GeminiService:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def fetch_trending_content(self, category='memes'):
        """
        Fetch trending topics using Gemini
        Categories: memes, news, pop_culture, music
        """
        prompt = f"""
        List the top 10 trending {category} as of {datetime.now().strftime('%B %Y')}.
        For each item, provide:
        1. Title/Name
        2. Brief description (one sentence)
        3. Why it's trending
        4. Suggested 3D scene ideas for meme creation
        
        Return as JSON array with keys: title, description, reason, scene_ideas
        """
        
        response = self.model.generate_content(prompt)
        return self._parse_trends(response.text)
    
    def generate_scene_suggestions(self, meme_type, user_prompt=None):
        """Generate creative 3D scene suggestions for a meme"""
        prompt = f"""
        Generate 5 creative 3D scene ideas for "{meme_type}" meme.
        User context: {user_prompt or 'General funny meme'}
        
        For each scene, provide:
        - Scene description
        - Camera angles (list of 3-4 angles)
        - Recommended lighting
        - Props/background elements
        
        Return as JSON array.
        """
        
        response = self.model.generate_content(prompt)
        return self._parse_scenes(response.text)
    
    def _parse_trends(self, response_text):
        # Extract JSON from Gemini response
        try:
            # Gemini might wrap JSON in markdown code blocks
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0]
            else:
                json_str = response_text
            return json.loads(json_str)
        except:
            return []
    
    def _parse_scenes(self, response_text):
        # Extract JSON from Gemini response for scene suggestions
        try:
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0]
            else:
                json_str = response_text
            return json.loads(json_str)
        except:
            return []
