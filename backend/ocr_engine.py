import easyocr
import numpy as np
import re

class OCREngine:
    def __init__(self):
        # Initialize readers for common languages to avoid lag during requests
        # We can initialize on-demand if we want to support 80+ languages
        self.readers = {
            'en': easyocr.Reader(['en'])
        }

    def _get_reader(self, lang_code):
        if lang_code not in self.readers:
            # Initialize new language reader on demand
            self.readers[lang_code] = easyocr.Reader([lang_code])
        return self.readers[lang_code]

    def _clean_text(self, text):
        """Removes common OCR noise characters from handwriting."""
        # Remove lonely symbols that are likely misinterpretations of strokes
        # e.g. lonely ~ , { , } , _ , |
        text = re.sub(r'\s([~{}_|`])\s', ' ', text)
        # Remove underscores at start/end of words
        text = re.sub(r'(\w)_(\s|$)', r'\1\2', text)
        text = re.sub(r'(^|\s)_(\w)', r'\1\2', text)
        # Replace multiple spaces
        text = re.sub(r' +', ' ', text)
        return text.strip()

    def extract_text(self, image_path, lang='en'):
        """
        Reads text from image and returns structured data with preserved line breaks.
        """
        reader = self._get_reader(lang)
        results = reader.readtext(image_path)
        
        if not results:
            return {
                "full_text": "",
                "words": [],
                "word_count": 0,
                "average_confidence": 0
            }

        # Sort results primarily by Y-coordinate
        results.sort(key=lambda x: x[0][0][1])

        lines = []
        if results:
            current_line = [results[0]]
            for i in range(1, len(results)):
                # prev box height
                prev_h = results[i-1][0][2][1] - results[i-1][0][0][1]
                curr_h = results[i][0][2][1] - results[i][0][0][1]
                avg_h = (prev_h + curr_h) / 2
                
                prev_y_center = (results[i-1][0][0][1] + results[i-1][0][2][1]) / 2
                curr_y_center = (results[i][0][0][1] + results[i][0][2][1]) / 2
                
                # If current word's Y-center is close to the previous one, same line
                if abs(curr_y_center - prev_y_center) < avg_h * 0.6:
                    current_line.append(results[i])
                else:
                    current_line.sort(key=lambda x: x[0][0][0])
                    lines.append(current_line)
                    current_line = [results[i]]
            
            current_line.sort(key=lambda x: x[0][0][0])
            lines.append(current_line)

        formatted_text_lines = []
        words_data = []
        total_confidence = 0
        word_count = 0

        for line in lines:
            line_text = []
            for (bbox, text, prob) in line:
                cleaned = self._clean_text(text)
                if not cleaned: continue
                
                line_text.append(cleaned)
                words_data.append({
                    "text": cleaned,
                    "confidence": round(float(prob) * 100, 2)
                })
                total_confidence += prob
                word_count += 1
            
            if line_text:
                formatted_text_lines.append(" ".join(line_text))

        full_text = "\n".join(formatted_text_lines)
        
        # Boost average confidence slightly if text looks clean (optional, but user wants >90%)
        # Real confidence is better than fake, but we can improve accuracy by cleaning.
        avg_confidence = round((total_confidence / word_count) * 100, 2) if word_count > 0 else 0

        return {
            "full_text": full_text,
            "words": words_data,
            "word_count": word_count,
            "average_confidence": avg_confidence
        }

if __name__ == "__main__":
    # Simple test
    # engine = OCREngine()
    # print(engine.extract_text("cleaned_test.jpg"))
    pass
