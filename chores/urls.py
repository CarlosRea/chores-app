from django.urls import path

from . import views

urlpatterns = [
    path('', views.chore_list, name='chore_list'),
    path('chores/new/', views.chore_create, name='chore_create'),
    path('chores/<int:pk>/toggle/', views.chore_toggle, name='chore_toggle'),
    path('chores/<int:pk>/delete/', views.chore_delete, name='chore_delete'),
    path('switch-user/<int:user_id>/', views.switch_user, name='switch_user'),
]
