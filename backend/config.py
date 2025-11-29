import os
from google.cloud import firestore
import google.generativeai as genai

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    UPLOAD_FOLDER = 'uploads/'
    OUTPUT_FOLDER = 'outputs/'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Firestore
    FIRESTORE_PROJECT_ID = os.environ.get('FIRESTORE_PROJECT_ID')
    db = firestore.Client(project=FIRESTORE_PROJECT_ID)
    
    # Gemini API
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Model Paths
    SAM3_MODEL_PATH = 'models/sam3_checkpoint.pth'
    DEPTH_MODEL_NAME = 'Intel/dpt-hybrid-midas'  # or LiheYoung/depth-anything-large-hf
    
    # Processing
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    OUTPUT_FORMATS = ['gif', 'mp4', 'glb']
