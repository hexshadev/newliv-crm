from .models import Mensagem, Conversa, Aviso
from django.db.models import Q
from clientes.models import Cliente
from django.utils import timezone

def unread_messages(request):
    """Adiciona contagem de mensagens não lidas ao contexto"""
    # Valores padrão
    context = {
        'mensagens_nao_lidas': 0,
        'avisos_nao_lidos': 0,
        'novos_leads': 0,
        'user_tipo': None
    }
    
    # Se o usuário não estiver autenticado, retorna o contexto padrão
    if not request.user.is_authenticated:
        return context
        
    try:
        # Verifica se o usuário tem perfil
        if not hasattr(request.user, 'perfil'):
            return context
            
        # Adiciona o tipo do usuário ao contexto
        context['user_tipo'] = request.user.perfil.tipo
        
        # Apenas processa o resto se o usuário for CORRETOR
        if request.user.perfil.tipo != 'CORRETOR':
            return context
            
        # Tenta contar mensagens não lidas de forma segura
        try:
            context['mensagens_nao_lidas'] = Mensagem.objects.filter(
                conversa__participantes=request.user,
                lida=False
            ).exclude(
                remetente=request.user
            ).count()
        except:
            pass
            
        # Tenta contar avisos não lidos de forma segura
        try:
            context['avisos_nao_lidos'] = Aviso.objects.filter(
                Q(todos_corretores=True) | Q(corretores=request.user),
                ativo=True,
                lido=False
            ).count()
        except:
            pass
            
        # Tenta contar novos leads de forma segura
        try:
            um_dia_atras = timezone.now() - timezone.timedelta(days=1)
            context['novos_leads'] = Cliente.objects.filter(
                responsavel=request.user,
                data_atribuicao__gte=um_dia_atras
            ).count()
        except:
            pass
            
    except Exception:
        # Se qualquer erro ocorrer, retorna o contexto padrão
        pass
        
    return context 