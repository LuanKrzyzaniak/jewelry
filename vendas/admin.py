from django.contrib import admin

from .models import Cliente, Fornecedor, ItemVenda, Venda


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'criado_em')
    search_fields = ('nome', 'telefone')


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'nome_fantasia', 'cnpj', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('razao_social', 'nome_fantasia', 'cnpj')


class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    extra = 0


@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'vendedor', 'status', 'valor_total', 'data_venda')
    list_filter = ('status', 'vendedor')
    search_fields = ('cliente__nome',)
    date_hierarchy = 'data_venda'
    inlines = [ItemVendaInline]
