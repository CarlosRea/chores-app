from django.urls import path

from . import views

urlpatterns = [
    path('switch-user/<int:user_id>/', views.switch_user, name='switch_user'),
]
