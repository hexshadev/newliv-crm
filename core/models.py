from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class GoogleCalendarConfig(models.Model):
    """Configurações de sincronização com Google Calendar"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='google_calendar_config')
    access_token = models.TextField('Access Token')
    refresh_token = models.TextField('Refresh Token')
    token_expiry = models.DateTimeField('Token Expiry')
    client_id = models.CharField('Client ID', max_length=255)
    client_secret = models.CharField('Client Secret', max_length=255)
    
    # Configurações de sincronização
    novas_acoes = models.BooleanField('Sincronizar novas ações', default=True)
    lembretes = models.BooleanField('Receber lembretes', default=True)
    bidirecional = models.BooleanField('Sincronização bidirecional', default=False)
    
    class Meta:
        verbose_name = 'Configuração Google Calendar'
        verbose_name_plural = 'Configurações Google Calendar'
    
    def __str__(self):
        return f'Configuração Google Calendar - {self.user.get_full_name()}'

class Aviso(models.Model):
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avisos_criados')
    todos_corretores = models.BooleanField(default=False)
    corretores = models.ManyToManyField(User, related_name='avisos_recebidos', blank=True)
    urgente = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)
    lido = models.BooleanField(default=False)
    lido_por = models.ManyToManyField(User, related_name='avisos_lidos', blank=True)

    class Meta:
        ordering = ['-data_criacao']
        verbose_name = 'Aviso'
        verbose_name_plural = 'Avisos'

    def __str__(self):
        return self.titulo

    def marcar_como_lido(self, usuario):
        """Marca o aviso como lido para um usuário específico"""
        if usuario not in self.lido_por.all():
            self.lido_por.add(usuario)
            # Se todos os destinatários leram, marca como lido
            if self.todos_corretores:
                corretores = User.objects.filter(perfil__tipo='CORRETOR')
                if all(corretor in self.lido_por.all() for corretor in corretores):
                    self.lido = True
            else:
                if all(corretor in self.lido_por.all() for corretor in self.corretores.all()):
                    self.lido = True
            self.save()

    def get_destinatarios_display(self):
        if self.todos_corretores:
            return "Todos os Corretores"
        return f"{self.corretores.count()} corretor(es)"

@receiver(post_save, sender=User)
def criar_perfil(sender, instance, created, **kwargs):
    """Cria um perfil automaticamente quando um usuário é criado"""
    if created:
        Perfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def salvar_perfil(sender, instance, **kwargs):
    """Salva o perfil quando o usuário é salvo"""
    instance.perfil.save()

class Conversa(models.Model):
    participantes = models.ManyToManyField(User, related_name='conversas')
    ultima_mensagem = models.DateTimeField(auto_now=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-ultima_mensagem']
        verbose_name = 'Conversa'
        verbose_name_plural = 'Conversas'
    
    def __str__(self):
        return f"Conversa {self.id} - {', '.join(user.get_full_name() for user in self.participantes.all())}"

class Mensagem(models.Model):
    conversa = models.ForeignKey(Conversa, on_delete=models.CASCADE, related_name='mensagens')
    remetente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mensagens_enviadas')
    conteudo = models.TextField()
    anexo = models.FileField(upload_to='chat_anexos/', null=True, blank=True)
    data_envio = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    deletada_por = models.ManyToManyField(User, related_name='mensagens_deletadas', blank=True)
    
    class Meta:
        ordering = ['data_envio']
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
    
    def __str__(self):
        return f"Mensagem de {self.remetente.get_full_name()} em {self.data_envio}"
    
    def marcar_como_lida(self):
        self.lida = True
        self.save()
    
    def deletar_para_usuario(self, user):
        self.deletada_por.add(user)
        self.save()
        
    def esta_deletada_para(self, user):
        return self.deletada_por.filter(id=user.id).exists()
