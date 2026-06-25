from django.contrib import admin

from .models import CotacaoMetal, FotoPeca, Liga, Metal, Peca, PrecoLiga, Produto, TipoProduto


@admin.register(Metal)
class MetalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'simbolo')
    search_fields = ('nome', 'simbolo')


@admin.register(Liga)
class LigaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'metal', 'pureza')
    list_filter = ('metal',)
    search_fields = ('nome',)


@admin.register(PrecoLiga)
class PrecoLigaAdmin(admin.ModelAdmin):
    list_display = ('liga', 'preco_por_grama', 'vigente_desde', 'definido_por')
    list_filter = ('liga',)
    date_hierarchy = 'vigente_desde'


@admin.register(CotacaoMetal)
class CotacaoMetalAdmin(admin.ModelAdmin):
    list_display = ('metal', 'data', 'preco_por_grama', 'fonte')
    list_filter = ('metal', 'fonte')
    date_hierarchy = 'data'


@admin.register(TipoProduto)
class TipoProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)


class FotoPecaInline(admin.TabularInline):
    model = FotoPeca
    extra = 1


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'liga', 'estoque_atual')
    list_filter = ('tipo', 'liga')
    search_fields = ('nome',)


@admin.register(Peca)
class PecaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'produto', 'status', 'peso_gramas', 'preco_sugerido', 'criado_em')
    list_filter = ('status', 'produto__tipo', 'produto__liga')
    search_fields = ('codigo', 'produto__nome')
    inlines = [FotoPecaInline]
