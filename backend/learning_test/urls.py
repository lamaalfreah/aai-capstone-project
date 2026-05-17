from django.urls import path
from . import views

app_name = 'learning_test'

urlpatterns = [
    path('', views.start_view, name='start'),
    path('q/<int:step>/', views.question_view, name='question'),
    path('result/', views.result_view, name='result'),
]
