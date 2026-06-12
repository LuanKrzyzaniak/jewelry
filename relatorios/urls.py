from django.urls import path

from . import views

app_name = 'relatorios'

urlpatterns = [
    path('vendas/', views.vendas, name='vendas'),
    path('giro/',   views.giro,   name='giro'),
]
