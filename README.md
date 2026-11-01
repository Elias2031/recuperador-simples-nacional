# Recuperador Tributário — Simples Nacional (Django)

> Este sistema está sendo substituído por agentes de IA; o código foi aberto como portfólio e referência.

Sistema web para identificar e calcular **tributos pagos a maior no Simples Nacional**, cruzando as notas fiscais de saída da empresa com os valores declarados no PGDAS-D.

## O problema de negócio

Empresas do Simples Nacional frequentemente recolhem o DAS sobre toda a receita, sem segregar as vendas de mercadorias sujeitas à **substituição tributária do ICMS** ou à **tributação monofásica de PIS/COFINS**. Nesses casos, a parcela de ICMS, PIS e COFINS embutida na alíquota do Simples é paga em duplicidade e pode ser recuperada.

Fazer esse levantamento à mão exige classificar item a item (NCM, CST/CSOSN, CFOP) milhares de notas por competência, refazer o cálculo do DAS e comparar com o que foi declarado. O sistema automatiza esse trabalho.

## Funcionalidades

- **Autenticação própria** (login por e-mail, cadastro e redefinição de senha por e-mail).
- **Cadastro de empresas**, com preenchimento automático a partir do CNPJ (APIs públicas `publica.cnpj.ws` e `receitaws`).
- **Importação em lote** de XMLs de NF-e e CT-e (avulsos ou em `.zip`), processados em segundo plano com **Celery + Redis**.
- **Importação do extrato do PGDAS-D (PDF)**, extraindo receita bruta, RBT12 e os valores pagos por tributo em cada competência.
- **Listagem de notas e itens** por empresa e período.
- **Análise tributária por NCM**: consulta à tabela TIPI e à API **Legisweb** (alíquota de ICMS, ST interna e interestadual, PIS/COFINS e benefícios fiscais) para classificar cada produto.
- **Apuração mensal**: identificação da faixa do Anexo I pela RBT12, cálculo da alíquota efetiva e da repartição entre tributos, segregação das receitas (tributada, ST, monofásica, isenta/imune) e cálculo do crédito de ICMS, PIS e COFINS a recuperar.
- **Espelho do PGDAS-D em PDF** com a apuração recalculada (xhtml2pdf).

## Arquitetura e stack

- **Python 3 / Django 5.2** — aplicação web (apps `accounts` e `core`).
- **SQLite** (padrão de desenvolvimento) via ORM do Django.
- **Celery 5 + Redis** — fila para o processamento dos XMLs.
- **pandas / openpyxl** — leitura da tabela TIPI e geração de planilhas.
- **PyPDF2** — leitura do extrato do PGDAS-D.
- **xhtml2pdf / reportlab** — geração do espelho em PDF.
- **Bootstrap 5, jQuery e DataTables** — interface.

```
recuperacao_sn_web/
├── accounts/            # usuário customizado (login por e-mail), cadastro e reset de senha
├── core/
│   ├── models.py        # Empresa, Competência, NotaFiscal, Itens, PGDAS, ApuraçãoFiscal, NCM...
│   ├── views/           # telas (upload, empresas, notas, apurações, análise tributária, espelho)
│   ├── services/        # extração de XML/PDF, cálculo do Simples, integração Legisweb e CNPJ
│   ├── tasks.py         # tarefas Celery
│   └── templates/
├── recuperacao_sn_web/  # settings, urls, celery
└── _RECURSOS_/tipi.xlsx # tabela TIPI (pública)
```

Alguns módulos em `core/services/` (por exemplo `sped.py`, `segregador.py`, `calculos_tributarios.py`) vieram de uma versão anterior, em linha de comando, que gerava SPED e planilhas de segregação; eles ainda importam o pacote antigo `MODULES` e não estão ligados às telas do Django.

## Como executar

Pré-requisitos: Python 3.11+ e um servidor Redis (para o Celery).

```bash
# 1. Ambiente virtual e dependências
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt

# 2. Variáveis de ambiente
copy .env.example .env         # Linux/macOS: cp .env.example .env
# edite o .env com sua SECRET_KEY, SMTP e token Legisweb

# 3. Banco de dados e usuário administrador
cd recuperacao_sn_web
python manage.py migrate
python manage.py createsuperuser

# 4. Worker do Celery (em outro terminal, com o Redis rodando)
celery -A recuperacao_sn_web worker -l info --pool=solo

# 5. Servidor web
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/`.

### Variáveis de ambiente

| Variável | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | chave secreta do Django (obrigatória em produção) |
| `DJANGO_DEBUG` | `True`/`False` |
| `DJANGO_ALLOWED_HOSTS` | hosts permitidos, separados por vírgula |
| `DEFAULT_DOMAIN` | domínio usado no link de redefinição de senha |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | envio de e-mail (SMTP) |
| `LEGISWEB_USER_ID`, `LEGISWEB_TOKEN` | credenciais da API Legisweb (análise por NCM) |
| `CELERY_BROKER_URL` | URL do Redis |
| `SPED_CONTABILISTA_*` | dados do contabilista no registro 0100 (módulo legado de SPED) |

O arquivo `.env` é carregado automaticamente pelo `settings.py` (via `python-dotenv`). Nunca versione o `.env`.

## Autor

**Elias Silva** — Morpho Automações · [github.com/Elias2031](https://github.com/Elias2031)

## Licença

[MIT](LICENSE)
