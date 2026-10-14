
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseNotAllowed

from .models import Course, Enrollment, Submission, Choice


def exam(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    questions = course.question_set.prefetch_related(
        "choice_set"
    ).all()

    return render(
        request,
        "exam.html",
        {
            "course": course,
            "questions": questions,
        }
    )


def submit(request, course_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if not request.user.is_authenticated:
        return redirect(
            f"/admin/login/?next=/exam/{course_id}/"
        )

    course = get_object_or_404(Course, id=course_id)

    enrollment, _ = Enrollment.objects.get_or_create(
        user=request.user,
        course=course,
        defaults={"mode": Enrollment.AUDIT},
    )

    selected_ids = []

    for key in request.POST:
        if key.startswith("choice_"):
            selected_ids.extend(request.POST.getlist(key))

    choices = Choice.objects.filter(
        id__in=selected_ids,
        question__course=course,
    )

    submission = Submission.objects.create(
        enrollment=enrollment
    )
    submission.choices.set(choices)

    return redirect(
        "show_exam_result",
        course_id=course.id,
        submission_id=submission.id,
    )


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, id=course_id)

    submission = get_object_or_404(
        Submission,
        id=submission_id,
        enrollment__course=course,
    )

    selected_ids = set(
        submission.choices.values_list("id", flat=True)
    )

    question_results = []
    correct_answers = 0

    questions = course.question_set.prefetch_related(
        "choice_set"
    ).all()

    for question in questions:
        question_choices = list(question.choice_set.all())

        correct_ids = {
            choice.id
            for choice in question_choices
            if choice.is_correct
        }

        selected_for_question = [
            choice for choice in question_choices
            if choice.id in selected_ids
        ]

        is_correct = (
            bool(correct_ids)
            and {
                choice.id for choice in selected_for_question
            } == correct_ids
        )

        if is_correct:
            correct_answers += 1

        question_results.append({
            "question": question,
            "selected_choices": selected_for_question,
            "correct_choices": [
                choice for choice in question_choices
                if choice.is_correct
            ],
            "is_correct": is_correct,
        })

    total_questions = len(question_results)

    score = (
        round(correct_answers * 100 / total_questions)
        if total_questions else 0
    )

    return render(
        request,
        "exam_result.html",
        {
            "course": course,
            "submission": submission,
            "score": score,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "question_results": question_results,
        }
    )
