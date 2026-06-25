from datetime import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalogo.models import Liga, Metal, Peca, PrecoLiga, Produto, TipoProduto
from estoque.models import ItemLote, LoteMovimentacao, MovimentacaoEstoque
from vendas.models import Cliente, Fornecedor, ItemVenda, Venda

Usuario = get_user_model()

# ── Dados base ────────────────────────────────────────────────────────────────

METAIS = [
    {'nome': 'Ouro',  'simbolo': 'XAU'},
    {'nome': 'Prata', 'simbolo': 'XAG'},
]

LIGAS = [
    {'nome': 'Ouro 18k',  'metal': 'Ouro',  'pureza': '0.75000'},
    {'nome': 'Ouro 10k',  'metal': 'Ouro',  'pureza': '0.41700'},
    {'nome': 'Prata 950', 'metal': 'Prata', 'pureza': '0.95000'},
]

TIPOS = [
    'Anel', 'Aliança', 'Brinco', 'Colar', 'Corrente',
    'Pulseira', 'Pingente', 'Bracelete', 'Piercing', 'Outros',
]

PRECOS_LIGA = {
    'Ouro 18k':  Decimal('350.00'),
    'Ouro 10k':  Decimal('195.00'),
    'Prata 950': Decimal('4.80'),
}

# ── Dados de teste ────────────────────────────────────────────────────────────

USUARIOS = [
    {
        'username':   'admin',
        'first_name': 'Admin',
        'last_name':  'Gerente',
        'password':   'admin',
        'perfil':     'GER',
        'is_staff':   True,
    },
    {
        'username':   'user',
        'first_name': 'João',
        'last_name':  'Silva',
        'password':   'user',
        'perfil':     'VEN',
    },
]

CLIENTES = [
    {'nome': 'Ana Paula Ferreira',   'telefone': '(11) 99123-4567', 'observacao': 'Cliente VIP — prefere ouro 18k.'},
    {'nome': 'Carlos Eduardo Souza', 'telefone': '(21) 98765-4321'},
    {'nome': 'Mariana Costa',        'telefone': '(31) 97654-3210', 'observacao': 'Compra alianças para revenda.'},
    {'nome': 'Roberto Lima',         'telefone': '(41) 96543-2109'},
    {'nome': 'Fernanda Oliveira',    'telefone': '(51) 95432-1098'},
    {'nome': 'José Almeida',         'telefone': '(61) 90000-0000', 'ativo': False, 'observacao': 'Cadastro antigo, sem compras recentes.'},
]

FORNECEDORES = [
    {'razao_social': 'Ouro Brasil Joias Ltda',          'nome_fantasia': 'OBJ Joias',   'cnpj': '12.345.678/0001-90', 'telefone': '(11) 3344-5566', 'observacao': 'Fornecedor principal de ouro 18k.'},
    {'razao_social': 'Prata & Cia Comércio de Metais',  'nome_fantasia': 'Prata & Cia', 'cnpj': '23.456.789/0001-01', 'telefone': '(11) 3322-1100', 'observacao': 'Entrega quinzenal.'},
    {'razao_social': 'Distribuidora Nacional de Joias', 'nome_fantasia': 'DNJ',          'cnpj': '34.567.890/0001-12', 'telefone': '(21) 3300-9900', 'ativo': False, 'observacao': 'Contrato encerrado em 2025 — mantido para histórico.'},
]

PRODUTOS = [
    ('Anel Solitário',          'Anel',      'Ouro 18k',  Decimal('3.5'),  Decimal('180.00')),
    ('Anel de Formatura',       'Anel',      'Ouro 18k',  Decimal('5.0'),  Decimal('250.00')),
    ('Anel Aparador',           'Anel',      'Ouro 10k',  Decimal('2.8'),  Decimal('120.00')),
    ('Aliança Tradicional',     'Aliança',   'Ouro 18k',  Decimal('4.2'),  Decimal('150.00')),
    ('Aliança com Friso',       'Aliança',   'Ouro 18k',  Decimal('4.8'),  Decimal('170.00')),
    ('Brinco Argola',           'Brinco',    'Prata 950', Decimal('2.1'),  Decimal('45.00')),
    ('Brinco Pérola',           'Brinco',    'Prata 950', Decimal('1.5'),  Decimal('55.00')),
    ('Brinco Gota',             'Brinco',    'Ouro 18k',  Decimal('1.9'),  Decimal('95.00')),
    ('Colar Veneziana',         'Colar',     'Ouro 10k',  Decimal('8.3'),  Decimal('220.00')),
    ('Corrente Groumet',        'Corrente',  'Ouro 10k',  Decimal('12.0'), Decimal('300.00')),
    ('Corrente Piastrine',      'Corrente',  'Ouro 18k',  Decimal('9.5'),  Decimal('280.00')),
    ('Pingente Coração',        'Pingente',  'Prata 950', Decimal('1.8'),  Decimal('35.00')),
    ('Pingente Cruz',           'Pingente',  'Ouro 18k',  Decimal('2.2'),  Decimal('90.00')),
    ('Pingente Infinito',       'Pingente',  'Prata 950', Decimal('1.2'),  Decimal('30.00')),
    ('Pulseira Elo Português',  'Pulseira',  'Ouro 18k',  Decimal('6.5'),  Decimal('200.00')),
    ('Pulseira Veneziana',      'Pulseira',  'Prata 950', Decimal('5.8'),  Decimal('80.00')),
]

