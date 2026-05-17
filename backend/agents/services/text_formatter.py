from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import re

client = OpenAI()


def clean_extracted_text(text):
    if not text:
        return ""

    text = text.replace("<!-- image -->", "")
    text = text.replace("\u200f", "").replace("\u200e", "")
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    cleaned = []
    previous = None

    for line in lines:
        # حذف التكرار المتتالي فقط
        if line != previous:
            cleaned.append(line)
        previous = line

    return "\n".join(cleaned)


def format_extracted_text(raw_text):
    if not raw_text or not raw_text.strip():
        return ""

    cleaned_text = clean_extracted_text(raw_text)

    prompt = f"""
أنت محرر ذكي للنصوص المستخرجة من ملفات PDF / Word / صور.

النص التالي مستخرج آليًا وقد يحتوي على مشاكل مثل:
- ترتيب جمل غير منطقي.
- تداخل عربي وإنجليزي.
- أسطر كود مكسّرة.
- عناوين في غير مكانها.
- رموز زائدة.
- كلمات أو أسطر مكررة.
- اتجاه نص خاطئ بسبب العربية والإنجليزية.

مهمتك:
أعد بناء النص ليصبح مفهومًا ومنظمًا للقارئ.

القواعد المهمة:
1. لا تضف معلومات جديدة غير موجودة في النص.
2. لا تحذف المعلومات المهمة.
3. أصلح ترتيب الجمل بحيث تصبح مفهومة.
4. إذا وجدت شرحًا عربيًا، اكتبه عربيًا فصيحًا وواضحًا.
5. إذا وجدت نصًا إنجليزيًا، أبقه إنجليزيًا كما هو لكن نظمه.
6. إذا وجدت كودًا، ضعه في قسم مستقل بعنوان: الكود
7. لا تجعل أرقام الأسطر مثل 1 2 3 داخل نفس السطر، واحذفها إذا كانت مجرد أرقام ترقيم.
8. لا تستخدم Markdown ثقيل مثل ## أو **.
9. لا تستخدم HTML.
10. استخدم عناوين واضحة فقط.
11. افصل بين الفقرات بسطر فارغ.
12. إذا كان النص خليط شرح + كود، اجعل الشرح أولًا ثم الكود.
13. رتب النص إلى أقسام مناسبة 


صيغة الإخراج المطلوبة:
- نص نظيف ومنظم.
- عناوين واضحة.
- فقرات قصيرة.
- كود مرتب عند الحاجة.
- بدون مقدمة مثل "بالطبع" أو "إليك النص".

النص المستخرج:
{cleaned_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert OCR/document reconstruction assistant. "
                    "Your job is to repair badly extracted Arabic/English mixed text, "
                    "reorder broken sentences, separate code blocks, and return clean readable plain text only."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.0
    )

    return response.choices[0].message.content.strip()