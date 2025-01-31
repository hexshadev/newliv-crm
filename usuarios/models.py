from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Perfil(models.Model):
    TIPO_CHOICES = (
        ('GESTOR', 'Gestor'),
        ('CORRETOR', 'Corretor'),
    )
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, default='CORRETOR')
    telefone = models.CharField('Telefone', max_length=20, blank=True, default='')
    celular = models.CharField('Celular', max_length=20, blank=True, default='')
    foto = models.ImageField('Foto', upload_to='perfis/', blank=True, null=True)
    creci = models.CharField('CRECI', max_length=20, blank=True, null=True)
    bio = models.TextField('Biografia', blank=True, default='')
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfis'
        ordering = ['usuario__first_name']

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.get_tipo_display()}"

@receiver(post_save, sender=User)
def criar_ou_atualizar_perfil(sender, instance, created, **kwargs):
    """Cria ou atualiza o perfil do usuário"""
    if created:
        Perfil.objects.create(usuario=instance)
    else:
        # Garante que o usuário tenha um perfil mesmo se não foi criado no signal
        Perfil.objects.get_or_create(usuario=instance)

@receiver(post_save, sender=User)
def salvar_perfil(sender, instance, **kwargs):
    instance.perfil.save()
