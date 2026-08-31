# Felicidade do Cliente — Olist

Análise de dados e dashboard interativo sobre o que realmente pesa na satisfação
do cliente em um e-commerce brasileiro: prazo de entrega, categoria de produto,
região, forma de pagamento — e o que os próprios clientes insatisfeitos dizem
com as palavras deles.

**Base de dados:** [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle) — cerca de 100 mil pedidos entre set/2016 e ago/2018.

---

## Principais achados

1. **Atraso na entrega é, disparado, o que mais derruba a satisfação.** A nota média cai de **4,29** (entrega no prazo) para **2,27** (atrasada) — e quanto maior o atraso, pior a nota. Só 6,7% dos pedidos atrasam, mas o estrago que isso causa é enorme.
2. **Os próprios comentários confirmam o número:** as palavras mais citadas pelos clientes insatisfeitos são sobre entrega (*recebi, entrega, chegou, prazo, aguardando*), não sobre o produto em si.
3. **Móveis de escritório** é a categoria com pior nota entre as com volume relevante (3,62); livros e alimentos ficam no topo (~4,4+).
4. **Região também importa, provavelmente pelo mesmo motivo:** os piores estados (RR, AL, MA) são os mais distantes dos centros de distribuição.
5. A janela da **Black Friday (nov/2017 a mar/2018)** é o pior trecho da série no tempo — bate com a ideia de que o volume extra sobrecarrega a entrega.

Análise completa, com a explicação por trás de cada achado: [`notebooks/analise_exploratoria.ipynb`](notebooks/analise_exploratoria.ipynb).

<p align="center">
  <img src="imagens/02_prazo_de_entrega.png" width="800" alt="Nota média cai de 4.29 para 2.27 quando a entrega atrasa">
</p>

---

## Dashboard interativo

`painel/app.py` (feito em Streamlit) deixa explorar os mesmos dados com filtros
ao vivo por período, estado, categoria e nível de satisfação:

- **Panorama** — visão geral e distribuição das notas
- **Entrega** — o motivo que mais pesa, com o efeito do atraso bem visível
- **Produto e região** — piores e melhores categorias e estados
- **Pagamento e tendência** — forma de pagamento, parcelamento e evolução mês a mês
- **Vozes do cliente** — palavras mais citadas por quem deu nota baixa (muda junto com os filtros) e alguns comentários reais

```bash
pip install -r requirements.txt
python codigo/etl_pipeline.py     # organiza os dados brutos em dados/processados/
streamlit run painel/app.py
```

---

## Como os dados foram organizados

`codigo/etl_pipeline.py` lê os 9 arquivos originais da Olist e monta um formato
bem comum em BI: uma tabela principal e um punhado de tabelas de apoio, todas
em `dados/processados/`.

- **`fato_pedidos`** é a tabela principal: uma linha para cada pedido avaliado (cerca de 98,7 mil linhas). É a base de praticamente tudo neste projeto.
- As tabelas de apoio guardam informação de clientes, produtos, vendedores e datas.
- **`fato_itens_pedido`** existe à parte, com uma linha por item do pedido, pra quando a análise precisa descer nesse nível de detalhe.

Duas decisões valem menção, porque mudam os números:

- **Um bug que encontrei e corrigi:** a primeira versão deste script cruzava as
  avaliações com os itens de cada pedido usando só o número do pedido. Pedidos
  com mais de um item faziam a mesma avaliação contar várias vezes — o arquivo
  final tinha 48.166 linhas para apenas 40.668 avaliações de verdade. Corrigi
  agrupando os itens por pedido antes de juntar com as avaliações, e deixei uma
  verificação automática no próprio script pra garantir que isso não se repita.
- **Amostra maior:** a primeira versão só usava avaliações que também tinham um
  comentário escrito (~41 mil). A versão atual usa todas as avaliações com nota,
  com ou sem comentário (~98,7 mil) — o texto continua disponível pra quem
  quiser analisar os comentários à parte.

---

## Estrutura do projeto

```
├── dados/
│   ├── brutos/            # arquivos originais da Olist (não vem no repositório - ver "Como rodar")
│   └── processados/       # dados organizados, gerados pelo script (também não vem no repositório)
├── codigo/
│   ├── etl_pipeline.py    # organiza os dados brutos
│   ├── viz_theme.py       # cores e estilo usados no notebook e no painel
│   └── text_utils.py      # limpeza de texto usada nos comentários dos clientes
├── notebooks/
│   └── analise_exploratoria.ipynb
├── painel/
│   └── app.py             # o dashboard
├── imagens/                # gráficos exportados (usados aqui no README e no post)
└── requirements.txt
```

`notebooks/` ficou em inglês por ser o nome do próprio recurso do Jupyter — é
assim que qualquer pessoa de dados vai procurar essa pasta. `README.md` e
`requirements.txt` também ficam como estão: são nomes que o GitHub e o pip
reconhecem especificamente por esse nome.

## Como rodar do zero

1. Baixe o [dataset no Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) e coloque os 9 arquivos em `dados/brutos/`.
2. `pip install -r requirements.txt`
3. `python codigo/etl_pipeline.py` — gera `dados/processados/`.
4. `streamlit run painel/app.py` — abre o dashboard, ou abra `notebooks/analise_exploratoria.ipynb` pra ver a análise completa.

## Tecnologias usadas

Python, pandas, numpy, matplotlib e seaborn (no notebook), Plotly e Streamlit (no dashboard).

## Próximos passos

Uma versão do mesmo dashboard em Power BI, como segunda peça do portfólio.

## Sobre os dados

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
disponibilizado publicamente no Kaggle sob a licença CC BY-NC-SA 4.0.
