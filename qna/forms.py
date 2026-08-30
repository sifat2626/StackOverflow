from django import forms
from .models import Question, Answer, Comment, Tags


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(required=False)

    class Meta:
        model = Question
        fields = ['title', 'description']

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('Title cannot be empty.')
        if len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters long.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if not description:
            raise forms.ValidationError('Description cannot be empty.')
        return description


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['answer']

    def clean_answer(self):
        answer = self.cleaned_data.get('answer', '').strip()
        if not answer:
            raise forms.ValidationError('Answer cannot be empty.')
        return answer


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if not comment:
            raise forms.ValidationError('Comment cannot be empty.')
        return comment


class TagForm(forms.ModelForm):
    class Meta:
        model = Tags
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip().lower()
        if not name:
            raise forms.ValidationError('Tag name is required.')
        return name
