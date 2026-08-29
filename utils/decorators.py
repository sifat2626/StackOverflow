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


def admin_required_json(view_func):
    """
    Decorator for views that checks that the user is logged in and is an admin/staff member,
    returning 401 if unauthenticated or 403 if unauthorized.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required.'}, status=401)
        if not (request.user.is_staff or request.user.is_superuser):
            return JsonResponse({'error': 'Permission denied. Admin access required.'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

