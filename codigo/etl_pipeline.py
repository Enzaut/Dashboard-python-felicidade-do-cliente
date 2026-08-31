"""
Pipeline de ETL - Projeto "Felicidade do Cliente" (Olist)

Le os dados brutos da Olist e organiza tudo em uma tabela principal
(fato_pedidos) + tabelas de apoio, prontas para o notebook, o dashboard
e depois o Power BI.

Corrigido em relacao a primeira versao (tratamento.py): o join antigo
duplicava avaliacoes de pedidos com mais de um item (48.166 linhas para
40.668 avaliacoes reais) e descartava quem avaliou sem escrever comentario.
Aqui os itens/pagamentos sao agregados por pedido antes do join, e todas
as avaliacoes com nota entram (nao so as com texto).
"""

import os

import numpy as np
import pandas as pd

DIR_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DIR_RAW = os.path.normpath(os.path.join(DIR_SCRIPT, '..', 'dados', 'brutos'))
DIR_PROCESSED = os.path.normpath(os.path.join(DIR_SCRIPT, '..', 'dados', 'processados'))
os.makedirs(DIR_PROCESSED, exist_ok=True)


def caminho_raw(nome_arquivo):
    return os.path.join(DIR_RAW, nome_arquivo)


print(f"Lendo os arquivos brutos em: {DIR_RAW}")

df_customers = pd.read_csv(caminho_raw('olist_customers_dataset.csv'))
df_geo = pd.read_csv(caminho_raw('olist_geolocation_dataset.csv'))
df_items = pd.read_csv(caminho_raw('olist_order_items_dataset.csv'))
df_payments = pd.read_csv(caminho_raw('olist_order_payments_dataset.csv'))
df_reviews = pd.read_csv(
    caminho_raw('olist_order_reviews_dataset.csv'),
    parse_dates=['review_creation_date', 'review_answer_timestamp'],
)
df_orders = pd.read_csv(
    caminho_raw('olist_orders_dataset.csv'),
    parse_dates=[
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date',
    ],
)
df_products = pd.read_csv(caminho_raw('olist_products_dataset.csv'))
df_sellers = pd.read_csv(caminho_raw('olist_sellers_dataset.csv'))
df_traducao = pd.read_csv(caminho_raw('product_category_name_translation.csv'))

print("Construindo as tabelas de apoio...")

dim_clientes = (
    df_customers
    .rename(columns={'customer_zip_code_prefix': 'zip_code_prefix'})
    .drop_duplicates(subset='customer_id')
    .copy()
)

dim_produtos = df_products.merge(df_traducao, on='product_category_name', how='left')
dim_produtos['product_category_name'] = dim_produtos['product_category_name'].fillna('categoria_nao_informada')
dim_produtos['product_category_name_english'] = dim_produtos['product_category_name_english'].fillna(
    dim_produtos['product_category_name']
)

# typos que ja vem do arquivo original da Olist (ex.: 'costruction_tools_tools')
CORRECOES_TYPO_CATEGORIA_EN = {
    'costruction_tools_garden': 'construction_tools_garden',
    'costruction_tools_tools': 'construction_tools_tools',
    'fashio_female_clothing': 'fashion_female_clothing',
    'home_confort': 'home_comfort',
}
dim_produtos['product_category_name_english'] = dim_produtos['product_category_name_english'].replace(
    CORRECOES_TYPO_CATEGORIA_EN
)
dim_produtos = dim_produtos.drop_duplicates(subset='product_id').copy()

dim_vendedores = (
    df_sellers
    .rename(columns={'seller_zip_code_prefix': 'zip_code_prefix'})
    .drop_duplicates(subset='seller_id')
    .copy()
)

# mediana de lat/lng por CEP: reduz o ruido de geocodificacao do dataset original
dim_geolocalizacao = (
    df_geo.groupby('geolocation_zip_code_prefix')
    .agg(
        lat=('geolocation_lat', 'median'),
        lng=('geolocation_lng', 'median'),
        cidade=('geolocation_city', lambda s: s.mode().iat[0] if not s.mode().empty else np.nan),
        estado=('geolocation_state', lambda s: s.mode().iat[0] if not s.mode().empty else np.nan),
    )
    .reset_index()
    .rename(columns={'geolocation_zip_code_prefix': 'zip_code_prefix'})
)

MESES_PT = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
    7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
}
DIAS_SEMANA_PT = {
    0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 3: 'Quinta-feira',
    4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo',
}

data_min = df_orders['order_purchase_timestamp'].min().normalize()
data_max = df_orders['order_estimated_delivery_date'].max().normalize()
dim_tempo = pd.DataFrame({'data': pd.date_range(data_min, data_max, freq='D')})
dim_tempo['ano'] = dim_tempo['data'].dt.year
dim_tempo['mes'] = dim_tempo['data'].dt.month
dim_tempo['nome_mes'] = dim_tempo['mes'].map(MESES_PT)
dim_tempo['trimestre'] = dim_tempo['data'].dt.quarter
dim_tempo['dia_semana'] = dim_tempo['data'].dt.dayofweek.map(DIAS_SEMANA_PT)
dim_tempo['ano_mes'] = dim_tempo['data'].dt.to_period('M').astype(str)

# Agrega itens e pagamentos por pedido ANTES do join final - e aqui que se
# evita a duplicacao de avaliacoes que existia na primeira versao do script.
print("Agregando itens e pagamentos por pedido...")

itens_com_categoria = df_items.merge(
    dim_produtos[['product_id', 'product_category_name_english']], on='product_id', how='left'
)

