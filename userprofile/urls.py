from django.urls import path
from .views import LoginView, LogoutView, WhoAmIView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('whoami/', WhoAmIView.as_view(), name='whoami'),
]
