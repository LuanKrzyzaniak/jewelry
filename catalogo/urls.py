from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    # Produtos
    path('produtos/',                  views.ProdutoListView.as_view(),   name='produto_list'),
    path('produtos/novo/',             views.ProdutoCreateView.as_view(), name='produto_create'),
    path('produtos/<int:pk>/',         views.ProdutoDetailView.as_view(), name='produto_detail'),
    path('produtos/<int:pk>/editar/',  views.ProdutoUpdateView.as_view(), name='produto_update'),
    path('produtos/<int:pk>/excluir/', views.ProdutoDeleteView.as_view(), name='produto_delete'),

    # Ligas
    path('ligas/',                            views.LigaListView.as_view(),   name='liga_list'),
    path('ligas/nova/',                       views.LigaCreateView.as_view(), name='liga_create'),
    path('ligas/<int:pk>/editar/',            views.LigaUpdateView.as_view(), name='liga_update'),
    path('ligas/<int:liga_pk>/preco/',        views.preco_liga_definir,       name='preco_liga_definir'),

    # Metais (somente leitura — dados gerenciados via seed)
    path('metais/', views.MetalListView.as_view(), name='metal_list'),

    # Tipos de produto
    path('tipos/',                 views.TipoProdutoListView.as_view(),   name='tipo_produto_list'),
    path('tipos/novo/',            views.TipoProdutoCreateView.as_view(), name='tipo_produto_create'),
    path('tipos/<int:pk>/editar/', views.TipoProdutoUpdateView.as_view(), name='tipo_produto_update'),

    # Cotações
    path('cotacoes/', views.CotacaoListView.as_view(), name='cotacao_list'),

    # Peças
    path('pecas/catalogo/',                                     views.peca_catalogo,             name='peca_catalogo'),
    path('pecas/',                                              views.PecaListView.as_view(),   name='peca_list'),
    path('pecas/nova/',                                         views.PecaCreateView.as_view(), name='peca_create'),
    path('pecas/<int:pk>/',                                     views.PecaDetailView.as_view(), name='peca_detail'),
    path('pecas/<int:pk>/editar/',                              views.PecaUpdateView.as_view(), name='peca_update'),
    path('pecas/<int:pk>/excluir/',                             views.PecaDeleteView.as_view(), name='peca_delete'),
    path('pecas/<int:pk>/fotos/',                               views.peca_foto_upload,         name='peca_foto_upload'),
    path('pecas/<int:pk>/fotos/<int:foto_pk>/excluir/',         views.peca_foto_delete,         name='peca_foto_delete'),
    path('pecas/<int:pk>/fotos/<int:foto_pk>/principal/',       views.peca_foto_set_principal,  name='peca_foto_set_principal'),
]
