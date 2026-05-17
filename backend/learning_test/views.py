from django.shortcuts import render, redirect, get_object_or_404
from .models import LearningTestSession, LearningAnswer
from .question_banks import get_questions_for_age, calculate_style_from_answers


def start_view(request):
    if request.method == "POST":
        age_group = request.POST.get("age_group", "")

        session = LearningTestSession.objects.create(age_group=age_group)
        request.session["learning_session_id"] = session.id

        questions = get_questions_for_age(age_group)
        request.session["ai_questions"] = questions

        return redirect("learning_test:question", step=1)

    selected_age = request.GET.get("age", "")
    return render(request, "learning_test/start.html", {"selected_age": selected_age})


def question_view(request, step):
    session_id = request.session.get("learning_session_id")
    questions = request.session.get("ai_questions")

    if not session_id or not questions:
        return redirect("learning_test:start")

    session = get_object_or_404(LearningTestSession, id=session_id)

    total = len(questions)
    step = max(1, min(step, total))
    question = questions[step - 1]

    if request.method == "POST":
        answer = request.POST.get("answer", "").strip()

        if answer:
            LearningAnswer.objects.update_or_create(
                session=session,
                question_order=step,
                defaults={
                    "question_text": question.get("text", ""),
                    "answer": answer,
                },
            )

        if step < total:
            return redirect("learning_test:question", step=step + 1)

        answers_data = []
        for ans in session.answers.all().order_by("question_order"):
            q_data = questions[ans.question_order - 1]

            selected_label = ""
            for option in q_data.get("options", []):
                if option.get("value") == ans.answer:
                    selected_label = option.get("label", "")

            answers_data.append({
                "question": q_data.get("text", ""),
                "selected_value": ans.answer,
                "selected_label": selected_label,
            })

        result = calculate_style_from_answers(answers_data)

        session.learning_style = result.get("learning_style", "بصري")
        session.ai_summary = result.get(
            "ai_summary",
            "تم تحليل إجاباتك وتحديد نمط التعلم المناسب لك."
        )
        session.save()

        request.session["learning_style"] = session.learning_style

        return redirect("learning_test:result")

    previous = LearningAnswer.objects.filter(
        session=session,
        question_order=step
    ).first()

    progress = int((step / total) * 100)

    return render(request, "learning_test/question.html", {
        "session": session,
        "question": question,
        "step": step,
        "total": total,
        "progress": progress,
        "previous_answer": previous.answer if previous else "",
    })


def result_view(request):
    session_id = request.session.get("learning_session_id")

    if not session_id:
        return redirect("learning_test:start")

    session = get_object_or_404(LearningTestSession, id=session_id)

    return render(request, "learning_test/result.html", {
        "session": session
    })
