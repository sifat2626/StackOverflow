import json
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from utils.decorators import login_required_json
from .models import UserProfile


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    def post(self, request):
        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

        username = body.get('username')
        password = body.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Username and password are required.'}, status=400)

        user = authenticate(request, username=username, password=password)
        if user is None:
            return JsonResponse({'error': 'Invalid username or password.'}, status=401)

        login(request, user)
        profile, _ = UserProfile.objects.get_or_create(user=user)

        return JsonResponse({
            'message': 'Logged in successfully!',
            'user': {
                'id': user.id,
                'username': user.username,
                'reputation': profile.reputation
            }
        }, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    @method_decorator(login_required_json)
    def post(self, request):
        logout(request)
        return JsonResponse({'message': 'Logged out successfully!'}, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class WhoAmIView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'is_authenticated': False}, status=200)

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return JsonResponse({
            'is_authenticated': True,
            'user': {
                'id': request.user.id,
                'username': request.user.username,
                'reputation': profile.reputation,
                'is_staff': request.user.is_staff
            }
        }, status=200)

