from django.urls import path
from . import views

urlpatterns = [
    path('', views.OportunidadeListView.as_view(), name='oportunidade_list'),
    path('<int:pk>/', views.OportunidadeDetailView.as_view(), name='oportunidade_detail'),
    path('nova/', views.OportunidadeCreateView.as_view(), name='oportunidade_create'),
    path('<int:pk>/editar/', views.OportunidadeUpdateView.as_view(), name='oportunidade_update'),
    path('<int:pk>/excluir/', views.OportunidadeDeleteView.as_view(), name='oportunidade_delete'),
] 