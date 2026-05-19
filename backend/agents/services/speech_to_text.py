# def transcribe_audio(file_obj):
#     """
#     TODO - Speech to Text Team:
#     Convert uploaded Arabic/English audio to text.

#     Expected return:
#     {
#         "success": True,
#         "text": "...",
#         "error": None
#     }
#     """
#     return {
#         "success": False,
#         "text": "",
#         "error": "خدمة تحويل الصوت إلى نص لم تكتمل بعد."
#     }

import os
import shutil
import validators
import yt_dlp
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def format_transcribed_text_auto(raw_text):
    """
Takes the raw text and detects its language, then rearranges it and its headings in the same original language.    """
   
    prompt = f"""
    You are an expert educational content designer and formatter.
    Analyze the following raw transcribed text, detect its language (Arabic or English),
    and rewrite it in a highly professional, organized, and beautiful structure USING THE SAME ORIGINAL LANGUAGE,
    do not change any text unless it is greeting or has no meaning.
    
    Strict Rules:
    1. do not use any format other than plain text, do not use markdown or html or any other format, just plain text.
    2. make a title and sub titles if it is needed, but do not add any new information, just rearrange the original text and its headings in a more organized way.
    Raw Transcribed Text to format:
    {raw_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional educational formatter who respects the input language automatically."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content

def transcribe_audio(file_obj):
    if not shutil.which("ffmpeg"):
        print("🛑 عذراً! يحتاج البرنامج لتثبيت أداة معالجة الصوت.")
        print("💡 الحل: اكتبي في التيرمينال: brew install ffmpeg")
        return "ERROR: FFmpeg missing"
    """
Convert local audio files or web links (such as YouTube) to written text using OpenAI Whisper.
"""

    
    is_web_url = validators.url(file_obj)
    
    if is_web_url:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'temp_downloaded_audio.%(ext)s',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([file_obj])
        source_for_whisper = "temp_downloaded_audio.mp3"
    else:
       
        source_for_whisper = file_obj

    
    
    with open(source_for_whisper, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    
    extracted_text = response.text
    formatted_text = format_transcribed_text_auto(extracted_text)

    if is_web_url and os.path.exists("temp_downloaded_audio.mp3"):
        os.remove("temp_downloaded_audio.mp3")
        
    return formatted_text