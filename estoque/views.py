from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from catalogo.models import Peca, Produto, TipoProduto

from .forms import (
    ItemLotePesoForm,
    LoteForm,
    LoteItemEntradaForm,
    LoteItemSaidaForm,
    MovimentacaoEntradaForm,
    MovimentacaoSaidaForm,
)
from .models import ItemLote, LoteMovimentacao, MovimentacaoEstoque


# ── Movimentação Avulsa ───────────────────────────────────────────────────────

class MovimentacaoListView(LoginRequiredMixin, ListView):
    model               = MovimentacaoEstoque
    template_name       = 'estoque/movimentacao_list.html'
    context_object_name = 'movimentacoes'
    paginate_by         = 30

    def get_queryset(self):
        qs = MovimentacaoEstoque.objects.select_related(
            'produto__liga', 'peca', 'responsavel', 'referencia_venda', 'lote'
        )
        if produto_id := self.request.GET.get('produto'):
            qs = qs.filter(produto_id=produto_id)
        if tipo := self.request.GET.get('tipo'):
            qs = qs.filter(tipo=tipo)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tipos']      = MovimentacaoEstoque.Tipo.choices
        ctx['tipo_atual'] = self.request.GET.get('tipo', '')
        return ctx


def movimentacao_entrada(request):
    if not request.user.is_authenticated:
        return redirect('login')

    form = MovimentacaoEntradaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        produto           = form.cleaned_data['produto']
        quantidade        = form.cleaned_data['quantidade']
        peso_padrao       = form.cleaned_data['peso_padrao']
        custo_mao_de_obra = form.cleaned_data['custo_mao_de_obra']
        fornecedor        = form.cleaned_data.get('fornecedor')
        obs               = form.cleaned_data.get('observacoes', '')

        with transaction.atomic():
            for _ in range(quantidade):
                peca = Peca.objects.create(
                    produto=produto,
                    status=Peca.Status.DISPONIVEL,
                    peso_gramas=peso_padrao,
                    custo_mao_de_obra=custo_mao_de_obra,
                )
                MovimentacaoEstoque.objects.create(
                    produto=produto,
                    peca=peca,
                    tipo=MovimentacaoEstoque.Tipo.ENTRADA,
                    quantidade=1,
                    fornecedor=fornecedor,
                    responsavel=request.user,
                    observacoes=obs,
                )

        messages.success(request, f'{quantidade} peça(s) de "{produto}" adicionadas ao estoque.')
        return redirect('estoque:movimentacao_list')

    return render(request, 'estoque/movimentacao_entrada_form.html', {'form': form})


def movimentacao_saida(request):
    if not request.user.is_authenticated:
        return redirect('login')

    tipos_produto = TipoProduto.objects.order_by('nome')

    if request.method == 'POST':
        form = MovimentacaoSaidaForm(request.POST)
        if form.is_valid():
            peca    = get_object_or_404(Peca, pk=form.cleaned_data['peca_id'])
            tipo    = form.cleaned_data['tipo']
            cliente = form.cleaned_data.get('cliente')
            obs     = form.cleaned_data.get('observacoes', '')

            novo_status = (
                Peca.Status.DISPONIVEL
                if tipo in (MovimentacaoEstoque.Tipo.AJUSTE_POS, MovimentacaoEstoque.Tipo.DEVOLUCAO)
                else Peca.Status.RETIRADA
            )

            with transaction.atomic():
                MovimentacaoEstoque.objects.create(
                    produto=peca.produto,
                    peca=peca,
                    tipo=tipo,
                    quantidade=1,
                    cliente=cliente,
                    responsavel=request.user,
                    observacoes=obs,
                )
                peca.status = novo_status
                peca.save(update_fields=['status'])

            messages.success(request, f'Movimentação da peça {peca.codigo} registrada.')
            return redirect('estoque:movimentacao_list')
    else:
        form = MovimentacaoSaidaForm()

    return render(request, 'estoque/movimentacao_saida_form.html', {
        'form':          form,
        'pecas_json':    _pecas_disponiveis_json(),
        'tipos_produto': tipos_produto,
    })


# ── Lotes ─────────────────────────────────────────────────────────────────────

class LoteListView(LoginRequiredMixin, ListView):
    model               = LoteMovimentacao
    template_name       = 'estoque/lote_list.html'
    context_object_name = 'lotes'
    paginate_by         = 20

    def get_queryset(self):
        return LoteMovimentacao.objects.select_related('responsavel', 'fornecedor', 'cliente')


