# Generated by Django 5.0.2 on 2025-01-31 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_aviso'),
    ]

    operations = [
        migrations.AddField(
            model_name='aviso',
            name='ativo',
            field=models.BooleanField(default=True),
        ),
    ]
