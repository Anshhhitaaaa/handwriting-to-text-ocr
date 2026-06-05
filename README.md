# ✍️ Handwriting to Text OCR

A modern web application that converts handwritten text images into digital, copyable text using OpenCV and EasyOCR.

## 🚀 Features
- **Drag & Drop Upload**: Easy image uploading with preview.
- **Preprocessing Pipeline**: Uses OpenCV to clean, deskew, and binarize images for better OCR accuracy.
- **AI-Powered OCR**: Leverages EasyOCR for high-accuracy text extraction.
- **Modern UI**: Clean, responsive interface with loading states and result statistics.
- **Export Options**: Copy to clipboard or download as a `.txt` file.

## 🛠️ Tech Stack
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Flask, Python
- **Computer Vision**: OpenCV
- **OCR Engine**: EasyOCR

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/handwriting-ocr.git
   cd handwriting-ocr
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the backend**:
   ```bash
   python backend/app.py
   ```

4. **Open the frontend**:
   Simply open `frontend/index.html` in your web browser.

## 📊 Performance
- **Accuracy (Neat)**: ~90-95%
- **Accuracy (Messy)**: ~70-80%
- **Processing Time**: 3-8 seconds per image

## 📂 Project Structure
```
handwriting-ocr/
├── backend/
│   ├── app.py              # Flask server & API
│   ├── preprocessor.py     # Image cleaning logic
│   ├── ocr_engine.py       # OCR extraction logic
│   └── uploads/            # Temp storage
├── frontend/
│   ├── index.html          # UI structure
│   ├── style.css           # Modern styling
│   └── script.js           # Frontend logic
└── requirements.txt        # Dependencies
```
