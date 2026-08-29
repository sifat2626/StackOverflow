from functools import wraps
from django.http import JsonResponse


def login_required_json(view_func):
    """
    Decorator for views that checks that the user is logged in,
    returning a 401 JsonResponse if unauthenticated.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required.'}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