LOTES_ENT = [
    (
        'OBJ Joias',
        'Compra de reposição — ouro',
        [
            ('Anel Solitário',         5, None),
            ('Anel de Formatura',      3, None),
            ('Aliança Tradicional',    4, None),
            ('Aliança com Friso',      3, None),
            ('Brinco Gota',            4, None),
            ('Pulseira Elo Português', 3, None),
            ('Corrente Piastrine',     3, None),
            ('Pingente Cruz',          5, None),
        ],
    ),
    (
        'Prata & Cia',
        'Compra de reposição — prata',
        [
            ('Brinco Argola',     6, None),
            ('Brinco Pérola',     5, None),
            ('Pingente Coração',  7, None),
            ('Pingente Infinito', 4, None),
            ('Pulseira Veneziana',4, None),
        ],
    ),
]

AVULSAS_ENT = [
    ('Anel Aparador',    4, 'DNJ',       'Entrada avulsa'),
    ('Corrente Groumet', 3, 'OBJ Joias', 'Entrada avulsa'),
    ('Colar Veneziana',  3, 'DNJ',       'Entrada avulsa'),
]

VENDAS = [
    ('Ana Paula Ferreira',   'admin', 'CON', Decimal('0.00'),   '',                             '2025-08-05', [('Brinco Argola', 2), ('Pingente Coração', 1)]),
    ('Carlos Eduardo Souza', 'user',  'CON', Decimal('0.00'),   '',                             '2025-08-18', [('Aliança Tradicional', 2)]),
    ('Mariana Costa',        'user',  'CON', Decimal('0.00'),   '',                             '2025-09-03', [('Corrente Groumet', 1)]),
    ('Roberto Lima',         'admin', 'CON', Decimal('50.00'),  'Desconto fidelidade',          '2025-09-14', [('Anel Solitário', 1), ('Brinco Gota', 1)]),
    ('Fernanda Oliveira',    'user',  'CON', Decimal('0.00'),   '',                             '2025-09-27', [('Pingente Infinito', 2), ('Brinco Pérola', 1)]),
    ('Ana Paula Ferreira',   'admin', 'CON', Decimal('0.00'),   '',                             '2025-10-02', [('Pulseira Veneziana', 1)]),
    ('Carlos Eduardo Souza', 'user',  'CON', Decimal('0.00'),   '',                             '2025-10-10', [('Pingente Cruz', 2), ('Brinco Argola', 1)]),
    ('Mariana Costa',        'admin', 'CON', Decimal('100.00'), 'Desconto especial',            '2025-10-21', [('Colar Veneziana', 1), ('Pingente Coração', 2)]),
    ('Roberto Lima',         'user',  'CAN', Decimal('0.00'),   'Cliente desistiu',             '2025-10-29', [('Anel de Formatura', 1)]),
    ('Fernanda Oliveira',    'admin', 'CON', Decimal('0.00'),   '',                             '2025-11-08', [('Aliança com Friso', 2)]),
    ('Ana Paula Ferreira',   'user',  'CON', Decimal('0.00'),   '',                             '2025-11-15', [('Corrente Piastrine', 1), ('Brinco Pérola', 2)]),
    ('Carlos Eduardo Souza', 'admin', 'CON', Decimal('80.00'),  'Desconto fidelidade',          '2025-11-28', [('Anel Aparador', 1), ('Pingente Infinito', 1)]),
    ('Mariana Costa',        'user',  'CON', Decimal('0.00'),   '',                             '2025-12-02', [('Brinco Gota', 2), ('Pingente Coração', 1)]),
    ('Roberto Lima',         'admin', 'CON', Decimal('0.00'),   '',                             '2025-12-05', [('Pulseira Elo Português', 1)]),
    ('Fernanda Oliveira',    'user',  'CON', Decimal('150.00'), 'Desconto natal',               '2025-12-10', [('Aliança Tradicional', 2), ('Brinco Argola', 2)]),
    ('Ana Paula Ferreira',   'admin', 'CON', Decimal('0.00'),   '',                             '2025-12-15', [('Colar Veneziana', 1), ('Pingente Cruz', 1)]),
    ('Carlos Eduardo Souza', 'user',  'CON', Decimal('200.00'), 'Presente de natal',            '2025-12-20', [('Anel de Formatura', 1), ('Aliança com Friso', 1)]),
    ('Mariana Costa',        'admin', 'CON', Decimal('0.00'),   '',                             '2026-01-09', [('Brinco Pérola', 2)]),
    ('Roberto Lima',         'user',  'CON', Decimal('0.00'),   '',                             '2026-01-23', [('Corrente Groumet', 1), ('Pingente Infinito', 1)]),
    ('Fernanda Oliveira',    'admin', 'CON', Decimal('0.00'),   '',                             '2026-02-06', [('Anel Solitário', 1)]),
    ('Ana Paula Ferreira',   'user',  'CON', Decimal('50.00'),  'Desconto dia dos namorados',   '2026-02-13', [('Aliança Tradicional', 1), ('Brinco Argola', 1)]),
    ('Carlos Eduardo Souza', 'admin', 'CON', Decimal('0.00'),   '',                             '2026-02-24', [('Pingente Coração', 3)]),
    ('Mariana Costa',        'user',  'CON', Decimal('0.00'),   '',                             '2026-03-07', [('Pulseira Veneziana', 1), ('Brinco Pérola', 1)]),
    ('Roberto Lima',         'admin', 'CON', Decimal('0.00'),   '',                             '2026-03-18', [('Corrente Piastrine', 1)]),
    ('Fernanda Oliveira',    'user',  'CON', Decimal('0.00'),   '',                             '2026-03-25', [('Anel Aparador', 2), ('Pingente Cruz', 1)]),
    ('Ana Paula Ferreira',   'admin', 'CON', Decimal('0.00'),   '',                             '2026-04-04', [('Brinco Gota', 1), ('Pingente Infinito', 1)]),
    ('Carlos Eduardo Souza', 'user',  'RES', Decimal('0.00'),   'Aguardando confirmação',       '2026-04-11', [('Aliança com Friso', 2)]),
    ('Mariana Costa',        'admin', 'CON', Decimal('100.00'), 'Desconto cliente recorrente',  '2026-04-22', [('Colar Veneziana', 1), ('Brinco Argola', 2)]),
    ('Roberto Lima',         'user',  'CON', Decimal('0.00'),   '',                             '2026-05-03', [('Pulseira Elo Português', 1)]),
    ('Fernanda Oliveira',    'admin', 'CON', Decimal('0.00'),   '',                             '2026-05-12', [('Anel Solitário', 1), ('Pingente Coração', 1)]),
    ('Ana Paula Ferreira',   'user',  'CON', Decimal('0.00'),   '',                             '2026-05-19', [('Corrente Groumet', 1)]),
    ('Carlos Eduardo Souza', 'admin', 'CON', Decimal('50.00'),  'Desconto fidelidade',          '2026-05-28', [('Aliança Tradicional', 1), ('Brinco Pérola', 1)]),
    ('Mariana Costa',        'user',  'CON', Decimal('0.00'),   '',                             '2026-06-02', [('Pingente Cruz', 2), ('Brinco Gota', 1)]),
    ('Roberto Lima',         'admin', 'ORC', Decimal('0.00'),   'Orçamento enviado por e-mail', '2026-06-05', [('Anel de Formatura', 1)]),
    ('Fernanda Oliveira',    'user',  'CON', Decimal('0.00'),   '',                             '2026-06-08', [('Pulseira Veneziana', 1), ('Pingente Infinito', 1)]),
]

