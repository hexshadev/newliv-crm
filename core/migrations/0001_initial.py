# Generated by Django 5.0.2 on 2025-01-31 00:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleCalendarConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField(verbose_name='Access Token')),
                ('refresh_token', models.TextField(verbose_name='Refresh Token')),
                ('token_expiry', models.DateTimeField(verbose_name='Token Expiry')),
                ('client_id', models.CharField(max_length=255, verbose_name='Client ID')),
                ('client_secret', models.CharField(max_length=255, verbose_name='Client Secret')),
                ('novas_acoes', models.BooleanField(default=True, verbose_name='Sincronizar novas ações')),
                ('lembretes', models.BooleanField(default=True, verbose_name='Receber lembretes')),
                ('bidirecional', models.BooleanField(default=False, verbose_name='Sincronização bidirecional')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='google_calendar_config', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Configuração Google Calendar',
                'verbose_name_plural': 'Configurações Google Calendar',
            },
        ),
    ]
