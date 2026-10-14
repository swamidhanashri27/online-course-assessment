from django.urls import path
from .views import exam, submit, show_exam_result


urlpatterns = [
    path("exam/<int:course_id>/", exam, name="exam"),
    path("submit/<int:course_id>/", submit, name="submit"),
    path(
        "exam-result/<int:course_id>/<int:submission_id>/",
        show_exam_result,
        name="show_exam_result",
    ),
]   