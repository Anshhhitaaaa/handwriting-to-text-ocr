import cv2
import numpy as np
import os

class ImagePreprocessor:
    def __init__(self, output_dir="uploads"):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def preprocess(self, image_path):
        """
        Enhanced pipeline for cleaning handwriting images:
        Returns: (ocr_ready_path, display_ready_path)
        """
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")

        # 1. Resize if too large (keep aspect ratio, max width 2000)
        h, w = img.shape[:2]
        if w > 2000:
            scale = 2000 / w
            img = cv2.resize(img, (2000, int(h * scale)), interpolation=cv2.INTER_AREA)

        # 2. Convert to grayscale early for speed
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Fast Shadow Removal / Background Leveling
        # Using a large median blur to estimate background
        struct_element = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
        dilated = cv2.dilate(gray, struct_element)
        bg = cv2.medianBlur(dilated, 21)
        diff = cv2.absdiff(gray, bg)
        diff = 255 - diff
        
        # 4. Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(diff, -1, kernel)

        # 5. Denoising
        denoised = cv2.GaussianBlur(sharpened, (3, 3), 0)
        
        # 6. Deskew (Straighten text)
        deskewed_ocr = self._deskew(denoised)

        # 7. Final Contrast Enhancement for OCR
        _, ocr_binary = cv2.threshold(deskewed_ocr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Save files
        filename = os.path.basename(image_path)
        ocr_path = os.path.join(self.output_dir, f"ocr_{filename}")
        display_path = os.path.join(self.output_dir, f"display_{filename}")
        
        cv2.imwrite(ocr_path, ocr_binary) 
        cv2.imwrite(display_path, deskewed_ocr) # Keep grayscale for display as it looks more "natural"

        return ocr_path, display_path

    def _deskew(self, image):
        """Detects tilt and rotates the image to straighten it."""
        try:
            # Threshold to get text-like areas
            _, thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            coords = np.column_stack(np.where(thresh > 0))
            
            if len(coords) == 0:
                return image

            # Get the rotation angle
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]

            # Handle different OpenCV versions for minAreaRect
            # In some versions it's (center, size, angle)
            # In others it might be slightly different
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            # Limit extreme rotations to avoid upside-down or vertical flips
            if abs(angle) > 20:
                return image

            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            return rotated
        except Exception as e:
            print(f"Deskew failed: {e}")
            return image

if __name__ == "__main__":
    # Simple test if run directly
    # preprocessor = ImagePreprocessor()
    # preprocessor.preprocess("test.jpg")
    pass
