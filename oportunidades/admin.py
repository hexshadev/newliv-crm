from django.contrib import admin
from .models import Oportunidade

@admin.register(Oportunidade)
class OportunidadeAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'cliente', 'valor', 'status', 'prioridade', 'data_previsao_fechamento']
    list_filter = ['status', 'prioridade', 'data_previsao_fechamento']
    search_fields = ['titulo', 'cliente__nome', 'descricao']
    list_per_page = 20
