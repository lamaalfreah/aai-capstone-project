from django.shortcuts import render, redirect
from .models import ChatMessage, ChatSession
from .services.response_router import route_user_request

def fake_agent_response(message, file_obj, learning_style):
    style = learning_style or 'غير محدد'
    return f'استلمت رسالتك. نمطك الحالي: {style}. سأحوّل المحتوى إلى صيغة مناسبة لك.'


def chat_view(request):
    learning_style = request.session.get('learning_style', '')

    if not request.session.session_key:
        request.session.create()

    browser_session_key = request.session.session_key

    if request.GET.get('new') == '1':
        new_session = ChatSession.objects.create(
            title="محادثة جديدة",
            session_key=browser_session_key
        )
        request.session['chat_session_id'] = new_session.id
        return redirect('agent_chat:chat')

    selected_session_id = request.GET.get('session')

    if selected_session_id:
        selected_session = ChatSession.objects.filter(
            id=selected_session_id,
            session_key=browser_session_key
        ).first()

        if selected_session:
            request.session['chat_session_id'] = selected_session.id
        else:
            request.session.pop('chat_session_id', None)
            return redirect('agent_chat:chat')

    chat_session_id = request.session.get('chat_session_id')

    chat_session = None

    if chat_session_id:
        chat_session = ChatSession.objects.filter(
            id=chat_session_id,
            session_key=browser_session_key
        ).first()

    if not chat_session:
        chat_session = ChatSession.objects.create(
            title="محادثة جديدة",
            session_key=browser_session_key
        )
        request.session['chat_session_id'] = chat_session.id

    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        attachment = request.FILES.get('attachment')

        if message or attachment:
            user_content = message

        ChatMessage.objects.create(
            session=chat_session,
            role='user',
            content=user_content,
            attachment=attachment,
            learning_style=learning_style,
        )

        if chat_session.title == "محادثة جديدة":
            if message:
                chat_session.title = message[:35]
            elif attachment:
                chat_session.title = attachment.name[:35]
            chat_session.save()

        agent_result = route_user_request(
            message=message,
            attachment=attachment,
            learning_style=learning_style,
        )

        ChatMessage.objects.create(
            session=chat_session,
            role='agent',
            content=agent_result.get("content", "تم استلام طلبك.").strip(),
            learning_style=learning_style,
        )

        return redirect('agent_chat:chat')

    chat_messages = chat_session.messages.all().order_by('created_at')

    chat_sessions = ChatSession.objects.filter(
        session_key=browser_session_key
    ).order_by('-created_at')

    return render(request, 'agents/chat.html', {
        'chat_messages': chat_messages,
        'chat_sessions': chat_sessions,
        'current_session': chat_session,
        'learning_style': learning_style,
    })


## TODO: By reem > Replace with AI-generated questions later 
ASSESSMENT_QUESTIONS = [
    {
        "text": "بعد قراءة أو سماع المحتوى، ما الفكرة الأساسية التي فهمتها؟",
        "options": [
            {"value": "excellent", "label": "أستطيع شرح الفكرة الأساسية بوضوح"},
            {"value": "good", "label": "فهمت الفكرة العامة لكن أحتاج مراجعة بسيطة"},
            {"value": "needs_review", "label": "ما زالت بعض النقاط غير واضحة"},
        ],
    },
    {
        "text": "لو طُلب منك تطبيق المحتوى في مثال، كيف سيكون استعدادك؟",
        "options": [
            {"value": "excellent", "label": "أستطيع تطبيقه على مثال جديد"},
            {"value": "good", "label": "أستطيع تطبيقه إذا كان المثال قريبًا مما شرح لي"},
            {"value": "needs_review", "label": "أحتاج شرحًا إضافيًا قبل التطبيق"},
        ],
    },
    {
        "text": "ما أفضل خطوة تالية لك بعد هذا الشرح؟",
        "options": [
            {"value": "excellent", "label": "الانتقال إلى أسئلة أصعب أو تطبيق عملي"},
            {"value": "good", "label": "مراجعة ملخص قصير ثم التطبيق"},
            {"value": "needs_review", "label": "إعادة شرح المحتوى بطريقة أبسط"},
        ],
    },
]
def question_view(request, step):
    """
    Post-content understanding assessment.

    This is a placeholder flow for the team member responsible for testing whether
    the user understood the generated content. She can replace ASSESSMENT_QUESTIONS
    with AI-generated questions later.
    """
    total = len(ASSESSMENT_QUESTIONS)
    step = max(1, min(step, total))
    question = ASSESSMENT_QUESTIONS[step - 1]

    answers = request.session.get("agent_assessment_answers", {})

    if request.method == "POST":
        answer = request.POST.get("answer", "")
        if answer:
            answers[str(step)] = answer
            request.session["agent_assessment_answers"] = answers

        if step < total:
            return redirect("agent_chat:question", step=step + 1)

        return redirect("agent_chat:result")

    progress = int((step / total) * 100)

    return render(request, "agents/question.html", {
        "question": question,
        "step": step,
        "total": total,
        "progress": progress,
        "previous_answer": answers.get(str(step), ""),
    })


def result_view(request):
    answers = request.session.get("agent_assessment_answers", {})

    counts = {
        "excellent": 0,
        "good": 0,
        "needs_review": 0,
    }

    for value in answers.values():
        if value in counts:
            counts[value] += 1
    if counts["excellent"] >= 2:
        result_title = "ممتاز، يبدو أنك فهمت المحتوى جيدًا."
        result_summary = "يمكنك الآن الانتقال إلى تطبيق عملي أو أسئلة أكثر تقدمًا."
        result_status = "success"

    elif counts["good"] >= 2:
        result_title = "جيد، فهمك للمحتوى مناسب."
        result_summary = "ننصحك بمراجعة ملخص قصير ثم تجربة تطبيق بسيط."
        result_status = "success"

    else:
        result_title = "يبدو أنك تحتاج إلى شرح إضافي."
        result_summary = "يفضل إعادة تحويل المحتوى بطريقة أبسط أو اختيار نمط عرض آخر."
        result_status = "failed"

    return render(request, "agents/result.html", {
        "result_title": result_title,
        "result_summary": result_summary,
        "counts": counts,
        "result_status": result_status,
    })
