from openai import OpenAI
import os
import json
from dotenv import load_dotenv
load_dotenv()

client = OpenAI()

def generate_quiz_from_content(content):
    """
    دالة بسيطة تولد أسئلة بناءً على المحتوى الممرر لها.
    """
    prompt = (
       """ بناءً على المحتوى التعليمي التالي:{content}
       * قم بتوليد 5 أسئلة خيارات متعددة (MCQs).
       * يجب أن تكون الأسئلة واضحة ومباشرة وتغطي نقاطًا مهمة من المحتوى.
       * لكل سؤال، قدم 3 خيارات للإجابة، مع تحديد الخيار الصحيح.
       * إذا كان المحتوى يقبل أكثر من 5 أسئلة فيمكنك توليد الميزيد، وإذا كان المحتوى لا يسمح بتوليد 5 أسئلة، فقم بتوليد أقل عدد ممكن من الأسئلة الجيدة.
       * لا تولد أي أسئلة غير مرتبطة بالمحتوى.
       * لا تزد عن 15 سؤال في كل الأحوال.
       * أرجع النتيجة بصيغة JSON قائمة من الكائنات. كل كائن يحتوي على: text (نص السؤال)، و options (قائمة كائنات، كل منها يحتوي على value و label)."""
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    
    
    raw_json = response.choices[0].message.content
    try:
        
        start = raw_json.find('[')
        end = raw_json.rfind(']') + 1
        return json.loads(raw_json[start:end])
    except:
        return [] 
    
def evaluate_system_and_student(user_style, tools_used, final_output, quiz_results):
    """
    تقيم جودة التوافق بين النمط والمحتوى، وتقيم نجاح الطالب.
    """
    prompt = f"""
    You are an AI Auditor for an educational platform.
    1. System Performance: User style is '{user_style}'. System used tools: {tools_used}. 
       Does the tool {final_output} match the style? (e.g., Visual style needs Image/Diagram generation). Give score out of 10.
    2. Educational Success: Student quiz results: {quiz_results}.
       Does the success of the student confirm the accuracy of the chosen learning style?
    
    Return as JSON:
    {{
        "system_score": 0-10,
        "system_feedback": "...",
        "style_accuracy_check": "Confirmed/Refuted",
        "final_conclusion": "..."
    }}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.choices[0].message.content)