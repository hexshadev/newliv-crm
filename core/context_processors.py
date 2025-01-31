from .models import Mensagem, Conversa, Aviso
from django.db.models import Q
from clientes.models import Cliente
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def unread_messages(request):
    """Context processor simplificado"""
    return {} 