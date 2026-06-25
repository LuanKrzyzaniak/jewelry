# Sistema de Gestão de Joalheria

Trabalho da disciplina de Tópicos Especiais em Programação — UFFS Campus Chapecó.
Sistema web em Django para controle de estoque, vendas e precificação dinâmica de peças de joalheria.

## Requisitos

- Python 3.11 ou superior (usei 3.14)
- pip

## Banco de dados

O projeto usa SQLite por padrão. 

Aplicar as migrações:
```
python manage.py migrate
```

## Populando dados iniciais (seed)

Existem dois comandos de seed:

- `seed`: cadastra apenas os dados base (metais, ligas e tipos de produto). Era pra ser uma seeds de prod, mas acabou ficando legado. Pode ignorar.
- `seed_dev`: cadastra dados base e também dados de teste completos (usuários, clientes, fornecedores, produtos, peças, vendas e movimentações de estoque).

Para rodar:
```
python manage.py seed_dev
```

Usuários criados pelo `seed_dev`:

| Usuário | Senha | Perfil   |
|---------|-------|----------|
| admin   | admin | Gerente  |
| user    | user  | Vendedor |

## Resetando o banco do zero

Para apagar o banco atual e recriar já populado com as seeds, rode no bash:
```
sh resetdb.sh
```

Esse script deleta o `db.sqlite3`, aplica as migrações e roda o `seed_dev`. 

## Rodando o servidor

```
python manage.py runserver
```

A página de login pede usuário e senha (ver tabela de usuários acima, criados na seed).

## Cotação de metais (integração com API externa)

A atualização de cotação de ouro e prata é feita pelo comando:
```
python manage.py atualizar_cotacoes
```

Por padrão, sem chave de API configurada, o comando usa valores fixos simulados (modo mock) para não bloquear o desenvolvimento. Para usar a API real (GoldAPI.io), definir a chave em `jewelry/settings.py`, na variável `GOLDAPI_KEY`.

## Rodando os testes automatizados

```
python manage.py test
```

Para rodar os testes de um app específico:
```
python manage.py test catalogo
python manage.py test vendas
```

## Estrutura do projeto

| App         | Responsabilidade                                                          |
|-------------|----------------------------------------------------------------------------|
| usuarios    | Autenticação e perfis de acesso (Gerente / Vendedor)                       |
| catalogo    | Metais, ligas, cotações, produtos e peças                                  |
| estoque     | Movimentações de estoque e lotes de entrada/saída                          |
| vendas      | Clientes, fornecedores e vendas                                            |
| dashboard   | Página inicial com indicadores gerenciais                                  |
| relatorios  | Relatórios de vendas por período e giro de estoque                         |

## Acesso por perfil

- Gerente: acesso completo, incluindo relatórios, cadastro de fornecedores, ligas, metais e cotações.
- Vendedor: acesso a vendas, clientes, peças e produtos, sem acesso aos relatórios gerenciais nem ao cadastro de fornecedores.
