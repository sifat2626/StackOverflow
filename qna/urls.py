from django.urls import path
from .views import (
    QuestionListView, QuestionDetailView, TagListView, TagDetailView,
    AnswerVoteView, AcceptAnswerView, QuestionAnswerListView, AnswerDetailView,
    QuestionCommentListView, CommentDetailView
)

urlpatterns = [
    path('questions/', QuestionListView.as_view(), name='question-list'),
    path('questions/<uuid:pk>/', QuestionDetailView.as_view(), name='question-detail'),
    path('questions/<uuid:pk>/answers/', QuestionAnswerListView.as_view(), name='question-answer-list'),
    path('questions/<uuid:pk>/comments/', QuestionCommentListView.as_view(), name='question-comment-list'),
    path('answers/<uuid:pk>/', AnswerDetailView.as_view(), name='answer-detail'),
    path('answers/<uuid:pk>/vote/', AnswerVoteView.as_view(), name='answer-vote'),
    path('answers/<uuid:pk>/accept/', AcceptAnswerView.as_view(), name='answer-accept'),
    path('comments/<uuid:pk>/', CommentDetailView.as_view(), name='comment-detail'),
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('tags/<uuid:pk>/', TagDetailView.as_view(), name='tag-detail'),
]

