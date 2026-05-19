import base64
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

openai_client = OpenAI()


def _get_mistral_client():
    """
    Creates a Mistral client only when needed.
    This keeps the project running even if Mistral is not configured yet.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return None

    try:
        from mistralai.client import Mistral
        return Mistral(api_key=api_key)
    except Exception:
        try:
            from mistralai import Mistral
            return Mistral(api_key=api_key)
        except Exception:
            return None


def _save_uploaded_image(image_obj):
    suffix = Path(image_obj.name).suffix.lower() or ".png"
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

    try:
        for chunk in image_obj.chunks():
            temp.write(chunk)
    finally:
        temp.close()

    return temp.name


def analyze_educational_image_clean(image_path):
    """
    Uses Mistral OCR when available. If OCR is not enough, GPT-4o analyzes the image.
    """
    with open(image_path, "rb") as img_file:
        base64_data = base64.b64encode(img_file.read()).decode("utf-8")

    data_url = (
        f"data:image/png;base64,{base64_data}"
        if image_path.lower().endswith(".png")
        else f"data:image/jpeg;base64,{base64_data}"
    )

    mistral_client = _get_mistral_client()

    if mistral_client:
        try:
            ocr_response = mistral_client.ocr.process(
                model="pixtral-large-latest",
                document={
                    "type": "image_url",
                    "image_url": data_url,
                },
            )

            extracted_text = ""
            if getattr(ocr_response, "pages", None):
                extracted_text = " ".join([page.markdown for page in ocr_response.pages]).strip()

            if len(extracted_text.split()) > 3:
                return extracted_text

        except Exception:
            pass

    system_instruction = (
        "You are an expert educational visual analyst. Analyze this image and explain "
        "its academic concepts, text, charts, or diagrams. Reply in Arabic if the image "
        "contains Arabic, otherwise reply in the original language."
    )

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_instruction},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        temperature=0.4,
    )

    return response.choices[0].message.content.strip()


def extract_text_from_image(image_obj):
    """
    Return:
    {
        "success": True,
        "text": "...",
        "error": None
    }
    """
    if not image_obj:
        return {
            "success": False,
            "text": "",
            "error": "لم يتم رفع صورة.",
        }

    temp_path = None

    try:
        if hasattr(image_obj, "chunks"):
            temp_path = _save_uploaded_image(image_obj)
            image_path = temp_path
        else:
            image_path = str(image_obj)

        text = analyze_educational_image_clean(image_path)

        if not text or not text.strip():
            return {
                "success": False,
                "text": "",
                "error": "لم يتم استخراج أو تحليل محتوى واضح من الصورة.",
            }

        return {
            "success": True,
            "text": text,
            "error": None,
        }

    except Exception as exc:
        return {
            "success": False,
            "text": "",
            "error": f"حدث خطأ أثناء تحليل الصورة: {exc}",
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)