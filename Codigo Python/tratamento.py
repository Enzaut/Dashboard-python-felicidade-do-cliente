import pandas as pd
import os

# 1. Definição robusta de caminhos
diretorio_script = os.path.dirname(os.path.abspath(__file__))
caminho_dados = os.path.normpath(os.path.join(diretorio_script, '..', 'BASE DE DADOS'))

# 2. Ingestão de Dados (Adicionando Itens e Produtos)
print(f"Buscando arquivos na pasta: {caminho_dados}")
df_reviews = pd.read_csv(os.path.join(caminho_dados, 'olist_order_reviews_dataset.csv'))
df_orders = pd.read_csv(os.path.join(caminho_dados, 'olist_orders_dataset.csv'))
df_items = pd.read_csv(os.path.join(caminho_dados, 'olist_order_items_dataset.csv'))
df_products = pd.read_csv(os.path.join(caminho_dados, 'olist_products_dataset.csv'))

# 3. Tratamento e Limpeza
print("Realizando a limpeza dos dados nulos...")
df_reviews_text = df_reviews.dropna(subset=['review_comment_message']).copy()

def classificar_sentimento(nota):
    if nota <= 2:
        return 'Negativo (Detrator)'
    elif nota == 3:
        return 'Neutro'
    else:
        return 'Positivo (Promotor)'

print("Aplicando regras de classificação de sentimento...")
df_reviews_text['categoria_sentimento'] = df_reviews_text['review_score'].apply(classificar_sentimento)

# 4. Enriquecimento de Dados (Data Merging com Produtos)
print("Executando os cruzamentos de dados (JOINs)...")

# JOIN 1: Avaliações com Pedidos (Logística)
df_voc = pd.merge(
    df_reviews_text,
    df_orders[['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp', 'order_delivered_customer_date']],
    on='order_id',
    how='inner'
)

# JOIN 2: Pedidos com Itens (Obtendo product_id e preço)
df_voc = pd.merge(
    df_voc,
    df_items[['order_id', 'product_id', 'price']],
    on='order_id',
    how='left'
)

# JOIN 3: Itens com Produtos (Obtendo a categoria do produto)
df_voc = pd.merge(
    df_voc,
    df_products[['product_id', 'product_category_name']],
    on='product_id',
    how='left'
)

# Ajuste de tipagem das datas
df_voc['order_purchase_timestamp'] = pd.to_datetime(df_voc['order_purchase_timestamp'])
df_voc['order_delivered_customer_date'] = pd.to_datetime(df_voc['order_delivered_customer_date'])

# 5. Armazenamento Estruturado (Camada Gold)
nome_arquivo_final = 'fato_voz_do_cliente.csv'
caminho_csv = os.path.join(caminho_dados, nome_arquivo_final)

print(f"Exportando os dados processados para: {caminho_csv}")
df_voc.to_csv(caminho_csv, index=False, encoding='utf-8')

print("Processamento concluído com sucesso. A base consolidada está pronta para o Power BI.")