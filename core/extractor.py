"""Extract text or image from uploaded invoice file."""
from PIL import Image
import pdfplumber
import io


def extract(file) -> dict:
    filename = (getattr(file, "name", "") or "").lower()

    if filename.endswith(".pdf"):
        # Try pdfplumber first for digital PDF text
        file.seek(0)
        text = ""
        with pdfplumber.open(file) as pdf:
            pages = len(pdf.pages)
            for page in pdf.pages:
                t = page.extract_text()
                text += (t or "")

        if len(text.strip()) > 100:
            return {
                "type": "text",
                "content": text,
                "method": "pdfplumber",
                "pages": pages,
            }

        # Scanned PDF — render first page to image
        file.seek(0)
        with pdfplumber.open(file) as pdf:
            page = pdf.pages[0]
            page_image = page.to_image(resolution=200)
            pil_image = page_image.original
        return {
            "type": "image",
            "content": pil_image,
            "method": "vision",
            "pages": 1,
        }

    # PNG, JPG, JPEG, TIFF, WEBP
    file.seek(0)
    image = Image.open(file)
    if image.mode != "RGB":
        image = image.convert("RGB")
    return {
        "type": "image",
        "content": image,
        "method": "vision",
        "pages": 1,
    }
