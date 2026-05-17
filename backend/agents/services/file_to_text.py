import os
import tempfile
from pathlib import Path

from docling.document_converter import DocumentConverter


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".txt",
    ".md",
    ".html",
    ".htm",
    ".png",
    ".jpg",
    ".jpeg",
}


def extract_text_from_file(file_obj):
    """
    Extract text from an uploaded file using Docling.

    Supports Arabic and English content depending on the quality of the file.
    For scanned PDFs or images, OCR quality may vary based on image clarity.
    """

    if not file_obj:
        return {
            "success": False,
            "text": "",
            "error": "لم يتم رفع أي ملف."
        }

    original_name = file_obj.name
    extension = Path(original_name).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return {
            "success": False,
            "text": "",
            "error": f"نوع الملف غير مدعوم حاليًا: {extension}"
        }

    temp_path = None

    try:
        # نحفظ الملف مؤقتًا لأن Docling يحتاج مسار ملف
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            temp_path = temp_file.name

            for chunk in file_obj.chunks():
                temp_file.write(chunk)

        converter = DocumentConverter()
        result = converter.convert(temp_path)

        # Markdown مناسب لأنه يحافظ على العناوين والجداول بشكل أوضح
        extracted_text = result.document.export_to_markdown()

        if not extracted_text.strip():
            return {
                "success": False,
                "text": "",
                "error": "لم يتم استخراج نص من الملف. قد يكون الملف صورة منخفضة الجودة أو ممسوحًا ضوئيًا بشكل غير واضح."
            }

        return {
            "success": True,
            "text": extracted_text,
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"حدث خطأ أثناء تحويل الملف إلى نص: {str(e)}"
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)