import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


def _safe_json_list(raw_text):
    try:
        return json.loads(raw_text)
    except Exception:
        start = raw_text.find("[")
        end = raw_text.rfind("]") + 1

        if start != -1 and end > start:
            try:
                return json.loads(raw_text[start:end])
            except Exception:
                return []

    return []


def generate_quiz_from_content(content):
    """
    Generate MCQ questions from the latest transformed educational content.

    Each option value should be:
    - excellent
    - good
    - needs_review

    Return:
    [
        {
            "text": "...",
            "options": [
                {"value": "excellent", "label": "..."},
                {"value": "good", "label": "..."},
                {"value": "needs_review", "label": "..."}
            ]
        }
    ]
    """
    if not content or not content.strip():
        return []

    prompt = f"""
Based on the following educational content, generate 5 short multiple-choice questions
to evaluate whether the learner understood the content.

Rules:
- Use the same language as the content.
- Questions must be directly related to the content.
- Each question must have exactly 3 options.
- The option values must be exactly:
  excellent, good, needs_review
- Labels should be natural answer choices.
- Return JSON only as a list of objects.
- Do not use markdown.

Required JSON shape:
[
  {{
    "text": "question text",
    "options": [
      {{"value": "excellent", "label": "correct / strong understanding option"}},
      {{"value": "good", "label": "partially correct option"}},
      {{"value": "needs_review", "label": "incorrect / needs review option"}}
    ]
  }}
]

Content:
{content}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You generate concise educational assessment questions in valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    )

    questions = _safe_json_list(response.choices[0].message.content.strip())

    if questions:
        return questions

    return fallback_quiz_questions()


def fallback_quiz_questions():
    return [
        {
            "text": "ما مدى وضوح الفكرة الأساسية بعد قراءة المحتوى؟",
            "options": [
                {"value": "excellent", "label": "أستطيع شرح الفكرة الأساسية بوضوح."},
                {"value": "good", "label": "فهمت الفكرة العامة لكن أحتاج مراجعة بسيطة."},
                {"value": "needs_review", "label": "ما زالت الفكرة غير واضحة."},
            ],
        },
        {
            "text": "هل تستطيع تطبيق المحتوى على مثال جديد؟",
            "options": [
                {"value": "excellent", "label": "نعم، أستطيع تطبيقه بثقة."},
                {"value": "good", "label": "أستطيع تطبيقه إذا كان المثال قريبًا من الشرح."},
                {"value": "needs_review", "label": "أحتاج شرحًا إضافيًا قبل التطبيق."},
            ],
        },
        {
            "text": "ما الخطوة الأنسب لك الآن؟",
            "options": [
                {"value": "excellent", "label": "الانتقال إلى تطبيق عملي أو أسئلة أصعب."},
                {"value": "good", "label": "مراجعة ملخص قصير ثم التطبيق."},
                {"value": "needs_review", "label": "إعادة شرح المحتوى بطريقة أبسط."},
            ],
        },
    ]


def evaluate_system_and_student(user_style, tools_used, final_output, quiz_results):
    """
    Optional evaluator for system quality and learner performance.
    """
    prompt = f"""
You are an AI Auditor for an educational platform.

Evaluate:
1. System Performance:
User style: {user_style}
Tools used: {tools_used}
Final output: {final_output}

2. Educational Success:
Student quiz results: {quiz_results}

Return valid JSON:
{{
  "system_score": 0,
  "system_feedback": "...",
  "style_accuracy_check": "Confirmed/Refuted",
  "final_conclusion": "..."
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return valid JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    try:
        return json.loads(response.choices[0].message.content.strip())
    except Exception:
        return {
            "system_score": None,
            "system_feedback": "Could not parse evaluator output.",
            "style_accuracy_check": "Unknown",
            "final_conclusion": response.choices[0].message.content.strip(),
        }
