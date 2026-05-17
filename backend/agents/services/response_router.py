"""
Response Router - Fahem Agent

This file is the central place that will connect all agent services together.

The purpose of this router is to decide which service should handle the user's request
based on:
- user message
- uploaded attachment
- learning style
- file type
- requested output format

Hessah: responsible for this file should complete the routing logic later.
"""

from pathlib import Path


# Supported file type groups
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".html", ".htm"}


def get_file_extension(attachment):
    """
    Return the uploaded file extension.

    Example:
    lecture.pdf -> .pdf
    image.png -> .png
    audio.mp3 -> .mp3
    """

    if not attachment:
        return ""

    return Path(attachment.name).suffix.lower()


def detect_user_intent(message, attachment, learning_style):
    """
    Detect what the user likely wants.

    This function should be completed later.

    Possible returned intents:
    - file_to_text
    - speech_to_text
    - image_to_text
    - audio_generation
    - image_generation
    - file_generation
    - text_response
    """

    # TODO:
    # Analyze the message, attachment type, and learning style.
    # Decide which service should handle the request.

    return "text_response"


def route_user_request(message, attachment, learning_style):
    """
    Main router function used by views.py.

    This function should call the correct service based on the detected intent.

    Expected return format:
    {
        "content": "response text shown to the user",
        "service": "service name",
        "metadata": {}
    }
    """

    message = (message or "").strip()
    learning_style = learning_style or "غير محدد"

    intent = detect_user_intent(
        message=message,
        attachment=attachment,
        learning_style=learning_style
    )

    # TODO:
    # Connect each intent with the correct service file.
    #
    # Example:
    # if intent == "file_to_text":
    #     call extract_text_from_file()
    #
    # if intent == "speech_to_text":
    #     call transcribe_audio()
    #
    # if intent == "image_to_text":
    #     call extract_text_from_image()
    #
    # if intent == "audio_generation":
    #     call generate_learning_audio()
    #
    # if intent == "image_generation":
    #     call generate_image_from_text()
    #
    # if intent == "file_generation":
    #     call generate_learning_file()

    return {
        "content": (
            f"استلمت طلبك. نمط تعلمك الحالي: {learning_style}.\n"
            "سيتم لاحقًا توجيه هذا الطلب إلى الخدمة المناسبة من خلال response_router."
        ),
        "service": intent,
        "metadata": {
            "learning_style": learning_style,
            "has_attachment": bool(attachment),
            "file_extension": get_file_extension(attachment),
        }
    }