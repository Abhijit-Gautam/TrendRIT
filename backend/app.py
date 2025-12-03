"""
TrendRIT Backend - Main Flask Application
Local/self-hosted 3D meme generation service
"""

from flask import Flask
from flask_cors import CORS
import os

from config import Config
from database import init_all_databases, db

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
CORS(app)

# Initialize directories
Config.init_directories()

# Initialize databases (SQLite + ChromaDB)
init_all_databases(app)

# Initialize services (lazy loading to avoid import errors)
depth_service = None
reconstruction_service = None
intelligence_service = None
gemini_service = None
export_service = None


def init_services():
    """Initialize all services"""
    global depth_service, reconstruction_service, intelligence_service, gemini_service, export_service
    
    print("[INFO] Initializing services...")
    
    # Depth estimation service
    from services.depth_service import DepthService
    depth_service = DepthService(model_name=Config.DEPTH_MODEL_NAME)
    
    # 3D reconstruction service
    from services.reconstruction_service import ReconstructionService
    reconstruction_service = ReconstructionService(output_folder=Config.MODELS_FOLDER)
    
    # Intelligence service (ChromaDB + sentence-transformers)
    from services.intelligence_service import IntelligenceService
    intelligence_service = IntelligenceService(
        model_name=Config.SENTENCE_TRANSFORMER_MODEL,
        chroma_path=Config.CHROMADB_PATH
    )
    intelligence_service.initialize_templates()
    
    # Gemini service (optional, may fail if no API key)
    try:
        if Config.GEMINI_API_KEY:
            from services.gemini_service import GeminiService
            gemini_service = GeminiService(Config.GEMINI_API_KEY)
            print("[OK] Gemini service initialized")
        else:
            print("[WARNING] No GEMINI_API_KEY, Gemini service disabled")
    except Exception as e:
        print(f"[WARNING] Could not initialize Gemini service: {e}")
        gemini_service = None
    
    # Export service
    from services.export_service import ExportService
    export_service = ExportService(output_folder=Config.EXPORTS_FOLDER)
    
    print("[OK] All services initialized")
    
    return depth_service, reconstruction_service, intelligence_service, gemini_service, export_service


# Initialize services
depth_service, reconstruction_service, intelligence_service, gemini_service, export_service = init_services()

# Register routes
from routes import api, main, init_routes
init_routes(depth_service, reconstruction_service, intelligence_service, gemini_service, export_service)
app.register_blueprint(api)
app.register_blueprint(main)


# Legacy endpoints for backward compatibility
@app.route('/health', methods=['GET'])
def health_legacy():
    """Legacy health endpoint"""
    import torch
    return {'status': 'healthy', 'gpu_available': torch.cuda.is_available()}


@app.route('/upload', methods=['POST'])
def upload_legacy():
    """Legacy upload endpoint - redirects to new API"""
    from flask import request, jsonify
    from werkzeug.utils import secure_filename
    from models.sql_models import Project
    from PIL import Image
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id', 'anonymous')
    
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in Config.ALLOWED_EXTENSIONS:
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        project = Project.create(user_id=user_id)
        filename = secure_filename(f"{project.id}_{file.filename}")
        filepath = Config.get_upload_path(filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        project.update_paths(original_image_path=filepath)
        project.update_status('uploaded')
        
        return jsonify({
            'meme_id': project.id,
            'image_url': f'/static/uploads/{filename}',
            'message': 'Upload successful'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/trending', methods=['GET'])
def trending_legacy():
    """Legacy trending endpoint"""
    from flask import request, jsonify
    category = request.args.get('category', 'memes')
    
    try:
        if intelligence_service:
            cached = intelligence_service.get_trending_by_category(category)
            if cached:
                return jsonify({'category': category, 'trends': cached}), 200
        
        if gemini_service:
            trends = gemini_service.fetch_trending_content(category)
            return jsonify({'category': category, 'trends': trends}), 200
        
        # Mock data fallback
        mock_trends = {
            'category': category,
            'trends': [
                {'title': 'Drake Meme', 'description': 'Classic approval/disapproval format', 'reason': 'Timeless', 'scene_ideas': ['Office', 'Concert', 'Wedding']},
                {'title': 'Loss Meme', 'description': '4-panel webcomic reference', 'reason': 'Internet culture', 'scene_ideas': ['Gaming', 'Work', 'School']},
                {'title': 'Stonks', 'description': 'Poor grammar stock market meme', 'reason': 'Financial humor', 'scene_ideas': ['Market', 'Trading', 'Office']}
            ],
            'note': 'Mock data'
        }
        return jsonify(mock_trends), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*50)
    print("TrendRIT Backend - Local/Self-Hosted")
    print("="*50)
    print(f"Upload folder: {Config.UPLOAD_FOLDER}")
    print(f"Models folder: {Config.MODELS_FOLDER}")
    print(f"Exports folder: {Config.EXPORTS_FOLDER}")
    print(f"ChromaDB path: {Config.CHROMADB_PATH}")
    print("="*50 + "\n")
    
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)