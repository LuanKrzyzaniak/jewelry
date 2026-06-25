from decimal import Decimal

from django import forms

from catalogo.models import Produto
from vendas.models import Cliente, Fornecedor

from .models import ItemLote, LoteMovimentacao, MovimentacaoEstoque


class MovimentacaoEntradaForm(forms.Form):
    """Movimentação de entrada avulsa: cria peças ao salvar."""
    produto           = forms.ModelChoiceField(
        queryset=Produto.objects.select_related('liga', 'tipo').order_by('nome'),
        empty_label='Selecione o produto',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Produto',
    )
    quantidade        = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        label='Quantidade',
    )
    peso_padrao       = forms.DecimalField(
        max_digits=8, decimal_places=3,
        min_value=Decimal('0.001'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'decimal-3'}),
        label='Peso por peça (g)',
    )
    custo_mao_de_obra = forms.DecimalField(
        max_digits=10, decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'decimal-2'}),
        label='Custo de mão de obra por peça (R$)',
    )
    fornecedor        = forms.ModelChoiceField(
        queryset=Fornecedor.objects.filter(ativo=True).order_by('razao_social'),
        required=False,
        empty_label='Selecione o fornecedor',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Fornecedor',
    )
    observacoes       = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Observações',
    )


class MovimentacaoSaidaForm(forms.Form):
    """Movimentação de saída/ajuste avulsa sobre peça específica."""
    peca_id     = forms.IntegerField(widget=forms.HiddenInput())
    tipo        = forms.ChoiceField(
        choices=[
            (MovimentacaoEstoque.Tipo.SAIDA,      'Saída'),
            (MovimentacaoEstoque.Tipo.AJUSTE_NEG, 'Ajuste Negativo'),
            (MovimentacaoEstoque.Tipo.AJUSTE_POS, 'Ajuste Positivo'),
            (MovimentacaoEstoque.Tipo.DEVOLUCAO,  'Devolução'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo',
    )
    cliente     = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(ativo=True).order_by('nome'),
        required=False,
        empty_label='Selecione o cliente',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Cliente',
    )
    observacoes = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Observações',
    )


class LoteForm(forms.ModelForm):
    class Meta:
        model  = LoteMovimentacao
        fields = ['tipo', 'fornecedor', 'cliente', 'observacoes']
        widgets = {
            'tipo':        forms.Select(attrs={'class': 'form-select', 'id': 'id_lote_tipo'}),
            'fornecedor':  forms.Select(attrs={'class': 'form-select'}),
            'cliente':     forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'tipo':        'Tipo',
            'fornecedor':  'Fornecedor',
            'cliente':     'Cliente',
            'observacoes': 'Observações',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].choices           = [('', 'Selecione o tipo')] + list(LoteMovimentacao.Tipo.choices)
        self.fields['fornecedor'].queryset    = Fornecedor.objects.filter(ativo=True).order_by('razao_social')
        self.fields['fornecedor'].empty_label = 'Selecione o fornecedor'
        self.fields['fornecedor'].required    = False
        self.fields['cliente'].queryset       = Cliente.objects.filter(ativo=True).order_by('nome')
        self.fields['cliente'].empty_label    = 'Selecione o cliente'
        self.fields['cliente'].required       = False

    def clean(self):
        cleaned    = super().clean()
        tipo       = cleaned.get('tipo')
        fornecedor = cleaned.get('fornecedor')
        if tipo == LoteMovimentacao.Tipo.ENTRADA and not fornecedor:
            self.add_error('fornecedor', 'Fornecedor é obrigatório para lotes de entrada.')
        return cleaned


class LoteItemEntradaForm(forms.Form):
    """Adiciona produto a lote de entrada (cria peças ao finalizar)."""
    produto           = forms.ModelChoiceField(
        queryset=Produto.objects.select_related('liga', 'tipo').order_by('nome'),
        empty_label='Selecione o produto',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Produto',
    )
    quantidade        = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        label='Quantidade',
    )
    peso_padrao       = forms.DecimalField(
        max_digits=8, decimal_places=3,
        min_value=Decimal('0.001'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'decimal-3'}),
        label='Peso por peça (g)',
    )
    custo_mao_de_obra = forms.DecimalField(
        max_digits=10, decimal_places=2,
        min_value=Decimal('0.00'),
        initial=Decimal('0.00'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'decimal-2'}),
        label='Custo de mão de obra por peça (R$)',
    )

    def __init__(self, lote=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lote = lote
        self.fields['produto'].queryset = Produto.objects.select_related('liga', 'tipo').order_by('nome')


class ItemLotePesoForm(forms.ModelForm):
    class Meta:
        model  = ItemLote
        fields = ['peso_padrao', 'custo_mao_de_obra']
        widgets = {
            'peso_padrao':       forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-mask': 'decimal-3'}),
            'custo_mao_de_obra': forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-mask': 'decimal-2'}),
        }
        labels = {
            'peso_padrao':       'Peso (g)',
            'custo_mao_de_obra': 'Mão de obra (R$)',
        }


class LoteItemSaidaForm(forms.Form):
    """Adiciona peça específica a lote de saída (via picker — peca_id vem do modal)."""
    peca_id = forms.IntegerField(widget=forms.HiddenInput())
