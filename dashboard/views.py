import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from catalogo.models import CotacaoMetal, Metal, Produto
from estoque.models import LoteMovimentacao, MovimentacaoEstoque as ME
from vendas.models import ItemVenda, Venda


@login_required
def index(request):
    hoje        = timezone.localdate()
    inicio_mes  = hoje.replace(day=1)
    inicio_30d  = hoje - timedelta(days=29)

    # Estoque por produto
    produtos_qs = Produto.objects.annotate(
        estoque_calc=Sum(
            'movimentacoes__quantidade',
            filter=Q(movimentacoes__tipo__in=[ME.Tipo.ENTRADA, ME.Tipo.AJUSTE_POS, ME.Tipo.DEVOLUCAO]),
            default=0,
        ) - Sum(
            'movimentacoes__quantidade',
            filter=Q(movimentacoes__tipo__in=[ME.Tipo.SAIDA, ME.Tipo.AJUSTE_NEG]),
            default=0,
        )
    )
    total_em_estoque = produtos_qs.filter(estoque_calc__gt=0).count()
    sem_estoque      = list(produtos_qs.filter(estoque_calc=0).select_related('liga', 'tipo').order_by('nome'))

    # Vendas hoje
    qs_hoje          = Venda.objects.filter(status=Venda.Status.CONFIRMADA, data_venda__date=hoje)
    vendas_hoje_agg  = qs_hoje.aggregate(total=Sum('valor_total'), count=Count('id'))
    vendas_hoje      = vendas_hoje_agg['total'] or 0
    num_vendas_hoje  = vendas_hoje_agg['count'] or 0

    # Vendas do mês
    qs_mes          = Venda.objects.filter(status=Venda.Status.CONFIRMADA, data_venda__date__gte=inicio_mes)
    vendas_mes_agg  = qs_mes.aggregate(total=Sum('valor_total'), count=Count('id'))
    vendas_mes      = vendas_mes_agg['total'] or 0
    num_vendas_mes  = vendas_mes_agg['count'] or 0
    ticket_medio    = round(vendas_mes / num_vendas_mes, 2) if num_vendas_mes else 0

    # Cotações mais recentes por metal
    cotacoes = {}
    for metal in Metal.objects.order_by('nome'):
        cot = CotacaoMetal.objects.filter(metal=metal).order_by('-data').first()
        if cot:
            cotacoes[metal.nome] = cot

    # Gráfico: vendas por dia nos últimos 30 dias
    vendas_por_dia = (
        Venda.objects.filter(
            status=Venda.Status.CONFIRMADA,
            data_venda__date__gte=inicio_30d,
            data_venda__date__lte=hoje,
        )
        .values('data_venda__date')
        .annotate(total=Sum('valor_total'))
        .order_by('data_venda__date')
    )
    mapa_dia = {str(v['data_venda__date']): float(v['total']) for v in vendas_por_dia}
    labels_30d, data_30d = [], []
    for i in range(30):
        d = inicio_30d + timedelta(days=i)
        labels_30d.append(d.strftime('%d/%m'))
        data_30d.append(mapa_dia.get(str(d), 0))

    # Top 5 produtos mais vendidos no mês
    top_produtos = (
        ItemVenda.objects
        .filter(venda__status=Venda.Status.CONFIRMADA, venda__data_venda__date__gte=inicio_mes)
        .values('peca__produto__nome')
        .annotate(qtd=Count('id'))
        .order_by('-qtd')[:5]
    )

    # Últimas 5 vendas confirmadas
    ultimas_vendas = (
        Venda.objects.filter(status=Venda.Status.CONFIRMADA)
        .select_related('cliente', 'vendedor')
        .order_by('-data_venda')[:5]
    )

    # Lotes em aberto
    lotes_abertos = (
        LoteMovimentacao.objects.filter(finalizado=False)
        .select_related('responsavel', 'fornecedor', 'cliente')
        .order_by('-criado_em')[:5]
    )

    ctx = {
        'hoje':              hoje,
        'total_em_estoque':  total_em_estoque,
        'sem_estoque':       sem_estoque,
        'vendas_hoje':       vendas_hoje,
        'num_vendas_hoje':   num_vendas_hoje,
        'vendas_mes':        vendas_mes,
        'num_vendas_mes':    num_vendas_mes,
        'ticket_medio':      ticket_medio,
        'cotacoes':          cotacoes,
        'labels_30d':        json.dumps(labels_30d),
        'data_30d':          json.dumps(data_30d),
        'top_produtos':      top_produtos,
        'ultimas_vendas':    ultimas_vendas,
        'lotes_abertos':     lotes_abertos,
    }
    return render(request, 'dashboard/index.html', ctx)
