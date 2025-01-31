from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Avg, Q, IntegerField, F, Case, When, BooleanField
from django.db.models.functions import Cast, TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
from clientes.models import Cliente, HistoricoLead, AcaoAgendada
from oportunidades.models import Oportunidade
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
from .forms import CorretorRegistrationForm
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import Aviso, Conversa, Mensagem
from usuarios.models import Perfil

# Certifique-se de que o modelo Cliente tem os campos necessários
from django.db.models import Count, Q

# Create your views here.

@login_required
def dashboard(request):
    """View simplificada do dashboard para teste"""
    return render(request, 'core/dashboard_simples.html')

@login_required
def dashboard_gestor(request):
    """Dashboard para gestores com métricas e distribuição de leads"""
    hoje = timezone.now()
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Verifica leads que devem ser devolvidos (sem contato após 6 horas)
    limite_devolucao = hoje - timedelta(hours=6)
    leads_para_devolver = Cliente.objects.filter(
        status='SEM_CONTATO',
        responsavel__isnull=False,
        data_ultimo_contato__lt=limite_devolucao
    )
    
    # Devolve os leads automaticamente
    if leads_para_devolver.exists():
        leads_para_devolver.update(
            responsavel=None,
            data_ultimo_contato=hoje,
            observacoes=F('observacoes') + '\nLead devolvido automaticamente por inatividade.'
        )
    
    # Métricas gerais
    total_leads = Cliente.objects.count()
    leads_novos_mes = Cliente.objects.filter(data_cadastro__gte=inicio_mes).count()
    leads_convertidos = Cliente.objects.filter(status='CONVERTIDO').count()
    taxa_conversao = (leads_convertidos / total_leads * 100) if total_leads > 0 else 0
    
    # Leads devolvidos
    leads_devolvidos = Cliente.objects.filter(
        Q(responsavel__isnull=True, status='SEM_CONTATO') |
        Q(status='SEM_CONTATO', data_ultimo_contato__lt=limite_devolucao)
    ).exclude(
        data_ultimo_contato__isnull=True
    ).order_by('-data_ultimo_contato')
    
    # Distribuição de leads por corretor
    leads_por_corretor = Cliente.objects.values(
        'responsavel__username',
        'responsavel__first_name',
        'responsavel__last_name'
    ).annotate(
        total_leads=Count('id'),
        leads_convertidos=Count('id', filter=Q(status='CONVERTIDO')),
        leads_em_atendimento=Count('id', filter=Q(status='EM_ATENDIMENTO'))
    ).exclude(responsavel__isnull=True)
    
    # Leads sem atendimento
    leads_sem_responsavel = Cliente.objects.filter(
        responsavel__isnull=True,
        status='NOVO'
    ).count()
    
    # Leads por origem
    leads_por_origem = Cliente.objects.values('origem').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Leads por status
    leads_por_status = Cliente.objects.values('status').annotate(
        total=Count('id')
    ).order_by('status')
    
    # Leads novos nos últimos 30 dias
    leads_ultimos_30_dias = Cliente.objects.filter(
        data_cadastro__gte=hoje - timedelta(days=30)
    ).annotate(
        data=TruncDate('data_cadastro')
    ).values('data').annotate(
        total=Count('id')
    ).order_by('data')
    
    context = {
        'total_leads': total_leads,
        'leads_novos_mes': leads_novos_mes,
        'leads_convertidos': leads_convertidos,
        'taxa_conversao': round(taxa_conversao, 2),
        'leads_por_corretor': leads_por_corretor,
        'leads_sem_responsavel': leads_sem_responsavel,
        'leads_por_origem': leads_por_origem,
        'leads_por_status': leads_por_status,
        'leads_ultimos_30_dias': leads_ultimos_30_dias,
        'leads_devolvidos': leads_devolvidos,
        'total_devolvidos': leads_devolvidos.count()
    }
    
    return render(request, 'core/dashboard_gestor.html', context)

@login_required
def dashboard_corretor(request):
    """Dashboard para corretores com seus leads e ações"""
    hoje = timezone.now()
    inicio_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Busca leads do corretor
    leads = Cliente.objects.filter(responsavel=request.user)
    
    # Métricas
    total_leads = leads.count()
    leads_novos = leads.filter(status='NOVO').count()
    leads_em_atendimento = leads.filter(status='EM_ATENDIMENTO').count()
    leads_convertidos = leads.filter(status='CONVERTIDO').count()
    taxa_conversao = (leads_convertidos / total_leads * 100) if total_leads > 0 else 0
    
    # Leads recebidos no mês atual
    leads_mes = leads.filter(data_cadastro__gte=inicio_mes).count()
    
    # Leads que precisam de atenção (sem contato há mais de 3 dias)
    leads_sem_contato = leads.filter(
        Q(status='NOVO') |
        Q(status='EM_ATENDIMENTO', data_ultimo_contato__lt=hoje - timedelta(days=3))
    ).annotate(
        dias_sem_contato=Cast(
            (hoje - F('data_ultimo_contato')) / timedelta(days=1),
            output_field=IntegerField()
        )
    ).order_by('-dias_sem_contato')
    
    # Próximas ações para hoje
    proximas_acoes = leads.filter(
        proxima_acao__date=hoje.date()
    ).order_by('proxima_acao')

    # Busca avisos para o corretor
    avisos = Aviso.objects.filter(
        Q(todos_corretores=True) | Q(corretores=request.user),
        ativo=True
    ).order_by('-data_criacao')[:5]  # Últimos 5 avisos ativos
    
    context = {
        'total_leads': total_leads,
        'leads_novos': leads_novos,
        'leads_em_atendimento': leads_em_atendimento,
        'leads_convertidos': leads_convertidos,
        'taxa_conversao': round(taxa_conversao, 2),
        'leads_mes': leads_mes,
        'leads_sem_contato': leads_sem_contato,
        'proximas_acoes': proximas_acoes,
        'avisos': avisos,
    }
    
    return render(request, 'core/dashboard_corretor.html', context)

