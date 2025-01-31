from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class CorretorPunicao(models.Model):
    corretor = models.OneToOneField(User, on_delete=models.CASCADE, related_name='punicao')
    em_punicao = models.BooleanField(default=False)
    inicio_punicao = models.DateTimeField(null=True, blank=True)
    fim_punicao = models.DateTimeField(null=True, blank=True)
    contagem_devolucoes = models.IntegerField(default=0)
    
    def aplicar_punicao(self):
        if self.contagem_devolucoes >= 3 and not self.em_punicao:
            self.em_punicao = True
            self.inicio_punicao = timezone.now()
            self.fim_punicao = self.inicio_punicao + timedelta(hours=12)
            self.save()
            
            # Criar aviso para o corretor
            from core.models import Aviso
            Aviso.objects.create(
                titulo='Punição por Devoluções Excessivas',
                mensagem='Você atingiu o limite de 3 devoluções de leads. Você está impossibilitado de receber novos leads por 12 horas.',
                criado_por=User.objects.filter(perfil__tipo='GESTOR').first(),
                todos_corretores=False,
                urgente=True
            ).corretores.add(self.corretor)
    
    def verificar_punicao(self):
        if self.em_punicao and timezone.now() >= self.fim_punicao:
            self.em_punicao = False
            self.contagem_devolucoes = 0
            self.inicio_punicao = None
            self.fim_punicao = None
            self.save()
    
    def incrementar_devolucoes(self):
        self.contagem_devolucoes += 1
        self.save()
        if self.contagem_devolucoes >= 3:
            self.aplicar_punicao()

