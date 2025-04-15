from extractText import PDFImageTextExtractor
from pdfProcessor import PDFProcessor
pdfDir = "./pdfs"
outputDir = "./extracted"

# Initialize the extractor
#extractor = PDFImageTextExtractor()

# Process a single PDF
#results = extractor.extract_drawings_from_page(pdfDir + "/S-202 Typical Details.pdf")

# # Process all PDFs in a directory
# directory_results = extractor.process_directory(
#     pdfDir,
#     output_file= outputDir+ "/extracted_text.txt"
# )

# Usage example
if __name__ == "__main__":
    processor = PDFProcessor()
    results = processor.process_pdf(pdfDir + "/S-202 Typical Details.pdf")
    print(f"Created output files with base path: {results['base_path']}")
    print(f"Extracted {results['num_pages']} pages")
    print(f"Processed {results['num_sections']} text sections")
    print(f"Found {sum(len(drawings) for drawings in results['drawings_info'].values())} individual drawings")