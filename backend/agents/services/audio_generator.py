from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import uuid
from pathlib import Path

import edge_tts
from django.conf import settings
from openai import OpenAI

client = OpenAI()


def _media_root():
    root = getattr(settings, "MEDIA_ROOT", None)
    if root:
        return Path(root)
    return Path(settings.BASE_DIR) / "media"


OUTPUT_DIR = _media_root() / "generated_audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _detect_language(text):
    # Simple Arabic character detection.
    if any("\u0600" <= ch <= "\u06FF" for ch in text):
        return "ar"
    return "en"


def rewrite_as_podcast(text, learning_style="auditory", language=None):
    language = language or _detect_language(text)

    if language == "ar":
        prompt = f"""
حوّل النص التالي إلى شرح صوتي ممتع بأسلوب بودكاست تعليمي بسيط وواضح.

اجعل الأسلوب:
- طبيعيًا ومناسبًا للاستماع.
- واضحًا ومختصرًا.
- مرتبًا بمقدمة قصيرة وانتقالات لطيفة.
- محافظًا على المعنى الأصلي دون إضافة معلومات غير مرتبطة.

النص:
{text}
"""
    else:
        prompt = f"""
Rewrite the following text as an engaging educational podcast script.

Make it:
- conversational
- easy to listen to
- natural and smooth
- suitable for audio narration
- faithful to the original meaning

Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert educational podcast writer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
    )

    return response.choices[0].message.content.strip()


async def text_to_speech(text, language=None):
    language = language or _detect_language(text)

    file_name = f"{uuid.uuid4().hex}.mp3"
    output_path = OUTPUT_DIR / file_name

    voice = "ar-SA-ZariyahNeural" if language == "ar" else "en-US-JennyNeural"

    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(str(output_path))

    return f"generated_audio/{file_name}"


def generate_learning_audio(text, language=None):
    """
    Converts educational text into a podcast-style explanation and MP3 file.

    Return:
    {
        "success": True,
        "podcast_text": "...",
        "audio_path": "generated_audio/example.mp3",
        "message": "..."
    }
    """
    if not text or not text.strip():
        return {
            "success": False,
            "podcast_text": "",
            "audio_path": None,
            "message": "لا يوجد نص كافٍ لإنشاء شرح صوتي.",
        }

    try:
        language = language or _detect_language(text)
        podcast_text = rewrite_as_podcast(text, language=language)
        audio_path = asyncio.run(text_to_speech(podcast_text, language=language))

        return {
            "success": True,
            "podcast_text": podcast_text,
            "audio_path": audio_path,
            "message": "تم إنشاء الشرح الصوتي بنجاح.",
        }

    except Exception as exc:
        return {
            "success": False,
            "podcast_text": "",
            "audio_path": None,
            "message": f"حدث خطأ أثناء إنشاء الشرح الصوتي: {exc}",
        }
