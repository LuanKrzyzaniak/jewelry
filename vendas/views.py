from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from catalogo.models import Peca, TipoProduto
from estoque.models import MovimentacaoEstoque
from estoque.views import _pecas_disponiveis_json
from usuarios.mixins import GerenteRequiredMixin

from .forms import ClienteForm, DescontoForm, FornecedorForm, ItemVendaForm, VendaForm
from .models import Cliente, Fornecedor, ItemVenda, Venda


# ---------------------------------------------------------------------------
# Cliente
# ---------------------------------------------------------------------------

class ClienteListView(LoginRequiredMixin, ListView):
    model               = Cliente
    template_name       = 'vendas/cliente_list.html'
    context_object_name = 'clientes'

    def get_queryset(self):
        qs = Cliente.objects.all()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(nome__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['busca'] = self.request.GET.get('q', '')
        return ctx


class ClienteCreateView(LoginRequiredMixin, CreateView):
    model         = Cliente
    form_class    = ClienteForm
    template_name = 'vendas/cliente_form.html'
    success_url   = reverse_lazy('vendas:cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente cadastrado.')
        return super().form_valid(form)


class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model         = Cliente
    form_class    = ClienteForm
    template_name = 'vendas/cliente_form.html'
    success_url   = reverse_lazy('vendas:cliente_list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente atualizado.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Fornecedor
# ---------------------------------------------------------------------------

class FornecedorListView(GerenteRequiredMixin, ListView):
    model               = Fornecedor
    template_name       = 'vendas/fornecedor_list.html'
    context_object_name = 'fornecedores'


class FornecedorCreateView(GerenteRequiredMixin, CreateView):
    model         = Fornecedor
    form_class    = FornecedorForm
    template_name = 'vendas/fornecedor_form.html'
    success_url   = reverse_lazy('vendas:fornecedor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Fornecedor cadastrado.')
        return super().form_valid(form)


class FornecedorUpdateView(GerenteRequiredMixin, UpdateView):
    model         = Fornecedor
    form_class    = FornecedorForm
    template_name = 'vendas/fornecedor_form.html'
    success_url   = reverse_lazy('vendas:fornecedor_list')

    def form_valid(self, form):
        messages.success(self.request, 'Fornecedor atualizado.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Venda
# ---------------------------------------------------------------------------

class VendaListView(LoginRequiredMixin, ListView):
    model               = Venda
    template_name       = 'vendas/venda_list.html'
    context_object_name = 'vendas'
    paginate_by         = 25

    def get_queryset(self):
        qs = Venda.objects.select_related('cliente', 'vendedor')

        if q := self.request.GET.get('q'):
            qs = qs.filter(cliente__nome__icontains=q)

        if status := self.request.GET.get('status'):
            qs = qs.filter(status=status)

        if vendedor_id := self.request.GET.get('vendedor'):
            qs = qs.filter(vendedor_id=vendedor_id)

        if data_de := self.request.GET.get('data_de'):
            qs = qs.filter(data_venda__date__gte=data_de)

        if data_ate := self.request.GET.get('data_ate'):
            qs = qs.filter(data_venda__date__lte=data_ate)

        return qs

    def get_context_data(self, **kwargs):
        from django.db.models import Sum
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = Venda.Status.choices
        ctx['status_atual']   = self.request.GET.get('status', '')
        ctx['vendedor_atual'] = self.request.GET.get('vendedor', '')
        ctx['busca']          = self.request.GET.get('q', '')
        ctx['data_de']        = self.request.GET.get('data_de', '')
        ctx['data_ate']       = self.request.GET.get('data_ate', '')
        ctx['vendedores']     = get_user_model().objects.order_by('first_name')
        ctx['total_filtrado'] = self.get_queryset().filter(
            status=Venda.Status.CONFIRMADA
        ).aggregate(total=Sum('valor_total'))['total'] or 0
        return ctx


class VendaDetailView(LoginRequiredMixin, DetailView):
    model               = Venda
    template_name       = 'vendas/venda_detail.html'
    context_object_name = 'venda'

    def get_object(self, queryset=None):
        qs = (
            Venda.objects
            .select_related('cliente', 'vendedor')
            .prefetch_related('itens__peca__produto__liga', 'itens__peca__fotos')
        )
        return get_object_or_404(qs, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        venda = self.object
        ja_na_venda = list(venda.itens.values_list('peca_id', flat=True))
        ctx['pecas_json']    = _pecas_disponiveis_json(excluir_ids=ja_na_venda)
        ctx['tipos_produto'] = TipoProduto.objects.order_by('nome')
        ctx['desconto_form'] = DescontoForm(initial={'tipo': 'valor', 'valor': venda.desconto_total})
        return ctx


class VendaCreateView(LoginRequiredMixin, CreateView):
    model         = Venda
    form_class    = VendaForm
    template_name = 'vendas/venda_form.html'

    def get_success_url(self):
        return reverse_lazy('vendas:venda_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.vendedor = self.request.user
        messages.success(self.request, 'Venda criada. Adicione as peças abaixo.')
        return super().form_valid(form)


class VendaUpdateView(LoginRequiredMixin, UpdateView):
    model         = Venda
    form_class    = VendaForm
    template_name = 'vendas/venda_form.html'

    def get_success_url(self):
        return reverse_lazy('vendas:venda_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Venda atualizada.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Desconto — editado via POST na tela de detalhe da venda
# ---------------------------------------------------------------------------

@login_required
def venda_desconto_atualizar(request, pk):
    venda = get_object_or_404(Venda, pk=pk)

    if venda.status == Venda.Status.CANCELADA:
        messages.error(request, 'Não é possível alterar o desconto de uma venda cancelada.')
        return redirect('vendas:venda_detail', pk=pk)

    if request.method != 'POST':
        return redirect('vendas:venda_detail', pk=pk)

    form = DescontoForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Desconto inválido.')
        return redirect('vendas:venda_detail', pk=pk)

    valor = form.cleaned_data['valor']
    if form.cleaned_data['tipo'] == 'percentual':
        subtotal = sum((item.subtotal for item in venda.itens.all()), Decimal('0.00'))
        desconto = (subtotal * valor / Decimal('100')).quantize(Decimal('0.01'))
    else:
        desconto = valor

    venda.desconto_total = desconto
    venda.save(update_fields=['desconto_total'])
    venda.recalcular_total()
    messages.success(request, 'Desconto atualizado.')
    return redirect('vendas:venda_detail', pk=pk)


# ---------------------------------------------------------------------------
# Item de Venda — adicionado via POST na tela de detalhe da venda
# ---------------------------------------------------------------------------

@login_required
def item_adicionar(request, venda_pk):
    venda = get_object_or_404(Venda, pk=venda_pk)

    if venda.status == Venda.Status.CANCELADA:
        messages.error(request, 'Não é possível adicionar itens a uma venda cancelada.')
        return redirect('vendas:venda_detail', pk=venda_pk)

    if request.method != 'POST':
        return redirect('vendas:venda_detail', pk=venda_pk)

    form = ItemVendaForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Dados inválidos.')
        return redirect('vendas:venda_detail', pk=venda_pk)

    peca = get_object_or_404(Peca, pk=form.cleaned_data['peca_id'], status=Peca.Status.DISPONIVEL)

    if ItemVenda.objects.filter(venda=venda, peca=peca).exists():
        messages.error(request, f'A peça {peca.codigo} já está nesta venda.')
        return redirect('vendas:venda_detail', pk=venda_pk)

    with transaction.atomic():
        ItemVenda.objects.create(venda=venda, peca=peca, preco_unitario_pago=peca.preco_sugerido)
        peca.status = Peca.Status.VENDIDA
        peca.save(update_fields=['status'])
        MovimentacaoEstoque.objects.create(
            produto=peca.produto,
            peca=peca,
            tipo=MovimentacaoEstoque.Tipo.SAIDA,
            quantidade=1,
            referencia_venda=venda,
            responsavel=request.user,
            observacoes=f'Venda #{venda.pk}',
        )
        venda.recalcular_total()

    messages.success(request, f'Peça {peca.codigo} adicionada à venda.')
    return redirect('vendas:venda_detail', pk=venda_pk)


@login_required
def venda_cancelar(request, pk):
    venda = get_object_or_404(Venda, pk=pk)

    if venda.status == Venda.Status.CANCELADA:
        messages.warning(request, 'Venda já está cancelada.')
        return redirect('vendas:venda_list')

    if request.method == 'POST':
        with transaction.atomic():
            for item in venda.itens.select_related('peca'):
                peca = item.peca
                MovimentacaoEstoque.objects.create(
                    produto=peca.produto,
                    peca=peca,
                    tipo=MovimentacaoEstoque.Tipo.DEVOLUCAO,
                    quantidade=1,
                    referencia_venda=venda,
                    responsavel=request.user,
                    observacoes=f'Cancelamento — Venda #{venda.pk}',
                )
                peca.status = Peca.Status.DISPONIVEL
                peca.save(update_fields=['status'])
            venda.status = Venda.Status.CANCELADA
            venda.save(update_fields=['status'])

        messages.success(request, f'Venda #{venda.pk} cancelada e peças devolvidas ao estoque.')

    return redirect('vendas:venda_list')


@login_required
def item_remover(request, venda_pk, item_pk):
    venda = get_object_or_404(Venda, pk=venda_pk)
    item  = get_object_or_404(ItemVenda, pk=item_pk, venda=venda)

    if request.method == 'POST':
        peca = item.peca
        with transaction.atomic():
            MovimentacaoEstoque.objects.create(
                produto=peca.produto,
                peca=peca,
                tipo=MovimentacaoEstoque.Tipo.DEVOLUCAO,
                quantidade=1,
                referencia_venda=venda,
                responsavel=request.user,
                observacoes=f'Remoção de item — Venda #{venda.pk}',
            )
            peca.status = Peca.Status.DISPONIVEL
            peca.save(update_fields=['status'])
            item.delete()
            venda.recalcular_total()

        messages.success(request, f'Peça {peca.codigo} removida e devolvida ao estoque.')

    return redirect('vendas:venda_detail', pk=venda_pk)
