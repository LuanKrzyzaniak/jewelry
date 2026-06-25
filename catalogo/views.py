from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from usuarios.mixins import GerenteRequiredMixin

from .forms import LigaForm, PecaForm, PrecoLigaForm, ProdutoForm, TipoProdutoForm
from .models import CotacaoMetal, FotoPeca, Liga, Metal, Peca, PrecoLiga, Produto, TipoProduto


class MetalListView(GerenteRequiredMixin, ListView):
    model               = Metal
    template_name       = 'catalogo/metal_list.html'
    context_object_name = 'metais'



class LigaListView(LoginRequiredMixin, ListView):
    model               = Liga
    template_name       = 'catalogo/liga_list.html'
    context_object_name = 'ligas'
    queryset            = Liga.objects.select_related('metal').prefetch_related('precos')


class LigaCreateView(GerenteRequiredMixin, CreateView):
    model         = Liga
    form_class    = LigaForm
    template_name = 'catalogo/liga_form.html'
    success_url   = reverse_lazy('catalogo:liga_list')

    def form_valid(self, form):
        messages.success(self.request, 'Liga cadastrada com sucesso.')
        return super().form_valid(form)


class LigaUpdateView(GerenteRequiredMixin, UpdateView):
    model         = Liga
    form_class    = LigaForm
    template_name = 'catalogo/liga_form.html'
    success_url   = reverse_lazy('catalogo:liga_list')

    def form_valid(self, form):
        messages.success(self.request, 'Liga atualizada.')
        return super().form_valid(form)


def preco_liga_definir(request, liga_pk):
    liga = get_object_or_404(Liga, pk=liga_pk)

    if not request.user.is_gerente:
        messages.error(request, 'Acesso restrito a gerentes.')
        return redirect('catalogo:liga_list')

    form = PrecoLigaForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        hoje = timezone.localdate()
        PrecoLiga.objects.update_or_create(
            liga=liga,
            vigente_desde=hoje,
            defaults={
                'preco_por_grama': form.cleaned_data['preco_por_grama'],
                'definido_por':    request.user,
            },
        )
        messages.success(request, f'Preço de {liga} atualizado.')
        return redirect('catalogo:liga_list')

    historico = liga.precos.order_by('-vigente_desde')[:10]
    return render(request, 'catalogo/preco_liga_form.html', {
        'liga':      liga,
        'form':      form,
        'historico': historico,
    })


def _anotar_estoque(qs):
    # Estoque = nº de peças disponíveis (mesma definição de Produto.estoque_atual),
    # nunca negativo — somar movimentações fica negativo quando há peças
    # vendidas/ajustadas sem uma ENTRADA correspondente.
    return qs.annotate(
        estoque_calc=Count(
            'pecas',
            filter=Q(pecas__status=Peca.Status.DISPONIVEL),
        )
    )


class ProdutoListView(LoginRequiredMixin, ListView):
    model               = Produto
    template_name       = 'catalogo/produto_list.html'
    context_object_name = 'produtos'
    paginate_by         = 24

    def get_queryset(self):
        qs = Produto.objects.select_related('liga__metal', 'tipo')
        qs = _anotar_estoque(qs)

        if busca := self.request.GET.get('q'):
            qs = qs.filter(nome__icontains=busca)

        if tipo_id := self.request.GET.get('tipo'):
            qs = qs.filter(tipo_id=tipo_id)

        if liga_ids := self.request.GET.getlist('liga'):
            qs = qs.filter(liga_id__in=liga_ids)

        if self.request.GET.get('sem_estoque'):
            qs = qs.filter(estoque_calc=0)

        return qs.order_by('nome')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['busca']             = self.request.GET.get('q', '')
        ctx['sem_estoque']       = self.request.GET.get('sem_estoque', '')
        ctx['tipo_atual']        = self.request.GET.get('tipo', '')
        ctx['todos_tipos']       = TipoProduto.objects.order_by('nome')
        ctx['ligas_selecionadas'] = self.request.GET.getlist('liga')
        ctx['todas_ligas']       = Liga.objects.select_related('metal').order_by('nome')
        return ctx


