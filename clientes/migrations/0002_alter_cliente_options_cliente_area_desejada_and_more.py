# Generated by Django 5.0.2 on 2025-01-30 23:45

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clientes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cliente',
            options={'ordering': ['-data_cadastro'], 'verbose_name': 'Lead', 'verbose_name_plural': 'Leads'},
        ),
        migrations.AddField(
            model_name='cliente',
            name='area_desejada',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Área Desejada'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='bairros_interesse',
            field=models.TextField(blank=True, null=True, verbose_name='Bairros de Interesse'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='data_ultimo_contato',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Último Contato'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='interesse',
            field=models.CharField(choices=[('COMPRA', 'Compra'), ('VENDA', 'Venda'), ('LOCACAO', 'Locação'), ('INVESTIMENTO', 'Investimento'), ('OUTRO', 'Outro')], default='OUTRO', max_length=20, verbose_name='Interesse'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='orcamento',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Orçamento'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='origem',
            field=models.CharField(choices=[('SITE', 'Site'), ('REDES_SOCIAIS', 'Redes Sociais'), ('INDICACAO', 'Indicação'), ('LIGACAO', 'Ligação'), ('WHATSAPP', 'WhatsApp'), ('OUTRO', 'Outro')], default='OUTRO', max_length=20, verbose_name='Origem do Lead'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='proxima_acao',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Próxima Ação'),
        ),
        migrations.AddField(
            model_name='cliente',
            name='responsavel',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='leads', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='cliente',
            name='status',
            field=models.CharField(choices=[('NOVO', 'Novo Lead'), ('EM_ATENDIMENTO', 'Em Atendimento'), ('CONVERTIDO', 'Lead Convertido'), ('PERDIDO', 'Lead Perdido'), ('INATIVO', 'Inativo')], default='NOVO', max_length=20, verbose_name='Status'),
        ),
    ]
