from django.urls import path

from . import views

app_name = 'vendas'

urlpatterns = [
    # Vendas
    path('',                                   views.VendaListView.as_view(),   name='venda_list'),
    path('nova/',                              views.VendaCreateView.as_view(), name='venda_create'),
    path('<int:pk>/',                          views.VendaDetailView.as_view(), name='venda_detail'),
    path('<int:pk>/editar/',                   views.VendaUpdateView.as_view(), name='venda_update'),
    path('<int:pk>/cancelar/',                 views.venda_cancelar,            name='venda_cancelar'),
    path('<int:pk>/desconto/',                 views.venda_desconto_atualizar,  name='venda_desconto_atualizar'),
    path('<int:venda_pk>/itens/adicionar/',    views.item_adicionar,            name='item_adicionar'),
    path('<int:venda_pk>/itens/<int:item_pk>/remover/', views.item_remover,     name='item_remover'),

    # Clientes
    path('clientes/',                  views.ClienteListView.as_view(),   name='cliente_list'),
    path('clientes/novo/',             views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/editar/',  views.ClienteUpdateView.as_view(), name='cliente_update'),

    # Fornecedores
    path('fornecedores/',                 views.FornecedorListView.as_view(),   name='fornecedor_list'),
    path('fornecedores/novo/',            views.FornecedorCreateView.as_view(), name='fornecedor_create'),
    path('fornecedores/<int:pk>/editar/', views.FornecedorUpdateView.as_view(), name='fornecedor_update'),
]
