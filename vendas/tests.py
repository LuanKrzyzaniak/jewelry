from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import Liga, Metal, PrecoLiga, Produto, Peca
from .models import Cliente, Venda, ItemVenda

Usuario = get_user_model()


class VendaItemTests(TestCase):

    def setUp(self):
        self.vendedor = Usuario.objects.create_user(username='vendedor', password='123', perfil=Usuario.Perfil.VENDEDOR)
        self.client.force_login(self.vendedor)

        metal = Metal.objects.create(nome='Ouro', simbolo='XAU')
        liga = Liga.objects.create(nome='Ouro 18k', metal=metal, pureza=Decimal('0.75000'))
        PrecoLiga.objects.create(
            liga=liga,
            preco_por_grama=Decimal('500.0000'),
            vigente_desde=timezone.localdate(),
            definido_por=self.vendedor,
        )
        produto = Produto.objects.create(nome='Anel', liga=liga)
        self.peca = Peca.objects.create(produto=produto, peso_gramas=Decimal('2.000'))
        self.cliente = Cliente.objects.create(nome='João da Silva')
        self.venda = Venda.objects.create(cliente=self.cliente, vendedor=self.vendedor)

    def test_nao_permite_vender_peca_ja_vendida(self):
        self.peca.status = Peca.Status.VENDIDA
        self.peca.save(update_fields=['status'])

        url = reverse('vendas:item_adicionar', kwargs={'venda_pk': self.venda.pk})
        response = self.client.post(url, {'peca_id': self.peca.pk})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(ItemVenda.objects.filter(venda=self.venda).count(), 0)

    def test_adicionar_item_usa_preco_sugerido_e_recalcula_total(self):
        url = reverse('vendas:item_adicionar', kwargs={'venda_pk': self.venda.pk})
        self.client.post(url, {'peca_id': self.peca.pk})

        self.venda.refresh_from_db()
        self.peca.refresh_from_db()
        self.assertEqual(self.venda.valor_total, self.peca.preco_sugerido)
        self.assertEqual(self.peca.status, Peca.Status.VENDIDA)


class VendaDescontoTests(TestCase):

    def setUp(self):
        self.vendedor = Usuario.objects.create_user(username='vendedor', password='123', perfil=Usuario.Perfil.VENDEDOR)
        self.client.force_login(self.vendedor)

        metal = Metal.objects.create(nome='Ouro', simbolo='XAU')
        liga = Liga.objects.create(nome='Ouro 18k', metal=metal, pureza=Decimal('0.75000'))
        PrecoLiga.objects.create(
            liga=liga,
            preco_por_grama=Decimal('500.0000'),
            vigente_desde=timezone.localdate(),
            definido_por=self.vendedor,
        )
        produto = Produto.objects.create(nome='Anel', liga=liga)
        self.peca = Peca.objects.create(produto=produto, peso_gramas=Decimal('2.000'))
        self.cliente = Cliente.objects.create(nome='João da Silva')
        self.venda = Venda.objects.create(cliente=self.cliente, vendedor=self.vendedor)
        ItemVenda.objects.create(venda=self.venda, peca=self.peca, preco_unitario_pago=Decimal('1000.00'))
        self.venda.recalcular_total()

    def test_desconto_em_valor(self):
        url = reverse('vendas:venda_desconto_atualizar', kwargs={'pk': self.venda.pk})
        self.client.post(url, {'tipo': 'valor', 'valor': '100.00'})

        self.venda.refresh_from_db()
        self.assertEqual(self.venda.desconto_total, Decimal('100.00'))
        self.assertEqual(self.venda.valor_total, Decimal('900.00'))

    def test_desconto_em_percentual(self):
        url = reverse('vendas:venda_desconto_atualizar', kwargs={'pk': self.venda.pk})
        self.client.post(url, {'tipo': 'percentual', 'valor': '10'})

        self.venda.refresh_from_db()
        self.assertEqual(self.venda.desconto_total, Decimal('100.00'))
        self.assertEqual(self.venda.valor_total, Decimal('900.00'))

    def test_percentual_acima_de_100_e_invalido(self):
        url = reverse('vendas:venda_desconto_atualizar', kwargs={'pk': self.venda.pk})
        self.client.post(url, {'tipo': 'percentual', 'valor': '150'})

        self.venda.refresh_from_db()
        self.assertEqual(self.venda.desconto_total, Decimal('0.00'))


class FornecedorAcessoTests(TestCase):

    def setUp(self):
        self.vendedor = Usuario.objects.create_user(username='vendedor', password='123', perfil=Usuario.Perfil.VENDEDOR)
        self.gerente = Usuario.objects.create_user(username='gerente', password='123', perfil=Usuario.Perfil.GERENTE)

    def test_vendedor_nao_acessa_lista_de_fornecedores(self):
        self.client.force_login(self.vendedor)
        response = self.client.get(reverse('vendas:fornecedor_list'))
        self.assertRedirects(response, reverse('dashboard:index'))

    def test_gerente_acessa_lista_de_fornecedores(self):
        self.client.force_login(self.gerente)
        response = self.client.get(reverse('vendas:fornecedor_list'))
        self.assertEqual(response.status_code, 200)
