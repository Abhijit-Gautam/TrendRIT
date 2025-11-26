# 3D Meme Generator - Backend Architecture Plan

## Project Overview
A Flask-based backend that processes meme images through SAM3 segmentation, creates 3D reconstructions, and integrates with trending content pipelines. The system will handle image uploads, 3D scene generation, pose manipulation, and export functionality.

---

## Tech Stack
- **Framework**: Python Flask
- **AI/ML**: SAM3 (Segment Anything Model 3), Gemini API
- **Database**: Google Cloud Firestore (NoSQL)
- **3D Processing**: Open3D, PyTorch3D, or similar libraries
- **Image Processing**: OpenCV, PIL/Pillow
- **Video/GIF Export**: MoviePy, imageio
- **API Integration**: Requests library for trending content APIs

---

## System Architecture

### High-Level Flow
```
User Upload → Flask API → SAM3 Segmentation → 3D Reconstruction → 
Scene Composition → Pose Manipulation → Export (GIF/Video) → Storage
                      ↓
              Trending Content Pipeline (Gemini API + External APIs)
```

### Architecture Layers

1. **API Layer** (Flask Routes)
   - Image upload endpoints
   - 3D scene manipulation endpoints
   - Export endpoints
   - Trending content endpoints

2. **Processing Layer**
   - SAM3 segmentation service
   - 3D reconstruction engine
   - Scene composition manager
   - Pose manipulation system

3. **Content Intelligence Layer**
   - Gemini API integration for context understanding
   - Trending topics aggregator (Twitter/X, Reddit, News APIs)
   - Meme template manager

4. **Storage Layer**
   - Firestore for metadata, user sessions, scene configurations
   - Cloud Storage for images, 3D models, exports

---

## Backend File Structure

```
backend/
├── app.py                      # Main Flask application entry point
├── config.py                   # Configuration (API keys, DB settings)
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
│
├── routes.py                   # All Flask route handlers
│
├── services.py                 # Core business logic services
│   # - SAM3SegmentationService
│   # - Reconstruction3DService
│   # - SceneCompositionService
│   # - ExportService
│   # - TrendingContentService
│
├── models.py                   # Data models and Firestore schemas
│   # - MemeProject
│   # - Scene3D
│   # - SegmentedObject
│   # - TrendingContent
│
├── utils.py                    # Utility functions
│   # - Image preprocessing
│   # - File handling
│   # - 3D mesh operations
│   # - Video/GIF generation
│
├── integrations.py             # External API integrations
│   # - Gemini API client
│   # - Trending APIs (Twitter, Reddit, etc.)
│   # - Cloud Storage operations
│
└── templates/                  # Meme templates and presets
    └── default_scenes.json
```

---

## Detailed Component Breakdown

### 1. **app.py** - Flask Application
- Initialize Flask app
- Configure CORS, file upload limits
- Register blueprints/routes
- Error handlers
- Health check endpoint

### 2. **config.py** - Configuration Management
- Environment variables loading
- API key management (SAM3, Gemini, Cloud APIs)
- Firestore initialization
- Upload folder paths
- Model loading paths
- Export settings (resolution, frame rates)

### 3. **routes.py** - API Endpoints

#### Core Endpoints:
- `POST /api/upload` - Upload meme image(s)
- `POST /api/segment` - Trigger SAM3 segmentation
- `GET /api/segments/<project_id>` - Retrieve segmented objects
- `POST /api/reconstruct` - Create 3D models from segments
- `POST /api/scene/create` - Initialize 3D scene
- `PUT /api/scene/<scene_id>/pose` - Update object poses
- `POST /api/scene/<scene_id>/export` - Generate GIF/video
- `GET /api/trending` - Fetch trending content
- `POST /api/scene/apply-trend` - Apply trending context to scene

#### Utility Endpoints:
- `GET /api/templates` - List available meme templates
- `GET /api/projects/<user_id>` - User's projects
- `DELETE /api/project/<project_id>` - Delete project

### 4. **services.py** - Business Logic

#### SAM3SegmentationService
- Load SAM3 model
- Process uploaded images
- Generate segmentation masks
- Extract individual subjects
- Return bounding boxes and masks

#### Reconstruction3DService
- Convert 2D segments to 3D meshes
- Depth estimation (using MiDaS or similar)
- Mesh generation and cleanup
- Texture mapping from original image

#### SceneCompositionService
- Manage 3D scene graph
- Position multiple objects
- Handle camera controls
- Lighting setup

#### PoseManipulationService
- Apply transformations (rotation, translation, scale)
- Skeleton/rigging for character poses
- Animation keyframe management

#### ExportService
- Render scene from multiple angles
- Generate frame sequences
- Create GIF with imageio
- Create MP4 with MoviePy
- Upload to Cloud Storage

#### TrendingContentService
- Fetch trending topics from APIs
- Use Gemini to analyze relevance
- Suggest meme templates based on trends
- Generate captions/text overlays

### 5. **models.py** - Data Schemas

#### Firestore Collections:

