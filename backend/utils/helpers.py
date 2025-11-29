from config import Config
from PIL import Image
import os

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def validate_image(filepath):
    """Validate if file is a valid image"""
    try:
        img = Image.open(filepath)
        img.verify()
        return True
    except:
        return False

def cleanup_temp_files(folder, age_hours=24):
    """Remove old temporary files"""
    import time
    now = time.time()
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            if os.stat(filepath).st_mtime < now - age_hours * 3600:
                os.remove(filepath)
