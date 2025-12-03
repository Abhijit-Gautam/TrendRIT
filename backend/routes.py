"""
API Routes for TrendRIT Backend
Defines all REST API endpoints for the meme 3D conversion service
"""

from flask import Blueprint, request, jsonify, send_file, send_from_directory, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from PIL import Image
import numpy as np

from database import db
from models.sql_models import Project, Scene, Export, MemeTemplate, TrendingTopic
from config import Config

# Create blueprints
api = Blueprint('api', __name__, url_prefix='/api')
main = Blueprint('main', __name__)

# Service instances (initialized in app.py)
depth_service = None
reconstruction_service = None
intelligence_service = None
gemini_service = None
export_service = None


def init_routes(depth, reconstruction, intelligence, gemini, export):
    """Initialize routes with service instances"""
    global depth_service, reconstruction_service, intelligence_service, gemini_service, export_service
    depth_service = depth
    reconstruction_service = reconstruction
    intelligence_service = intelligence
    gemini_service = gemini
    export_service = export


# ===== Health & Static Routes =====

@main.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    import torch
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'gpu_available': torch.cuda.is_available(),
        'services': {
            'depth': depth_service is not None,
            'reconstruction': reconstruction_service is not None,
            'intelligence': intelligence_service is not None,
            'gemini': gemini_service is not None,
            'export': export_service is not None
        }
    })