agg_itens = itens_com_categoria.groupby('order_id').agg(
    valor_produtos=('price', 'sum'),
    valor_frete=('freight_value', 'sum'),
    qtd_itens=('order_item_id', 'count'),
).reset_index()

# categoria do item de maior valor do pedido, so como rotulo representativo -
# para analises de categoria de verdade, usar o fato_itens_pedido abaixo
produto_principal = (
    itens_com_categoria.sort_values('price', ascending=False)
    .drop_duplicates(subset='order_id', keep='first')
    [['order_id', 'product_id', 'product_category_name_english']]
    .rename(columns={'product_category_name_english': 'categoria_produto_principal'})
)

agg_itens = agg_itens.merge(produto_principal, on='order_id', how='left')
agg_itens['valor_total_pedido'] = agg_itens['valor_produtos'] + agg_itens['valor_frete']

pagamento_principal = (
    df_payments.sort_values('payment_sequential')
    .drop_duplicates(subset='order_id', keep='first')
    [['order_id', 'payment_type', 'payment_installments']]
    .rename(columns={
        'payment_type': 'forma_pagamento_principal',
        'payment_installments': 'parcelas_pagamento_principal',
    })
)
agg_pagamentos = df_payments.groupby('order_id').agg(
    valor_total_pago=('payment_value', 'sum'),
    qtd_formas_pagamento=('payment_type', 'nunique'),
).reset_index()
agg_pagamentos = agg_pagamentos.merge(pagamento_principal, on='order_id', how='left')

reviews_dedup = (
    df_reviews.sort_values('review_creation_date')
    .drop_duplicates(subset='order_id', keep='last')
    .copy()
)

print("Construindo o fato_pedidos...")

fato_pedidos = (
    reviews_dedup
    .merge(df_orders, on='order_id', how='inner')
    .merge(agg_itens, on='order_id', how='left')
    .merge(agg_pagamentos, on='order_id', how='left')
)

fato_pedidos['dias_entrega'] = (
    fato_pedidos['order_delivered_customer_date'] - fato_pedidos['order_purchase_timestamp']
).dt.days
fato_pedidos['atraso_dias'] = (
    fato_pedidos['order_delivered_customer_date'] - fato_pedidos['order_estimated_delivery_date']
).dt.days

fato_pedidos['entrega_no_prazo'] = (fato_pedidos['atraso_dias'] <= 0).astype('boolean')
fato_pedidos.loc[fato_pedidos['order_delivered_customer_date'].isna(), 'entrega_no_prazo'] = pd.NA


def faixa_satisfacao(nota):
    if nota <= 2:
        return 'Detrator'
    elif nota == 3:
        return 'Neutro'
    else:
        return 'Promotor'


fato_pedidos['faixa_satisfacao'] = fato_pedidos['review_score'].apply(faixa_satisfacao)
fato_pedidos['tem_comentario'] = fato_pedidos['review_comment_message'].notna()

fato_pedidos = fato_pedidos[[
    'order_id', 'customer_id', 'review_id', 'review_score', 'faixa_satisfacao',
    'review_comment_title', 'review_comment_message', 'tem_comentario',
    'review_creation_date', 'review_answer_timestamp',
    'order_status', 'order_purchase_timestamp', 'order_approved_at',
    'order_delivered_carrier_date', 'order_delivered_customer_date',
    'order_estimated_delivery_date', 'dias_entrega', 'atraso_dias', 'entrega_no_prazo',
    'qtd_itens', 'valor_produtos', 'valor_frete', 'valor_total_pedido',
    'product_id', 'categoria_produto_principal',
    'forma_pagamento_principal', 'parcelas_pagamento_principal',
    'valor_total_pago', 'qtd_formas_pagamento',
]].copy()

print(
    f"  fato_pedidos: {len(fato_pedidos):,} linhas | "
    f"order_id unicos: {fato_pedidos['order_id'].nunique():,} | "
    f"review_id unicos: {fato_pedidos['review_id'].nunique():,}"
)
assert len(fato_pedidos) == fato_pedidos['order_id'].nunique(), "Duplicidade detectada no fato_pedidos!"

# fato_itens_pedido fica no grao de item de proposito (1 linha por item, nao
# por pedido) - use esta tabela para analises por categoria/vendedor.
print("Construindo o fato_itens_pedido...")

fato_itens_pedido = (
    itens_com_categoria
    .merge(
        df_orders[['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp']],
        on='order_id', how='left',
    )
    .merge(dim_vendedores[['seller_id', 'seller_state']], on='seller_id', how='left')
    .merge(reviews_dedup[['order_id', 'review_score']], on='order_id', how='left')
    .rename(columns={'product_category_name_english': 'categoria_produto'})
)

print(f"Exportando as tabelas para: {DIR_PROCESSED}")

tabelas = {
    'dim_clientes.csv': dim_clientes,
    'dim_produtos.csv': dim_produtos,
    'dim_vendedores.csv': dim_vendedores,
    'dim_geolocalizacao.csv': dim_geolocalizacao,
    'dim_tempo.csv': dim_tempo,
    'fato_pedidos.csv': fato_pedidos,
    'fato_itens_pedido.csv': fato_itens_pedido,
}
for nome, tabela in tabelas.items():
    tabela.to_csv(os.path.join(DIR_PROCESSED, nome), index=False, encoding='utf-8')
    print(f"  {nome}: {len(tabela):,} linhas, {len(tabela.columns)} colunas")

print("Pipeline concluido com sucesso. Dados prontos em dados/processados/.")
