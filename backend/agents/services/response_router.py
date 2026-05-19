"""
Response Router - Fahem Agent

This file connects the chat view with the agent services.

Main goals:
- Use GPT as the main conversation agent.
- Detect the request type from message, attachment, and learning style.
- Extract content from files/images/audio when needed.
- Transform the content according to the learner style.
- Return a standard dictionary that the view can store and display.
"""

from pathlib import Path

from django.conf import settings
from dotenv import load_dotenv
from openai import OpenAI

from .audio_generator import generate_learning_audio
from .file_generator import generate_learning_file
from .file_to_text import extract_text_from_file
from .image_generator import generate_image_from_text
from .image_to_text import extract_text_from_image
from .speech_to_text import transcribe_audio
from .text_formatter import format_extracted_text

load_dotenv()

client = OpenAI()

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".webm"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".html", ".htm"}


def get_file_extension(attachment):
    if not attachment:
        return ""
    return Path(attachment.name).suffix.lower()


def _normalize_style(learning_style):
    style = (learning_style or "").strip().lower()

    if any(word in style for word in ["visual", "بصري"]):
        return "visual"
    if any(word in style for word in ["auditory", "سمعي"]):
        return "auditory"
    if any(word in style for word in ["reading", "read", "write", "قرائي", "كتابي"]):
        return "reading"
    if any(word in style for word in ["kinesthetic", "حركي", "تطبيقي"]):
        return "kinesthetic"

    return "unknown"


def _style_label(style):
    labels = {
        "visual": "بصري",
        "auditory": "سمعي",
        "reading": "قرائي / كتابي",
        "kinesthetic": "حركي / تطبيقي",
        "unknown": "غير محدد",
    }
    return labels.get(style, "غير محدد")


def detect_user_intent(message, attachment, learning_style):
    """
    Returns one of:
    - document_to_text
    - image_to_text
    - speech_to_text
    - audio_generation
    - image_generation
    - file_generation
    - content_transformation
    - general_chat
    """

    message = (message or "").lower()
    extension = get_file_extension(attachment)

    if attachment:
        if extension in IMAGE_EXTENSIONS:
            return "image_to_text"
        if extension in AUDIO_EXTENSIONS:
            return "speech_to_text"
        if extension in DOCUMENT_EXTENSIONS:
            return "document_to_text"

    if any(k in message for k in ["صوت", "بودكاست", "استماع", "audio", "podcast", "voice"]):
        return "audio_generation"

    if any(k in message for k in ["صورة", "مخطط", "خريطة", "رسم", "diagram", "mind map", "mindmap", "flowchart", "visual"]):
        return "image_generation"

    if any(k in message for k in ["ملف", "pdf", "download", "worksheet", "ورقة عمل", "لتحميل"]):
        return "file_generation"

    if len(message.strip()) > 40:
        return "content_transformation"

    return "general_chat"


def _call_gpt(system_prompt, user_prompt, temperature=0.4):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _extract_content_from_attachment(attachment):
    extension = get_file_extension(attachment)

    if extension in DOCUMENT_EXTENSIONS:
        result = extract_text_from_file(attachment)
        if not result.get("success"):
            return {
                "success": False,
                "content": "",
                "error": result.get("error") or "تعذر استخراج النص من الملف.",
                "source_service": "file_to_text",
            }

        formatted = format_extracted_text(result.get("text", ""))
        return {
            "success": True,
            "content": formatted,
            "error": None,
            "source_service": "file_to_text",
        }

    if extension in IMAGE_EXTENSIONS:
        result = extract_text_from_image(attachment)
        if not result.get("success"):
            return {
                "success": False,
                "content": "",
                "error": result.get("error") or "تعذر تحليل الصورة.",
                "source_service": "image_to_text",
            }

        formatted = format_extracted_text(result.get("text", ""))
        return {
            "success": True,
            "content": formatted,
            "error": None,
            "source_service": "image_to_text",
        }

    if extension in AUDIO_EXTENSIONS:
        result = transcribe_audio(attachment)
        if not result.get("success"):
            return {
                "success": False,
                "content": "",
                "error": result.get("error") or "تعذر تحويل الصوت إلى نص.",
                "source_service": "speech_to_text",
            }

        formatted = format_extracted_text(result.get("text", ""))
        return {
            "success": True,
            "content": formatted,
            "error": None,
            "source_service": "speech_to_text",
        }

    return {
        "success": False,
        "content": "",
        "error": f"نوع الملف غير مدعوم: {extension}",
        "source_service": "unknown",
    }


