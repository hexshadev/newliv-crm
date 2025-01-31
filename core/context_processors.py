from .models import Mensagem, Conversa, Aviso
from django.db.models import Q
from clientes.models import Cliente
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

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
        # Log para debug
        logger.debug('Context processor: usuário autenticado')
        
        # Verifica se o usuário tem perfil
        if not hasattr(request.user, 'perfil'):
            logger.debug('Context processor: usuário sem perfil')
            return context
            
        # Log do tipo de usuário
        logger.debug(f'Context processor: tipo de usuário = {request.user.perfil.tipo}')
        
        # Adiciona apenas o tipo do usuário ao contexto
        context['user_tipo'] = request.user.perfil.tipo
        
    except Exception as e:
        # Log do erro
        logger.error(f'Context processor error: {str(e)}')
        
    return context 