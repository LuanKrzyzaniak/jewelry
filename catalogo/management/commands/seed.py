from django.core.management.base import BaseCommand

from catalogo.models import Liga, Metal, TipoProduto


METAIS = [
    {'nome': 'Ouro',  'simbolo': 'XAU'},
    {'nome': 'Prata', 'simbolo': 'XAG'},
]

LIGAS = [
    {'nome': 'Ouro 18k',  'metal': 'Ouro',  'pureza': '0.75000'},
    {'nome': 'Ouro 10k',  'metal': 'Ouro',  'pureza': '0.41700'},
    {'nome': 'Prata 950', 'metal': 'Prata', 'pureza': '0.95000'},
]

TIPOS_PRODUTO = [
    'Anel', 'Aliança', 'Brinco', 'Colar', 'Corrente',
    'Pulseira', 'Pingente', 'Bracelete', 'Piercing', 'Outros',
]


class Command(BaseCommand):
    help = 'Popula o banco com dados base: metais, ligas e tipos de produto.'

    def handle(self, *args, **options):
        self._seed_metais()
        self._seed_ligas()
        self._seed_tipos()

    def _seed_metais(self):
        for dados in METAIS:
            _, criado = Metal.objects.get_or_create(
                simbolo=dados['simbolo'],
                defaults={'nome': dados['nome']},
            )
            self.stdout.write(f"Metal {dados['nome']}: {'criado' if criado else 'já existe'}")

    def _seed_ligas(self):
        for dados in LIGAS:
            try:
                metal = Metal.objects.get(nome=dados['metal'])
            except Metal.DoesNotExist:
                self.stderr.write(f"Metal \"{dados['metal']}\" não encontrado.")
                continue
            _, criada = Liga.objects.get_or_create(
                nome=dados['nome'],
                defaults={'metal': metal, 'pureza': dados['pureza']},
            )
            self.stdout.write(f"Liga {dados['nome']}: {'criada' if criada else 'já existe'}")

    def _seed_tipos(self):
        for nome in TIPOS_PRODUTO:
            _, criado = TipoProduto.objects.get_or_create(nome=nome)
            self.stdout.write(f"Tipo {nome}: {'criado' if criado else 'já existe'}")
