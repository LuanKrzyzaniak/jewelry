from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Metal(models.Model):
    nome    = models.CharField(max_length=50, unique=True)
    simbolo = models.CharField(max_length=10, unique=True, help_text='Símbolo da API. Ex: XAU, XAG')

    class Meta:
        verbose_name        = 'Metal'
        verbose_name_plural = 'Metais'
        ordering            = ['nome']

    def __str__(self):
        return self.nome


class Liga(models.Model):
    nome   = models.CharField(max_length=50, unique=True)
    metal  = models.ForeignKey(Metal, on_delete=models.PROTECT, related_name='ligas')
    pureza = models.DecimalField(
        max_digits=6, decimal_places=5,
        validators=[MinValueValidator(Decimal('0.00001')), MaxValueValidator(Decimal('1.0'))],
        help_text='Fração pura do metal. Ex: 0.75000 para Ouro 18k',
    )

    class Meta:
        verbose_name        = 'Liga'
        verbose_name_plural = 'Ligas'
        ordering            = ['metal', 'nome']

    def __str__(self):
        return f'{self.nome} ({self.metal})'

    @property
    def preco_atual(self):
        return self.precos.order_by('-vigente_desde').first()


class PrecoLiga(models.Model):
    liga            = models.ForeignKey(Liga, on_delete=models.PROTECT, related_name='precos')
    preco_por_grama = models.DecimalField(
        max_digits=12, decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
    )
    vigente_desde = models.DateField(db_index=True)
    definido_por  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='precos_definidos',
    )

    class Meta:
        verbose_name        = 'Preço de Liga'
        verbose_name_plural = 'Preços de Liga'
        unique_together     = [('liga', 'vigente_desde')]
        ordering            = ['liga', '-vigente_desde']

    def __str__(self):
        return f'{self.liga} — R$ {self.preco_por_grama}/g a partir de {self.vigente_desde.strftime("%d/%m/%Y")}'


class CotacaoMetal(models.Model):
    metal           = models.ForeignKey(Metal, on_delete=models.PROTECT, related_name='cotacoes', db_index=True)
    data            = models.DateField(db_index=True)
    preco_por_grama = models.DecimalField(
        max_digits=12, decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
    )
    fonte = models.CharField(max_length=20, default='api')  # 'api' ou 'manual'

    class Meta:
        verbose_name        = 'Cotação de Metal'
        verbose_name_plural = 'Cotações de Metais'
        unique_together     = [('metal', 'data')]
        ordering            = ['-data', 'metal']

    def __str__(self):
        return f'{self.metal} — R$ {self.preco_por_grama}/g em {self.data.strftime("%d/%m/%Y")}'


class TipoProduto(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name        = 'Tipo de Produto'
        verbose_name_plural = 'Tipos de Produto'
        ordering            = ['nome']

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome      = models.CharField(max_length=150, db_index=True)
    descricao = models.TextField(blank=True)
    tipo      = models.ForeignKey(TipoProduto, on_delete=models.PROTECT, null=True, blank=True, related_name='produtos')
    liga      = models.ForeignKey(Liga, on_delete=models.PROTECT, null=True, blank=True, related_name='produtos')
    criado_em     = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering            = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.liga})' if self.liga else self.nome

    @property
    def estoque_atual(self):
        return self.pecas.filter(status=Peca.Status.DISPONIVEL).count()

    @property
    def is_relogio(self):
        return bool(self.tipo_id and self.tipo and self.tipo.nome == 'Relógio')


class Peca(models.Model):

    class Status(models.TextChoices):
        DISPONIVEL = 'DIS', 'Disponível'
        RESERVADA  = 'RES', 'Reservada'
        CONSIGNADA = 'CON', 'Consignada'
        VENDIDA    = 'VEN', 'Vendida'
        RETIRADA   = 'RET', 'Retirada'   # saiu via movimentação, não venda

    produto           = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name='pecas')
    codigo            = models.CharField(max_length=20, unique=True, blank=True, db_index=True)
    status            = models.CharField(max_length=3, choices=Status.choices, default=Status.DISPONIVEL, db_index=True)
    peso_gramas       = models.DecimalField(
        max_digits=8, decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name='Peso (g)',
    )
    custo_mao_de_obra = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    preco_proprio = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Usado apenas para relógios.',
    )
    observacoes   = models.TextField(blank=True)
    criado_em     = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Peça'
        verbose_name_plural = 'Peças'
        ordering            = ['-criado_em']

    def __str__(self):
        return f'{self.codigo} — {self.produto.nome}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.codigo:
            prefix = ''.join(c for c in self.produto.nome if c.isalpha())[:4].upper()
            self.codigo = f'{prefix}-{self.pk:04d}'
            Peca.objects.filter(pk=self.pk).update(codigo=self.codigo)

    @property
    def is_relogio(self):
        return self.produto.is_relogio

    @property
    def preco_sugerido(self):
        if self.is_relogio:
            return (self.preco_proprio or Decimal('0.00')).quantize(Decimal('0.01'))
        if not self.produto.liga:
            return self.custo_mao_de_obra.quantize(Decimal('0.01'))
        preco_liga = self.produto.liga.preco_atual
        if not preco_liga:
            return Decimal('0.00')
        return (self.peso_gramas * preco_liga.preco_por_grama + self.custo_mao_de_obra).quantize(Decimal('0.01'))

    @property
    def foto_principal(self):
        return self.fotos.filter(principal=True).first() or self.fotos.first()


class FotoPeca(models.Model):
    peca      = models.ForeignKey(Peca, on_delete=models.CASCADE, related_name='fotos')
    imagem    = models.ImageField(upload_to='pecas/%Y/%m/')
    principal = models.BooleanField(default=False)
    ordem     = models.PositiveSmallIntegerField(default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Foto de Peça'
        verbose_name_plural = 'Fotos de Peças'
        ordering            = ['ordem', 'criado_em']

    def __str__(self):
        return f'Foto {self.pk} de {self.peca}'
