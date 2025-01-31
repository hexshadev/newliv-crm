from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from usuarios.models import Perfil

class Command(BaseCommand):
    help = 'Cria perfis para usuários que não possuem'

    def handle(self, *args, **kwargs):
        users_sem_perfil = User.objects.filter(perfil__isnull=True)
        count = 0
        
        for user in users_sem_perfil:
            Perfil.objects.create(usuario=user)
            count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Perfil criado para o usuário: {user.username}')
            )
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Todos os usuários já possuem perfil.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'{count} perfis foram criados.')
            ) 