**projects**
```python
{
  'project_id': str,
  'user_id': str,
  'created_at': timestamp,
  'updated_at': timestamp,
  'status': str,  # 'uploaded', 'segmented', 'reconstructed', 'completed'
  'original_images': [str],  # Cloud Storage URLs
  'name': str
}
```

**segments**
```python
{
  'segment_id': str,
  'project_id': str,
  'image_url': str,
  'mask_url': str,
  'bbox': dict,  # {x, y, width, height}
  'confidence': float
}
```

**scenes_3d**
```python
{
  'scene_id': str,
  'project_id': str,
  'objects': [
    {
      'object_id': str,
      'segment_id': str,
      'model_url': str,  # 3D model file
      'position': [x, y, z],
      'rotation': [rx, ry, rz],
      'scale': [sx, sy, sz]
    }
  ],
  'camera': {
    'position': [x, y, z],
    'target': [x, y, z],
    'fov': float
  },
  'export_url': str  # Final GIF/video
}
```

**trending_cache**
```python
{
  'trend_id': str,
  'type': str,  # 'topic', 'meme', 'news', 'music'
  'content': str,
  'metadata': dict,
  'fetched_at': timestamp,
  'relevance_score': float  # From Gemini analysis
}
```

### 6. **utils.py** - Helper Functions

- `preprocess_image()` - Resize, normalize images
- `create_mesh_from_depth()` - 3D reconstruction helper
- `apply_texture()` - Map 2D texture to 3D mesh
- `render_frame()` - Render single frame from scene
- `frames_to_gif()` - Convert frame sequence to GIF
- `frames_to_video()` - Convert frames to MP4
- `upload_to_storage()` - Cloud Storage upload wrapper
- `generate_thumbnail()` - Create preview images

### 7. **integrations.py** - External Services

#### GeminiClient
- `analyze_trend()` - Analyze trending content relevance
- `suggest_caption()` - Generate meme captions
- `match_template()` - Find best meme template for trend

#### TrendingAPIs

### **1. YouTube Trending (Videos + Music + Pop Culture)**

