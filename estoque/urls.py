from django.urls import path

from . import views

app_name = 'estoque'

urlpatterns = [
    path('',       views.MovimentacaoListView.as_view(), name='movimentacao_list'),
    path('entrada/', views.movimentacao_entrada,         name='movimentacao_entrada'),
    path('saida/',   views.movimentacao_saida,           name='movimentacao_saida'),

    path('lotes/',                                          views.LoteListView.as_view(),  name='lote_list'),
    path('lotes/novo/',                                     views.LoteCreateView.as_view(), name='lote_create'),
    path('lotes/<int:pk>/',                                 views.LoteDetailView.as_view(), name='lote_detail'),
    path('lotes/<int:lote_pk>/item/adicionar/',             views.lote_item_adicionar,      name='lote_item_adicionar'),
    path('lotes/<int:lote_pk>/item/<int:item_pk>/remover/', views.lote_item_remover,        name='lote_item_remover'),
    path('lotes/<int:lote_pk>/finalizar/',                  views.lote_finalizar,           name='lote_finalizar'),
    path('lotes/<int:lote_pk>/cancelar/',                   views.lote_cancelar,            name='lote_cancelar'),
]
