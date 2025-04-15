import fitz  # PyMuPDF
import os
import pprint

class extractDrawings:
    def __init__(self, output_dir="output", dpi=300):
        self.output_dir = output_dir
        self.dpi = dpi 
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "drawings"), exist_ok=True)
            

    def extract_drawings(self, pdf_path):
        doc = fitz.open(pdf_path)
        pages_extracted = 0
        drawings_info = {}
        """Checking changes"""
        for page_num in range(len(doc)):
            page = doc[page_num]
            paths = page.get_drawings()  # extract existing drawings
            """pprint.pprint(paths)"""
            outpdf = fitz.open()
            outpage = outpdf.new_page(width=page.rect.width, height=page.rect.height)
            shape = outpage.new_shape()  
            for path in paths:
                for item in path["items"]:  # these are the draw commands
                    if item[0] == "l":  # line
                        shape.draw_line(item[1], item[2])
                    elif item[0] == "re":  # rectangle
                        shape.draw_rect(item[1])
                    elif item[0] == "qu":  # quad
                        shape.draw_quad(item[1])
                    elif item[0] == "c":  # curve
                        shape.draw_bezier(item[1], item[2], item[3], item[4])
                    else:
                        raise ValueError("unhandled drawing", item)

                line_cap = path.get("lineCap")
                line_cap_value = max(line_cap) if line_cap else 0  # Default to 0

                line_join = path.get("lineJoin")
                line_join_value = line_join if isinstance(line_join, int) else 0 

                # Ensure opacity values are valid numbers between 0 and 1
                stroke_opacity = path.get("stroke_opacity")
                fill_opacity = path.get("fill_opacity")
        
                # Default to 1 (fully opaque) if None or invalid
                stroke_opacity = 1 if stroke_opacity is None or not (0 <= stroke_opacity <= 1) else stroke_opacity
                fill_opacity = 1 if fill_opacity is None or not (0 <= fill_opacity <= 1) else fill_opacity

                width = path.get("width")
                width_value = width if isinstance(width, (int, float)) else 1  # Default to 1 if None

                shape.finish(
                    fill=path.get("fill"),
                    color=path.get("color"),
                    dashes=path.get("dashes"),
                    even_odd=path.get("even_odd", True),
                    closePath=path.get("closePath", False),
                    lineJoin=line_join_value,
                    lineCap=line_cap_value,
                    width=width_value,
                    stroke_opacity=stroke_opacity,
                    fill_opacity=fill_opacity,
                )

            #Move this to infividual drawing in a separate file.
            shape.commit()
            outpdf.save(f"drawings-page-{page_num}.pdf")

        doc.close()
        outpdf.close()


if __name__ == "__main__":
    pdfDir = "./pdfs"
    processor = extractDrawings()
    results = processor.extract_drawings(pdfDir + "/S-202 Typical Details.pdf")