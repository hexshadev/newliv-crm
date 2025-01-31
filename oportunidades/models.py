from django.db import models
from django.urls import reverse
from clientes.models import Cliente

class Oportunidade(models.Model):
    STATUS_CHOICES = (
        ('NOVO', 'Novo'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('AGUARDANDO_CLIENTE', 'Aguardando Cliente'),
        ('FECHADO_GANHO', 'Fechado Ganho'),
        ('FECHADO_PERDIDO', 'Fechado Perdido'),
    )
    
    PRIORIDADE_CHOICES = (
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
    )
    
    titulo = models.CharField('Título', max_length=200)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='oportunidades')
    valor = models.DecimalField('Valor', max_digits=10, decimal_places=2)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='NOVO')
    prioridade = models.CharField('Prioridade', max_length=20, choices=PRIORIDADE_CHOICES, default='MEDIA')
    descricao = models.TextField('Descrição', blank=True, null=True)
    data_previsao_fechamento = models.DateField('Previsão de Fechamento')
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    data_modificacao = models.DateTimeField('Data de Modificação', auto_now=True)
    responsavel = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='oportunidades_responsavel')

    class Meta:
        verbose_name = 'Oportunidade'
        verbose_name_plural = 'Oportunidades'
        ordering = ['-data_cadastro']

    def __str__(self):
        return f"{self.titulo} - {self.cliente.nome}"

    def get_absolute_url(self):
        return reverse('oportunidade_detail', kwargs={'pk': self.pk})
