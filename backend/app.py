from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import open3d as o3d
from config import Config
from services.sam3_service import SAM3Service
from services.depth_service import DepthService
from services.gemini_service import GeminiService
from services.export_service import ExportService
from models.firestore_models import MemeModel, TrendingCache
from utils.helpers import allowed_file, validate_image

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Initialize services
sam3 = SAM3Service()
depth = DepthService()
gemini = GeminiService(Config.GEMINI_API_KEY)
exporter = ExportService()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'gpu_available': sam3.device == 'cuda'})

@app.route('/upload', methods=['POST'])
def upload_meme():
    """Upload meme image and get segmentation"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Create database entry
    meme_id = MemeModel.create(
        user_id=request.form.get('user_id', 'anonymous'),
        image_url=filepath,
        metadata={'original_filename': filename}
    )

    return jsonify({'meme_id': meme_id, 'message': 'Upload successful'}), 200


@app.route('/generate-3d/<meme_id>', methods=['POST'])
def generate_3d(meme_id):
    """Generate 3D model from uploaded meme"""
    meme_data = MemeModel.get(meme_id)
    if not meme_data:
        return jsonify({'error': 'Meme not found'}), 404


    try:
        # Step 1: Segment subjects
        subjects = sam3.segment_subjects(meme_data['image_url'])
        
        # Step 2: Generate 3D for each subject
        results = []
        for subject in subjects:
            depth_map = depth.generate_depth_map(subject['image'])
            mesh, pcd = depth.create_3d_mesh(
                subject['image'], 
                depth_map, 
                subject['mask']
            )
            
            # Save mesh
            mesh_path = f"outputs/{meme_id}_subject_{subject['id']}.glb"
            o3d.io.write_triangle_mesh(mesh_path, mesh)
            
            results.append({
                'subject_id': subject['id'],
                'mesh_url': mesh_path,
                'bbox': subject['bbox']
            })
        
        # Update database
        MemeModel.update_status(meme_id, 'completed', results)
        
        return jsonify({'status': 'success', 'results': results}), 200
        
    except Exception as e:
        MemeModel.update_status(meme_id, 'failed')
        return jsonify({'error': str(e)}), 500

@app.route('/export/<meme_id>', methods=['POST'])
def export_meme(meme_id):
    """Export as GIF/video with scene"""
    data = request.json
    format_type = data.get('format', 'gif')
    scene_id = data.get('scene_id', 'default')

    meme_data = MemeModel.get(meme_id)
    if not meme_data or meme_data['status'] != 'completed':
        return jsonify({'error': 'Meme not ready'}), 400

    try:
        # Get first mesh
        mesh_path = meme_data['outputs']['mesh_url']
        
        if format_type == 'gif':
            output_path = exporter.create_rotating_gif(mesh_path, meme_id)
            return send_file(output_path, mimetype='image/gif')
        
        return jsonify({'error': 'Format not supported yet'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/trending', methods=['GET'])
def get_trending():
    """Get trending content for meme ideas"""
    category = request.args.get('category', 'memes')

    # Check cache first
    cached = TrendingCache.get(category)
    if cached:
        return jsonify(cached), 200

    # Fetch fresh data
    trends = gemini.fetch_trending_content(category)
    TrendingCache.store(category, trends)

    return jsonify(trends), 200

@app.route('/scene-suggestions', methods=['POST'])
def get_scene_suggestions():
    """Get AI-generated scene suggestions"""
    data = request.json
    meme_type = data.get('meme_type', 'funny')

    suggestions = gemini.generate_scene_suggestions(meme_type)
    return jsonify(suggestions), 200

if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)