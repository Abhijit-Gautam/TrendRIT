from config import Config
from datetime import datetime, timedelta
import uuid

class MemeModel:
    """Firestore model for storing meme processing data"""
    collection = 'trendrit_memes'
    
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
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc_id = str(uuid.uuid4())
        doc_ref = Config.db.collection(MemeModel.collection).document(doc_id)
        
        data = {
            'id': doc_id,
            'user_id': user_id,
            'image_url': image_url,
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'status': 'processing',
            'outputs': []
        }
        doc_ref.set(data)
        return doc_id
    
    @staticmethod
    def update_status(doc_id, status, output_urls=None, error_message=None):
        """
        Update meme processing status
        
        Args:
            doc_id: Document ID
            status: New status ('processing', 'completed', 'failed')
            output_urls: Optional list of output URLs
            error_message: Optional error message if failed
        """
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc_ref = Config.db.collection(MemeModel.collection).document(doc_id)
        update_data = {'status': status, 'updated_at': datetime.utcnow()}
        
        if output_urls:
            update_data['outputs'] = output_urls
        if error_message:
            update_data['error'] = error_message
            
        doc_ref.update(update_data)
    
    @staticmethod
    def get(doc_id):
        """Get meme document by ID"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc = Config.db.collection(MemeModel.collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else None
    
    @staticmethod
    def get_by_user(user_id, limit=50):
        """Get all memes by a user"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        query = Config.db.collection(MemeModel.collection).where(
            'user_id', '==', user_id
        ).order_by('created_at', direction='DESCENDING').limit(limit)
        
        return [doc.to_dict() for doc in query.stream()]
    
    @staticmethod
    def update_outputs(doc_id, outputs):
        """Update output files for a meme"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc_ref = Config.db.collection(MemeModel.collection).document(doc_id)
        doc_ref.update({
            'outputs': outputs,
            'updated_at': datetime.utcnow()
        })
    
    @staticmethod
    def delete(doc_id):
        """Delete a meme document"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        Config.db.collection(MemeModel.collection).document(doc_id).delete()


class SubjectModel:
    """Firestore model for 3D mesh subjects extracted from memes"""
    collection = 'trendrit_subjects'
    
    @staticmethod
    def create(meme_id, subject_index, segmentation_data, mesh_url):
        """Create a subject document"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc_id = f"{meme_id}_subject_{subject_index}"
        doc_ref = Config.db.collection(SubjectModel.collection).document(doc_id)
        
        data = {
            'id': doc_id,
            'meme_id': meme_id,
            'subject_index': subject_index,
            'segmentation_data': segmentation_data,
            'mesh_url': mesh_url,
            'created_at': datetime.utcnow()
        }
        doc_ref.set(data)
        return doc_id
    
    @staticmethod
    def get(doc_id):
        """Get subject by ID"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc = Config.db.collection(SubjectModel.collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else None
    
    @staticmethod
    def get_by_meme(meme_id):
        """Get all subjects for a meme"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        query = Config.db.collection(SubjectModel.collection).where(
            'meme_id', '==', meme_id
        )
        return [doc.to_dict() for doc in query.stream()]


class ExportModel:
    """Firestore model for export operations"""
    collection = 'trendrit_exports'
    
    @staticmethod
    def create(meme_id, export_type, export_url, metadata=None):
        """Create export record"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc_id = str(uuid.uuid4())
        doc_ref = Config.db.collection(ExportModel.collection).document(doc_id)
        
        data = {
            'id': doc_id,
            'meme_id': meme_id,
            'export_type': export_type,  # 'gif', 'video', 'glb'
            'export_url': export_url,
            'metadata': metadata or {},
            'created_at': datetime.utcnow()
        }
        doc_ref.set(data)
        return doc_id
    
    @staticmethod
    def get_by_meme(meme_id):
        """Get all exports for a meme"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        query = Config.db.collection(ExportModel.collection).where(
            'meme_id', '==', meme_id
        ).order_by('created_at', direction='DESCENDING')
        
        return [doc.to_dict() for doc in query.stream()]


class TrendingCache:
    """Firestore collection for caching trending data"""
    collection = 'trendrit_trending'
    
    @staticmethod
    def store(category, data, ttl_hours=6):
        """Store trending data with TTL"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc_ref = Config.db.collection(TrendingCache.collection).document(category)
        doc_ref.set({
            'category': category,
            'data': data,
            'updated_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=ttl_hours)
        })
    
    @staticmethod
    def get(category):
        """Get trending data if not expired"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc = Config.db.collection(TrendingCache.collection).document(category).get()
        if doc.exists:
            data = doc.to_dict()
            if data.get('expires_at', datetime.utcnow()) > datetime.utcnow():
                return data.get('data')
        return None
    
    @staticmethod
    def delete(category):
        """Delete cached category"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        Config.db.collection(TrendingCache.collection).document(category).delete()


class UserModel:
    """Firestore model for user profiles"""
    collection = 'trendrit_users'
    
    @staticmethod
    def create_or_update(user_id, profile_data):
        """Create or update user profile"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc_ref = Config.db.collection(UserModel.collection).document(user_id)
        
        data = {
            'user_id': user_id,
            'profile': profile_data,
            'meme_count': 0,
            'last_activity': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
        doc_ref.set(data, merge=True)
    
    @staticmethod
    def get(user_id):
        """Get user profile"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc = Config.db.collection(UserModel.collection).document(user_id).get()
        return doc.to_dict() if doc.exists else None
    
    @staticmethod
    def increment_meme_count(user_id):
        """Increment user's meme count"""
        if not Config.db:
            raise RuntimeError("Firestore not initialized")
            
        doc_ref = Config.db.collection(UserModel.collection).document(user_id)
        doc_ref.update({
            'meme_count': firestore.Increment(1),
            'last_activity': datetime.utcnow()
        })


# Import firestore Increment for atomic operations
from google.cloud import firestore
