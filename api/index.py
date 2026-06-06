import sys
import os

# Add the current directory to sys.path to ensure local imports work on Vercel
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import uuid
import base64

# Import local modules
try:
    import cv2
    import numpy as np
    from preprocessor import ImagePreprocessor
    from ocr_engine import OCREngine
    print("All modules imported successfully")
except ImportError as e:
    print(f"Import Error: {e}")
    # Don't raise yet, let the app start so we might see logs
    cv2 = None

app = Flask(__name__)
CORS(app)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "status": "online",
        "cv2": cv2.__version__ if cv2 else "missing",
        "python": sys.version
    })

# Configuration
# Use /tmp for Vercel (only writable directory in serverless)
if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
    UPLOAD_FOLDER = '/tmp'
else:
    # Local development path
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'uploads')

# Ensure upload directory exists (safe check for /tmp)
if not os.path.exists(UPLOAD_FOLDER):
    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    except Exception as e:
        print(f"Directory creation error: {e}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Global components (lazy loaded)
_preprocessor = None
_ocr_engine = None

def get_components():
    global _preprocessor, _ocr_engine
    if _preprocessor is None:
        _preprocessor = ImagePreprocessor(output_dir=app.config['UPLOAD_FOLDER'])
    if _ocr_engine is None:
        _ocr_engine = OCREngine()
    return _preprocessor, _ocr_engine

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "OCR Server is running"}), 200

@app.route('/extract', methods=['POST'])
def extract_text():
    preprocessor, ocr_engine = get_components()
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    lang = request.form.get('lang', 'eng')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 1. Preprocess the image
            ocr_path, display_path = preprocessor.preprocess(filepath)
            
            # 2. Extract text
            results = ocr_engine.extract_text(ocr_path, lang=lang)
            
            # 3. Read display image as base64 for reliable delivery on Vercel
            with open(display_path, "rb") as img_file:
                b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                results['cleaned_image_b64'] = f"data:image/jpeg;base64,{b64_string}"
            
            return jsonify(results), 200
            
        except Exception as e:
            print(f"ERROR: {str(e)}") # This will show in Vercel logs
            return jsonify({"error": str(e)}), 500
        finally:
            # Note: In a production app, you might want a background task to clean up old files
            # For now, we'll keep them for debugging or use a manual cleanup script
            pass
            
    return jsonify({"error": "Invalid file type. Only JPG, PNG allowed."}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
