from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from clientes.models import Cliente, HistoricoLead
from .models import GoogleCalendarConfig
import json
from datetime import datetime

@login_required
@require_http_methods(["GET"])
def get_lembrete(request, lembrete_id):
    """Retorna os dados de um lembrete específico"""
    lead = get_object_or_404(Cliente, pk=lembrete_id, responsavel=request.user)
    
    if not lead.proxima_acao:
        return JsonResponse({'error': 'Lembrete não encontrado'}, status=404)
    
    return JsonResponse({
        'id': lead.pk,
        'lead_id': lead.pk,
        'data': lead.proxima_acao.strftime('%Y-%m-%d'),
        'hora': lead.proxima_acao.strftime('%H:%M'),
        'tipo': lead.tipo_proxima_acao if hasattr(lead, 'tipo_proxima_acao') else 'LIGACAO',
        'observacoes': lead.observacoes_proxima_acao if hasattr(lead, 'observacoes_proxima_acao') else '',
        'lembrete': '30',  # Valor padrão
        'sync_google': hasattr(request.user, 'google_calendar_config')
    })

@login_required
@require_http_methods(["POST"])
def criar_lembrete(request):
    """Cria um novo lembrete para um lead"""
    try:
        lead_id = request.POST.get('leadId')
        data = request.POST.get('data')
        hora = request.POST.get('hora')
        tipo = request.POST.get('tipo', 'LIGACAO')
        observacoes = request.POST.get('observacoes', '')
        sync_google = request.POST.get('syncGoogle') == 'on'
        
        lead = get_object_or_404(Cliente, pk=lead_id, responsavel=request.user)
        
        # Combina data e hora
        proxima_acao = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M")
        proxima_acao = timezone.make_aware(proxima_acao)
        
        # Atualiza o lead
        lead.proxima_acao = proxima_acao
        if hasattr(lead, 'tipo_proxima_acao'):
            lead.tipo_proxima_acao = tipo
        if hasattr(lead, 'observacoes_proxima_acao'):
            lead.observacoes_proxima_acao = observacoes
        lead.save()
        
        # Sincroniza com Google Calendar se solicitado
        if sync_google and hasattr(request.user, 'google_calendar_config'):
            sincronizar_com_google_calendar(lead, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Lembrete criado com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["POST"])
def atualizar_lembrete(request, lembrete_id):
    """Atualiza um lembrete existente"""
    try:
        lead = get_object_or_404(Cliente, pk=lembrete_id, responsavel=request.user)
        
        data = request.POST.get('data')
        hora = request.POST.get('hora')
        tipo = request.POST.get('tipo', 'LIGACAO')
        observacoes = request.POST.get('observacoes', '')
        sync_google = request.POST.get('syncGoogle') == 'on'
        
        # Combina data e hora
        proxima_acao = datetime.strptime(f"{data} {hora}", "%Y-%m-%d %H:%M")
        proxima_acao = timezone.make_aware(proxima_acao)
        
        # Atualiza o lead
        lead.proxima_acao = proxima_acao
        if hasattr(lead, 'tipo_proxima_acao'):
            lead.tipo_proxima_acao = tipo
        if hasattr(lead, 'observacoes_proxima_acao'):
            lead.observacoes_proxima_acao = observacoes
        lead.save()
        
        # Sincroniza com Google Calendar se solicitado
        if sync_google and hasattr(request.user, 'google_calendar_config'):
            sincronizar_com_google_calendar(lead, request.user)
        
        return JsonResponse({
            'success': True,
            'message': 'Lembrete atualizado com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def conectar_google(request):
    """Inicia o fluxo de autenticação com o Google Calendar"""
    from google_auth_oauthlib.flow import Flow
    
    # Configurações do OAuth2
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri=request.build_absolute_uri('/oauth2callback/')
    )
    
    # Gera URL de autorização
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    # Salva o state na sessão
    request.session['google_auth_state'] = state
    
    return JsonResponse({
        'success': True,
        'authorization_url': authorization_url
    })

@login_required
@require_http_methods(["POST"])
def desconectar_google(request):
    """Remove a conexão com o Google Calendar"""
    try:
        if hasattr(request.user, 'google_calendar_config'):
            request.user.google_calendar_config.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Conta Google desconectada com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@require_http_methods(["POST"])
def atualizar_config_sync(request):
    """Atualiza as configurações de sincronização com o Google Calendar"""
    try:
        data = json.loads(request.body)
        
        config, created = GoogleCalendarConfig.objects.get_or_create(
            user=request.user,
            defaults={
                'novas_acoes': data.get('novas_acoes', False),
                'lembretes': data.get('lembretes', False),
                'bidirecional': data.get('bidirecional', False)
            }
        )
        
        if not created:
            config.novas_acoes = data.get('novas_acoes', False)
            config.lembretes = data.get('lembretes', False)
            config.bidirecional = data.get('bidirecional', False)
            config.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Configurações atualizadas com sucesso'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def sincronizar_com_google_calendar(lead, user):
    """Função auxiliar para sincronizar um lembrete com o Google Calendar"""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    config = user.google_calendar_config
    credentials = Credentials(
        token=config.access_token,
        refresh_token=config.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=config.client_id,
        client_secret=config.client_secret,
        scopes=['https://www.googleapis.com/auth/calendar']
    )
    
    service = build('calendar', 'v3', credentials=credentials)
    
    # Cria ou atualiza o evento
    event = {
        'summary': f'Contato com {lead.nome}',
        'description': lead.observacoes_proxima_acao if hasattr(lead, 'observacoes_proxima_acao') else '',
        'start': {
            'dateTime': lead.proxima_acao.isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
        'end': {
            'dateTime': (lead.proxima_acao + timezone.timedelta(hours=1)).isoformat(),
            'timeZone': 'America/Sao_Paulo',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 30},
            ],
        },
    }
    
    # Verifica se já existe um evento para este lembrete
    if hasattr(lead, 'google_calendar_event_id'):
        service.events().update(
            calendarId='primary',
            eventId=lead.google_calendar_event_id,
            body=event
        ).execute()
    else:
        event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        if hasattr(lead, 'google_calendar_event_id'):
            lead.google_calendar_event_id = event['id']
            lead.save()

