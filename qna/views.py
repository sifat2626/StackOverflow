from userprofile.models import UserProfile
from django.http import JsonResponse
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
from django.views import View
from .models import Question, Tags
from utils.decorators import login_required_json, admin_required_json


def serialize_question_summary(question):
    return {
        'id': str(question.id),
        'title': question.title,
        'created_by': question.created_by.user.username,
        'tags': [tag.name for tag in question.tags.all()],
        'answers_count': getattr(question, 'answers_count', question.answers.count()),
        'created_at': question.created_at.isoformat(),
    }


@method_decorator(csrf_exempt, name='dispatch')
class QuestionListView(View):
    def get(self, request):
        questions = Question.objects.select_related('created_by__user') \
                                   .prefetch_related('tags') \
                                   .annotate(answers_count=Count('answers')) \
                                   .order_by('-created_at')
        data = [serialize_question_summary(q) for q in questions]
        return JsonResponse({'questions': data}, status=200)

    @method_decorator(login_required_json)
    def post(self, request):
        try:
            body = json.loads(request.body)
            title = body.get('title')
            description = body.get('description')
            tags = body.get('tags', [])
            
            if not title or not description:
                return JsonResponse({'error': 'Title and description are required.'}, status=400)

            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

            question = Question.objects.create(
                title=title,
                description=description,
                created_by=user_profile,
            )

            if isinstance(tags, list):
                is_admin = request.user.is_staff or request.user.is_superuser
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        tag_name = tag.strip().lower()
                        if is_admin:
                            tag_obj, _ = Tags.objects.get_or_create(name=tag_name)
                        else:
                            tag_obj = Tags.objects.filter(name=tag_name).first()
                        if tag_obj:
                            question.tags.add(tag_obj)

            return JsonResponse({
                'message': 'Question created successfully!',
                'question': serialize_question_summary(question)
            }, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class QuestionDetailView(View):
    def get_object(self, pk):
        try:
            return Question.objects.select_related('created_by__user').prefetch_related('tags', 'answers__created_by__user').get(pk=pk)
        except Question.DoesNotExist:
            return None

    def get(self, request, pk):
        question = self.get_object(pk)
        if not question:
            return JsonResponse({'error': 'Question not found.'}, status=404)

        data = {
            'id': str(question.id),
            'title': question.title,
            'description': question.description,
            'created_by': question.created_by.user.username,
            'tags': [tag.name for tag in question.tags.all()],
            'created_at': question.created_at.isoformat(),
            'answers': [
                {
                    'id': str(answer.id),
                    'description': answer.answer,
                    'created_by': answer.created_by.user.username,
                    'created_at': answer.created_at.isoformat()
                }
                for answer in question.answers.all()
            ]
        }
        return JsonResponse({'question': data}, status=200)

    @method_decorator(login_required_json)
    def put(self, request, pk):
        return self._update_question(request, pk, partial=False)

    @method_decorator(login_required_json)
    def patch(self, request, pk):
        return self._update_question(request, pk, partial=True)

    def _update_question(self, request, pk, partial=False):
        question = self.get_object(pk)
        if not question:
            return JsonResponse({'error': 'Question not found.'}, status=404)

        if question.created_by.user != request.user:
            return JsonResponse({'error': 'Permission denied.'}, status=403)

        try:
            body = json.loads(request.body)
            title = body.get('title')
            description = body.get('description')
            tag_names = body.get('tags')

            if not partial:
                if not title or not description:
                    return JsonResponse({'error': 'Title and description are required.'}, status=400)
                question.title = title
                question.description = description
            else:
                if title is not None:
                    question.title = title
                if description is not None:
                    question.description = description

            question.save()

            if tag_names is not None and isinstance(tag_names, list):
                question.tags.clear()
                is_admin = request.user.is_staff or request.user.is_superuser
                for name in tag_names:
                    if isinstance(name, str) and name.strip():
                        tag_name = name.strip().lower()
                        if is_admin:
                            tag_obj, _ = Tags.objects.get_or_create(name=tag_name)
                        else:
                            tag_obj = Tags.objects.filter(name=tag_name).first()
                        if tag_obj:
                            question.tags.add(tag_obj)

            return JsonResponse({
                'message': 'Question updated successfully!',
                'question': serialize_question_summary(question)
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

    @method_decorator(login_required_json)
    def delete(self, request, pk):
        question = self.get_object(pk)
        if not question:
            return JsonResponse({'error': 'Question not found.'}, status=404)

        if question.created_by.user != request.user:
            return JsonResponse({'error': 'Permission denied.'}, status=403)

        question.delete()
        return JsonResponse({'message': 'Question deleted successfully!'}, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class TagListView(View):
    def get(self, request):
        tags = Tags.objects.all()
        data = [{'id': str(tag.id), 'name': tag.name} for tag in tags]
        return JsonResponse({'tags': data}, status=200)
    
    @method_decorator(admin_required_json)
    def post(self, request):
        try:
            body = json.loads(request.body)
            name = body.get('name')
            if not name or not isinstance(name, str) or not name.strip():
                return JsonResponse({'error': 'Name is required.'}, status=400)
            tag_name = name.strip().lower()
            if Tags.objects.filter(name=tag_name).exists():
                return JsonResponse({'error': 'Tag with this name already exists.'}, status=400)
            tag = Tags.objects.create(name=tag_name)
            return JsonResponse({'message': 'Tag created successfully!', 'tag': {'id': str(tag.id), 'name': tag.name}}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class TagDetailView(View):
    def get(self, request, pk):
        try:
            tag = Tags.objects.get(pk=pk)
            return JsonResponse({'tag': {'id': str(tag.id), 'name': tag.name}}, status=200)
        except Tags.DoesNotExist:
            return JsonResponse({'error': 'Tag not found.'}, status=404)

    @method_decorator(admin_required_json)
    def delete(self, request, pk):
        try:
            tag = Tags.objects.get(pk=pk)
            tag.delete()
            return JsonResponse({'message': 'Tag deleted successfully!'}, status=200)
        except Tags.DoesNotExist:
            return JsonResponse({'error': 'Tag not found.'}, status=404)

    @method_decorator(admin_required_json)
    def put(self, request, pk):
        return self._update_tag(request, pk, partial=False)

    @method_decorator(admin_required_json)
    def patch(self, request, pk):
        return self._update_tag(request, pk, partial=True)

    def _update_tag(self, request, pk, partial=False):
        try:
            tag = Tags.objects.get(pk=pk)
            body = json.loads(request.body)
            name = body.get('name')

            if not partial:
                if not name or not isinstance(name, str) or not name.strip():
                    return JsonResponse({'error': 'Name is required.'}, status=400)
            else:
                if name is None:
                    return JsonResponse({'message': 'No changes provided.', 'tag': {'id': str(tag.id), 'name': tag.name}}, status=200)
                if not isinstance(name, str) or not name.strip():
                    return JsonResponse({'error': 'Invalid name provided.'}, status=400)

            tag_name = name.strip().lower()
            if Tags.objects.filter(name=tag_name).exclude(pk=pk).exists():
                return JsonResponse({'error': 'Tag with this name already exists.'}, status=400)

            tag.name = tag_name
            tag.save()
            return JsonResponse({'message': 'Tag updated successfully!', 'tag': {'id': str(tag.id), 'name': tag.name}}, status=200)

        except Tags.DoesNotExist:
            return JsonResponse({'error': 'Tag not found.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


        
            