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

        # 1. Resize if too small/large (aim for ~1500px width)
        h, w = img.shape[:2]
        target_width = 1500
        if w != target_width:
            scale = target_width / w
            img = cv2.resize(img, (target_width, int(h * scale)), interpolation=cv2.INTER_CUBIC)

        # 2. Shadow Removal
        rgb_planes = cv2.split(img)
        result_planes = []
        for plane in rgb_planes:
            dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
            bg_img = cv2.medianBlur(dilated_img, 21)
            diff_img = 255 - cv2.absdiff(plane, bg_img)
            norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
            result_planes.append(norm_img)
        img = cv2.merge(result_planes)

        # 3. Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 4. Sharpening (Subtle)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)

        # 5. Denoising
        # Bilateral filter is great for preserving edges (strokes) while removing background noise
        denoised = cv2.bilateralFilter(sharpened, 9, 75, 75)
        
        # 6. Deskew
        deskewed_ocr = self._deskew(denoised)

        # 7. Binarization for Display ONLY (Adaptive is better for visuals)
        display_binary = cv2.adaptiveThreshold(
            deskewed_ocr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )

        # Save files
        filename = os.path.basename(image_path)
        ocr_path = os.path.join(self.output_dir, f"ocr_{filename}")
        display_path = os.path.join(self.output_dir, f"display_{filename}")
        
        cv2.imwrite(ocr_path, deskewed_ocr) # OCR works best on high-contrast grayscale
        cv2.imwrite(display_path, display_binary)

        return ocr_path, display_path

    def _deskew(self, image):
        """Detects tilt and rotates the image to straighten it."""
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        
        # OpenCV angle convention
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated

if __name__ == "__main__":
    # Simple test if run directly
    # preprocessor = ImagePreprocessor()
    # preprocessor.preprocess("test.jpg")
    pass
