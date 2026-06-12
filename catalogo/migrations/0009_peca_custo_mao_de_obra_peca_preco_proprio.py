from decimal import Decimal

import django.core.validators
from django.db import migrations, models


def copiar_dados_produto_para_peca(apps, schema_editor):
    Peca = apps.get_model('catalogo', 'Peca')
    for peca in Peca.objects.select_related('produto'):
        produto = peca.produto
        if not peca.peso_gramas:
            peca.peso_gramas = produto.peso_gramas
        peca.custo_mao_de_obra = produto.custo_mao_de_obra
        if produto.preco_proprio is not None:
            peca.preco_proprio = produto.preco_proprio
        peca.save()


class Migration(migrations.Migration):

    dependencies = [
        ('catalogo', '0008_peca_peso_gramas_alter_peca_status'),
    ]

    operations = [
        # 1. Adiciona novos campos em Peca (custo nullable até a data migration)
        migrations.AddField(
            model_name='peca',
            name='custo_mao_de_obra',
            field=models.DecimalField(
                decimal_places=2, default=Decimal('0.00'), max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.AddField(
            model_name='peca',
            name='preco_proprio',
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=10, null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                help_text='Usado apenas para relógios.',
            ),
        ),
        # 2. Data migration: copia valores do produto para cada peça
        migrations.RunPython(copiar_dados_produto_para_peca, migrations.RunPython.noop),
        # 3. Torna peso_gramas obrigatório
        migrations.AlterField(
            model_name='peca',
            name='peso_gramas',
            field=models.DecimalField(
                decimal_places=3, max_digits=8,
                validators=[django.core.validators.MinValueValidator(Decimal('0.001'))],
                verbose_name='Peso (g)',
            ),
        ),
        # 4. Remove os campos de Produto
        migrations.RemoveField(model_name='produto', name='peso_gramas'),
        migrations.RemoveField(model_name='produto', name='custo_mao_de_obra'),
        migrations.RemoveField(model_name='produto', name='preco_proprio'),
    ]
