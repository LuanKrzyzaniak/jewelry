from decimal import Decimal

from django import forms

from .models import Cliente, Fornecedor, Venda


class ClienteForm(forms.ModelForm):
    class Meta:
        model  = Cliente
        fields = ['nome', 'telefone', 'observacao']
        widgets = {
            'nome':       forms.TextInput(attrs={'class': 'form-control'}),
            'telefone':   forms.TextInput(attrs={'class': 'form-control'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'nome':       'Nome',
            'telefone':   'Telefone',
            'observacao': 'Observação',
        }


class FornecedorForm(forms.ModelForm):
    class Meta:
        model  = Fornecedor
        fields = ['razao_social', 'nome_fantasia', 'cnpj', 'telefone', 'email', 'ativo']
        widgets = {
            'razao_social':  forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj':          forms.TextInput(attrs={'class': 'form-control'}),
            'telefone':      forms.TextInput(attrs={'class': 'form-control'}),
            'email':         forms.EmailInput(attrs={'class': 'form-control'}),
            'ativo':         forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'razao_social':  'Razão Social',
            'nome_fantasia': 'Nome Fantasia',
            'cnpj':          'CNPJ',
            'telefone':      'Telefone',
            'email':         'E-mail',
            'ativo':         'Ativo',
        }


class VendaForm(forms.ModelForm):
    class Meta:
        model  = Venda
        fields = ['cliente', 'status', 'desconto_total', 'observacoes']
        widgets = {
            'cliente':        forms.Select(attrs={'class': 'form-select'}),
            'status':         forms.Select(attrs={'class': 'form-select'}),
            'desconto_total': forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'decimal-2'}),
            'observacoes':    forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'cliente':        'Cliente',
            'status':         'Status',
            'desconto_total': 'Desconto total (R$)',
            'observacoes':    'Observações',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].empty_label      = 'Selecione o cliente'
        self.fields['status'].empty_label       = None
        self.fields['desconto_total'].required  = False
        self.fields['desconto_total'].initial   = '0.00'
        self.fields['status'].choices = [
            (v, l) for v, l in Venda.Status.choices if v != Venda.Status.CANCELADA
        ]


class ItemVendaForm(forms.Form):
    """Form para POST de adição de peça à venda."""
    peca_id             = forms.IntegerField(widget=forms.HiddenInput())
    preco_unitario_pago = forms.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'data-mask': 'decimal-2'}),
        label='Preço (R$)',
    )
