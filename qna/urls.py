from django.urls import path
from .views import (
    QuestionListView, QuestionDetailView, TagListView, TagDetailView,
    AnswerVoteView, AcceptAnswerView
)

urlpatterns = [
    path('questions/', QuestionListView.as_view(), name='question-list'),
    path('questions/<uuid:pk>/', QuestionDetailView.as_view(), name='question-detail'),
    path('answers/<uuid:pk>/vote/', AnswerVoteView.as_view(), name='answer-vote'),
    path('answers/<uuid:pk>/accept/', AcceptAnswerView.as_view(), name='answer-accept'),
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('tags/<uuid:pk>/', TagDetailView.as_view(), name='tag-detail'),
]

