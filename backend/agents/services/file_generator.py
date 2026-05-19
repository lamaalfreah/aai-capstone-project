
import os
import io
from mistralai.client import Mistral
from dotenv import load_dotenv

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ARABIC
import arabic_reshaper
from bidi.algorithm import get_display

load_dotenv()
mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def generate_educational_pdf_final(raw_text):
    
    system_prompt = (
        "You are an academic assistant. Format the text into a clean academic structure. "
        "Do not translate or convert the text to English. "
        "For mathematical equations, write them clearly like 'القوة = الكتلة * التسارع (F = ma)'. "
        "Keep the output professional."
        "use the original language of the text (Arabic/English) and return ONLY the formatted text without any explanations or extra content."
        "if the context is written as a markdown, translate it into a formatted  text."
        "do not delete or change any part of the original text unless it is a greeting."
        "markdown > PDF if it is between **text** make it bold, if it is between *text* make it italic, if it is between `text` make it code style, if it is after #text make it a title, if it is between ##text make it a subtitle."
        "if the text is equations, do not delete them, just write them as they are in the original text"
    )
    
    
    
    response = mistral_client.chat.complete(
        model="pixtral-large-latest", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text}
        ]
    )
    clean_text = response.choices[0].message.content

    print("صياغة الملف جارية...")
    
    
    try:
        font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
        pdfmetrics.registerFont(TTFont('ArabicFont', font_path))
    except:
        pass

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    style = ParagraphStyle('ArabicStyle', fontName='ArabicFont', fontSize=12, alignment=2)
    
    story = []
    for line in clean_text.split('\n'):
        if line.strip():
            reshaped_text = arabic_reshaper.reshape(line.strip())
            bidi_text = get_display(reshaped_text)
            story.append(Paragraph(bidi_text, style))
            story.append(Spacer(1, 12))
            
    doc.build(story)
    buffer.seek(0)
    return buffer
