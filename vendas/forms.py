from decimal import Decimal

from django import forms

from .models import Cliente, Fornecedor, Venda


class ClienteForm(forms.ModelForm):
    class Meta:
        model  = Cliente
        fields = ['nome', 'telefone', 'observacao', 'ativo']
        widgets = {
            'nome':       forms.TextInput(attrs={'class': 'form-control'}),
            'telefone':   forms.TextInput(attrs={'class': 'form-control'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo':      forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nome':       'Nome',
            'telefone':   'Telefone',
            'observacao': 'Observação',
            'ativo':      'Ativo',
        }


class FornecedorForm(forms.ModelForm):
    class Meta:
        model  = Fornecedor
        fields = ['razao_social', 'nome_fantasia', 'cnpj', 'telefone', 'email', 'observacao', 'ativo']
        widgets = {
            'razao_social':  forms.TextInput(attrs={'class': 'form-control'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj':          forms.TextInput(attrs={'class': 'form-control'}),
            'telefone':      forms.TextInput(attrs={'class': 'form-control'}),
            'email':         forms.EmailInput(attrs={'class': 'form-control'}),
            'observacao':    forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo':         forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'razao_social':  'Razão Social',
            'nome_fantasia': 'Nome Fantasia',
            'cnpj':          'CNPJ',
            'telefone':      'Telefone',
            'email':         'E-mail',
            'observacao':    'Observação',
            'ativo':         'Ativo',
        }


class VendaForm(forms.ModelForm):
    class Meta:
        model  = Venda
        fields = ['cliente', 'status', 'observacoes']
        widgets = {
            'cliente':     forms.Select(attrs={'class': 'form-select'}),
            'status':      forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
        labels = {
            'cliente':     'Cliente',
            'status':      'Status',
            'observacoes': 'Observações',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset    = Cliente.objects.filter(ativo=True).order_by('nome')
        self.fields['cliente'].empty_label = 'Selecione o cliente'
        self.fields['status'].empty_label  = None
        self.fields['status'].choices = [
            (v, l) for v, l in Venda.Status.choices if v != Venda.Status.CANCELADA
        ]


class DescontoForm(forms.Form):
    TIPO_CHOICES = [
        ('valor',       'R$'),
        ('percentual',  '%'),
    ]
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm', 'style': 'max-width:70px'}),
    )
    valor = forms.DecimalField(
        max_digits=12, decimal_places=2,
        min_value=Decimal('0.00'),
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'data-mask': 'decimal-2'}),
        label='Desconto',
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('tipo') == 'percentual' and cleaned.get('valor') is not None and cleaned['valor'] > 100:
            self.add_error('valor', 'O percentual não pode ser maior que 100%.')
        return cleaned


class ItemVendaForm(forms.Form):
    peca_id = forms.IntegerField(widget=forms.HiddenInput())
