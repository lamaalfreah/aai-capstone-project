
import os
import base64
from dotenv import load_dotenv
from openai import OpenAI
from mistralai.client import Mistral


load_dotenv()

openai_client = OpenAI()
mistral_client = Mistral()

def analyze_educational_image_clean(image_path):
    """
   This method converts the image to Base64 and then sends it to MISTRAL OCR.
   If it contains text, it extracts it; if not, it is sent to gpt-4o for analysis.
    """
    #print(f"\n🔍 [Vision AI]: بدء فحص الصورة برمجياً -> {image_path}")
    
    with open(image_path, "rb") as img_file:
        base64_data = base64.b64encode(img_file.read()).decode("utf-8")
    
    
    data_url = f"data:image/png;base64,{base64_data}" if image_path.lower().endswith('.png') else f"data:image/jpeg;base64,{base64_data}"

    #MISTRAL OCR:
    try:

        ocr_response = mistral_client.ocr.process(
            #model="mistral-ocr-latest",
            model="pixtral-large-latest",
            document={
                "type": "image_url",
                "image_url": data_url 
            }
        )
        
        extracted_text = ""
        if ocr_response.pages:
            extracted_text = " ".join([page.markdown for page in ocr_response.pages]).strip()


        if len(extracted_text.split()) > 3:
            return extracted_text
        else:
            return "لم يُعثر على نصوص كافية في الصورة."
            
    except Exception as e:
        print(f"حدث خلل أثناء الفحص: {e}")


    # GPT -40:
    
    system_instruction = (
        "You are an expert educational visual analyst. Analyze this image "
        "and explain its academic concepts, charts, or diagrams thoroughly in Arabic."
    )
    
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_instruction},
                    {"type": "image_url", "image_url": {"url": data_url}} 
                ]
            }
        ],
        temperature=0.4
    )
    
    return response.choices[0].message.content