class Cliente(models.Model):
    TIPO_CHOICES = (
        ('PF', 'Pessoa Física'),
        ('PJ', 'Pessoa Jurídica'),
    )
    
    STATUS_CHOICES = (
        ('SEM_CONTATO', 'Sem Contato'),
        ('EM_NEGOCIACAO', 'Em Negociação'),
        ('INFO_ERRADA', 'Informação Errada'),
        ('CLIENTE_RECUSOU', 'Cliente Recusou'),
        ('CONTRATO_APROVADO', 'Contrato Aprovado'),
        ('PERDIDO', 'Perdido'),
    )
    
    ORIGEM_CHOICES = (
        ('SITE', 'Site'),
        ('REDES_SOCIAIS', 'Redes Sociais'),
        ('INDICACAO', 'Indicação'),
        ('LIGACAO', 'Ligação'),
        ('WHATSAPP', 'WhatsApp'),
        ('OUTRO', 'Outro'),
    )
    
    INTERESSE_CHOICES = (
        ('COMPRA', 'Compra'),
        ('VENDA', 'Venda'),
        ('LOCACAO', 'Locação'),
        ('INVESTIMENTO', 'Investimento'),
        ('OUTRO', 'Outro'),
    )
    
    TIPO_ACAO_CHOICES = (
        ('LIGACAO', 'Ligação'),
        ('VISITA', 'Visita'),
        ('REUNIAO', 'Reunião'),
        ('EMAIL', 'E-mail'),
        ('WHATSAPP', 'WhatsApp'),
    )
    
    nome = models.CharField('Nome', max_length=200)
    tipo = models.CharField('Tipo', max_length=2, choices=TIPO_CHOICES)
    cpf_cnpj = models.CharField('CPF/CNPJ', max_length=20, unique=True)
    email = models.EmailField('E-mail', max_length=200)
    telefone = models.CharField('Telefone', max_length=20)
    celular = models.CharField('Celular', max_length=20)
    endereco = models.CharField('Endereço', max_length=200)
    numero = models.CharField('Número', max_length=20)
    complemento = models.CharField('Complemento', max_length=200, blank=True, null=True)
    bairro = models.CharField('Bairro', max_length=100)
    cidade = models.CharField('Cidade', max_length=100)
    uf = models.CharField('UF', max_length=2)
    cep = models.CharField('CEP', max_length=10)
    
    # Campos específicos para leads
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='NOVO')
    origem = models.CharField('Origem do Lead', max_length=20, choices=ORIGEM_CHOICES, default='OUTRO')
    interesse = models.CharField('Interesse', max_length=20, choices=INTERESSE_CHOICES, default='OUTRO')
    orcamento = models.DecimalField('Orçamento', max_digits=12, decimal_places=2, null=True, blank=True)
    area_desejada = models.CharField('Área Desejada', max_length=100, blank=True, null=True)
    bairros_interesse = models.TextField('Bairros de Interesse', blank=True, null=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    # Campos de controle
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads')
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    data_modificacao = models.DateTimeField('Data de Modificação', auto_now=True)
    data_ultimo_contato = models.DateTimeField('Último Contato', null=True, blank=True)
    proxima_acao = models.DateTimeField('Próxima Ação', null=True, blank=True)
    
    # Campos para lembretes e Google Calendar
    tipo_proxima_acao = models.CharField('Tipo da Próxima Ação', max_length=20, choices=TIPO_ACAO_CHOICES, null=True, blank=True)
    observacoes_proxima_acao = models.TextField('Observações da Próxima Ação', blank=True, null=True)
    google_calendar_event_id = models.CharField('ID do Evento no Google Calendar', max_length=255, blank=True, null=True)
    lembrete_minutos = models.IntegerField('Minutos para Lembrete', default=30)
    
    data_atribuicao = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-data_cadastro']

    def __str__(self):
        return self.nome

    def get_absolute_url(self):
        return reverse('cliente_detail', kwargs={'pk': self.pk})

    def save(self, *args, **kwargs):
        # Verifica se houve mudança de status para DEVOLVIDO
        if self.pk:
            old_instance = Cliente.objects.get(pk=self.pk)
            if old_instance.status != 'DEVOLVIDO' and self.status == 'DEVOLVIDO' and self.responsavel:
                punicao, created = CorretorPunicao.objects.get_or_create(corretor=self.responsavel)
                punicao.incrementar_devolucoes()
        
        # Se o responsável foi alterado, atualiza a data de atribuição
        if self.pk:
            old_instance = Cliente.objects.get(pk=self.pk)
            if old_instance.responsavel != self.responsavel and self.responsavel is not None:
                # Verifica se o corretor está em punição
                try:
                    punicao = self.responsavel.punicao
                    punicao.verificar_punicao()
                    if punicao.em_punicao:
                        raise ValueError('Corretor está em período de punição e não pode receber leads.')
                except CorretorPunicao.DoesNotExist:
                    pass
                self.data_atribuicao = timezone.now()
        elif self.responsavel is not None:
            self.data_atribuicao = timezone.now()
        
        super().save(*args, **kwargs)

    @classmethod
    def calcular_taxa_conversao(cls, corretor):
        total_leads = cls.objects.filter(responsavel=corretor).count()
        if total_leads == 0:
            return 0
        
        leads_convertidos = cls.objects.filter(
            responsavel=corretor,
            status='CONTRATO_APROVADO'
        ).count()
        
        return (leads_convertidos / total_leads) * 100

class HistoricoLead(models.Model):
    TIPO_CHOICES = (
        ('STATUS', 'Alteração de Status'),
        ('CONTATO', 'Contato Realizado'),
        ('AGENDAMENTO', 'Agendamento'),
        ('OBSERVACAO', 'Observação'),
        ('DEVOLUCAO', 'Devolução'),
        ('REDISTRIBUICAO', 'Redistribuição'),
    )
    
    lead = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='historico'
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descricao = models.TextField()
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='historicos_lead'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.lead.nome}"
    
    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Histórico'
        verbose_name_plural = 'Históricos'

class AcaoAgendada(models.Model):
    lead = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='acoes'
    )
    data_acao = models.DateTimeField()
    descricao = models.TextField()
    concluida = models.BooleanField(default=False)
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Ação para {self.lead.nome} em {self.data_acao}"
    
    def marcar_concluida(self):
        self.concluida = True
        self.data_conclusao = timezone.now()
        self.save()
    
    class Meta:
        ordering = ['data_acao']
        verbose_name = 'Ação Agendada'
        verbose_name_plural = 'Ações Agendadas'