[https://www.youtube.com/feed/trending](https://www.youtube.com/feed/trending)

### **2. YouTube Data API (Official Free API)**

[https://developers.google.com/youtube/v3](https://developers.google.com/youtube/v3)

---

### **3. YouTube Music Charts (Trending Songs)**

[https://charts.youtube.com/](https://charts.youtube.com/)

---

### **4. GNews (Free News API Alternative)**

[https://gnews.io/](https://gnews.io/)

---

### **5. Global News RSS Feeds (Fully Free, No API Key)**

CNN RSS: [https://rss.cnn.com/rss/edition.rss](https://rss.cnn.com/rss/edition.rss)
BBC News RSS: [https://feeds.bbci.co.uk/news/rss.xml](https://feeds.bbci.co.uk/news/rss.xml)
Al Jazeera RSS: [https://www.aljazeera.com/xml/rss/all.xml](https://www.aljazeera.com/xml/rss/all.xml)

---

### **6. Wikipedia Trending / Pageviews API (Free Official API)**

[https://wikimedia.org/api/rest_v1/#/](https://wikimedia.org/api/rest_v1/#/)

---

### **7. Google Trends (via PyTrends – Free Unofficial API)**

PyTrends GitHub:
[https://github.com/GeneralMills/pytrends](https://github.com/GeneralMills/pytrends)

Google Trends website:
[https://trends.google.com/](https://trends.google.com/)

---

### **8. TikTok Trending (Free via RapidAPI Tier)**

RapidAPI TikTok Trending:
[https://rapidapi.com/solutionapi/api/tiktok-api](https://rapidapi.com/solutionapi/api/tiktok-api)

---

### **9. Pinterest Popular Trends (Free Web)**

[https://in.pinterest.com/trending/](https://in.pinterest.com/trending/)

---


#### CloudStorageClient
- Upload/download from Google Cloud Storage
- Generate signed URLs
- Manage file lifecycle

---

## Processing Pipeline

### Stage 1: Upload & Segmentation
1. User uploads meme image(s)
2. Store in Cloud Storage, create project in Firestore
3. Load SAM3 model
4. Run segmentation on each image
5. Store masks and segments in Firestore
6. Return segment previews to user

### Stage 2: 3D Reconstruction
1. User selects segments to convert to 3D
2. For each segment:
   - Estimate depth map
   - Generate 3D mesh
   - Apply texture from original image
   - Clean mesh (remove artifacts)
3. Store 3D models in Cloud Storage
4. Update Firestore with model URLs

### Stage 3: Scene Composition
1. Create empty 3D scene
2. Load selected 3D objects into scene
3. Apply default positions/rotations
4. User adjusts poses via API
5. Save scene configuration to Firestore

### Stage 4: Export
1. Set up camera trajectory (for 360° rotation)
2. Render frames at specified intervals
3. Compile frames into GIF or MP4
4. Upload to Cloud Storage
5. Return download URL

### Trending Content Integration
1. Background job fetches trending content hourly
2. Gemini API analyzes and scores relevance
3. Store in trending_cache collection
4. User requests trending suggestions
5. Return matched templates and caption ideas
6. User applies to existing scene or creates new project

---

## Database Schema Design

### Firestore Collections Structure

**Collections:**
- `projects` - Main project documents
  - `segments` (subcollection) - Segmented objects per project
- `scenes` - 3D scene configurations
- `trending` - Trending content cache
- `templates` - Meme template library
- `users` - User profiles and preferences (if needed)

**Indexes:**
- `projects`: `user_id`, `created_at`
- `trending`: `type`, `relevance_score`, `fetched_at`
- `scenes`: `project_id`, `updated_at`

---

## API Response Formats

### Standard Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message"
  }
}
```

---

## Key Implementation Considerations

### Performance Optimization
1. **Model Loading**: Load SAM3 model once at startup, keep in memory
2. **Caching**: Cache segmentation results for re-processing
3. **Async Processing**: Use background tasks for heavy operations (segmentation, 3D reconstruction, export)
4. **Batch Processing**: Process multiple images in parallel where possible

### Error Handling
1. Validate all file uploads (format, size, content)
2. Handle SAM3 segmentation failures gracefully
3. Timeout protection for long-running operations
4. Retry logic for external API calls

### Scalability
1. Consider using task queues (Celery) for heavy processing
2. Implement request rate limiting
3. Use Cloud Storage for all large files
4. Implement pagination for list endpoints

### Security
1. Validate and sanitize all inputs
2. Implement file upload restrictions (size, type)
3. Secure API keys in environment variables
4. Implement CORS properly for frontend integration
5. Add authentication/authorization (optional for MVP)

---

## Development Phases

### Phase 1: Core Functionality (MVP)
- Flask setup and basic routing
- SAM3 integration and segmentation
- Simple 3D reconstruction (depth-based)
- Basic scene composition
- GIF export functionality
- Firestore integration for projects and scenes

### Phase 2: Trending Content Integration
- Gemini API integration
- External trending APIs setup
- Content analysis and scoring
- Template matching system
- Auto-caption generation

### Phase 3: Advanced Features
- Complex pose manipulation
- Animation support
- Video export with music
- Multi-object scenes
- Template marketplace

### Phase 4: Optimization
- Background job processing
- Caching layer
- Performance tuning
- Monitoring and logging

---

## Required Python Packages

```
flask==3.0.0
flask-cors==4.0.0
python-dotenv==1.0.0
google-cloud-firestore==2.14.0
google-cloud-storage==2.14.0
opencv-python==4.9.0
Pillow==10.2.0
torch==2.2.0
torchvision==0.17.0
numpy==1.26.3
open3d==0.18.0
trimesh==4.0.10
moviepy==1.0.3
imageio==2.33.1
requests==2.31.0
google-generativeai==0.3.2
segment-anything==1.0  # SAM3 SDK
midas==0.1  # For depth estimation
flask-limiter==3.5.0  # Rate limiting
python-multipart==0.0.6  # File uploads
```

---

## Environment Variables (.env)

```
FLASK_ENV=development
FLASK_DEBUG=True
UPLOAD_FOLDER=./uploads
MODELS_FOLDER=./models
EXPORT_FOLDER=./exports

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
FIRESTORE_COLLECTION_PREFIX=meme3d
STORAGE_BUCKET=meme3d-storage

# API Keys
GEMINI_API_KEY=your-gemini-key
TWITTER_API_KEY=your-twitter-key
REDDIT_CLIENT_ID=your-reddit-id
REDDIT_CLIENT_SECRET=your-reddit-secret

# Processing Settings
MAX_UPLOAD_SIZE_MB=50
SAM3_MODEL_PATH=./models/sam3_checkpoint.pth
RENDER_RESOLUTION=1920x1080
GIF_FPS=15
VIDEO_FPS=30
```

---

## Next Steps

1. Set up Flask project structure
2. Configure Google Cloud (Firestore + Storage)
3. Integrate SAM3 SDK and test segmentation
4. Implement basic 3D reconstruction pipeline
5. Build core API endpoints
6. Integrate Gemini API for trending analysis
7. Test end-to-end flow with sample memes
8. Deploy and iterate based on testing

---

## Potential Challenges & Solutions

### Challenge 1: SAM3 Processing Time
**Solution**: Implement async task processing, show loading states, cache results

### Challenge 2: 3D Reconstruction Quality
**Solution**: Use multiple depth estimation models, allow manual adjustments, provide quality presets

### Challenge 3: Large File Handling
**Solution**: Implement chunked uploads, compression, Cloud Storage direct uploads

### Challenge 4: API Rate Limits
**Solution**: Implement caching for trending data, batch API calls, use webhooks where available

### Challenge 5: Complex 3D Poses
**Solution**: Start with basic transformations, add preset poses library, implement simple rigging for Phase 3

---

## Success Metrics

- Average segmentation time < 5 seconds per image
- 3D reconstruction success rate > 90%
- Export generation time < 30 seconds for GIFs
- Trending content freshness < 1 hour lag
- API response time < 500ms for non-processing endpoints
- 99% uptime for core services