import os
from pymongo import MongoClient
import google.generativeai as genai
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
    UPLOAD_FOLDER = 'uploads/'
    OUTPUT_FOLDER = 'outputs/'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # MongoDB Configuration
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb+srv://kamalkarteek1:rvZSeyVHhgOd2fbE@gbh.iliw2.mongodb.net/trendrit?retryWrites=true&w=majority')
    MONGO_DB_NAME = 'trendrit'
    
    # Initialize MongoDB Client
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        mongo_client.admin.command('ping')
        db = mongo_client[MONGO_DB_NAME]
        print("[OK] MongoDB Atlas connected successfully!")
    except Exception as e:
        print(f"[WARNING] Could not connect to MongoDB: {e}")
        db = None
        mongo_client = None
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET
    )
    
    # Model Paths
    SAM3_MODEL_PATH = os.environ.get('SAM3_MODEL_PATH', 'models/sam3_checkpoint.pth')
    DEPTH_MODEL_NAME = 'Intel/dpt-hybrid-midas'  # or LiheYoung/depth-anything-large-hf
    
    # Processing
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    OUTPUT_FORMATS = ['gif', 'mp4', 'glb']
    MAX_UPLOAD_SIZE_MB = int(os.environ.get('MAX_UPLOAD_SIZE_MB', 50))