def _transform_content_for_style(content, learning_style):
    style = _normalize_style(learning_style)
    label = _style_label(style)

    style_instructions = {
        "visual": (
            "حوّل المحتوى إلى شرح بصري واضح. استخدم عناوين قصيرة، علاقات بين المفاهيم، "
            "ونقاط مناسبة لإنشاء مخطط أو خريطة ذهنية."
        ),
        "auditory": (
            "حوّل المحتوى إلى سكربت شرح صوتي طبيعي وممتع كأنه بودكاست تعليمي قصير. "
            "اجعل الجمل سهلة الاستماع."
        ),
        "reading": (
            "حوّل المحتوى إلى ملخص منظم بعناوين واضحة ونقاط مرتبة وملاحظات قابلة للمذاكرة."
        ),
        "kinesthetic": (
            "حوّل المحتوى إلى خطوات تطبيقية وتمارين قصيرة وأمثلة عملية تساعد المتعلم على التجربة."
        ),
        "unknown": (
            "رتّب المحتوى تعليميًا بشكل واضح ومختصر مع عناوين ونقاط سهلة الفهم."
        ),
    }

    system_prompt = (
        "You are Fahem, an adaptive educational assistant. "
        "You transform educational content based on the learner's style. "
        "Keep the original language of the content. "
        "Do not add unrelated information. Return clean plain text only."
    )

    user_prompt = f"""
Learner style: {label}

Task:
{style_instructions.get(style, style_instructions["unknown"])}

Content:
{content}
"""

    transformed = _call_gpt(system_prompt, user_prompt, temperature=0.3)

    return {
        "style": style,
        "style_label": label,
        "transformed_content": transformed,
    }


def _build_general_chat_response(message, learning_style):
    style = _normalize_style(learning_style)
    label = _style_label(style)

    system_prompt = (
        "You are Fahem, a friendly adaptive learning assistant. "
        "Reply in the user's language. Be concise, welcoming, and helpful. "
        "Mention the user's learning style if available. "
        "Invite the user to send or upload learning content."
    )

    user_prompt = f"""
User message:
{message or "ابدأ المحادثة"}

Current learning style:
{label}

Write a friendly reply for the user.
"""

    return _call_gpt(system_prompt, user_prompt, temperature=0.5)


def _with_follow_up(text):
    follow_up = "هل عندك محتوى آخر تبي نحوله لك؟"
    if follow_up in text:
        return text.strip()
    return f"{text.strip()}\n\n{follow_up}"


def route_user_request(message, attachment, learning_style):
    """
    Standard return format:
    {
        "content": "...",
        "service": "...",
        "metadata": {},
        "learning_content": "...",
        "is_learning_output": True/False
    }
    """

    message = (message or "").strip()
    style = _normalize_style(learning_style)
    style_label = _style_label(style)
    intent = detect_user_intent(message, attachment, learning_style)

    metadata = {
        "intent": intent,
        "learning_style": style_label,
        "file_extension": get_file_extension(attachment),
    }

    try:
        # 1) Get the base content from attachment or message.
        extracted_content = ""
        source_service = None

        if attachment:
            extraction = _extract_content_from_attachment(attachment)
            if not extraction.get("success"):
                return {
                    "content": extraction.get("error", "تعذر معالجة المرفق."),
                    "service": extraction.get("source_service", "attachment_processing"),
                    "metadata": metadata,
                    "learning_content": "",
                    "is_learning_output": False,
                }

            extracted_content = extraction["content"]
            source_service = extraction["source_service"]
            metadata["source_service"] = source_service

        base_content = extracted_content or message

        # 2) If it is a normal chat message, reply as the main GPT assistant.
        if intent == "general_chat":
            reply = _build_general_chat_response(message, learning_style)
            return {
                "content": reply,
                "service": "gpt_chat",
                "metadata": metadata,
                "learning_content": "",
                "is_learning_output": False,
            }

        # 3) Transform educational content according to the style.
        transformation = _transform_content_for_style(base_content, learning_style)
        transformed = transformation["transformed_content"]
        metadata["style"] = transformation["style"]
        metadata["style_label"] = transformation["style_label"]

        content_parts = [
            f"نمطك الحالي: {style_label}",
            "",
            transformed,
        ]

        # 4) Generate style-specific output or requested output.
        if intent == "image_generation" or style == "visual":
            image_result = generate_image_from_text(transformed, learning_style=style)
            metadata["image_result"] = image_result
            if image_result.get("success"):
                metadata["image_path"] = image_result.get("image_path")
                content_parts.append("")
                content_parts.append(image_result.get("message", "تم إنشاء المخطط التعليمي."))

        if intent == "audio_generation" or style == "auditory":
            audio_result = generate_learning_audio(transformed, language="ar")
            metadata["audio_result"] = audio_result
            if audio_result.get("success"):
                metadata["audio_path"] = audio_result.get("audio_path")
                content_parts.append("")
                content_parts.append("تم إنشاء شرح صوتي مناسب لنمطك السمعي.")

        if intent == "file_generation":
            file_result = generate_learning_file(transformed, learning_style=style)
            metadata["file_result"] = file_result
            if file_result.get("success"):
                metadata["file_path"] = file_result.get("file_path")
                content_parts.append("")
                content_parts.append(file_result.get("message", "تم إنشاء الملف التعليمي."))

        final_content = _with_follow_up("\n".join(content_parts))

        return {
            "content": final_content,
            "service": "adaptive_content_router",
            "metadata": metadata,
            "learning_content": transformed,
            "is_learning_output": True,
        }

    except Exception as exc:
        return {
            "content": f"حدث خطأ أثناء معالجة طلبك: {exc}",
            "service": "response_router_error",
            "metadata": metadata,
            "learning_content": "",
            "is_learning_output": False,
        }