@login_required
@require_http_methods(["GET"])
def meus_leads(request):
    """API para listar leads do corretor com filtro por status"""
    if request.user.perfil.tipo != 'CORRETOR':
        return JsonResponse({'error': 'Acesso não autorizado'}, status=403)
    
    status = request.GET.get('status')
    leads = Cliente.objects.filter(responsavel=request.user)
    
    if status:
        leads = leads.filter(status=status)
    
    leads = leads.order_by('-data_cadastro')
    
    leads_data = [{
        'id': lead.id,
        'nome': lead.nome,
        'email': lead.email,
        'celular': lead.celular,
        'status': lead.status,
        'data_cadastro': lead.data_cadastro.isoformat() if lead.data_cadastro else None,
        'data_ultimo_contato': lead.data_ultimo_contato.isoformat() if lead.data_ultimo_contato else None,
        'proxima_acao': lead.proxima_acao.isoformat() if lead.proxima_acao else None,
        'observacoes': lead.observacoes
    } for lead in leads]
    
    return JsonResponse({'leads': leads_data})

@login_required
@require_http_methods(["POST"])
def atualizar_status_lead(request):
    """API para atualizar o status de um lead"""
    if request.user.perfil.tipo != 'CORRETOR':
        return JsonResponse({'error': 'Acesso não autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        novo_status = data.get('status')
        
        if not lead_id or not novo_status:
            return JsonResponse({'error': 'Dados inválidos'}, status=400)
        
        lead = Cliente.objects.filter(
            id=lead_id,
            responsavel=request.user
        ).first()
        
        if not lead:
            return JsonResponse({'error': 'Lead não encontrado'}, status=404)
        
        # Verifica se o lead já teve seu status alterado
        if HistoricoLead.objects.filter(
            lead=lead,
            tipo='STATUS'
        ).exists():
            return JsonResponse({'error': 'Este lead já teve seu status alterado anteriormente'}, status=400)
        
        # Cria um registro no histórico
        HistoricoLead.objects.create(
            lead=lead,
            tipo='STATUS',
            descricao=f'Status alterado de {lead.get_status_display()} para {dict(Cliente.STATUS_CHOICES)[novo_status]}',
            usuario=request.user
        )
        
        lead.status = novo_status
        lead.data_ultimo_contato = timezone.now()
        lead.save()
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def agendar_acao(request):
    """API para agendar uma ação para um lead"""
    if request.user.perfil.tipo != 'CORRETOR':
        return JsonResponse({'error': 'Acesso não autorizado'}, status=403)
    
    try:
        lead_id = request.POST.get('leadId')
        data_acao = request.POST.get('dataAcao')
        observacoes = request.POST.get('obsAcao')
        
        if not lead_id or not data_acao:
            return JsonResponse({'error': 'Dados inválidos'}, status=400)
        
        lead = Cliente.objects.filter(
            id=lead_id,
            responsavel=request.user
        ).first()
        
        if not lead:
            return JsonResponse({'error': 'Lead não encontrado'}, status=404)
        
        lead.proxima_acao = data_acao
        lead.observacoes_proxima_acao = observacoes
        lead.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500) 