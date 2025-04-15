import fitz  # PyMuPDF
import pandas as pd
import re
import os
import cv2
import numpy as np
from PIL import Image
import json

class PDFProcessor:
    def __init__(self, output_dir="output", dpi=300):
        self.output_dir = output_dir
        self.dpi = dpi  # New configurable DPI setting
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "drawings"), exist_ok=True)
        
    def detect_drawings(self, image_path):
        """Detect and extract individual drawings from an image using contour detection"""
        # Read the image
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        drawings = []
        min_area = 10000  # Minimum area to consider as a drawing
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                # Add some padding
                padding = 10
                x = max(0, x - padding)
                y = max(0, y - padding)
                w = min(img.shape[1] - x, w + 2*padding)
                h = min(img.shape[0] - y, h + 2*padding)
                
                drawing = img[y:y+h, x:x+w]
                drawings.append({
                    'image': drawing,
                    'coordinates': (x, y, w, h)
                })
        
        return drawings

    def clean_drawing(self, image):
        """Apply image processing to clean up the drawing"""
        # Convert to grayscale if not already
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Adaptive threshold to improve line clarity
        binary = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Remove small noise
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        return cleaned

    def extract_pages_as_images(self, pdf_path):
        """Extract each page as a high-resolution image with automatic drawing detection"""
        doc = fitz.open(pdf_path)
        pages_extracted = 0
        drawings_info = {}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Calculate zoom factor based on desired DPI
            zoom = self.dpi / 72  # 72 is the base PDF DPI
            mat = fitz.Matrix(zoom, zoom)
            
            try:
                # Get the page's pixmap
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Save the full page
                page_filename = f"page_{page_num + 1}.png"
                page_path = os.path.join(self.output_dir, "drawings", page_filename)
                pix.save(page_path)
                
                # Detect and extract individual drawings
                drawings = self.detect_drawings(page_path)
                drawings_info[page_num + 1] = []
                
                for idx, drawing in enumerate(drawings):
                    # Clean the drawing
                    cleaned_drawing = self.clean_drawing(drawing['image'])
                    
                    # Save in multiple formats
                    basename = f"page_{page_num + 1}_drawing_{idx + 1}"
                    
                    # Save PNG
                    png_path = os.path.join(self.output_dir, "drawings", f"{basename}.png")
                    cv2.imwrite(png_path, cleaned_drawing)
                    
                    # Save JPEG
                    jpg_path = os.path.join(self.output_dir, "drawings", f"{basename}.jpg")
                    cv2.imwrite(jpg_path, cleaned_drawing, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    
                    # Save SVG (using Potrace or similar library if installed)
                    try:
                        from potrace import Bitmap
                        from svg.path import Path
                        bitmap = Bitmap(cleaned_drawing)
                        path = bitmap.trace()
                        svg_path = os.path.join(self.output_dir, "drawings", f"{basename}.svg")
                        with open(svg_path, 'w') as f:
                            f.write(path.to_svg())
                    except ImportError:
                        print("Potrace not installed - skipping SVG export")
                    
                    drawings_info[page_num + 1].append({
                        'filename': basename,
                        'coordinates': drawing['coordinates'],
                        'formats': ['png', 'jpg', 'svg']
                    })
                
                pages_extracted += 1
                print(f"Successfully processed page {page_num + 1}")
                
            except Exception as e:
                print(f"Error processing page {page_num + 1}: {str(e)}")
                continue
        
        # Save drawings info to JSON
        with open(os.path.join(self.output_dir, "drawings_info.json"), 'w') as f:
            json.dump(drawings_info, f, indent=2)
        
        doc.close()
        return pages_extracted, drawings_info

    def extract_headings_and_content(self, text):
        """Extract headings and their associated content from text"""
        # Original heading extraction code remains the same
        heading_patterns = [
            r"^[A-Z\s\-]+:.*$",
            r"^[A-Z][A-Za-z\s\-]+\([A-Z]+\).*$",
            r"^[A-Z][A-Za-z\s\-]+ DETAIL.*$",
            r"^TYPICAL.*$",
            r"^N\.T\.S\.$"
        ]
        
        combined_pattern = '|'.join(heading_patterns)
        sections = {}
        current_heading = "General"
        current_content = []
        
        for line in text.split('\n'):
            line = line.strip()
            if line and re.match(combined_pattern, line):
                if current_content:
                    sections[current_heading] = ' '.join(current_content).strip()
                current_heading = line
                current_content = []
            elif line:
                current_content.append(line)
        
        if current_content:
            sections[current_heading] = ' '.join(current_content).strip()
            
        return sections

    def process_pdf(self, pdf_path):
        """Process PDF and create output files with extracted text and drawings"""
        # Extract text
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        
        # Extract sections
        sections = self.extract_headings_and_content(full_text)
        
        # Create DataFrame
        df = pd.DataFrame(list(sections.items()), columns=['Heading', 'Content'])
        
        # Save to multiple formats
        base_path = os.path.join(self.output_dir, "extracted_content")
        
        # Excel
        df.to_excel(f"{base_path}.xlsx", index=False)
        
        # CSV
        df.to_csv(f"{base_path}.csv", index=False)
        
        # JSON
        df.to_json(f"{base_path}.json", orient='records', indent=2)
        
        # Extract and process pages
        num_pages, drawings_info = self.extract_pages_as_images(pdf_path)
        
        return {
            'base_path': base_path,
            'num_pages': num_pages,
            'num_sections': len(sections),
            'drawings_info': drawings_info
        }