@login_required
def distribuir_lead(request, lead_id):
    """Distribui um lead para um corretor"""
    if request.user.perfil.tipo != 'GESTOR':
        messages.error(request, 'Você não tem permissão para distribuir leads.')
        return redirect('dashboard')
    
    lead = get_object_or_404(Cliente, pk=lead_id)
    if lead.responsavel:
        messages.warning(request, 'Este lead já possui um responsável.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        corretor_id = request.POST.get('corretor')
        lead.responsavel_id = corretor_id
        lead.status = 'EM_ATENDIMENTO'
        lead.data_ultimo_contato = timezone.now()
        lead.save()
        messages.success(request, f'Lead distribuído com sucesso para {lead.responsavel.get_full_name()}')
    
    return redirect('dashboard')

@login_required
def marcar_acao_concluida(request, lead_id):
    """Marca uma ação como concluída e atualiza o lead"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    lead = get_object_or_404(Cliente, pk=lead_id, responsavel=request.user)
    
    # Atualiza o lead
    lead.data_ultimo_contato = timezone.now()
    lead.proxima_acao = None
    lead.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Ação marcada como concluída'
    })

@login_required
def importar_leads(request):
    """View para importação de leads via arquivo Excel"""
    if request.user.perfil.tipo != 'GESTOR':
        messages.error(request, 'Você não tem permissão para importar leads.')
        return redirect('dashboard')
    
    if request.method == 'POST' and request.FILES.get('arquivo_leads'):
        arquivo = request.FILES['arquivo_leads']
        if not arquivo.name.endswith('.xlsx'):
            messages.error(request, 'Por favor, envie um arquivo Excel (.xlsx)')
            return redirect('importar_leads')
        
        try:
            import pandas as pd
            df = pd.read_excel(arquivo)
            leads_importados = []
            
            for _, row in df.iterrows():
                lead = Cliente(
                    nome=row['nome'],
                    email=row.get('email', ''),
                    celular=row.get('celular', ''),
                    interesse=row.get('interesse', 'IMOVEL'),
                    origem=row.get('origem', 'IMPORTACAO'),
                    observacoes=row.get('observacoes', ''),
                    status='NOVO'
                )
                leads_importados.append(lead)
            
            Cliente.objects.bulk_create(leads_importados)
            messages.success(request, f'{len(leads_importados)} leads importados com sucesso!')
            
            # Salva os leads importados na sessão para distribuição
            request.session['leads_importados'] = [lead.id for lead in leads_importados]
            return redirect('distribuir_leads')
            
        except Exception as e:
            messages.error(request, f'Erro ao importar leads: {str(e)}')
            return redirect('importar_leads')
    
    return render(request, 'core/importar_leads.html')

@login_required
def distribuir_leads(request):
    """View para distribuição de leads importados"""
    if request.user.perfil.tipo != 'GESTOR':
        messages.error(request, 'Você não tem permissão para distribuir leads.')
        return redirect('dashboard')
    
    # Obtém todos os corretores
    corretores = get_user_model().objects.filter(perfil__tipo='CORRETOR')
    
    if request.method == 'POST':
        try:
            # Obtém os dados do formulário
            leads_data = json.loads(request.POST.get('leads', '[]'))
            corretores_ids = request.POST.getlist('corretores')
            tipo_distribuicao = request.POST.get('tipoDistribuicao')
            
            if not leads_data or not corretores_ids:
                return JsonResponse({
                    'success': False,
                    'error': 'Selecione pelo menos um lead e um corretor.'
                })
            
            # Cria os leads
            leads_criados = []
            for lead_data in leads_data:
                lead = Cliente(
                    nome=lead_data['nome'],
                    celular=lead_data['telefone'],
                    email=lead_data['email'],
                    tipo='PJ' if lead_data['possui_cnpj'].upper() == 'SIM' else 'PF',
                    observacoes=f"Profissão: {lead_data['profissao']}\n"
                               f"Plano Atual: {lead_data['plano_atual']}\n"
                               f"Idades: {lead_data['idades']}\n"
                               f"Observações: {lead_data['observacoes']}",
                    status='NOVO',
                    origem='IMPORTACAO'
                )
                leads_criados.append(lead)
            
            # Salva os leads em batch
            Cliente.objects.bulk_create(leads_criados)
            
            # Distribui os leads
            if tipo_distribuicao == 'igual':
                # Distribuição igual entre os corretores
                leads_por_corretor = len(leads_criados) // len(corretores_ids)
                resto = len(leads_criados) % len(corretores_ids)
                
                inicio = 0
                for i, corretor_id in enumerate(corretores_ids):
                    qtd = leads_por_corretor + (1 if i < resto else 0)
                    if qtd > 0:
                        Cliente.objects.filter(
                            id__in=[l.id for l in leads_criados[inicio:inicio + qtd]]
                        ).update(
                            responsavel_id=corretor_id,
                            status='EM_ATENDIMENTO',
                            data_ultimo_contato=timezone.now()
                        )
                        inicio += qtd
            else:
                # Distribuição manual
                inicio = 0
                for corretor_id in corretores_ids:
                    qtd = int(request.POST.get(f'qtd_{corretor_id}', 0))
                    if qtd > 0:
                        Cliente.objects.filter(
                            id__in=[l.id for l in leads_criados[inicio:inicio + qtd]]
                        ).update(
                            responsavel_id=corretor_id,
                            status='EM_ATENDIMENTO',
                            data_ultimo_contato=timezone.now()
                        )
                        inicio += qtd
            
            return JsonResponse({
                'success': True,
                'message': 'Leads distribuídos com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    context = {
        'corretores': corretores
    }
    return render(request, 'core/distribuir_leads.html', context)

@login_required
def meus_leads(request):
    """
    View para exibir os leads atribuídos ao corretor logado.
    Permite filtrar por status e gerenciar os leads.
    """
    # Verifica se o usuário é um corretor
    if not request.user.perfil.tipo == 'CORRETOR':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('dashboard')
    
    # Obtém o status do filtro, se houver
    status = request.GET.get('status')
    
    # Query base para os leads do corretor
    leads = Cliente.objects.filter(responsavel=request.user)
    
    # Aplica filtro por status se fornecido
    if status:
        leads = leads.filter(status=status)
    
    # Verifica leads que devem ser devolvidos (sem contato após 6 horas)
    limite_devolucao = timezone.now() - timedelta(hours=6)
    leads_para_devolver = leads.filter(
        status='SEM_CONTATO',
        data_ultimo_contato__lt=limite_devolucao
    )
    
    # Devolve os leads automaticamente
    if leads_para_devolver.exists():
        leads_para_devolver.update(
            responsavel=None,
            data_ultimo_contato=timezone.now(),
            observacoes=F('observacoes') + '\nLead devolvido automaticamente por inatividade.'
        )
    
    # Ordena por data de criação, mais recentes primeiro
    leads = leads.order_by('-data_cadastro')
    
    # Adiciona informação de status_alterado
    leads = leads.annotate(
        alteracoes_status=Count('historico', filter=Q(historico__tipo='STATUS')),
        status_alterado=Case(
            When(alteracoes_status__gte=2, then=True),
            default=False,
            output_field=BooleanField()
        )
    )
    
    # Adiciona informação de tempo restante para leads com status SEM_CONTATO
    agora = timezone.now()
    for lead in leads:
        if lead.status == 'SEM_CONTATO':
            if lead.data_ultimo_contato:
                tempo_passado = agora - lead.data_ultimo_contato
                tempo_restante = timedelta(hours=6) - tempo_passado
                if tempo_restante.total_seconds() > 0:
                    horas = int(tempo_restante.total_seconds() // 3600)
                    minutos = int((tempo_restante.total_seconds() % 3600) // 60)
                    lead.tempo_expiracao = f"{horas}h {minutos}m"
                else:
                    lead.tempo_expiracao = "Expirado"
            else:
                # Se não houver data_ultimo_contato, considera a data_cadastro
                tempo_passado = agora - lead.data_cadastro
                tempo_restante = timedelta(hours=6) - tempo_passado
                if tempo_restante.total_seconds() > 0:
                    horas = int(tempo_restante.total_seconds() // 3600)
                    minutos = int((tempo_restante.total_seconds() % 3600) // 60)
                    lead.tempo_expiracao = f"{horas}h {minutos}m"
                else:
                    lead.tempo_expiracao = "Expirado"
        else:
            lead.tempo_expiracao = None
    
    context = {
        'leads': leads,
        'status_atual': status,
    }
    
    return render(request, 'core/meus_leads.html', context)

@login_required
def agenda(request):
    """Agenda do corretor com próximas ações e compromissos"""
    if request.user.perfil.tipo != 'CORRETOR':
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('dashboard')
    
    hoje = timezone.now()
    
    # Busca ações agendadas para os próximos 30 dias
    acoes_futuras = Cliente.objects.filter(
        responsavel=request.user,
        proxima_acao__isnull=False,
        proxima_acao__gte=hoje,
        proxima_acao__lte=hoje + timedelta(days=30)
    ).order_by('proxima_acao')
    
    # Agrupa ações por data
    from itertools import groupby
    from django.template.defaultfilters import date as date_filter
    
    acoes_por_dia = []
    for data, acoes in groupby(acoes_futuras, key=lambda x: date_filter(x.proxima_acao, "d/m/Y")):
        acoes_por_dia.append({
            'data': data,
            'acoes': list(acoes)
        })
    
    context = {
        'acoes_por_dia': acoes_por_dia,
        'hoje': hoje
    }
    return render(request, 'core/agenda.html', context)

@login_required
def processar_upload_leads(request):
    """Processa o upload de leads via arquivo Excel ou CSV"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    # Verifica se o usuário é gestor
    if request.user.perfil.tipo != 'GESTOR':
        return JsonResponse({
            'error': 'Apenas gestores podem fazer upload de leads'
        }, status=403)
    
    try:
        import pandas as pd
        import numpy as np
        import io
        
        # Lê o arquivo
        arquivo = request.FILES.get('arquivo_leads')
        if not arquivo:
            return JsonResponse({'error': 'Nenhum arquivo enviado'}, status=400)
        
        # Lê todo o conteúdo do arquivo
        conteudo = arquivo.read()
        
        # Determina o tipo de arquivo pela extensão
        nome_arquivo = arquivo.name.lower()
        print(f"Processando arquivo: {nome_arquivo}")  # Debug
        
        if nome_arquivo.endswith('.xlsx'):
            try:
                df = pd.read_excel(io.BytesIO(conteudo), dtype=str, engine='openpyxl')
                print(f"Colunas encontradas no Excel: {df.columns.tolist()}")  # Debug
            except Exception as e:
                print(f"Erro ao ler Excel: {str(e)}")  # Debug
                return JsonResponse({'error': f'Erro ao ler arquivo Excel: {str(e)}'}, status=400)
        
        elif nome_arquivo.endswith('.csv'):
            # Tenta diferentes encodings e delimitadores
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
            delimiters = [',', ';', '\t']
            df = None
            last_error = None
            
            for encoding in encodings:
                if df is not None:
                    break
                    
                for delimiter in delimiters:
                    try:
                        df = pd.read_csv(
                            io.BytesIO(conteudo),
                            encoding=encoding,
                            sep=delimiter,
                            dtype=str,
                            on_bad_lines='skip'  # Pula linhas com problemas
                        )
                        # Se conseguiu ler mais de uma coluna, assume que deu certo
                        if len(df.columns) > 1:
                            print(f"Sucesso com encoding {encoding} e delimitador {delimiter}")
                            print(f"Colunas encontradas: {df.columns.tolist()}")  # Debug
                            break
                    except Exception as e:
                        last_error = str(e)
                        print(f"Erro com {encoding} e {delimiter}: {str(e)}")  # Debug
                        continue
            
            if df is None:
                error_msg = f'Não foi possível ler o arquivo CSV. Último erro: {last_error}'
                print(error_msg)  # Debug
                return JsonResponse({'error': error_msg}, status=400)
        else:
            return JsonResponse({
                'error': 'Formato de arquivo não suportado. Use Excel (.xlsx) ou CSV (.csv)'
            }, status=400)
        
        if df is None or df.empty:
            return JsonResponse({'error': 'Arquivo vazio ou sem dados válidos'}, status=400)
            
        # Remove colunas vazias e linhas completamente vazias
        df = df.replace({np.nan: '', None: ''})
        df = df.dropna(how='all')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        
        # Normaliza os nomes das colunas
        df.columns = [col.lower().strip() for col in df.columns]
        
        # Mapeia as colunas para os nomes esperados
        mapeamento_colunas = {
            'nome': ['nome', 'name', 'cliente', 'lead'],
            'telefone': ['telefone', 'tel', 'celular', 'fone', 'phone', 'whatsapp'],
            'email': ['email', 'e-mail', 'mail'],
            'cpf_cnpj': ['cpf_cnpj', 'cpf', 'cnpj', 'documento', 'doc'],
            'possui_cnpj': ['possui cnpj', 'possui_cnpj', 'tipo', 'pessoa'],
            'profissao': ['profissao', 'profissão', 'occupation', 'cargo'],
            'plano_atual': ['plano atual', 'plano_atual', 'plano'],
            'idades': ['idades', 'idade', 'age'],
            'observacoes': ['observacoes', 'observações', 'obs', 'notes']
        }
        
        # Encontra as colunas no arquivo
        colunas_encontradas = {}
        for col_destino, possiveis_nomes in mapeamento_colunas.items():
            for nome in possiveis_nomes:
                if nome in df.columns:
                    colunas_encontradas[col_destino] = nome
                    break
        
        # Processa os dados
        leads = []
        erros = []
        
        for idx, row in df.iterrows():
            try:
                nome = str(row[colunas_encontradas['nome']]).strip()
                if not nome:  # Pula registros sem nome
                    continue
                    
                # Limpa e formata o telefone
                telefone = str(row[colunas_encontradas.get('telefone', '')]).strip() if 'telefone' in colunas_encontradas else ''
                if pd.notna(telefone):
                    telefone = ''.join(filter(str.isdigit, telefone))
                
                # Processa CPF/CNPJ
                cpf_cnpj = str(row[colunas_encontradas.get('cpf_cnpj', '')]).strip() if 'cpf_cnpj' in colunas_encontradas else ''
                if pd.notna(cpf_cnpj):
                    cpf_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))
                
                # Se não tiver CPF/CNPJ, gera um valor único
                if not cpf_cnpj:
                    cpf_cnpj = f"LEAD{idx+1:06d}"
                
                lead = {
                    'nome': nome,
                    'telefone': telefone,
                    'email': str(row[colunas_encontradas.get('email', '')]).strip() if 'email' in colunas_encontradas else '',
                    'cpf_cnpj': cpf_cnpj,
                    'possui_cnpj': 'SIM' if 'possui_cnpj' in colunas_encontradas and 
                                          any(termo in str(row[colunas_encontradas['possui_cnpj']]).upper() 
                                              for termo in ['SIM', 'S', 'PJ', 'CNPJ']) else 'NÃO',
                    'profissao': str(row[colunas_encontradas.get('profissao', '')]).strip() if 'profissao' in colunas_encontradas else '',
                    'plano_atual': str(row[colunas_encontradas.get('plano_atual', '')]).strip() if 'plano_atual' in colunas_encontradas else '',
                    'idades': str(row[colunas_encontradas.get('idades', '')]).strip() if 'idades' in colunas_encontradas else '',
                    'observacoes': str(row[colunas_encontradas.get('observacoes', '')]).strip() if 'observacoes' in colunas_encontradas else ''
                }
                
                leads.append(lead)
                
            except Exception as e:
                erros.append(f"Erro na linha {idx + 2}: {str(e)}")
                continue
        
        if not leads:
            error_msg = 'Nenhum lead válido encontrado no arquivo.'
            if erros:
                error_msg += f'\nErros encontrados:\n{chr(10).join(erros)}'
            return JsonResponse({'error': error_msg}, status=400)
            
        return JsonResponse({
            'success': True,
            'leads': leads,
            'total': len(leads),
            'warnings': erros if erros else None
        })
        
    except Exception as e:
        import traceback
        error_msg = f'Erro ao processar arquivo: {str(e)}'
        print(error_msg)  # Debug
        print(traceback.format_exc())  # Debug completo
        return JsonResponse({'error': error_msg}, status=400)