@main.route('/static/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve uploaded files"""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


@main.route('/static/models/<path:filename>')
def serve_models(filename):
    """Serve 3D model files"""
    return send_from_directory(Config.MODELS_FOLDER, filename)


@main.route('/static/exports/<path:filename>')
def serve_exports(filename):
    """Serve exported files (GIFs, videos)"""
    return send_from_directory(Config.EXPORTS_FOLDER, filename)


# ===== Upload & Project Routes =====

@api.route('/upload', methods=['POST'])
def upload_image():
    """
    Upload an image and create a new project
    
    Returns:
        project_id, image_url, status
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    user_id = request.form.get('user_id', 'anonymous')
    project_name = request.form.get('name', None)
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate file type
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in Config.ALLOWED_EXTENSIONS:
        return jsonify({'error': f'Invalid file type. Allowed: {Config.ALLOWED_EXTENSIONS}'}), 400
    
    try:
        # Create project
        project = Project.create(user_id=user_id, name=project_name)
        
        # Save file locally
        filename = secure_filename(f"{project.id}_{file.filename}")
        filepath = Config.get_upload_path(filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        
        # Update project with image path
        project.update_paths(original_image_path=filepath)
        project.update_status('uploaded')
        
        return jsonify({
            'project_id': project.id,
            'image_url': f'/static/uploads/{filename}',
            'status': 'uploaded',
            'message': 'Image uploaded successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/project/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get project details with scenes and exports"""
    project = Project.get(project_id)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.get_by_project(project_id)
    exports = Export.get_by_project(project_id)
    
    return jsonify({
        'project': project.to_dict(),
        'scenes': [s.to_dict() for s in scenes],
        'exports': [e.to_dict() for e in exports]
    }), 200


@api.route('/projects', methods=['GET'])
def get_user_projects():
    """Get all projects for a user"""
    user_id = request.args.get('user_id', 'anonymous')
    limit = request.args.get('limit', 50, type=int)
    
    projects = Project.get_by_user(user_id, limit=limit)
    
    return jsonify({
        'projects': [p.to_dict() for p in projects],
        'count': len(projects)
    }), 200


# ===== 3D Processing Routes =====

@api.route('/process/depth/<project_id>', methods=['POST'])
def generate_depth(project_id):
    """
    Generate depth map for a project's image
    
    Returns:
        depth_map_url, status
    """
    project = Project.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if not project.original_image_path:
        return jsonify({'error': 'No image uploaded for this project'}), 400
    
    try:
        project.update_status('processing_depth')
        
        # Load image
        image = Image.open(project.original_image_path).convert('RGB')
        
        # Generate depth map
        depth_map = depth_service.generate_depth_map(image)
        
        # Save depth map as image
        depth_filename = f"{project_id}_depth.png"
        depth_path = Config.get_upload_path(depth_filename)
        
        # Normalize and save depth visualization
        depth_normalized = ((depth_map - depth_map.min()) / (depth_map.max() - depth_map.min()) * 255).astype(np.uint8)
        depth_image = Image.fromarray(depth_normalized)
        depth_image.save(depth_path)
        
        # Also save raw depth as numpy file
        depth_npy_path = Config.get_upload_path(f"{project_id}_depth.npy")
        np.save(depth_npy_path, depth_map)
        
        project.update_paths(depth_map_path=depth_npy_path)
        project.update_status('depth_completed')
        
        return jsonify({
            'project_id': project_id,
            'depth_map_url': f'/static/uploads/{depth_filename}',
            'status': 'depth_completed'
        }), 200
        
    except Exception as e:
        project.update_status('failed', error_message=str(e))
        return jsonify({'error': str(e)}), 500


@api.route('/process/3d/<project_id>', methods=['POST'])
def generate_3d(project_id):
    """
    Generate 3D mesh from depth map
    
    Returns:
        mesh_url, point_cloud_url, stats
    """
    project = Project.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if not project.depth_map_path:
        return jsonify({'error': 'Depth map not generated. Run /process/depth first'}), 400
    
    try:
        project.update_status('processing_3d')
        
        # Load image and depth
        image = Image.open(project.original_image_path).convert('RGB')
        depth_map = np.load(project.depth_map_path)
        
        # Reconstruct 3D
        result = reconstruction_service.reconstruct_from_image(
            image=image,
            depth_map=depth_map,
            project_id=project_id
        )
        
        # Create scene record
        scene = Scene.create(project_id=project_id, scene_index=0, name='Main Scene')
        scene.update_paths(
            mesh_path=result['mesh_glb_path'],
            point_cloud_path=result['point_cloud_path']
        )
        
        project.update_status('completed')
        
        # Get relative paths for URLs
        mesh_filename = os.path.basename(result['mesh_glb_path'])
        pcd_filename = os.path.basename(result['point_cloud_path'])
        
        return jsonify({
            'project_id': project_id,
            'scene_id': scene.id,
            'mesh_url': f'/static/models/{mesh_filename}',
            'point_cloud_url': f'/static/models/{pcd_filename}',
            'stats': result['stats'],
            'status': 'completed'
        }), 200
        
    except Exception as e:
        project.update_status('failed', error_message=str(e))
        return jsonify({'error': str(e)}), 500


@api.route('/process/full/<project_id>', methods=['POST'])
def process_full_pipeline(project_id):
    """
    Run full processing pipeline: depth + 3D reconstruction
    
    Returns:
        All outputs from the pipeline
    """
    project = Project.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if not project.original_image_path:
        return jsonify({'error': 'No image uploaded'}), 400
    
    try:
        # Step 1: Generate depth
        project.update_status('processing_depth')
        image = Image.open(project.original_image_path).convert('RGB')
        depth_map = depth_service.generate_depth_map(image)
        
        # Save depth
        depth_npy_path = Config.get_upload_path(f"{project_id}_depth.npy")
        np.save(depth_npy_path, depth_map)
        project.update_paths(depth_map_path=depth_npy_path)
        
        # Step 2: 3D Reconstruction
        project.update_status('processing_3d')
        result = reconstruction_service.reconstruct_from_image(
            image=image,
            depth_map=depth_map,
            project_id=project_id
        )
        
        # Create scene
        scene = Scene.create(project_id=project_id, scene_index=0, name='Main Scene')
        scene.update_paths(
            mesh_path=result['mesh_glb_path'],
            point_cloud_path=result['point_cloud_path']
        )
        
        project.update_status('completed')
        
        mesh_filename = os.path.basename(result['mesh_glb_path'])
        
        return jsonify({
            'project_id': project_id,
            'scene_id': scene.id,
            'mesh_url': f'/static/models/{mesh_filename}',
            'stats': result['stats'],
            'status': 'completed'
        }), 200
        
    except Exception as e:
        project.update_status('failed', error_message=str(e))
        return jsonify({'error': str(e)}), 500


# ===== Export Routes =====

@api.route('/export/<project_id>', methods=['POST'])
def export_project(project_id):
    """
    Export project as GIF or video
    
    Body:
        format: 'gif' | 'mp4' | 'webm'
        frames: number of frames (default 36)
        duration: frame duration in seconds
    """
    project = Project.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if project.status != 'completed':
        return jsonify({'error': 'Project not ready. Run processing first'}), 400
    
    data = request.json or {}
    export_format = data.get('format', 'gif')
    frames = data.get('frames', Config.DEFAULT_GIF_FRAMES)
    duration = data.get('duration', Config.DEFAULT_GIF_DURATION)
    
    if export_format not in ['gif', 'mp4', 'webm']:
        return jsonify({'error': f'Unsupported format: {export_format}'}), 400
    
    try:
        scenes = Scene.get_by_project(project_id)
        if not scenes:
            return jsonify({'error': 'No scenes found for project'}), 404
        
        mesh_path = scenes[0].mesh_path
        
        if export_format == 'gif':
            output_path = export_service.create_rotating_gif(
                mesh_path,
                project_id,
                frames=frames
            )
        else:
            return jsonify({'error': f'Format {export_format} not yet implemented'}), 400
        
        # Record export
        export = Export.create(
            project_id=project_id,
            export_type=export_format,
            export_path=output_path,
            settings={'frames': frames, 'duration': duration}
        )
        
        export_filename = os.path.basename(output_path)
        
        return jsonify({
            'export_id': export.id,
            'url': f'/static/exports/{export_filename}',
            'format': export_format,
            'status': 'completed'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== Trending & Intelligence Routes =====

@api.route('/trending', methods=['GET'])
def get_trending():
    """
    Get trending content/meme ideas
    
    Query params:
        category: memes, news, pop_culture, music, gaming
    """
    category = request.args.get('category', 'memes')
    
    try:
        # Try to get from ChromaDB cache first
        if intelligence_service:
            cached_trends = intelligence_service.get_trending_by_category(category)
            if cached_trends:
                return jsonify({
                    'category': category,
                    'trends': cached_trends,
                    'source': 'cache'
                }), 200
        
        # Fetch fresh from Gemini
        if gemini_service:
            trends = gemini_service.fetch_trending_content(category)
            
            # Cache in ChromaDB
            if intelligence_service and trends:
                intelligence_service.add_trends_batch(trends, ttl_hours=Config.TRENDING_CACHE_TTL_HOURS)
            
            return jsonify({
                'category': category,
                'trends': trends,
                'source': 'gemini'
            }), 200
        
        # Fallback mock data
        return jsonify({
            'category': category,
            'trends': _get_mock_trends(category),
            'source': 'mock'
        }), 200
        
    except Exception as e:
        return jsonify({
            'category': category,
            'trends': _get_mock_trends(category),
            'source': 'mock',
            'error': str(e)
        }), 200


@api.route('/templates', methods=['GET'])
def get_meme_templates():
    """Get all available meme templates"""
    try:
        if intelligence_service:
            templates = intelligence_service.get_all_templates()
            return jsonify({'templates': templates}), 200
        
        return jsonify({'templates': [], 'error': 'Intelligence service not available'}), 200
        
    except Exception as e:
        return jsonify({'templates': [], 'error': str(e)}), 200


@api.route('/templates/match', methods=['POST'])
def match_templates():
    """
    Match templates to a trend or query
    
    Body:
        query: search text
        limit: max results (default 5)
    """
    data = request.json or {}
    query = data.get('query', '')
    limit = data.get('limit', 5)
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        if intelligence_service:
            matches = intelligence_service.match_trend_to_templates(query, limit=limit)
            return jsonify({'matches': matches}), 200
        
        return jsonify({'matches': [], 'error': 'Intelligence service not available'}), 200
        
    except Exception as e:
        return jsonify({'matches': [], 'error': str(e)}), 200


@api.route('/search/trends', methods=['POST'])
def search_trends():
    """
    Semantic search for trends
    
    Body:
        query: search text
        category: optional category filter
        limit: max results
    """
    data = request.json or {}
    query = data.get('query', '')
    category = data.get('category', None)
    limit = data.get('limit', 10)
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        if intelligence_service:
            results = intelligence_service.search_trends(query, category=category, limit=limit)
            return jsonify({'results': results}), 200
        
        return jsonify({'results': [], 'error': 'Intelligence service not available'}), 200
        
    except Exception as e:
        return jsonify({'results': [], 'error': str(e)}), 200


@api.route('/scene-suggestions', methods=['POST'])
def get_scene_suggestions():
    """
    Get AI-generated scene suggestions for a meme type
    
    Body:
        meme_type: type of meme
        user_prompt: optional context
    """
    data = request.json or {}
    meme_type = data.get('meme_type', 'funny')
    user_prompt = data.get('user_prompt', None)
    
    try:
        if gemini_service:
            suggestions = gemini_service.generate_scene_suggestions(meme_type, user_prompt)
            return jsonify(suggestions), 200
        
        # Fallback mock suggestions
        return jsonify(_get_mock_scene_suggestions(meme_type)), 200
        
    except Exception as e:
        return jsonify({
            **_get_mock_scene_suggestions(meme_type),
            'error': str(e)
        }), 200


# ===== Helper Functions =====

def _get_mock_trends(category):
    """Return mock trending data"""
    return [
        {
            'title': 'Drake Meme',
            'description': 'Classic approval/disapproval format',
            'reason': 'Timeless and versatile',
            'scene_ideas': ['Office', 'Concert', 'Wedding']
        },
        {
            'title': 'Distracted Boyfriend',
            'description': 'Man looking at other woman while girlfriend disapproves',
            'reason': 'Relatable relationship humor',
            'scene_ideas': ['Street', 'Mall', 'Party']
        },
        {
            'title': 'Stonks',
            'description': 'Poor grammar stock market meme',
            'reason': 'Financial humor',
            'scene_ideas': ['Office', 'Trading Floor', 'Home']
        }
    ]


def _get_mock_scene_suggestions(meme_type):
    """Return mock scene suggestions"""
    return {
        'meme_type': meme_type,
        'scenes': [
            {
                'name': 'Office Environment',
                'description': 'Corporate setting with desks',
                'props': ['Computer', 'Desk', 'Coffee Cup']
            },
            {
                'name': 'Outdoor Park',
                'description': 'Green space with trees',
                'props': ['Bench', 'Trees', 'Grass']
            },
            {
                'name': 'Gaming Setup',
                'description': 'Gaming room with equipment',
                'props': ['Monitor', 'Keyboard', 'Headphones']
            }
        ]
    }