PECAS = [
    ('Anel Solitário',         'DIS'),
    ('Anel Solitário',         'DIS'),
    ('Anel Solitário',         'RES'),
    ('Anel Solitário',         'VEN'),
    ('Anel de Formatura',      'DIS'),
    ('Anel de Formatura',      'DIS'),
    ('Anel Aparador',          'DIS'),
    ('Aliança Tradicional',    'DIS'),
    ('Aliança Tradicional',    'DIS'),
    ('Aliança Tradicional',    'VEN'),
    ('Aliança com Friso',      'DIS'),
    ('Aliança com Friso',      'RES'),
    ('Brinco Argola',          'DIS'),
    ('Brinco Argola',          'DIS'),
    ('Brinco Argola',          'DIS'),
    ('Brinco Pérola',          'DIS'),
    ('Brinco Pérola',          'RES'),
    ('Brinco Gota',            'DIS'),
    ('Colar Veneziana',        'DIS'),
    ('Colar Veneziana',        'RES'),
    ('Corrente Groumet',       'DIS'),
    ('Corrente Piastrine',     'DIS'),
    ('Corrente Piastrine',     'DIS'),
    ('Pingente Coração',       'DIS'),
    ('Pingente Coração',       'DIS'),
    ('Pingente Coração',       'VEN'),
    ('Pingente Cruz',          'DIS'),
    ('Pingente Infinito',      'DIS'),
    ('Pingente Infinito',      'DIS'),
    ('Pulseira Elo Português', 'DIS'),
    ('Pulseira Veneziana',     'DIS'),
    ('Pulseira Veneziana',     'DIS'),
]


