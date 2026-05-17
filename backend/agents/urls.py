from django.urls import path
from . import views

app_name = 'agent_chat'

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('assessment/q/<int:step>/', views.question_view, name='question'),
    path('assessment/result/', views.result_view, name='result'),
]
