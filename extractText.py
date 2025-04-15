import fitz  # PyMuPDF
import PIL.Image
import io
import pytesseract
from pathlib import Path

class PDFImageTextExtractor:
    def __init__(self, tesseract_path=None):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
    def extract_text_from_pdf(self, pdf_path):
        results = {}
        
        pdf_document = fitz.open(pdf_path)
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num]
            
            images = self._extract_images_from_page(page)
            
            if images:
                page_text = []
                for img in images:
                    pil_image = PIL.Image.open(io.BytesIO(img))
                    
                    text = pytesseract.image_to_string(pil_image)
                    if text.strip():
                        page_text.append(text.strip())
                
                if page_text:
                    results[page_num + 1] = "\n".join(page_text)
            
        pdf_document.close()
        return results
    
    def _extract_images_from_page(self, page):

        images = []
        
        # Get image list
        #image_list = page.get_images(full=True)
        image_list = page. get_drawings()
        
        for img_index, img_info in enumerate(image_list):
            base_image = pdf_document.extract_image(img_info[0])
            if base_image:
                images.append(base_image["image"])
                
        return images
    
    def process_directory(self, directory_path, output_file=None):

        results = {}
        directory = Path(directory_path)
        
        for pdf_file in directory.glob("*.pdf"):
            try:
                extracted_text = self.extract_text_from_pdf(str(pdf_file))
                if extracted_text:
                    results[pdf_file.name] = extracted_text
            except Exception as e:
                print(f"Error processing {pdf_file.name}: {str(e)}")
                
        if output_file:
            self._save_results(results, output_file)
            
        return results
    
    def _save_results(self, results, output_file):
        with open(output_file, 'w', encoding='utf-8') as f:
            for pdf_name, page_texts in results.items():
                f.write(f"\n{'='*50}\n")
                f.write(f"File: {pdf_name}\n")
                f.write(f"{'='*50}\n\n")
                
                for page_num, text in page_texts.items():
                    f.write(f"Page {page_num}:\n")
                    f.write(f"{text}\n\n")