from config import Config
from datetime import datetime, timedelta
import uuid

class MemeModel:
    collection = 'memes'
    
    @staticmethod
    def create(user_id, image_url, metadata):
        doc_id = str(uuid.uuid4())
        doc_ref = Config.db.collection(MemeModel.collection).document(doc_id)
        
        data = {
            'id': doc_id,
            'user_id': user_id,
            'image_url': image_url,
            'metadata': metadata,
            'created_at': datetime.utcnow(),
            'status': 'processing'
        }
        doc_ref.set(data)
        return doc_id
    
    @staticmethod
    def update_status(doc_id, status, output_urls=None):
        doc_ref = Config.db.collection(MemeModel.collection).document(doc_id)
        update_data = {'status': status, 'updated_at': datetime.utcnow()}
        if output_urls:
            update_data['outputs'] = output_urls
        doc_ref.update(update_data)
    
    @staticmethod
    def get(doc_id):
        doc = Config.db.collection(MemeModel.collection).document(doc_id).get()
        return doc.to_dict() if doc.exists else None

class TrendingCache:
    collection = 'trending'
    
    @staticmethod
    def store(category, data, ttl_hours=6):
        doc_ref = Config.db.collection(TrendingCache.collection).document(category)
        doc_ref.set({
            'data': data,
            'updated_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=ttl_hours)
        })
    
    @staticmethod
    def get(category):
        doc = Config.db.collection(TrendingCache.collection).document(category).get()
        if doc.exists:
            data = doc.to_dict()
            if data['expires_at'] > datetime.utcnow():
                return data['data']
        return None
