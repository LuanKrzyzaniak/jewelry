from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class LoteMovimentacao(models.Model):

    class Tipo(models.TextChoices):
        ENTRADA = 'ENT', 'Entrada'
        SAIDA   = 'SAI', 'Saída'

    tipo        = models.CharField(max_length=3, choices=Tipo.choices)
    fornecedor  = models.ForeignKey(
        'vendas.Fornecedor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='lotes',
    )
    cliente     = models.ForeignKey(
        'vendas.Cliente',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='lotes',
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='lotes_registrados',
    )
    observacoes = models.CharField(max_length=300, blank=True)
    criado_em   = models.DateTimeField(auto_now_add=True)
    finalizado  = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Lote de Movimentação'
        verbose_name_plural = 'Lotes de Movimentação'
        ordering            = ['-criado_em']

    def __str__(self):
        return f'Lote #{self.pk} — {self.get_tipo_display()} ({self.criado_em.strftime("%d/%m/%Y")})'

    @property
    def total_itens(self):
        return self.itens.count()


class ItemLote(models.Model):
    lote = models.ForeignKey(LoteMovimentacao, on_delete=models.CASCADE, related_name='itens')

    # Lote de ENTRADA: produto + quantidade + peso_padrao + custo_mao_de_obra (cria peças ao finalizar)
    produto           = models.ForeignKey(
        'catalogo.Produto', on_delete=models.PROTECT,
        null=True, blank=True, related_name='itens_lote',
    )
    quantidade        = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    peso_padrao       = models.DecimalField(
        max_digits=8, decimal_places=3,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name='Peso por peça (g)',
    )
    custo_mao_de_obra = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )

    # Lote de SAÍDA: peça específica (OneToOne — cada peça em no máximo um lote ativo)
    peca = models.OneToOneField(
        'catalogo.Peca', on_delete=models.PROTECT,
        null=True, blank=True, related_name='item_lote',
    )

    class Meta:
        verbose_name        = 'Item de Lote'
        verbose_name_plural = 'Itens de Lote'
        ordering            = ['produto__nome', 'peca__codigo']

    def __str__(self):
        if self.peca:
            return f'{self.peca.codigo} — {self.peca.produto.nome}'
        return f'{self.produto} × {self.quantidade}'


class MovimentacaoEstoque(models.Model):

    class Tipo(models.TextChoices):
        ENTRADA    = 'ENT', 'Entrada'
        SAIDA      = 'SAI', 'Saída'
        AJUSTE_POS = 'AJP', 'Ajuste Positivo'
        AJUSTE_NEG = 'AJN', 'Ajuste Negativo'
        DEVOLUCAO  = 'DEV', 'Devolução'

    produto          = models.ForeignKey(
        'catalogo.Produto',
        on_delete=models.PROTECT,
        related_name='movimentacoes',
        db_index=True,
    )
    peca             = models.ForeignKey(
        'catalogo.Peca',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimentacoes',
    )
    tipo             = models.CharField(max_length=3, choices=Tipo.choices, db_index=True)
    quantidade       = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    fornecedor       = models.ForeignKey(
        'vendas.Fornecedor',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimentacoes',
    )
    cliente          = models.ForeignKey(
        'vendas.Cliente',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimentacoes',
    )
    referencia_venda = models.ForeignKey(
        'vendas.Venda',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimentacoes',
    )
    lote             = models.ForeignKey(
        LoteMovimentacao,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='movimentacoes',
    )
    responsavel      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='movimentacoes_realizadas',
    )
    observacoes      = models.CharField(max_length=200, blank=True)
    data_hora        = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = 'Movimentação de Estoque'
        verbose_name_plural = 'Movimentações de Estoque'
        ordering            = ['-data_hora']
        indexes = [
            models.Index(fields=['produto', '-data_hora'], name='idx_movest_produto_data'),
        ]

    def __str__(self):
        return (
            f'{self.get_tipo_display()} | {self.produto} | '
            f'Qtd: {self.quantidade} | {self.data_hora.strftime("%d/%m/%Y")}'
        )
