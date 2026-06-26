from datetime import date, timedelta

from django.db.models import Count, DecimalField, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import redirect, render

from catalogo.models import Peca, Produto
from estoque.models import MovimentacaoEstoque as ME
from usuarios.decorators import gerente_required
from vendas.models import ItemVenda, Venda


def _parse_periodo(request):
    hoje = date.today()
    try:
        inicio = date.fromisoformat(request.GET.get('inicio', ''))
    except ValueError:
        inicio = hoje.replace(day=1)
    try:
        fim = date.fromisoformat(request.GET.get('fim', ''))
    except ValueError:
        fim = hoje
    return inicio, fim


@gerente_required
def vendas(request):
    inicio, fim = _parse_periodo(request)

    qs = Venda.objects.filter(
        data_venda__date__gte=inicio,
        data_venda__date__lte=fim,
        status=Venda.Status.CONFIRMADA,
    ).select_related('cliente', 'vendedor').prefetch_related('itens')

    totais = qs.aggregate(
        num_vendas=Count('id'),
        valor_total=Sum('valor_total'),
    )
    num_vendas  = totais['num_vendas'] or 0
    valor_total = totais['valor_total'] or 0
    ticket_medio = (valor_total / num_vendas) if num_vendas else 0

    por_vendedor = (
        qs.values('vendedor__first_name', 'vendedor__last_name', 'vendedor__username')
        .annotate(qtd=Count('id'), total=Sum('valor_total'))
        .order_by('-total')
    )

    ctx = {
        'inicio':       inicio,
        'fim':          fim,
        'vendas':       qs,
        'num_vendas':   num_vendas,
        'valor_total':  valor_total,
        'ticket_medio': round(ticket_medio, 2),
        'por_vendedor': por_vendedor,
    }
    return render(request, 'relatorios/vendas.html', ctx)


@gerente_required
def giro(request):
    inicio, fim = _parse_periodo(request)

    saidas = (
        ME.objects.filter(
            tipo__in=[ME.Tipo.SAIDA, ME.Tipo.AJUSTE_NEG],
            data_hora__date__gte=inicio,
            data_hora__date__lte=fim,
        )
        .values('produto_id')
        .annotate(total_saida=Sum('quantidade'))
    )
    saidas_map = {s['produto_id']: s['total_saida'] for s in saidas}

    produtos = Produto.objects.select_related('liga', 'tipo').annotate(
        estoque_calc=Count(
            'pecas',
            filter=Q(pecas__status=Peca.Status.DISPONIVEL),
        )
    ).order_by('tipo__nome', 'nome')

    for produto in produtos:
        produto.saida_periodo = saidas_map.get(produto.pk, 0)

    por_liga = {}
    por_tipo = {}
    for produto in produtos:
        liga = str(produto.liga) if produto.liga else 'Sem liga'
        if liga not in por_liga:
            por_liga[liga] = {'saida': 0, 'estoque': 0}
        por_liga[liga]['saida']   += produto.saida_periodo
        por_liga[liga]['estoque'] += produto.estoque_calc

        tipo = produto.tipo.nome if produto.tipo else 'Sem tipo'
        if tipo not in por_tipo:
            por_tipo[tipo] = {'saida': 0, 'estoque': 0}
        por_tipo[tipo]['saida']   += produto.saida_periodo
        por_tipo[tipo]['estoque'] += produto.estoque_calc

    por_liga = sorted(por_liga.items(), key=lambda x: x[1]['saida'], reverse=True)
    por_tipo = sorted(por_tipo.items(), key=lambda x: x[1]['saida'], reverse=True)
    produtos_ordenados = sorted(produtos, key=lambda p: p.saida_periodo, reverse=True)

    ctx = {
        'inicio':    inicio,
        'fim':       fim,
        'produtos':  produtos_ordenados,
        'por_liga':  por_liga,
        'por_tipo':  por_tipo,
    }
    return render(request, 'relatorios/giro.html', ctx)
