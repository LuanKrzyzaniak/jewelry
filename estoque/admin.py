from django.contrib import admin

from .models import ItemLote, LoteMovimentacao, MovimentacaoEstoque


class ItemLoteInline(admin.TabularInline):
    model = ItemLote
    extra = 0


@admin.register(LoteMovimentacao)
class LoteMovimentacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'fornecedor', 'cliente', 'responsavel', 'finalizado', 'criado_em', 'total_itens')
    list_filter = ('tipo', 'finalizado')
    search_fields = ('observacoes',)
    inlines = [ItemLoteInline]


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'peca', 'tipo', 'quantidade', 'responsavel', 'data_hora')
    list_filter = ('tipo',)
    search_fields = ('produto__nome', 'peca__codigo')
    date_hierarchy = 'data_hora'
