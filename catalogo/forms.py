from decimal import Decimal

from django import forms

from .models import Liga, Peca, PrecoLiga, Produto, TipoProduto


class LigaForm(forms.ModelForm):
    class Meta:
        model  = Liga
        fields = ['nome', 'metal', 'pureza']
        widgets = {
            'nome':   forms.TextInput(attrs={'class': 'form-control'}),
            'metal':  forms.Select(attrs={'class': 'form-select'}),
            'pureza': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00001'}),
        }
        labels = {
            'nome':   'Nome',
            'metal':  'Metal base',
            'pureza': 'Pureza',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['metal'].empty_label = 'Selecione o metal base'


class PrecoLigaForm(forms.Form):
    preco_por_grama = forms.DecimalField(
        max_digits=12, decimal_places=4,
        min_value=Decimal('0.0001'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'decimal-4'}),
        label='Preço cobrado por grama (R$)',
    )


class TipoProdutoForm(forms.ModelForm):
    class Meta:
        model  = TipoProduto
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nome': 'Nome',
        }


class ProdutoForm(forms.ModelForm):
    class Meta:
        model  = Produto
        fields = ['nome', 'descricao', 'tipo', 'liga']
        widgets = {
            'nome':      forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo':      forms.Select(attrs={'class': 'form-select'}),
            'liga':      forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'nome':      'Nome',
            'descricao': 'Descrição',
            'tipo':      'Tipo de produto',
            'liga':      'Liga',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tipo'].empty_label = 'Selecione o tipo'
        self.fields['tipo'].required    = True
        self.fields['liga'].empty_label = 'Selecione a liga'

    def clean(self):
        cleaned = super().clean()
        liga_na = self.data.get('liga_na') == '1'
        if not liga_na and not cleaned.get('liga'):
            self.add_error('liga', 'Selecione a liga ou marque "Não se aplica".')
        return cleaned


class PecaForm(forms.ModelForm):
    class Meta:
        model  = Peca
        fields = ['produto', 'status', 'peso_gramas', 'custo_mao_de_obra', 'observacoes']
        widgets = {
            'produto':           forms.Select(attrs={'class': 'form-select'}),
            'status':            forms.Select(attrs={'class': 'form-select'}),
            'peso_gramas':       forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'decimal-3'}),
            'custo_mao_de_obra': forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'decimal-2'}),
            'observacoes':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'produto':           'Produto (modelo)',
            'status':            'Status',
            'peso_gramas':       'Peso (g)',
            'custo_mao_de_obra': 'Custo de mão de obra (R$)',
            'observacoes':       'Observações',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].queryset    = Produto.objects.select_related('tipo').order_by('nome')
        self.fields['produto'].empty_label = 'Selecione o produto'
