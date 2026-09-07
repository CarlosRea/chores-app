from django.urls import path

from . import views

urlpatterns = [
    path('', views.chore_list, name='chore_list'),
    path('switch-user/<int:user_id>/', views.switch_user, name='switch_user'),
]
