from django.contrib import admin
from .models import Question, Answer, Vote, Comment, Tags


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ('answer', 'created_by', 'upvote_count', 'downvote_count', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'is_closed', 'accepted_answer', 'created_at')
    list_filter = ('is_closed', 'created_at', 'tags')
    search_fields = ('title', 'description', 'created_by__user__username')
    inlines = [AnswerInline]
    actions = ['mark_as_closed', 'mark_as_open']

    @admin.action(description='Mark selected questions as closed')
    def mark_as_closed(self, request, queryset):
        updated_count = queryset.update(is_closed=True)
        self.message_user(request, f"{updated_count} question(s) were successfully marked as closed.")

    @admin.action(description='Mark selected questions as open')
    def mark_as_open(self, request, queryset):
        updated_count = queryset.update(is_closed=False)
        self.message_user(request, f"{updated_count} question(s) were successfully marked as open.")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('answer_snippet', 'question', 'created_by', 'upvote_count', 'downvote_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('answer', 'created_by__user__username', 'question__title')

    def answer_snippet(self, obj):
        return obj.answer[:50] + ('...' if len(obj.answer) > 50 else '')
    answer_snippet.short_description = 'Answer'


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('answer', 'created_by', 'vote', 'created_at')
    list_filter = ('vote', 'created_at')
    search_fields = ('created_by__user__username', 'answer__answer')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment_snippet', 'question', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment', 'created_by__user__username', 'question__title')

    def comment_snippet(self, obj):
        return obj.comment[:50] + ('...' if len(obj.comment) > 50 else '')
    comment_snippet.short_description = 'Comment'


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)

