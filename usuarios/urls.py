from django.urls import path
from . import views

urlpatterns = [
    path('atualizar-perfil/', views.atualizar_perfil, name='atualizar_perfil'),
] 
