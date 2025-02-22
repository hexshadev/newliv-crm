# Generated by Django 5.0.2 on 2025-01-31 01:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0003_cliente_google_calendar_event_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AcaoAgendada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_acao', models.DateTimeField()),
                ('descricao', models.TextField()),
                ('concluida', models.BooleanField(default=False)),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('data_conclusao', models.DateTimeField(blank=True, null=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='acoes', to='clientes.cliente')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Ação Agendada',
                'verbose_name_plural': 'Ações Agendadas',
                'ordering': ['data_acao'],
            },
        ),
        migrations.CreateModel(
            name='HistoricoLead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('STATUS', 'Alteração de Status'), ('CONTATO', 'Contato Realizado'), ('AGENDAMENTO', 'Agendamento'), ('OBSERVACAO', 'Observação')], max_length=20)),
                ('descricao', models.TextField()),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('lead', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historico', to='clientes.cliente')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Histórico',
                'verbose_name_plural': 'Históricos',
                'ordering': ['-data_criacao'],
            },
        ),
    ]
