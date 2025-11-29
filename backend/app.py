from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
import open3d as o3d
from config import Config
from services.sam3_service import SAM3Service
from services.depth_service import DepthService
from services.gemini_service import GeminiService
from services.export_service import ExportService
from services.storage_service import CloudinaryStorageService
from models.mongodb_models import MemeModel, SubjectModel, ExportModel, UserModel, TrendingCache
from utils.helpers import allowed_file, validate_image

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
CORS(app)

# Initialize services
sam3 = SAM3Service()
depth = DepthService()
gemini = GeminiService(Config.GEMINI_API_KEY)
exporter = ExportService()
storage = CloudinaryStorageService()

# Serve static files (for local storage fallback)
@app.route('/static/uploads/<path:filename>')
def serve_static_uploads(filename):
    return send_from_directory('static/uploads', filename)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'gpu_available': sam3.device == 'cuda'})

@app.route('/upload', methods=['POST'])
def upload_meme():
    """Upload meme image to Cloudinary and create Firestore entry"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id', 'anonymous')
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Save temporarily to process
        filename = secure_filename(file.filename)
        temp_filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        file.save(temp_filepath)

        # Upload to Cloudinary
        upload_result = storage.upload_meme_image(
            temp_filepath,
            user_id,
            filename
        )
        
        # Create Firestore document
        meme_id = MemeModel.create(
            user_id=user_id,
            image_url=upload_result['url'],
            metadata={
                'original_filename': filename,
                'cloudinary_public_id': upload_result['public_id'],
                'width': upload_result.get('width'),
                'height': upload_result.get('height')
            }
        )
        
        # Update user stats
        UserModel.increment_meme_count(user_id)
        
        # Clean up temporary file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

        return jsonify({
            'meme_id': meme_id,
            'image_url': upload_result['url'],
            'message': 'Upload successful'
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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
        outputs = []
        
        for idx, subject in enumerate(subjects):
            depth_map = depth.generate_depth_map(subject['image'])
            mesh, pcd = depth.create_3d_mesh(
                subject['image'], 
                depth_map, 
                subject['mask']
            )
            
            # Save mesh temporarily
            os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
            mesh_local_path = os.path.join(Config.OUTPUT_FOLDER, f"{meme_id}_subject_{idx}.glb")
            o3d.io.write_triangle_mesh(mesh_local_path, mesh)
            
            # Upload mesh to Cloudinary
            mesh_upload = storage.upload_mesh(mesh_local_path, meme_id, idx)
            
            # Create Firestore subject document
            subject_id = SubjectModel.create(
                meme_id=meme_id,
                subject_index=idx,
                segmentation_data=subject,
                mesh_url=mesh_upload['url']
            )
            
            results.append({
                'subject_id': subject_id,
                'mesh_url': mesh_upload['url'],
                'bbox': subject.get('bbox'),
                'public_id': mesh_upload['public_id']
            })
            
            outputs.append({
                'type': 'mesh',
                'url': mesh_upload['url'],
                'public_id': mesh_upload['public_id']
            })
            
            # Clean up temporary file
            if os.path.exists(mesh_local_path):
                os.remove(mesh_local_path)
        
        # Update database with completed status and outputs
        MemeModel.update_status(meme_id, 'completed')
        MemeModel.update_outputs(meme_id, outputs)
        
        return jsonify({'status': 'success', 'results': results}), 200
        
    except Exception as e:
        MemeModel.update_status(meme_id, 'failed', error_message=str(e))
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
        # Get mesh URLs from outputs
        subjects = SubjectModel.get_by_meme(meme_id)
        if not subjects:
            return jsonify({'error': 'No subjects found'}), 404
        
        # Get first subject mesh
        first_subject = subjects[0]
        
        # Download mesh temporarily for processing
        mesh_local_path = os.path.join(Config.OUTPUT_FOLDER, f"temp_mesh_{meme_id}.glb")
        os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
        
        # For now, use the mesh URL directly if supported, or download it
        # This is a simplified version - you may need to download the mesh first
        
        if format_type == 'gif':
            # Create GIF from mesh
            output_path = exporter.create_rotating_gif(
                first_subject['mesh_url'], 
                meme_id
            )
            
            # Upload GIF to Cloudinary
            gif_upload = storage.upload_gif(output_path, meme_id)
            
            # Record export in Firestore
            export_id = ExportModel.create(
                meme_id=meme_id,
                export_type='gif',
                export_url=gif_upload['url'],
                metadata={
                    'frames': gif_upload.get('frames'),
                    'cloudinary_public_id': gif_upload['public_id']
                }
            )
            
            # Clean up temporary file
            if os.path.exists(output_path):
                os.remove(output_path)
            
            return jsonify({
                'export_id': export_id,
                'url': gif_upload['url'],
                'format': 'gif'
            }), 200
        
        return jsonify({'error': 'Format not supported yet'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/trending', methods=['GET'])
def get_trending():
    """Get trending content for meme ideas"""
    category = request.args.get('category', 'memes')

    try:
        # Check cache first
        cached = TrendingCache.get(category)
        if cached:
            return jsonify(cached), 200
    except Exception as cache_err:
        # If Firestore fails, return mock data
        pass

    try:
        # Fetch fresh data
        trends = gemini.fetch_trending_content(category)
        try:
            TrendingCache.store(category, trends)
        except:
            pass  # Ignore cache storage errors
        return jsonify(trends), 200
    
    except Exception as e:
        # Return mock trending data if Gemini fails
        mock_trends = {
            'category': category,
            'trends': [
                {'title': 'Drake Meme', 'description': 'Classic approval/disapproval format', 'reason': 'Timeless', 'scene_ideas': ['Office', 'Concert', 'Wedding']},
                {'title': 'Loss Meme', 'description': '4-panel webcomic reference', 'reason': 'Internet culture', 'scene_ideas': ['Gaming', 'Work', 'School']},
                {'title': 'Stonks', 'description': 'Poor grammar stock market meme', 'reason': 'Financial humor', 'scene_ideas': ['Market', 'Trading', 'Office']}
            ],
            'note': 'Mock data (Firestore/Gemini unavailable)'
        }
        return jsonify(mock_trends), 200

@app.route('/scene-suggestions', methods=['POST'])
def get_scene_suggestions():
    """Get AI-generated scene suggestions"""
    data = request.json
    meme_type = data.get('meme_type', 'funny')

    try:
        suggestions = gemini.generate_scene_suggestions(meme_type)
        return jsonify(suggestions), 200
    
    except Exception as e:
        # Return mock scene suggestions if Gemini fails
        mock_suggestions = {
            'meme_type': meme_type,
            'scenes': [
                {'name': 'Office Environment', 'description': 'Corporate setting with desks and meetings', 'props': ['Computer', 'Desk', 'Coffee Cup']},
                {'name': 'Outdoor Park', 'description': 'Green space with trees and benches', 'props': ['Bench', 'Trees', 'Grass']},
                {'name': 'Gaming Setup', 'description': 'Gaming room with monitors and equipment', 'props': ['Monitor', 'Keyboard', 'Headphones']}
            ],
            'note': 'Mock data (Gemini API unavailable)'
        }
        return jsonify(mock_suggestions), 200

@app.route('/meme/<meme_id>', methods=['GET'])
def get_meme(meme_id):
    """Get meme details with all outputs"""
    try:
        try:
            meme_data = MemeModel.get(meme_id)
        except:
            meme_data = None
            
        if not meme_data:
            # Return mock meme data if not found or Firestore fails
            mock_meme = {
                'meme': {
                    'id': meme_id,
                    'user_id': 'test-user',
                    'image_url': 'https://via.placeholder.com/300',
                    'status': 'completed',
                    'created_at': datetime.utcnow().isoformat()
                },
                'subjects': [
                    {
                        'id': 'subject-1',
                        'subject_index': 0,
                        'mesh_url': 'https://example.com/mesh1.glb',
                        'bbox': {'x': 0, 'y': 0, 'width': 100, 'height': 100}
                    }
                ],
                'exports': [
                    {
                        'id': 'export-1',
                        'export_type': 'gif',
                        'url': 'https://example.com/output.gif'
                    }
                ],
                'note': 'Mock data (Firestore unavailable)'
            }
            return jsonify(mock_meme), 200
        
        try:
            subjects = SubjectModel.get_by_meme(meme_id)
        except:
            subjects = []
            
        try:
            exports = ExportModel.get_by_meme(meme_id)
        except:
            exports = []
        
        return jsonify({
            'meme': meme_data,
            'subjects': subjects,
            'exports': exports
        }), 200
    
    except Exception as e:
        # Fallback mock data
        mock_meme = {
            'meme': {
                'id': meme_id,
                'user_id': 'test-user',
                'image_url': 'https://via.placeholder.com/300',
                'status': 'completed',
                'created_at': datetime.utcnow().isoformat()
            },
            'subjects': [],
            'exports': [],
            'note': 'Mock data (Firestore unavailable)'
        }
        return jsonify(mock_meme), 200

@app.route('/user/<user_id>/memes', methods=['GET'])
def get_user_memes(user_id):
    """Get all memes by a user"""
    try:
        limit = request.args.get('limit', 50, type=int)
        try:
            memes = MemeModel.get_by_user(user_id, limit=limit)
        except:
            # If Firestore fails, return mock data
            memes = None
            
        if not memes:
            # Return mock user memes
            mock_memes = {
                'memes': [
                    {
                        'id': 'meme-1',
                        'user_id': user_id,
                        'image_url': 'https://via.placeholder.com/300',
                        'status': 'completed',
                        'created_at': datetime.utcnow().isoformat()
                    },
                    {
                        'id': 'meme-2',
                        'user_id': user_id,
                        'image_url': 'https://via.placeholder.com/300',
                        'status': 'processing',
                        'created_at': (datetime.utcnow() - timedelta(hours=1)).isoformat()
                    }
                ],
                'note': 'Mock data (Firestore unavailable)'
            }
            return jsonify(mock_memes), 200
            
        return jsonify({'memes': memes}), 200
    
    except Exception as e:
        # Fallback mock data
        mock_memes = {
            'memes': [
                {
                    'id': 'meme-1',
                    'user_id': user_id,
                    'image_url': 'https://via.placeholder.com/300',
                    'status': 'completed',
                    'created_at': datetime.utcnow().isoformat()
                }
            ],
            'note': 'Mock data (Firestore unavailable)'
        }
        return jsonify(mock_memes), 200

if __name__ == '__main__':
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)