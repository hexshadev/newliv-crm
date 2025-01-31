from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'interesse', 'status', 'origem', 'responsavel', 'data_ultimo_contato', 'proxima_acao']
    list_filter = ['status', 'origem', 'interesse', 'responsavel', 'cidade', 'uf']
    search_fields = ['nome', 'cpf_cnpj', 'email', 'celular']
    list_per_page = 20
    date_hierarchy = 'data_cadastro'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'tipo', 'cpf_cnpj', 'email', 'telefone', 'celular')
        }),
        ('Endereço', {
            'fields': ('endereco', 'numero', 'complemento', 'bairro', 'cidade', 'uf', 'cep')
        }),
        ('Informações do Lead', {
            'fields': ('status', 'origem', 'interesse', 'orcamento', 'area_desejada', 'bairros_interesse')
        }),
        ('Acompanhamento', {
            'fields': ('responsavel', 'data_ultimo_contato', 'proxima_acao', 'observacoes')
        }),
    )
