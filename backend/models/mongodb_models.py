from config import Config
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import uuid

class MemeModel:
    """MongoDB model for storing meme processing data"""
    collection_name = 'memes'
    
    @staticmethod
    def get_collection():
        """Get MongoDB collection"""
        if Config.db is None:
            raise RuntimeError("MongoDB not initialized")
        return Config.db[MemeModel.collection_name]
    
    @staticmethod
    def create(user_id, image_url, metadata=None):
        """
        Create a new meme document
        
        Args:
            user_id: User who uploaded the meme
            image_url: Cloudinary URL of the meme image
            metadata: Optional metadata dict
            
        Returns:
            Document ID
        """
        collection = MemeModel.get_collection()
        
        doc_id = str(uuid.uuid4())
        data = {
            '_id': doc_id,
            'user_id': user_id,
            'image_url': image_url,
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'processing',
            'outputs': []
        }
        collection.insert_one(data)
        return doc_id
    
    @staticmethod
    def update_status(doc_id, status, output_urls=None, error_message=None):
        """Update meme processing status"""
        collection = MemeModel.get_collection()
        
        update_data = {'status': status, 'updated_at': datetime.utcnow()}
        
        if output_urls:
            update_data['outputs'] = output_urls
        if error_message:
            update_data['error'] = error_message
            
        collection.update_one({'_id': doc_id}, {'$set': update_data})
    
    @staticmethod
    def get(doc_id):
        """Get meme document by ID"""
        collection = MemeModel.get_collection()
        doc = collection.find_one({'_id': doc_id})
        return doc
    
    @staticmethod
    def get_by_user(user_id, limit=50):
        """Get all memes by a user"""
        collection = MemeModel.get_collection()
        memes = list(collection.find({'user_id': user_id}).sort('created_at', -1).limit(limit))
        return memes
    
    @staticmethod
    def update_outputs(doc_id, outputs):
        """Update output files for a meme"""
        collection = MemeModel.get_collection()
        collection.update_one({'_id': doc_id}, {'$set': {
            'outputs': outputs,
            'updated_at': datetime.utcnow()
        }})
    
    @staticmethod
    def delete(doc_id):
        """Delete a meme document"""
        collection = MemeModel.get_collection()
        collection.delete_one({'_id': doc_id})


class SubjectModel:
    """MongoDB model for 3D mesh subjects extracted from memes"""
    collection_name = 'subjects'
    
    @staticmethod
    def get_collection():
        """Get MongoDB collection"""
        if Config.db is None:
            raise RuntimeError("MongoDB not initialized")
        return Config.db[SubjectModel.collection_name]
    
    @staticmethod
    def create(meme_id, subject_index, segmentation_data, mesh_url):
        """Create a subject document"""
        collection = SubjectModel.get_collection()
        
        doc_id = f"{meme_id}_subject_{subject_index}"
        data = {
            '_id': doc_id,
            'meme_id': meme_id,
            'subject_index': subject_index,
            'segmentation_data': segmentation_data,
            'mesh_url': mesh_url,
            'created_at': datetime.utcnow()
        }
        collection.insert_one(data)
        return doc_id
    
    @staticmethod
    def get(doc_id):
        """Get subject by ID"""
        collection = SubjectModel.get_collection()
        return collection.find_one({'_id': doc_id})
    
    @staticmethod
    def get_by_meme(meme_id):
        """Get all subjects for a meme"""
        collection = SubjectModel.get_collection()
        return list(collection.find({'meme_id': meme_id}))


class ExportModel:
    """MongoDB model for export operations"""
    collection_name = 'exports'
    
    @staticmethod
    def get_collection():
        """Get MongoDB collection"""
        if Config.db is None:
            raise RuntimeError("MongoDB not initialized")
        return Config.db[ExportModel.collection_name]
    
    @staticmethod
    def create(meme_id, export_type, export_url, metadata=None):
        """Create export record"""
        collection = ExportModel.get_collection()
        
        doc_id = str(uuid.uuid4())
        data = {
            '_id': doc_id,
            'meme_id': meme_id,
            'export_type': export_type,  # 'gif', 'video', 'glb'
            'export_url': export_url,
            'metadata': metadata or {},
            'created_at': datetime.utcnow()
        }
        collection.insert_one(data)
        return doc_id
    
    @staticmethod
    def get_by_meme(meme_id):
        """Get all exports for a meme"""
        collection = ExportModel.get_collection()
        return list(collection.find({'meme_id': meme_id}).sort('created_at', -1))


class TrendingCache:
    """MongoDB collection for caching trending data"""
    collection_name = 'trending_cache'
    
    @staticmethod
    def get_collection():
        """Get MongoDB collection"""
        if Config.db is None:
            raise RuntimeError("MongoDB not initialized")
        return Config.db[TrendingCache.collection_name]
    
    @staticmethod
    def store(category, data, ttl_hours=6):
        """Store trending data with TTL"""
        collection = TrendingCache.get_collection()
        
        collection.update_one(
            {'_id': category},
            {'$set': {
                'category': category,
                'data': data,
                'updated_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(hours=ttl_hours)
            }},
            upsert=True
        )
    
    @staticmethod
    def get(category):
        """Get trending data if not expired"""
        collection = TrendingCache.get_collection()
        
        doc = collection.find_one({'_id': category})
        if doc:
            if doc.get('expires_at', datetime.utcnow()) > datetime.utcnow():
                return doc.get('data')
        return None
    
    @staticmethod
    def delete(category):
        """Delete cached category"""
        collection = TrendingCache.get_collection()
        collection.delete_one({'_id': category})


class UserModel:
    """MongoDB model for user profiles"""
    collection_name = 'users'
    
    @staticmethod
    def get_collection():
        """Get MongoDB collection"""
        if Config.db is None:
            raise RuntimeError("MongoDB not initialized")
        return Config.db[UserModel.collection_name]
    
    @staticmethod
    def create_or_update(user_id, profile_data):
        """Create or update user profile"""
        collection = UserModel.get_collection()
        
        data = {
            '_id': user_id,
            'user_id': user_id,
            'profile': profile_data,
            'meme_count': 0,
            'last_activity': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
        collection.update_one({'_id': user_id}, {'$set': data}, upsert=True)
    
    @staticmethod
    def get(user_id):
        """Get user profile"""
        collection = UserModel.get_collection()
        return collection.find_one({'_id': user_id})
    
    @staticmethod
    def increment_meme_count(user_id):
        """Increment user's meme count"""
        collection = UserModel.get_collection()
        collection.update_one(
            {'_id': user_id},
            {'$inc': {'meme_count': 1}, '$set': {'last_activity': datetime.utcnow()}},
            upsert=True
        )
