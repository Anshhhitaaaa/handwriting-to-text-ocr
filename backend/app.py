from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from preprocessor import ImagePreprocessor
from ocr_engine import OCREngine
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
# Use /tmp for Vercel (only writable directory in serverless)
if os.environ.get('VERCEL'):
    UPLOAD_FOLDER = '/tmp'
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize components
preprocessor = ImagePreprocessor(output_dir=UPLOAD_FOLDER)
ocr_engine = OCREngine()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "OCR Server is running"}), 200

@app.route('/extract', methods=['POST'])
def extract_text():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    file = request.files['image']
    lang = request.form.get('lang', 'eng')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename to avoid collisions
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # 1. Preprocess the image
            # Returns two paths: one optimized for OCR, one for visual display
            ocr_path, display_path = preprocessor.preprocess(filepath)
            
            # 2. Extract text using OCR from the optimized image
            results = ocr_engine.extract_text(ocr_path, lang=lang)
            
            # Add preview URL for the cleaned/display image
            results['cleaned_image_url'] = f"/uploads/{os.path.basename(display_path)}"
            
            return jsonify(results), 200
            
        except Exception as e:
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
