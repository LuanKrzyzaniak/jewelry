from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .models import Liga, Metal, PrecoLiga, Produto, Peca

Usuario = get_user_model()


class PecaPrecoSugeridoTests(TestCase):

    def setUp(self):
        self.gerente = Usuario.objects.create_user(username='gerente', password='123', perfil=Usuario.Perfil.GERENTE)
        self.metal = Metal.objects.create(nome='Ouro', simbolo='XAU')
        self.liga = Liga.objects.create(nome='Ouro 18k', metal=self.metal, pureza=Decimal('0.75000'))
        PrecoLiga.objects.create(
            liga=self.liga,
            preco_por_grama=Decimal('500.0000'),
            vigente_desde=timezone.localdate(),
            definido_por=self.gerente,
        )
        self.produto = Produto.objects.create(nome='Anel Solitário', liga=self.liga)

    def test_preco_sugerido_considera_peso_liga_e_mao_de_obra(self):
        peca = Peca.objects.create(
            produto=self.produto,
            peso_gramas=Decimal('2.000'),
            custo_mao_de_obra=Decimal('50.00'),
        )
        self.assertEqual(peca.preco_sugerido, Decimal('1050.00'))

    def test_codigo_e_gerado_automaticamente_ao_salvar(self):
        peca = Peca.objects.create(
            produto=self.produto,
            peso_gramas=Decimal('1.500'),
        )
        self.assertTrue(peca.codigo)
        self.assertTrue(peca.codigo.startswith('ANEL'))
