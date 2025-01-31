from django.urls import path
from . import views
from . import api

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('gestor/', views.dashboard_gestor, name='dashboard_gestor'),
    path('register/', views.register, name='register'),
    path('distribuir-lead/<int:lead_id>/', views.distribuir_lead, name='distribuir_lead'),
    path('marcar-acao-concluida/<int:lead_id>/', views.marcar_acao_concluida, name='marcar_acao_concluida'),
    path('importar-leads/', views.importar_leads, name='importar_leads'),
    path('distribuir-leads/', views.distribuir_leads, name='distribuir_leads'),
    path('meus-leads/', views.meus_leads, name='meus_leads'),
    path('agenda/', views.agenda, name='agenda'),
    
    # APIs de Lembretes
    path('api/get-lembrete/<int:lembrete_id>/', api.get_lembrete, name='get_lembrete'),
    path('api/criar-lembrete/', api.criar_lembrete, name='criar_lembrete'),
    path('api/atualizar-lembrete/<int:lembrete_id>/', api.atualizar_lembrete, name='atualizar_lembrete'),
    
    # APIs do Google Calendar
    path('api/conectar-google/', api.conectar_google, name='conectar_google'),
    path('api/desconectar-google/', api.desconectar_google, name='desconectar_google'),
    path('api/atualizar-config-sync/', api.atualizar_config_sync, name='atualizar_config_sync'),
    
    # APIs de Upload e Distribuição de Leads
    path('api/processar-upload-leads/', views.processar_upload_leads, name='processar_upload_leads'),
    path('api/distribuir-leads-importados/', views.distribuir_leads_importados, name='distribuir_leads_importados'),
    path('api/corretores-ativos/', views.corretores_ativos, name='corretores_ativos'),
    
    # APIs do Dashboard do Corretor
    path('api/atualizar-status-lead/', views.atualizar_status_lead, name='atualizar_status_lead'),
    path('api/agendar-acao/', views.agendar_acao, name='agendar_acao'),

    # URLs para Avisos
    path('avisos-corretores/', views.avisos_corretores, name='avisos_corretores'),
    path('aviso/criar/', views.criar_aviso, name='criar_aviso'),
    path('aviso/<int:aviso_id>/', views.get_aviso, name='get_aviso'),
    path('aviso/<int:aviso_id>/atualizar/', views.atualizar_aviso, name='atualizar_aviso'),
    path('aviso/<int:aviso_id>/excluir/', views.excluir_aviso, name='excluir_aviso'),

    # URLs para Leads Devolvidos
    path('leads-devolvidos/', views.leads_devolvidos, name='leads_devolvidos'),
    path('redistribuir-lead/', views.redistribuir_lead, name='redistribuir_lead'),

    # Chat
    path('chat/', views.chat, name='chat'),
    path('chat/<int:conversa_id>/', views.chat, name='visualizar_conversa'),
    path('chat/criar/', views.criar_conversa, name='criar_conversa'),
    path('chat/enviar/', views.enviar_mensagem, name='enviar_mensagem'),
    path('chat/mensagens/<int:conversa_id>/', views.carregar_mensagens, name='carregar_mensagens'),
    path('chat/deletar/<int:mensagem_id>/', views.deletar_mensagem, name='deletar_mensagem'),
] 