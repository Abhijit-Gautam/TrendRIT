# TrendRIT
## Project Overview

A Flask-based backend system that transforms 2D user images into animated 3D meme scenes using depth estimation and local semantic search. It features trending content recognition powered by a local vector database (ChromaDB), context-aware meme template matching, and full 3D export—all running in a self-hosted/local environment.

---

## Features

* **Image Upload \& 3D Conversion**: Converts 2D images to realistic 3D scenes using MiDaS depth estimation
* **Trending Aware**: Tracks trending topics, matching them to meme templates via local vector search (ChromaDB)
* **Automated Captioning**: Generates context-aware meme captions through Gemini API
* **Export**: Produces animated GIFs/videos from the 3D scene (camera movement, rotation)
* **Fully Local/Offline**: No reliance on cloud services—ideal for privacy and speed

---

## Tech Stack

* **Framework:** Flask (Python)
* **AI/ML:** MiDaS (Torch/Timm), Gemini API, Mask R-CNN, Sentence Transformers
* **Vector Database:** ChromaDB (local, persistent)
* **Transactional DB:** SQLite (via SQLAlchemy)
* **3D Processing:** Open3D, Trimesh, PyTorch3D
* **Image Processing:** OpenCV, Pillow
* **Export:** MoviePy, imageio
* **Deployment:** Local/self-hosted, environment-configurable

---

## High-Level Architecture

```

User Upload
│
Flask API (Image Endpoint)
│
Depth Estimation (MiDaS)
│
3D Mesh Generation (Open3D, Trimesh)
│
Scene Composition \\\& Animation
│
GIF/Video Export (MoviePy)
│
Local Storage
│
Trending Pipeline (ChromaDB, Gemini)
\[Semantic Matching: Trend ↔ Meme Template]

```

---

## Backend File Structure

```

backend/
├── app.py                  \\# Main Flask application
├── config.py               \\# Configuration (paths, env)
├── requirements.txt        \\# Python dependencies
├── .env                    \\# Environment variables
├── routes.py               \\# API endpoints
├── database.py             \\# SQLAlchemy \\\& ChromaDB setup
├── services/               \\# Logic Modules
│   ├── \_\_init\_\_.py
│   ├── depth\_service.py        \\# MiDaS depth logic
│   ├── reconstruction\_service.py \\# 3D mesh generation
│   ├── export\_service.py        \\# GIF/Video export
│   └── intelligence\_service.py  \\# ChromaDB trending logic
├── models/
│   ├── sql\_models.py           \\# SQLAlchemy models
│   └── vector\_schemas.py       \\# ChromaDB schemas
├── utils.py                 \\# Helpers
└── integrations.py          \\# Gemini/trending integrations

```

---

## Key Components

### 1\. `database.py`

Handles SQLite (project/scene data) and initializes ChromaDB for vector search. Ensures all collections (meme\_templates, trending\_context) are present.

### 2\. `services/depth\_service.py`

Loads MiDaS for depth prediction. Supports standard Mask R-CNN for quick person/foreground segmentation.

### 3\. `services/intelligence\_service.py`

Adds/tracks trends using sentence-transformers. Matches trending topics to meme templates via ChromaDB semantic search.

### 4\. `services/reconstruction\_service.py`

Converts depth+RGB images into 3D point clouds and meshes. Textures the mesh with original images.

### 5\. `models/sql\_models.py`

Project and Scene SQLAlchemy classes with tracking statuses and file paths.

---

## Workflow

1. **Upload \& Depth**: User uploads image; MiDaS depth generated and stored
2. **3D Reconstruction**: Depth map and original image produce a colored 3D mesh
3. **Trending \& Matching**: Trends collected and semantically matched via ChromaDB
4. **Captioning**: Gemini API proposes meme captions
5. **Export**: Animated scene (camera movement) rendered to GIF/MP4

---

## Required Python Packages

```

flask==3.0.0
flask-cors==4.0.0
flask-sqlalchemy==3.1.1
chromadb==0.4.22
sentence-transformers==2.3.1
python-dotenv==1.0.0
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
timm==0.9.12

```

---

## Environment Variables (`.env`)

```

FLASK\_ENV=development
UPLOAD\_FOLDER=./data/uploads
MODELS\_FOLDER=./data/3d\_models
EXPORTS\_FOLDER=./data/exports

SQLITE\_DB\_PATH=sqlite:///meme3d.db
CHROMADB\_PATH=./data/chroma\_db

GEMINI\_API\_KEY=your-gemini-key

```

---

## Getting Started

1. **Install requirements**:

```

pip install -r requirements.txt

```

2. **Set Environment**:  
   Copy `.env.example` to `.env` and edit as needed
3. **Run Server**:

```

python app.py

```