class Command(BaseCommand):
    help = 'Popula o banco com dados de teste'

    def handle(self, *args, **options):
        gerente = self._seed_usuarios()
        self._seed_metais()
        self._seed_ligas()
        self._seed_tipos()
        self._seed_precos_liga(gerente)
        self._seed_clientes()
        self._seed_fornecedores()
        self._seed_produtos()
        self._seed_pecas(gerente)
        self._seed_movimentacoes(gerente)
        self._seed_vendas(gerente)
        self.stdout.write(self.style.SUCCESS('\nSeed de desenvolvimento concluído.'))

    # ── helpers ──────────────────────────────────────────────────────────────

    def _seed_usuarios(self):
        gerente = None
        for dados in USUARIOS:
            perfil   = dados.pop('perfil')
            is_staff = dados.pop('is_staff', False)
            password = dados.pop('password')

            usuario, criado = Usuario.objects.get_or_create(
                username=dados['username'],
                defaults={**dados, 'perfil': perfil, 'is_staff': is_staff},
            )
            if criado:
                usuario.set_password(password)
                usuario.save(update_fields=['password'])
                self.stdout.write(f"Usuário {usuario.username} criado (senha: {password})")
            else:
                self.stdout.write(f"Usuário {usuario.username}: já existe")

            if perfil == 'GER':
                gerente = usuario

            dados['perfil']   = perfil
            dados['is_staff'] = is_staff
            dados['password'] = password

        return gerente

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
                self.stderr.write(f"Metal \"{dados['metal']}\" não encontrado, pulando liga {dados['nome']}.")
                continue
            _, criada = Liga.objects.get_or_create(
                nome=dados['nome'],
                defaults={'metal': metal, 'pureza': dados['pureza']},
            )
            self.stdout.write(f"Liga {dados['nome']}: {'criada' if criada else 'já existe'}")

    def _seed_tipos(self):
        for nome in TIPOS:
            _, criado = TipoProduto.objects.get_or_create(nome=nome)
            self.stdout.write(f"Tipo {nome}: {'criado' if criado else 'já existe'}")

    def _seed_precos_liga(self, gerente):
        hoje = timezone.localdate()
        for nome_liga, preco in PRECOS_LIGA.items():
            try:
                liga = Liga.objects.get(nome=nome_liga)
            except Liga.DoesNotExist:
                continue
            _, criado = PrecoLiga.objects.get_or_create(
                liga=liga,
                vigente_desde=hoje,
                defaults={'preco_por_grama': preco, 'definido_por': gerente},
            )
            self.stdout.write(f"Preço {nome_liga}: {'criado' if criado else 'já existe'}")

    def _seed_clientes(self):
        for dados in CLIENTES:
            _, criado = Cliente.objects.get_or_create(
                nome=dados['nome'],
                defaults={k: v for k, v in dados.items() if k != 'nome'},
            )
            self.stdout.write(f"Cliente {dados['nome']}: {'criado' if criado else 'já existe'}")

    def _seed_fornecedores(self):
        for dados in FORNECEDORES:
            _, criado = Fornecedor.objects.get_or_create(
                razao_social=dados['razao_social'],
                defaults={k: v for k, v in dados.items() if k != 'razao_social'},
            )
            self.stdout.write(f"Fornecedor {dados['razao_social']}: {'criado' if criado else 'já existe'}")

    def _seed_produtos(self):
        for nome, tipo_nome, liga_nome, *_ in PRODUTOS:
            tipo = TipoProduto.objects.filter(nome=tipo_nome).first()
            liga = Liga.objects.filter(nome=liga_nome).first() if liga_nome else None
            _, criado = Produto.objects.get_or_create(
                nome=nome,
                defaults={'tipo': tipo, 'liga': liga},
            )
            self.stdout.write(f"Produto {nome}: {'criado' if criado else 'já existe'}")

    def _seed_pecas(self, gerente):
        defaults_map = {nome: (peso, custo) for nome, _, _, peso, custo in PRODUTOS}
        criadas = 0
        for nome_produto, status in PECAS:
            produto = Produto.objects.filter(nome=nome_produto).first()
            if not produto:
                self.stderr.write(f"Produto \"{nome_produto}\" não encontrado, pulando peça.")
                continue
            peso, custo = defaults_map.get(nome_produto, (Decimal('1.0'), Decimal('0.00')))
            peca = Peca.objects.create(
                produto=produto,
                status=status,
                peso_gramas=peso,
                custo_mao_de_obra=custo,
            )
            MovimentacaoEstoque.objects.create(
                produto=produto,
                peca=peca,
                tipo=MovimentacaoEstoque.Tipo.ENTRADA,
                quantidade=1,
                responsavel=gerente,
                observacoes='Estoque inicial',
            )
            if status == Peca.Status.VENDIDA:
                MovimentacaoEstoque.objects.create(
                    produto=produto,
                    peca=peca,
                    tipo=MovimentacaoEstoque.Tipo.SAIDA,
                    quantidade=1,
                    responsavel=gerente,
                    observacoes='Saída histórica',
                )
            criadas += 1
        self.stdout.write(f"Peças de estoque criadas: {criadas}")

    def _seed_movimentacoes(self, gerente):
        if LoteMovimentacao.objects.exists():
            self.stdout.write('Movimentações: já existem, pulando.')
            return

        defaults_map = {nome: (peso, custo) for nome, _, _, peso, custo in PRODUTOS}

        with transaction.atomic():
            for forn_nome, obs, itens in LOTES_ENT:
                fornecedor = Fornecedor.objects.filter(nome_fantasia=forn_nome).first()
                lote = LoteMovimentacao.objects.create(
                    tipo=LoteMovimentacao.Tipo.ENTRADA,
                    fornecedor=fornecedor,
                    responsavel=gerente,
                    observacoes=obs,
                    finalizado=True,
                )
                obs_mov = f'Lote #{lote.pk}' + (f' — {obs}' if obs else '')

                for nome_produto, qtd, peso_por_peca in itens:
                    produto = Produto.objects.filter(nome=nome_produto).first()
                    if not produto:
                        continue
                    _, custo = defaults_map.get(nome_produto, (None, Decimal('0.00')))
                    peso_def, _ = defaults_map.get(nome_produto, (Decimal('1.0'), Decimal('0.00')))
                    peso = peso_por_peca or peso_def
                    ItemLote.objects.create(
                        lote=lote,
                        produto=produto,
                        quantidade=qtd,
                        peso_padrao=peso,
                        custo_mao_de_obra=custo,
                    )
                    for _ in range(qtd):
                        peca = Peca.objects.create(
                            produto=produto,
                            status=Peca.Status.DISPONIVEL,
                            peso_gramas=peso,
                            custo_mao_de_obra=custo,
                        )
                        MovimentacaoEstoque.objects.create(
                            produto=produto,
                            peca=peca,
                            tipo=MovimentacaoEstoque.Tipo.ENTRADA,
                            quantidade=1,
                            fornecedor=fornecedor,
                            lote=lote,
                            responsavel=gerente,
                            observacoes=obs_mov,
                        )

                self.stdout.write(f'Lote #{lote.pk} (Entrada, {len(itens)} tipos): criado')

            for nome_produto, qtd, forn_nome, obs in AVULSAS_ENT:
                produto    = Produto.objects.filter(nome=nome_produto).first()
                fornecedor = Fornecedor.objects.filter(nome_fantasia=forn_nome).first() if forn_nome else None
                if not produto:
                    continue
                peso, custo = defaults_map.get(nome_produto, (Decimal('1.0'), Decimal('0.00')))
                for _ in range(qtd):
                    peca = Peca.objects.create(
                        produto=produto,
                        status=Peca.Status.DISPONIVEL,
                        peso_gramas=peso,
                        custo_mao_de_obra=custo,
                    )
                    MovimentacaoEstoque.objects.create(
                        produto=produto,
                        peca=peca,
                        tipo=MovimentacaoEstoque.Tipo.ENTRADA,
                        quantidade=1,
                        fornecedor=fornecedor,
                        responsavel=gerente,
                        observacoes=obs,
                    )
                self.stdout.write(f'Avulsa ENT — {nome_produto} × {qtd}: criada')

    def _seed_vendas(self, gerente):
        if Venda.objects.exists():
            self.stdout.write('Vendas: já existem, pulando.')
            return

        defaults_map = {nome: (peso, custo) for nome, _, _, peso, custo in PRODUTOS}

        with transaction.atomic():
            for cli_nome, vend_user, status, desconto, obs, data_str, itens in VENDAS:
                cliente  = Cliente.objects.filter(nome=cli_nome).first()
                vendedor = Usuario.objects.filter(username=vend_user).first()

                if not cliente or not vendedor:
                    self.stderr.write('Cliente ou vendedor não encontrado, pulando venda.')
                    continue

                data_venda = timezone.make_aware(datetime.strptime(data_str, '%Y-%m-%d'))
                venda = Venda.objects.create(
                    cliente=cliente,
                    vendedor=vendedor,
                    status=status,
                    desconto_total=desconto,
                    observacoes=obs,
                    data_venda=data_venda,
                )

                for nome_produto, qtd in itens:
                    produto = Produto.objects.filter(nome=nome_produto).first()
                    if not produto:
                        self.stderr.write(f'  Produto "{nome_produto}" não encontrado, pulando item.')
                        continue

                    peso, custo = defaults_map.get(nome_produto, (Decimal('1.0'), Decimal('0.00')))
                    for _ in range(qtd):
                        peca = Peca.objects.create(
                            produto=produto,
                            status=Peca.Status.DISPONIVEL,
                            peso_gramas=peso,
                            custo_mao_de_obra=custo,
                        )
                        MovimentacaoEstoque.objects.create(
                            produto=produto,
                            peca=peca,
                            tipo=MovimentacaoEstoque.Tipo.ENTRADA,
                            quantidade=1,
                            responsavel=gerente,
                            observacoes='Estoque inicial',
                        )

                        ItemVenda.objects.create(
                            venda=venda,
                            peca=peca,
                            preco_unitario_pago=peca.preco_sugerido,
                        )

                        if status == Venda.Status.CONFIRMADA:
                            peca.status = Peca.Status.VENDIDA
                            MovimentacaoEstoque.objects.create(
                                produto=produto, peca=peca,
                                tipo=MovimentacaoEstoque.Tipo.SAIDA, quantidade=1,
                                referencia_venda=venda, responsavel=gerente,
                                observacoes=f'Venda #{venda.pk}',
                            )
                        elif status == Venda.Status.RESERVADA:
                            peca.status = Peca.Status.RESERVADA
                        elif status == Venda.Status.ORCAMENTO:
                            peca.status = Peca.Status.DISPONIVEL
                        elif status == Venda.Status.CANCELADA:
                            MovimentacaoEstoque.objects.create(
                                produto=produto, peca=peca,
                                tipo=MovimentacaoEstoque.Tipo.SAIDA, quantidade=1,
                                referencia_venda=venda, responsavel=gerente,
                                observacoes=f'Venda #{venda.pk}',
                            )
                            MovimentacaoEstoque.objects.create(
                                produto=produto, peca=peca,
                                tipo=MovimentacaoEstoque.Tipo.DEVOLUCAO, quantidade=1,
                                referencia_venda=venda, responsavel=gerente,
                                observacoes=f'Cancelamento da venda #{venda.pk}',
                            )
                            peca.status = Peca.Status.DISPONIVEL
                        peca.save(update_fields=['status'])

                venda.recalcular_total()
                self.stdout.write(
                    f'Venda #{venda.pk} — {cli_nome} ({venda.get_status_display()})'
                    f' R$ {venda.valor_total}: criada'
                )