class ProdutoDetailView(LoginRequiredMixin, DetailView):
    model               = Produto
    template_name       = 'catalogo/produto_detail.html'
    context_object_name = 'produto'
    queryset            = Produto.objects.select_related('liga__metal', 'tipo')


class ProdutoCreateView(GerenteRequiredMixin, CreateView):
    model         = Produto
    form_class    = ProdutoForm
    template_name = 'catalogo/produto_form.html'
    success_url   = reverse_lazy('catalogo:produto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produto cadastrado com sucesso.')
        return super().form_valid(form)


class ProdutoUpdateView(GerenteRequiredMixin, UpdateView):
    model         = Produto
    form_class    = ProdutoForm
    template_name = 'catalogo/produto_form.html'

    def get_success_url(self):
        return reverse_lazy('catalogo:produto_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Produto atualizado.')
        return super().form_valid(form)


class ProdutoDeleteView(GerenteRequiredMixin, DeleteView):
    model         = Produto
    template_name = 'catalogo/produto_confirm_delete.html'
    success_url   = reverse_lazy('catalogo:produto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Produto removido.')
        return super().form_valid(form)


class TipoProdutoListView(GerenteRequiredMixin, ListView):
    model               = TipoProduto
    template_name       = 'catalogo/tipo_produto_list.html'
    context_object_name = 'tipos'


class TipoProdutoCreateView(GerenteRequiredMixin, CreateView):
    model         = TipoProduto
    form_class    = TipoProdutoForm
    template_name = 'catalogo/tipo_produto_form.html'
    success_url   = reverse_lazy('catalogo:tipo_produto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tipo cadastrado.')
        return super().form_valid(form)


class TipoProdutoUpdateView(GerenteRequiredMixin, UpdateView):
    model         = TipoProduto
    form_class    = TipoProdutoForm
    template_name = 'catalogo/tipo_produto_form.html'
    success_url   = reverse_lazy('catalogo:tipo_produto_list')

    def form_valid(self, form):
        messages.success(self.request, 'Tipo atualizado.')
        return super().form_valid(form)


class CotacaoListView(LoginRequiredMixin, ListView):
    model               = CotacaoMetal
    template_name       = 'catalogo/cotacao_list.html'
    context_object_name = 'cotacoes'
    queryset            = CotacaoMetal.objects.select_related('metal').order_by('-data')[:60]


# ── Peças ────────────────────────────────────────────────────────────────────

class PecaListView(LoginRequiredMixin, ListView):
    model               = Peca
    template_name       = 'catalogo/peca_list.html'
    context_object_name = 'pecas'
    paginate_by         = 24

    def get_queryset(self):
        qs = Peca.objects.select_related('produto__tipo', 'produto__liga__metal').prefetch_related('fotos')

        if busca := self.request.GET.get('q'):
            qs = qs.filter(Q(codigo__icontains=busca) | Q(produto__nome__icontains=busca))

        # Default para Disponível quando nenhum status é explicitamente escolhido.
        # Usar status='' na URL para ver todos.
        status = self.request.GET.get('status', None)
        if status is None:
            qs = qs.filter(status=Peca.Status.DISPONIVEL)
        elif status:
            qs = qs.filter(status=status)
        # status == '' → sem filtro (mostrar todos)

        if tipo_id := self.request.GET.get('tipo'):
            qs = qs.filter(produto__tipo_id=tipo_id)

        if liga_ids := self.request.GET.getlist('liga'):
            qs = qs.filter(produto__liga_id__in=liga_ids)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['busca']              = self.request.GET.get('q', '')
        # None (sem param) → default DIS; '' → todos; valor → filtrado
        status_param = self.request.GET.get('status', None)
        ctx['status_atual']       = Peca.Status.DISPONIVEL if status_param is None else status_param
        ctx['tipo_atual']         = self.request.GET.get('tipo', '')
        ctx['ligas_selecionadas'] = self.request.GET.getlist('liga')
        ctx['todos_tipos']        = TipoProduto.objects.order_by('nome')
        ctx['todas_ligas']        = Liga.objects.select_related('metal').order_by('nome')
        ctx['status_choices']     = Peca.Status.choices
        return ctx


