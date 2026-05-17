from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import os
import uuid
import edge_tts
import asyncio
client = OpenAI()


def rewrite_as_podcast(text, learning_style="auditory", language="ar"):

    if language == "ar":
        prompt = f"""
        حوّل النص التالي إلى شرح صوتي ممتع بأسلوب بودكاست تعليمي بسيط وواضح.
        
        اجعل الأسلوب:
        - طبيعي
        - سهل الفهم
        - مناسب للاستماع
        - فيه انتقالات صوتية لطيفة
        
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

        Text:
        {text}
        """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert educational podcast writer."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7
    )

    return response.choices[0].message.content



OUTPUT_DIR = "media/generated_audio"

os.makedirs(OUTPUT_DIR, exist_ok=True)


async def text_to_speech(text, language="ar"):

    file_name = f"{uuid.uuid4()}.mp3"

    output_path = os.path.join(OUTPUT_DIR, file_name)

    if language == "ar":
        voice = "ar-SA-ZariyahNeural"
    else:
        voice = "en-US-JennyNeural"

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice
    )

    await communicate.save(output_path)

    return output_path


def generate_learning_audio(text, language="ar"):

    # 1- Rewriting the text
    podcast_text = rewrite_as_podcast(
        text,
        language=language
    )

    # 2- Converting text to speech
    audio_path = asyncio.run(
        text_to_speech(
            podcast_text,
            language
        )
    )

    return {
        "podcast_text": podcast_text,
        "audio_path": audio_path
    }