import requests
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from catalogo.models import CotacaoMetal, Metal


class Command(BaseCommand):
    help = 'Busca a cotação atual dos metais via API e salva no banco.'

    # GoldAPI.io — plano gratuito, 100 req/mês (suficiente para 1x/dia)
    BASE_URL = 'https://www.goldapi.io/api/{symbol}/BRL'

    def handle(self, *args, **options):
        api_key = getattr(settings, 'GOLDAPI_KEY', None)
        hoje = timezone.localdate()

        metais = Metal.objects.all()
        if not metais.exists():
            self.stderr.write('Nenhum metal cadastrado. Cadastre primeiro no admin.')
            return

        for metal in metais:
            if api_key:
                preco = self._buscar_via_api(metal.simbolo, api_key)
            else:
                # Modo desenvolvimento: usa valor fixo para não travar o fluxo
                preco = self._preco_mock(metal.simbolo)
                self.stdout.write(f'[MOCK] {metal.nome}: R$ {preco}/g')

            if preco is None:
                self.stderr.write(f'Falha ao obter cotação de {metal.nome}. Pulando.')
                continue

            cotacao, criada = CotacaoMetal.objects.update_or_create(
                metal=metal,
                data=hoje,
                defaults={
                    'preco_por_grama': preco,
                    'fonte': 'api' if api_key else 'mock',
                },
            )
            acao = 'Criada' if criada else 'Atualizada'
            self.stdout.write(f'{acao}: {metal.nome} — R$ {preco}/g em {hoje.strftime("%d/%m/%Y")}')

    def _buscar_via_api(self, simbolo, api_key):
        try:
            url = self.BASE_URL.format(symbol=simbolo)
            resp = requests.get(url, headers={'x-access-token': api_key}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # goldapi.io retorna price_gram_24k para ouro puro; usamos como base
            preco_grama = data.get('price_gram_24k') or (data['price'] / Decimal('31.1035'))
            return Decimal(str(preco_grama)).quantize(Decimal('0.0001'))
        except Exception as e:
            self.stderr.write(f'Erro na API ({simbolo}): {e}')
            return None

    def _preco_mock(self, simbolo):
        # Valores aproximados de referência para desenvolvimento
        mock = {'XAU': Decimal('320.0000'), 'XAG': Decimal('4.0000')}
        return mock.get(simbolo, Decimal('1.0000'))