@login_required
def distribuir_leads_importados(request):
    """Distribui os leads importados para os corretores"""
    if request.user.perfil.tipo != 'GESTOR':
        return JsonResponse({
            'error': 'Apenas gestores podem distribuir leads'
        }, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        print("Iniciando distribuição de leads...")  # Debug
        
        # Obtém os dados do request
        try:
            data = json.loads(request.body.decode('utf-8'))
            print(f"Dados recebidos: {data}")  # Debug
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {str(e)}")  # Debug
            return JsonResponse({
                'error': 'Dados inválidos: JSON mal formatado'
            }, status=400)
        
        # Valida os dados necessários
        leads_data = data.get('leads', [])
        corretores_ids = data.get('corretores', [])
        tipo_distribuicao = data.get('tipoDistribuicao')
        
        print(f"Leads: {len(leads_data)}, Corretores: {len(corretores_ids)}, Tipo: {tipo_distribuicao}")  # Debug
        
        # Validações
        if not leads_data:
            return JsonResponse({'error': 'Nenhum lead para distribuir'}, status=400)
        if not corretores_ids:
            return JsonResponse({'error': 'Nenhum corretor selecionado'}, status=400)
        if not tipo_distribuicao:
            return JsonResponse({'error': 'Tipo de distribuição não especificado'}, status=400)
        
        # Verifica se os corretores existem
        User = get_user_model()
        corretores_validos = User.objects.filter(
            id__in=corretores_ids,
            perfil__tipo='CORRETOR'
        ).values_list('id', flat=True)
        
        if not corretores_validos:
            return JsonResponse({'error': 'Nenhum corretor válido encontrado'}, status=400)
        
        if len(corretores_validos) != len(corretores_ids):
            return JsonResponse({'error': 'Um ou mais corretores inválidos'}, status=400)
        
        # Cria os leads
        leads_criados = []
        erros = []
        
        for lead_data in leads_data:
            try:
                # Validação dos dados do lead
                nome = lead_data.get('nome', '').strip()
                if not nome:
                    erros.append(f"Lead sem nome: {lead_data}")
                    continue
                
                # Formata o telefone
                telefone = lead_data.get('telefone', '').strip()
                if telefone:
                    telefone = ''.join(filter(str.isdigit, telefone))
                
                # Verifica se já existe um lead com o mesmo CPF/CNPJ
                cpf_cnpj = lead_data.get('cpf_cnpj', '').strip()
                if not cpf_cnpj:
                    cpf_cnpj = f"LEAD{len(leads_criados)+1:06d}"  # Gera um valor único
                
                if Cliente.objects.filter(cpf_cnpj=cpf_cnpj).exists():
                    erros.append(f"Lead {nome} já existe com o CPF/CNPJ {cpf_cnpj}")
                    continue
                
                # Processa o email
                email = lead_data.get('email', '').strip()
                if not email:
                    email = f"{cpf_cnpj}@sem-email.com"  # Gera um email único
                
                # Cria o lead
                lead = Cliente(
                    nome=nome,
                    celular=telefone if telefone else None,
                    email=email,  # Email agora sempre terá um valor
                    cpf_cnpj=cpf_cnpj,  # CPF/CNPJ sempre terá um valor
                    tipo='PJ' if lead_data.get('possui_cnpj', '').upper() == 'SIM' else 'PF',
                    status='SEM_CONTATO',
                    origem='IMPORTACAO'
                )
                
                # Monta as observações
                observacoes = []
                if not telefone:
                    observacoes.append("Lead importado sem telefone")
                if not lead_data.get('email'):
                    observacoes.append("Lead importado sem email")
                if lead_data.get('profissao'):
                    observacoes.append(f"Profissão: {lead_data['profissao']}")
                if lead_data.get('plano_atual'):
                    observacoes.append(f"Plano Atual: {lead_data['plano_atual']}")
                if lead_data.get('idades'):
                    observacoes.append(f"Idades: {lead_data['idades']}")
                if lead_data.get('observacoes'):
                    observacoes.append(f"Observações: {lead_data['observacoes']}")
                
                lead.observacoes = "\n".join(observacoes) if observacoes else None
                leads_criados.append(lead)
                
            except Exception as e:
                erros.append(f"Erro ao processar lead {lead_data.get('nome')}: {str(e)}")
                continue
        
        if not leads_criados:
            return JsonResponse({
                'error': 'Nenhum lead válido para importar',
                'detalhes': erros
            }, status=400)
        
        # Salva os leads em batch
        try:
            Cliente.objects.bulk_create(leads_criados)
            print(f"Leads salvos: {len(leads_criados)}")  # Debug
        except Exception as e:
            print(f"Erro ao salvar leads: {str(e)}")  # Debug
            return JsonResponse({
                'error': f'Erro ao salvar leads: {str(e)}',
                'detalhes': erros
            }, status=400)
        
        # Obtém os IDs dos leads criados
        leads_ids = Cliente.objects.filter(
            nome__in=[lead.nome for lead in leads_criados],
            status='SEM_CONTATO',
            responsavel__isnull=True
        ).values_list('id', flat=True)
        
        print(f"IDs dos leads criados: {leads_ids}")  # Debug
        
        # Distribui os leads
        if tipo_distribuicao == 'igual':
            leads_por_corretor = len(leads_ids) // len(corretores_validos)
            resto = len(leads_ids) % len(corretores_validos)
            
            inicio = 0
            for i, corretor_id in enumerate(corretores_validos):
                qtd = leads_por_corretor + (1 if i < resto else 0)
                if qtd > 0:
                    ids_para_corretor = list(leads_ids)[inicio:inicio + qtd]
                    Cliente.objects.filter(id__in=ids_para_corretor).update(
                        responsavel_id=corretor_id,
                        data_ultimo_contato=timezone.now()
                    )
                    inicio += qtd
                    print(f"Distribuídos {qtd} leads para corretor {corretor_id}")  # Debug
        else:
            # Distribuição manual
            inicio = 0
            for corretor_id in corretores_validos:
                qtd = int(data.get(f'qtd_{corretor_id}', 0))
                if qtd > 0:
                    ids_para_corretor = list(leads_ids)[inicio:inicio + qtd]
                    if ids_para_corretor:  # Só atualiza se houver leads para distribuir
                        Cliente.objects.filter(id__in=ids_para_corretor).update(
                            responsavel_id=corretor_id,
                            data_ultimo_contato=timezone.now()
                        )
                        inicio += qtd
                        print(f"Distribuídos {qtd} leads para corretor {corretor_id}")  # Debug
        
        return JsonResponse({
            'success': True,
            'message': 'Leads distribuídos com sucesso!',
            'total': len(leads_criados),
            'distribuidos': Cliente.objects.filter(
                id__in=leads_ids,
                responsavel__isnull=False
            ).count(),
            'erros': erros if erros else None
        })
        
    except Exception as e:
        import traceback
        print(f"Erro ao distribuir leads: {str(e)}")  # Debug
        print(traceback.format_exc())  # Debug completo
        return JsonResponse({
            'error': f'Erro ao distribuir leads: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=400)

def register(request):
    """Registra um novo corretor"""
    if request.method == 'POST':
        form = CorretorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()
            
            # Cria ou atualiza o perfil como CORRETOR
            perfil = user.perfil
            perfil.tipo = 'CORRETOR'  # Garante que novos registros sejam sempre CORRETOR
            perfil.celular = form.cleaned_data['celular']
            perfil.save()
            
            messages.success(request, 'Conta criada com sucesso! Você já pode fazer login.')
            return redirect('login')
    else:
        form = CorretorRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def corretores_ativos(request):
    """Retorna lista de corretores ativos com contagem de leads"""
    try:
        if request.user.perfil.tipo != 'GESTOR':
            return JsonResponse({'error': 'Acesso não autorizado'}, status=403)
        
        User = get_user_model()
        corretores = User.objects.filter(
            perfil__tipo='CORRETOR',
            is_active=True
        ).annotate(
            total_leads=Count('leads', distinct=True)
        ).values('id', 'first_name', 'last_name', 'total_leads')
        
        # Formata os dados para o frontend
        corretores_data = [{
            'id': c['id'],
            'nome': f"{c['first_name']} {c['last_name']}".strip() or f"Corretor {c['id']}",
            'total_leads': c['total_leads']
        } for c in corretores]
        
        print(f"Total de corretores encontrados: {len(corretores_data)}")  # Debug
        return JsonResponse(corretores_data, safe=False)
        
    except Exception as e:
        import traceback
        print(f"Erro ao buscar corretores: {str(e)}")  # Debug
        print(traceback.format_exc())  # Debug completo
        return JsonResponse(
            {'error': f'Erro ao buscar corretores: {str(e)}'}, 
            status=500
        )

@login_required
@require_http_methods(['POST'])
def atualizar_status_lead(request):
    """
    View para atualizar o status de um lead via API.
    Requer que o usuário seja o corretor responsável pelo lead.
    """
    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        novo_status = data.get('status')
        
        if not lead_id or not novo_status:
            return JsonResponse({'error': 'Dados inválidos'}, status=400)
        
        # Busca o lead e verifica permissão
        lead = Cliente.objects.get(id=lead_id, responsavel=request.user)
        
        # Atualiza o status
        lead.status = novo_status
        lead.save()
        
        # Registra a alteração no histórico
        HistoricoLead.objects.create(
            lead=lead,
            tipo='STATUS',
            descricao=f'Status alterado para {lead.get_status_display()}',
            usuario=request.user
        )
        
        return JsonResponse({'success': True})
        
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Lead não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(['POST'])
def agendar_acao(request):
    """
    View para agendar uma nova ação para um lead.
    Requer que o usuário seja o corretor responsável pelo lead.
    """
    try:
        lead_id = request.POST.get('leadId')
        data_acao = request.POST.get('dataAcao')
        observacoes = request.POST.get('obsAcao')
        
        if not lead_id or not data_acao:
            return JsonResponse({'error': 'Dados inválidos'}, status=400)
        
        # Busca o lead e verifica permissão
        lead = Cliente.objects.get(id=lead_id, responsavel=request.user)
        
        # Converte a string da data para datetime
        data_acao = datetime.strptime(data_acao, '%Y-%m-%dT%H:%M')
        
        # Cria a ação agendada
        AcaoAgendada.objects.create(
            lead=lead,
            data_acao=data_acao,
            descricao=observacoes or 'Ação agendada',
            usuario=request.user
        )
        
        # Atualiza a próxima ação do lead
        lead.proxima_acao = data_acao
        lead.save()
        
        # Registra no histórico
        HistoricoLead.objects.create(
            lead=lead,
            tipo='AGENDAMENTO',
            descricao=f'Nova ação agendada para {data_acao.strftime("%d/%m/%Y %H:%M")}',
            usuario=request.user
        )
        
        return JsonResponse({'success': True})
        
    except Cliente.DoesNotExist:
        return JsonResponse({'error': 'Lead não encontrado'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Data inválida'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.perfil.tipo == 'GESTOR')
def avisos_corretores(request):
    """View para gerenciar avisos aos corretores"""
    # Busca todos os avisos ordenados por data de criação (mais recentes primeiro)
    avisos = Aviso.objects.all().order_by('-data_criacao')
    
    # Busca corretores ativos
    corretores = User.objects.filter(
        perfil__tipo='CORRETOR',
        is_active=True
    ).order_by('first_name', 'last_name')
    
    context = {
        'avisos': avisos,
        'corretores': corretores
    }
    return render(request, 'core/avisos_corretores.html', context)

@login_required
@user_passes_test(lambda u: u.perfil.tipo == 'GESTOR')
def criar_aviso(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        titulo = request.POST.get('titulo')
        mensagem = request.POST.get('mensagem')
        todos_corretores = request.POST.get('todos_corretores') == 'on'
        urgente = request.POST.get('urgente') == 'on'
        
        aviso = Aviso.objects.create(
            titulo=titulo,
            mensagem=mensagem,
            criado_por=request.user,
            todos_corretores=todos_corretores,
            urgente=urgente,
            ativo=True
        )
        
        if not todos_corretores:
            corretores_ids = request.POST.getlist('corretores')
            aviso.corretores.set(corretores_ids)
            num_corretores = len(corretores_ids)
        else:
            num_corretores = User.objects.filter(perfil__tipo='CORRETOR', is_active=True).count()
        
        return JsonResponse({
            'success': True,
            'message': f'Aviso "{titulo}" criado com sucesso e enviado para {num_corretores} corretor(es).'
        })
    except Exception as e:
        return JsonResponse({
            'error': f'Erro ao criar aviso: {str(e)}',
            'details': str(e)
        }, status=400)

@login_required
@user_passes_test(lambda u: u.perfil.tipo == 'GESTOR')
def atualizar_aviso(request, aviso_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        aviso = Aviso.objects.get(id=aviso_id)
        
        aviso.titulo = request.POST.get('titulo')
        aviso.mensagem = request.POST.get('mensagem')
        aviso.todos_corretores = request.POST.get('todos_corretores') == 'on'
        aviso.urgente = request.POST.get('urgente') == 'on'
        aviso.save()
        
        if not aviso.todos_corretores:
            corretores_ids = request.POST.getlist('corretores')
            aviso.corretores.set(corretores_ids)
        
        return JsonResponse({'success': True})
    except Aviso.DoesNotExist:
        return JsonResponse({'error': 'Aviso não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(lambda u: u.perfil.tipo == 'GESTOR')
@require_http_methods(['POST'])
def excluir_aviso(request, aviso_id):
    """Exclui um aviso"""
    try:
        aviso = get_object_or_404(Aviso, id=aviso_id)
        titulo = aviso.titulo  # Guarda o título para a mensagem
        aviso.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Aviso "{titulo}" excluído com sucesso.'
        })
        
    except Aviso.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Aviso não encontrado.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao excluir aviso: {str(e)}'
        }, status=500)

@login_required
def get_aviso(request, aviso_id):
    try:
        aviso = Aviso.objects.get(id=aviso_id)
        data = {
            'id': aviso.id,
            'titulo': aviso.titulo,
            'mensagem': aviso.mensagem,
            'todos_corretores': aviso.todos_corretores,
            'urgente': aviso.urgente,
            'corretores': list(aviso.corretores.values_list('id', flat=True))
        }
        return JsonResponse(data)
    except Aviso.DoesNotExist:
        return JsonResponse({'error': 'Aviso não encontrado'}, status=404)

@login_required
def leads_devolvidos(request):
    """Lista os leads que foram devolvidos e precisam ser redistribuídos"""
    if request.user.perfil.tipo != 'GESTOR':
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('dashboard')
    
    # Obtém os leads devolvidos (sem responsável)
    leads = Cliente.objects.filter(
        responsavel__isnull=True,
        historico__tipo='DEVOLUCAO'
    ).distinct().order_by('-historico__data_criacao')
    
    # Obtém os corretores ativos com contagem de leads
    corretores = get_user_model().objects.filter(
        perfil__tipo='CORRETOR',
        is_active=True
    ).annotate(
        leads_ativos=Count(
            'leads',
            filter=Q(
                leads__status__in=['NOVO', 'SEM_CONTATO', 'EM_ATENDIMENTO']
            )
        )
    ).order_by('first_name', 'last_name')
    
    context = {
        'leads': leads,
        'corretores': corretores
    }
    
    return render(request, 'core/leads_devolvidos.html', context)

@login_required
def redistribuir_lead(request):
    """Redistribui um lead devolvido para um novo corretor"""
    if request.user.perfil.tipo != 'GESTOR':
        messages.error(request, 'Você não tem permissão para redistribuir leads.')
        return redirect('leads_devolvidos')
    
    if request.method != 'POST':
        return redirect('leads_devolvidos')
    
    lead_id = request.POST.get('lead_id')
    corretor_id = request.POST.get('corretor_id')
    
    if not lead_id or not corretor_id:
        messages.error(request, 'Dados inválidos para redistribuição.')
        return redirect('leads_devolvidos')
    
    try:
        lead = Cliente.objects.get(pk=lead_id, responsavel__isnull=True)
        corretor = get_user_model().objects.get(pk=corretor_id, perfil__tipo='CORRETOR')
        
        lead.responsavel = corretor
        lead.status = 'SEM_CONTATO'
        lead.data_ultimo_contato = timezone.now()
        lead.save()
        
        # Registra no histórico
        HistoricoLead.objects.create(
            lead=lead,
            tipo='REDISTRIBUICAO',
            descricao=f'Lead redistribuído para {corretor.get_full_name()}',
            usuario=request.user
        )
        
        messages.success(request, f'Lead redistribuído com sucesso para {corretor.get_full_name()}')
    except Cliente.DoesNotExist:
        messages.error(request, 'Lead não encontrado ou já possui responsável.')
    except get_user_model().DoesNotExist:
        messages.error(request, 'Corretor não encontrado.')
    except Exception as e:
        messages.error(request, f'Erro ao redistribuir lead: {str(e)}')
    
    return redirect('leads_devolvidos')

@login_required
def chat(request, conversa_id=None):
    # Busca todas as conversas do usuário
    conversas = Conversa.objects.filter(participantes=request.user).order_by('-ultima_mensagem')
    
    # Busca a conversa atual se o ID foi fornecido
    conversa_atual = None
    if conversa_id:
        try:
            conversa_atual = Conversa.objects.get(id=conversa_id, participantes=request.user)
        except Conversa.DoesNotExist:
            messages.error(request, 'Conversa não encontrada.')
            return redirect('chat')
    
    # Busca usuários para nova conversa (excluindo o usuário atual)
    usuarios = User.objects.filter(is_active=True).exclude(id=request.user.id)
    
    context = {
        'conversas': conversas,
        'conversa_atual': conversa_atual,
        'usuarios': usuarios,
    }
    
    return render(request, 'core/chat.html', context)

@login_required
def criar_conversa(request):
    """Cria uma nova conversa"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        participante_id = request.POST.get('participante_id')
        participante = User.objects.get(id=participante_id)
        
        # Verifica se já existe uma conversa entre os usuários
        conversa_existente = Conversa.objects.filter(
            participantes=request.user
        ).filter(
            participantes=participante
        ).first()
        
        if conversa_existente:
            return JsonResponse({
                'success': True,
                'conversa_id': conversa_existente.id
            })
        
        # Cria nova conversa
        conversa = Conversa.objects.create()
        conversa.participantes.add(request.user, participante)
        
        return JsonResponse({
            'success': True,
            'conversa_id': conversa.id
        })
        
    except User.DoesNotExist:
        return JsonResponse({'error': 'Usuário não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def enviar_mensagem(request):
    """Envia uma nova mensagem"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        conversa_id = request.POST.get('conversa_id')
        conteudo = request.POST.get('conteudo')
        anexo = request.FILES.get('anexo')
        
        conversa = Conversa.objects.get(
            id=conversa_id,
            participantes=request.user
        )
        
        mensagem = Mensagem.objects.create(
            conversa=conversa,
            remetente=request.user,
            conteudo=conteudo,
            anexo=anexo
        )
        
        # Atualiza a data da última mensagem
        conversa.save()  # auto_now do ultima_mensagem será atualizado
        
        return JsonResponse({
            'success': True,
            'mensagem_id': mensagem.id,
            'data_envio': mensagem.data_envio.strftime('%d/%m/%Y %H:%M')
        })
        
    except Conversa.DoesNotExist:
        return JsonResponse({'error': 'Conversa não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def carregar_mensagens(request, conversa_id):
    """Carrega as mensagens de uma conversa"""
    try:
        conversa = Conversa.objects.get(
            id=conversa_id,
            participantes=request.user
        )
        
        # Marca mensagens como lidas
        Mensagem.objects.filter(
            conversa=conversa,
            remetente__in=conversa.participantes.exclude(id=request.user.id)
        ).exclude(
            lida=True
        ).update(lida=True)
        
        # Busca mensagens não deletadas para o usuário
        mensagens = conversa.mensagens.exclude(
            deletada_por=request.user
        ).select_related('remetente')
        
        data = []
        for msg in mensagens:
            data.append({
                'id': msg.id,
                'remetente': msg.remetente.get_full_name(),
                'conteudo': msg.conteudo,
                'anexo': msg.anexo.url if msg.anexo else None,
                'data_envio': msg.data_envio.strftime('%d/%m/%Y %H:%M'),
                'lida': msg.lida,
                'e_remetente': msg.remetente_id == request.user.id
            })
        
        return JsonResponse({
            'success': True,
            'mensagens': data
        })
        
    except Conversa.DoesNotExist:
        return JsonResponse({'error': 'Conversa não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def deletar_mensagem(request, mensagem_id):
    """Deleta uma mensagem para o usuário"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        mensagem = Mensagem.objects.get(
            id=mensagem_id,
            conversa__participantes=request.user
        )
        
        mensagem.deletar_para_usuario(request.user)
        
        return JsonResponse({'success': True})
        
    except Mensagem.DoesNotExist:
        return JsonResponse({'error': 'Mensagem não encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