class PecaCreateView(GerenteRequiredMixin, CreateView):
    model         = Peca
    form_class    = PecaForm
    template_name = 'catalogo/peca_form.html'

    def get_success_url(self):
        return reverse_lazy('catalogo:peca_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Peça cadastrada com sucesso.')
        return super().form_valid(form)


class PecaDetailView(LoginRequiredMixin, DetailView):
    model               = Peca
    template_name       = 'catalogo/peca_detail.html'
    context_object_name = 'peca'
    queryset            = Peca.objects.select_related('produto__tipo', 'produto__liga__metal').prefetch_related('fotos')


class PecaUpdateView(GerenteRequiredMixin, UpdateView):
    model         = Peca
    form_class    = PecaForm
    template_name = 'catalogo/peca_form.html'

    def get_success_url(self):
        return reverse_lazy('catalogo:peca_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Peça atualizada.')
        return super().form_valid(form)


class PecaDeleteView(GerenteRequiredMixin, DeleteView):
    model         = Peca
    template_name = 'catalogo/peca_confirm_delete.html'
    success_url   = reverse_lazy('catalogo:peca_list')

    def form_valid(self, form):
        messages.success(self.request, 'Peça removida.')
        return super().form_valid(form)


def peca_foto_upload(request, pk):
    peca = get_object_or_404(Peca, pk=pk)

    if not request.user.is_gerente:
        messages.error(request, 'Acesso restrito a gerentes.')
        return redirect('catalogo:peca_detail', pk=pk)

    if request.method == 'POST':
        arquivos = request.FILES.getlist('imagens')
        if not arquivos:
            messages.error(request, 'Nenhuma imagem selecionada.')
        else:
            for arquivo in arquivos:
                FotoPeca.objects.create(peca=peca, imagem=arquivo)
            messages.success(request, f'{len(arquivos)} foto(s) adicionada(s).')

    return redirect('catalogo:peca_detail', pk=pk)


def peca_foto_delete(request, pk, foto_pk):
    peca = get_object_or_404(Peca, pk=pk)
    foto = get_object_or_404(FotoPeca, pk=foto_pk, peca=peca)

    if not request.user.is_gerente:
        messages.error(request, 'Acesso restrito a gerentes.')
        return redirect('catalogo:peca_detail', pk=pk)

    if request.method == 'POST':
        foto.imagem.delete(save=False)
        foto.delete()
        messages.success(request, 'Foto removida.')

    return redirect('catalogo:peca_detail', pk=pk)


def peca_catalogo(request):
    ids_raw = request.GET.get('ids', '')
    ids     = [int(i) for i in ids_raw.split(',') if i.strip().isdigit()]
    pecas   = (
        Peca.objects
        .filter(pk__in=ids)
        .select_related('produto__tipo', 'produto__liga__metal')
        .prefetch_related('fotos')
    )
    # Mantém a ordem da seleção
    pecas_ordenadas = sorted(pecas, key=lambda p: ids.index(p.pk) if p.pk in ids else 0)
    return render(request, 'catalogo/peca_catalogo.html', {'pecas': pecas_ordenadas})


def peca_foto_set_principal(request, pk, foto_pk):
    peca = get_object_or_404(Peca, pk=pk)
    foto = get_object_or_404(FotoPeca, pk=foto_pk, peca=peca)

    if not request.user.is_gerente:
        messages.error(request, 'Acesso restrito a gerentes.')
        return redirect('catalogo:peca_detail', pk=pk)

    if request.method == 'POST':
        peca.fotos.update(principal=False)
        foto.principal = True
        foto.save(update_fields=['principal'])

    return redirect('catalogo:peca_detail', pk=pk)
