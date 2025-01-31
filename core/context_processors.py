from .models import Mensagem, Conversa, Aviso
from django.db.models import Q
from clientes.models import Cliente
from django.utils import timezone

def unread_messages(request):
    """Adiciona contagem de mensagens não lidas ao contexto"""
    context = {
        'mensagens_nao_lidas': 0,
        'avisos_nao_lidos': 0,
        'novos_leads': 0
    }
    
    if request.user.is_authenticated:
        # Conta mensagens não lidas
        context['mensagens_nao_lidas'] = Mensagem.objects.filter(
            conversa__participantes=request.user,
            lida=False
        ).exclude(
            remetente=request.user
        ).count()
        
        # Para corretores, conta avisos não lidos e novos leads
        if request.user.perfil.tipo == 'CORRETOR':
            # Avisos não lidos
            context['avisos_nao_lidos'] = Aviso.objects.filter(
                Q(todos_corretores=True) | Q(corretores=request.user),
                ativo=True,
                lido=False
            ).count()
            
            # Novos leads (recebidos nas últimas 24 horas)
            um_dia_atras = timezone.now() - timezone.timedelta(days=1)
            context['novos_leads'] = Cliente.objects.filter(
                responsavel=request.user,
                data_atribuicao__gte=um_dia_atras
            ).count()
    
    return context 