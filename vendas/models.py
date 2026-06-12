from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    nome       = models.CharField(max_length=150, db_index=True)
    telefone   = models.CharField(max_length=20, blank=True)
    observacao = models.TextField(blank=True)
    criado_em  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering            = ['nome']

    def __str__(self): 
        return self.nome


class Fornecedor(models.Model):
    razao_social  = models.CharField(max_length=200, db_index=True)
    nome_fantasia = models.CharField(max_length=200, blank=True)
    cnpj          = models.CharField(max_length=18, unique=True, blank=True, null=True)
    email         = models.EmailField(blank=True)
    telefone      = models.CharField(max_length=20, blank=True)
    ativo         = models.BooleanField(default=True)
    criado_em     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering            = ['razao_social']

    def __str__(self):
        return self.nome_fantasia or self.razao_social


class Venda(models.Model):

    class Status(models.TextChoices):
        ORCAMENTO  = 'ORC', 'Orçamento'
        RESERVADA  = 'RES', 'Reservada'
        CONFIRMADA = 'CON', 'Confirmada'
        CANCELADA  = 'CAN', 'Cancelada'

    cliente        = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='vendas', db_index=True)
    vendedor       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='vendas_realizadas',
        db_index=True,
    )
    status         = models.CharField(max_length=3, choices=Status.choices, default=Status.CONFIRMADA, db_index=True)
    data_venda     = models.DateTimeField(default=timezone.now, db_index=True)
    valor_total    = models.DecimalField(
        max_digits=14, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    desconto_total = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    observacoes    = models.TextField(blank=True)
    criado_em      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Venda'
        verbose_name_plural = 'Vendas'
        ordering            = ['-data_venda']
        indexes = [
            models.Index(fields=['-data_venda', 'status'], name='idx_venda_data_status'),
        ]

    def __str__(self):
        return f'Venda #{self.pk} — {self.cliente} | R$ {self.valor_total} ({self.data_venda.strftime("%d/%m/%Y")})'

    def recalcular_total(self):
        total = sum(item.subtotal for item in self.itens.all())
        self.valor_total = total - self.desconto_total
        self.save(update_fields=['valor_total'])


class ItemVenda(models.Model):
    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name='itens', db_index=True)
    peca  = models.ForeignKey(
        'catalogo.Peca',
        on_delete=models.PROTECT,
        related_name='itens_vendidos',
        db_index=True,
        null=True,   # null=True apenas para migração; sempre preenchido pelo código
    )
    preco_unitario_pago = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        verbose_name        = 'Item de Venda'
        verbose_name_plural = 'Itens de Venda'
        unique_together     = [('venda', 'peca')]
        ordering            = ['venda']

    def __str__(self):
        return f'{self.peca.codigo} @ R$ {self.preco_unitario_pago}'

    @property
    def produto(self):
        return self.peca.produto

    @property
    def subtotal(self):
        return self.preco_unitario_pago.quantize(Decimal('0.01'))