class LoteCreateView(LoginRequiredMixin, CreateView):
    model         = LoteMovimentacao
    form_class    = LoteForm
    template_name = 'estoque/lote_form.html'

    def get_initial(self):
        initial = super().get_initial()
        tipo = self.request.GET.get('tipo')
        if tipo in dict(LoteMovimentacao.Tipo.choices):
            initial['tipo'] = tipo
        return initial

    def form_valid(self, form):
        form.instance.responsavel = self.request.user
        messages.success(self.request, 'Lote criado. Adicione os itens abaixo.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('estoque:lote_detail', kwargs={'pk': self.object.pk})


class LoteDetailView(LoginRequiredMixin, DetailView):
    model               = LoteMovimentacao
    template_name       = 'estoque/lote_detail.html'
    context_object_name = 'lote'

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        lote = self.object

        if lote.tipo == LoteMovimentacao.Tipo.ENTRADA:
            ctx['form']          = LoteItemEntradaForm(lote=lote)
            ctx['tipos_produto'] = TipoProduto.objects.order_by('nome')
            ctx['produtos_json'] = _produtos_json()
            ctx['itens'] = (
                lote.itens
                .select_related('produto__liga', 'produto__tipo')
                .filter(peca__isnull=True)
            )
            ctx['total_pecas'] = sum(i.quantidade for i in ctx['itens'])
        else:
            itens = (
                lote.itens
                .select_related('peca__produto__liga', 'peca__produto__tipo')
                .filter(produto__isnull=True)
                .prefetch_related('peca__fotos')
            )
            ctx['form']          = LoteItemSaidaForm()
            ctx['itens']         = itens
            ctx['pecas_json']    = _pecas_disponiveis_json(
                excluir_ids=[i.peca_id for i in itens]
            )
            ctx['tipos_produto'] = TipoProduto.objects.order_by('nome')

        return ctx


def lote_item_adicionar(request, lote_pk):
    lote = get_object_or_404(LoteMovimentacao, pk=lote_pk)

    if lote.finalizado:
        messages.error(request, 'Este lote já foi finalizado.')
        return redirect('estoque:lote_detail', pk=lote_pk)

    if request.method != 'POST':
        return redirect('estoque:lote_detail', pk=lote_pk)

    if lote.tipo == LoteMovimentacao.Tipo.ENTRADA:
        form = LoteItemEntradaForm(lote=lote, data=request.POST)
        if form.is_valid():
            produto    = form.cleaned_data['produto']
            quantidade = form.cleaned_data['quantidade']
            # Uma linha por peça (não agrupada), para permitir ajustar peso/custo individualmente.
            ItemLote.objects.bulk_create([
                ItemLote(
                    lote=lote,
                    produto=produto,
                    quantidade=1,
                    peso_padrao=form.cleaned_data['peso_padrao'],
                    custo_mao_de_obra=form.cleaned_data['custo_mao_de_obra'],
                )
                for _ in range(quantidade)
            ])
            messages.success(request, f'{quantidade}x "{produto}" adicionado(s).')
            return redirect('estoque:lote_detail', pk=lote_pk)

        itens = lote.itens.select_related('produto__liga', 'produto__tipo').filter(peca__isnull=True)
        return render(request, 'estoque/lote_detail.html', {
            'lote': lote, 'form': form, 'itens': itens,
            'tipos_produto':  TipoProduto.objects.order_by('nome'),
            'produtos_json':  _produtos_json(),
            'total_pecas':    sum(i.quantidade for i in itens),
        })

    else:  # SAÍDA
        peca_id = request.POST.get('peca_id')
        peca    = get_object_or_404(Peca, pk=peca_id, status=Peca.Status.DISPONIVEL)

        if ItemLote.objects.filter(lote=lote, peca=peca).exists():
            messages.error(request, f'A peça {peca.codigo} já está neste lote.')
        else:
            ItemLote.objects.create(lote=lote, peca=peca)
            messages.success(request, f'Peça {peca.codigo} adicionada.')

        return redirect('estoque:lote_detail', pk=lote_pk)


def lote_item_remover(request, lote_pk, item_pk):
    lote = get_object_or_404(LoteMovimentacao, pk=lote_pk)
    item = get_object_or_404(ItemLote, pk=item_pk, lote=lote)

    if lote.finalizado:
        messages.error(request, 'Lote já finalizado.')
        return redirect('estoque:lote_detail', pk=lote_pk)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item removido do lote.')

    return redirect('estoque:lote_detail', pk=lote_pk)


def lote_item_atualizar(request, lote_pk, item_pk):
    lote = get_object_or_404(LoteMovimentacao, pk=lote_pk)
    item = get_object_or_404(ItemLote, pk=item_pk, lote=lote)

    if lote.finalizado:
        messages.error(request, 'Lote já finalizado.')
        return redirect('estoque:lote_detail', pk=lote_pk)

    if request.method != 'POST':
        return redirect('estoque:lote_detail', pk=lote_pk)

    form = ItemLotePesoForm(request.POST, instance=item)
    if not form.is_valid():
        messages.error(request, 'Peso ou custo inválido.')
        return redirect('estoque:lote_detail', pk=lote_pk)

    form.save()
    messages.success(request, 'Item atualizado.')
    return redirect('estoque:lote_detail', pk=lote_pk)


def lote_cancelar(request, lote_pk):
    lote = get_object_or_404(LoteMovimentacao, pk=lote_pk)

    if lote.finalizado:
        messages.error(request, 'Não é possível cancelar um lote já finalizado.')
        return redirect('estoque:lote_detail', pk=lote_pk)

    if request.method == 'POST':
        num = lote.pk
        lote.delete()
        messages.success(request, f'Lote #{num} cancelado.')
        return redirect('estoque:lote_list')

    return redirect('estoque:lote_detail', pk=lote_pk)


def lote_finalizar(request, lote_pk):
    lote = get_object_or_404(LoteMovimentacao, pk=lote_pk)

    if lote.finalizado:
        messages.warning(request, 'Lote já finalizado.')
        return redirect('estoque:lote_list')

    if not lote.itens.exists():
        messages.error(request, 'Adicione ao menos um item antes de finalizar.')
        return redirect('estoque:lote_detail', pk=lote_pk)

    if request.method == 'POST':
        obs_base = f'Lote #{lote.pk}' + (f' — {lote.observacoes}' if lote.observacoes else '')

        with transaction.atomic():
            if lote.tipo == LoteMovimentacao.Tipo.ENTRADA:
                _finalizar_entrada(lote, obs_base, request.user)
            else:
                _finalizar_saida(lote, obs_base, request.user)
            lote.finalizado = True
            lote.save(update_fields=['finalizado'])

        messages.success(request, f'Lote #{lote.pk} finalizado.')
        return redirect('estoque:lote_list')

    return redirect('estoque:lote_detail', pk=lote_pk)


# ── helpers ───────────────────────────────────────────────────────────────────

def _finalizar_entrada(lote, obs_base, responsavel):
    for item in lote.itens.select_related('produto').filter(peca__isnull=True):
        for _ in range(item.quantidade):
            peca = Peca.objects.create(
                produto=item.produto,
                status=Peca.Status.DISPONIVEL,
                peso_gramas=item.peso_padrao,
                custo_mao_de_obra=item.custo_mao_de_obra,
            )
            MovimentacaoEstoque.objects.create(
                produto=item.produto,
                peca=peca,
                tipo=MovimentacaoEstoque.Tipo.ENTRADA,
                quantidade=1,
                fornecedor=lote.fornecedor,
                lote=lote,
                responsavel=responsavel,
                observacoes=obs_base,
            )


def _finalizar_saida(lote, obs_base, responsavel):
    for item in lote.itens.select_related('peca__produto').filter(produto__isnull=True):
        peca = item.peca
        MovimentacaoEstoque.objects.create(
            produto=peca.produto,
            peca=peca,
            tipo=MovimentacaoEstoque.Tipo.SAIDA,
            quantidade=1,
            cliente=lote.cliente,
            lote=lote,
            responsavel=responsavel,
            observacoes=obs_base,
        )
        peca.status = Peca.Status.RETIRADA
        peca.save(update_fields=['status'])


def _pecas_disponiveis_json(excluir_ids=None):
    qs = (
        Peca.objects
        .filter(status=Peca.Status.DISPONIVEL)
        .select_related('produto__tipo', 'produto__liga__metal')
        .prefetch_related('fotos')
        .order_by('produto__nome', 'codigo')
    )
    if excluir_ids:
        qs = qs.exclude(pk__in=excluir_ids)

    resultado = []
    for p in qs:
        foto = p.foto_principal
        resultado.append({
            'id':       p.pk,
            'codigo':   p.codigo,
            'nome':     p.produto.nome,
            'tipo_id':  p.produto.tipo_id or 0,
            'tipo':     str(p.produto.tipo) if p.produto.tipo else '',
            'liga':     p.produto.liga.nome if p.produto.liga else '',
            'peso':     str(p.peso_gramas),
            'preco':    str(p.preco_sugerido),
            'foto_url': foto.imagem.url if foto else None,
        })
    return resultado


def _produtos_json():
    produtos = Produto.objects.select_related('tipo', 'liga__metal').order_by('nome')
    return [
        {
            'id':      p.pk,
            'nome':    p.nome,
            'tipo_id': p.tipo_id or 0,
            'tipo':    str(p.tipo) if p.tipo else '',
            'liga':    p.liga.nome if p.liga else '',
        }
        for p in produtos
    ]
