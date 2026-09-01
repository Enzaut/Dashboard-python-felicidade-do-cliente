"""
Dashboard "Felicidade do Cliente" - Olist

Roda com: streamlit run painel/app.py

Consome os dados gerados por codigo/etl_pipeline.py (rode esse script
antes, se os arquivos em dados/processados/ ainda não existirem).
"""

import os
import sys
from collections import Counter

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'codigo'))
from text_utils import tokeniza, corrige_texto  # noqa: E402
from viz_theme import (  # noqa: E402
    CATEGORICO_ORDEM, COR_ADIANTADO, COR_ATRASADO, COR_DETRATOR, COR_NEUTRO,
    COR_PROMOTOR, GRADE, SEQUENCIAL_AZUL, SUPERFICIE, TINTA_MUTED, TINTA_PRIMARIA, TINTA_SECUNDARIA,
)

DIR_PROCESSED = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dados', 'processados')
N_MIN_CORTE = 30  # amostra mínima pra entrar nos gráficos de categoria/estado/pagamento

st.set_page_config(page_title='Felicidade do Cliente — Olist', layout='wide')


@st.cache_data
def carregar_dados():
    caminho = os.path.join(DIR_PROCESSED, 'fato_pedidos.csv')
    if not os.path.exists(caminho):
        return None
    fp = pd.read_csv(
        caminho,
        parse_dates=['order_purchase_timestamp', 'order_delivered_customer_date', 'order_estimated_delivery_date'],
    )
    dim_clientes = pd.read_csv(os.path.join(DIR_PROCESSED, 'dim_clientes.csv'))
    fp = fp.merge(dim_clientes[['customer_id', 'customer_state']], on='customer_id', how='left')
    return fp


fato_pedidos = carregar_dados()

if fato_pedidos is None:
    st.error(
        'Não encontrei os dados processados em `dados/processados/`. '
        'Rode `python codigo/etl_pipeline.py` a partir da raiz do projeto antes de abrir o dashboard.'
    )
    st.stop()

TEMPLATE_PLOTLY = dict(
    plot_bgcolor=SUPERFICIE, paper_bgcolor=SUPERFICIE,
    font=dict(color=TINTA_PRIMARIA, family='Segoe UI, system-ui, sans-serif'),
    margin=dict(t=50, b=40, l=10, r=10),
)


# filtros na barra lateral, aplicados a todas as abas
st.sidebar.header('Filtros')

data_min = fato_pedidos['order_purchase_timestamp'].min().date()
data_max = fato_pedidos['order_purchase_timestamp'].max().date()
intervalo = st.sidebar.date_input('Período da compra', (data_min, data_max), min_value=data_min, max_value=data_max)
if isinstance(intervalo, tuple) and len(intervalo) == 2:
    inicio, fim = intervalo
else:
    inicio, fim = data_min, data_max

estados_opcoes = sorted(fato_pedidos['customer_state'].dropna().unique())
estados_sel = st.sidebar.multiselect('Estado do cliente', estados_opcoes)

categorias_opcoes = sorted(fato_pedidos['categoria_produto_principal'].dropna().unique())
categorias_sel = st.sidebar.multiselect('Categoria do produto', categorias_opcoes)

faixas_opcoes = ['Promotor', 'Neutro', 'Detrator']
faixas_sel = st.sidebar.multiselect('Faixa de satisfação', faixas_opcoes)

df = fato_pedidos[
    (fato_pedidos['order_purchase_timestamp'].dt.date >= inicio)
    & (fato_pedidos['order_purchase_timestamp'].dt.date <= fim)
].copy()
if estados_sel:
    df = df[df['customer_state'].isin(estados_sel)]
if categorias_sel:
    df = df[df['categoria_produto_principal'].isin(categorias_sel)]
if faixas_sel:
    df = df[df['faixa_satisfacao'].isin(faixas_sel)]

st.sidebar.caption(f'{len(df):,} de {len(fato_pedidos):,} pedidos selecionados')

with st.sidebar.expander('Sobre os dados'):
    st.markdown(
        '''
Base: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle).

Cada linha desta tabela é um pedido avaliado (não um item) — ver
[`codigo/etl_pipeline.py`](../codigo/etl_pipeline.py) e o
[notebook de análise](../notebooks/analise_exploratoria.ipynb) pra mais detalhe.
        '''
    )

if df.empty:
    st.warning('Nenhum pedido para os filtros selecionados. Ajuste os filtros na barra lateral.')
    st.stop()


st.title('Felicidade do Cliente — Olist')
st.caption('O que faz um cliente virar promotor ou detrator neste e-commerce brasileiro.')

nota_media = df['review_score'].mean()
nota_media_geral = fato_pedidos['review_score'].mean()
pct_promotor = (df['faixa_satisfacao'] == 'Promotor').mean() * 100
taxa_no_prazo = df['entrega_no_prazo'].astype('boolean').mean() * 100
ticket_medio = df['valor_total_pedido'].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric('Pedidos avaliados', f'{len(df):,}')
c2.metric('Nota média', f'{nota_media:.2f}', delta=f'{nota_media - nota_media_geral:+.2f} vs. geral' if len(df) != len(fato_pedidos) else None)
c3.metric('% Promotores', f'{pct_promotor:.1f}%')
c4.metric('Entregas no prazo', f'{taxa_no_prazo:.1f}%')
c5.metric('Ticket médio', f'R$ {ticket_medio:,.2f}')

# barra única empilhada com a composição Detrator / Neutro / Promotor -
# barmode='stack' já empilha sozinho, não precisa somar um base= manual
contagem_fx = df['faixa_satisfacao'].value_counts()
total_fx = contagem_fx.sum()
fig_fx = go.Figure()
for faixa, cor in [('Detrator', COR_DETRATOR), ('Neutro', COR_NEUTRO), ('Promotor', COR_PROMOTOR)]:
    valor = contagem_fx.get(faixa, 0)
    pct = valor / total_fx * 100
    fig_fx.add_trace(go.Bar(
        y=[''], x=[pct], orientation='h', name=f'{faixa} ({pct:.0f}%)',
        marker_color=cor,
        hovertemplate=f'{faixa}: {valor:,} pedidos ({pct:.1f}%)<extra></extra>',
        text=f'{pct:.0f}%' if pct > 4 else '', textposition='inside', textfont=dict(color='white'),
    ))
fig_fx.update_layout(
    barmode='stack', height=110, showlegend=True, legend=dict(orientation='h', y=-0.5),
    xaxis=dict(visible=False, range=[0, 100]), yaxis=dict(visible=False), **TEMPLATE_PLOTLY,
)
st.plotly_chart(fig_fx, width='stretch', config={'displayModeBar': False})

st.divider()

aba_panorama, aba_entrega, aba_produto, aba_pagamento, aba_texto = st.tabs([
    'Panorama', 'Entrega', 'Produto e região', 'Pagamento e tendência', 'Vozes do cliente',
])

with aba_panorama:
    cor_por_nota = {1: COR_DETRATOR, 2: COR_DETRATOR, 3: COR_NEUTRO, 4: COR_PROMOTOR, 5: COR_PROMOTOR}
    contagem_notas = df['review_score'].value_counts().sort_index()
    fig = go.Figure(go.Bar(
        x=contagem_notas.index, y=contagem_notas.values,
        marker_color=[cor_por_nota[n] for n in contagem_notas.index],
        text=[f'{v / len(df) * 100:.1f}%' for v in contagem_notas.values], textposition='outside',
        hovertemplate='Nota %{x}: %{y:,} pedidos<extra></extra>',
    ))
    fig.update_layout(
        title='Distribuição das notas', xaxis=dict(title='Nota', tickmode='array', tickvals=[1, 2, 3, 4, 5]),
        yaxis=dict(title='Qtd. de pedidos', gridcolor=GRADE), height=420, **TEMPLATE_PLOTLY,
    )
    st.plotly_chart(fig, width='stretch')

with aba_entrega:
    entregues = df.dropna(subset=['entrega_no_prazo']).copy()
    entregues['entrega_no_prazo'] = entregues['entrega_no_prazo'].astype('boolean')

    col_a, col_b = st.columns([1, 2])

    # reindex([True, False]) porque o groupby ordena por booleano (False antes
    # de True), o que bate errado com a ordem dos rótulos abaixo se não fixar
    resumo_prazo = entregues.groupby('entrega_no_prazo', observed=True)['review_score'].agg(['mean', 'count'])
    resumo_prazo = resumo_prazo.reindex([True, False])
    resumo_prazo.index = ['No prazo', 'Atrasada']
    fig1 = go.Figure(go.Bar(
        x=resumo_prazo.index, y=resumo_prazo['mean'], marker_color=[COR_PROMOTOR, COR_DETRATOR],
        text=[f'{v:.2f}' for v in resumo_prazo['mean']], textposition='outside',
        customdata=resumo_prazo['count'], hovertemplate='%{x}: nota %{y:.2f} (n=%{customdata:,})<extra></extra>',
    ))
    fig1.update_layout(title='No prazo vs. atrasada', yaxis=dict(title='Nota média', range=[0, 5.3], gridcolor=GRADE), height=420, **TEMPLATE_PLOTLY)
    col_a.plotly_chart(fig1, width='stretch')

    bins = [-9999, 0, 3, 7, 15, 9999]
    labels = ['No prazo', 'Atraso 1-3d', 'Atraso 4-7d', 'Atraso 8-15d', 'Atraso 16d+']
    cores_faixa = [COR_PROMOTOR, COR_NEUTRO, '#eb6834', COR_ATRASADO, COR_DETRATOR]
    entregues['faixa_atraso'] = pd.cut(entregues['atraso_dias'], bins=bins, labels=labels)
    resumo_atraso = entregues.groupby('faixa_atraso', observed=True)['review_score'].agg(['mean', 'count']).reindex(labels)
    fig2 = go.Figure(go.Bar(
        x=labels, y=resumo_atraso['mean'], marker_color=cores_faixa,
        text=[f'{v:.2f}' if pd.notna(v) else '' for v in resumo_atraso['mean']], textposition='outside',
        customdata=resumo_atraso['count'].fillna(0), hovertemplate='%{x}: nota %{y:.2f} (n=%{customdata:,.0f})<extra></extra>',
    ))
    fig2.update_layout(title='Efeito gradual: quanto mais atraso, pior a nota', yaxis=dict(title='Nota média', range=[0, 5.3], gridcolor=GRADE), height=420, **TEMPLATE_PLOTLY)
    col_b.plotly_chart(fig2, width='stretch')

    taxa = entregues['entrega_no_prazo'].mean() * 100
    st.info(f'{taxa:.1f}% dos pedidos (no recorte atual) chegam no prazo. Prazo de entrega é o que mais pesa na satisfação nesta base.')

with aba_produto:
    col_a, col_b = st.columns(2)

    def grafico_extremos(dados, coluna_grupo, titulo, n_top=8):
        resumo = dados.groupby(coluna_grupo).agg(nota=('review_score', 'mean'), qtd=('order_id', 'count'))
        resumo = resumo[resumo['qtd'] >= N_MIN_CORTE].sort_values('nota')
        if resumo.empty:
            return None
        extremos = pd.concat([resumo.head(n_top), resumo.tail(n_top)]).reset_index()
        extremos = extremos.drop_duplicates(subset=coluna_grupo)
        cores = [COR_DETRATOR if v < nota_media else CATEGORICO_ORDEM[0] for v in extremos['nota']]
        fig = go.Figure(go.Bar(
            y=extremos[coluna_grupo], x=extremos['nota'], orientation='h', marker_color=cores,
            customdata=extremos['qtd'], hovertemplate='%{y}: nota %{x:.2f} (n=%{customdata:,})<extra></extra>',
        ))
        fig.add_vline(x=nota_media, line_dash='dash', line_color=TINTA_MUTED)
        fig.update_layout(
            title=f'{titulo} (mín. {N_MIN_CORTE} pedidos)', xaxis=dict(title='Nota média', range=[3, 5], gridcolor=GRADE),
            height=520, **TEMPLATE_PLOTLY,
        )
        return fig

    fig_cat = grafico_extremos(df, 'categoria_produto_principal', 'Categorias: piores e melhores')
    if fig_cat:
        col_a.plotly_chart(fig_cat, width='stretch')
    else:
        col_a.info(f'Poucos dados no recorte atual para exibir categorias (mín. {N_MIN_CORTE} pedidos por categoria).')

    fig_uf = grafico_extremos(df, 'customer_state', 'Estados: piores e melhores', n_top=27)
    if fig_uf:
        col_b.plotly_chart(fig_uf, width='stretch')
    else:
        col_b.info(f'Poucos dados no recorte atual para exibir estados (mín. {N_MIN_CORTE} pedidos por estado).')

with aba_pagamento:
    col_a, col_b = st.columns(2)

    traducao_pagamento = {
        'credit_card': 'Cartão de crédito', 'boleto': 'Boleto', 'voucher': 'Voucher',
        'debit_card': 'Cartão de débito', 'not_defined': 'Não definido',
    }
    resumo_pg = df.groupby('forma_pagamento_principal').agg(nota=('review_score', 'mean'), qtd=('order_id', 'count'))
    resumo_pg = resumo_pg[resumo_pg['qtd'] >= N_MIN_CORTE].sort_values('qtd', ascending=False)
    resumo_pg.index = resumo_pg.index.map(lambda k: traducao_pagamento.get(k, k))
    fig_pg = go.Figure(go.Bar(
        x=resumo_pg.index, y=resumo_pg['nota'], marker_color=CATEGORICO_ORDEM[0],
        text=[f'{v:.2f}' for v in resumo_pg['nota']], textposition='outside',
    ))
    fig_pg.update_layout(title='Nota média por forma de pagamento', yaxis=dict(title='Nota média', range=[0, 5.3], gridcolor=GRADE), height=420, **TEMPLATE_PLOTLY)
    col_a.plotly_chart(fig_pg, width='stretch')

    df_parc = df.copy()
    df_parc['faixa_parcelas'] = pd.cut(df_parc['parcelas_pagamento_principal'], bins=[-1, 1, 3, 6, 12, 99], labels=['1x', '2-3x', '4-6x', '7-12x', '13x+'])
    resumo_parc = df_parc.groupby('faixa_parcelas', observed=True)['review_score'].mean()
    fig_parc = go.Figure(go.Bar(x=resumo_parc.index.astype(str), y=resumo_parc.values, marker_color=SEQUENCIAL_AZUL[2:7], text=[f'{v:.2f}' for v in resumo_parc.values], textposition='outside'))
    fig_parc.update_layout(title='Nota média por parcelamento', yaxis=dict(title='Nota média', range=[0, 5.3], gridcolor=GRADE), height=420, **TEMPLATE_PLOTLY)
    col_b.plotly_chart(fig_parc, width='stretch')

    df_tempo = df.copy()
    df_tempo['ano_mes'] = df_tempo['order_purchase_timestamp'].dt.to_period('M').astype(str)
    mensal = df_tempo.groupby('ano_mes').agg(nota=('review_score', 'mean'), pedidos=('order_id', 'count'))
    mensal = mensal[mensal['pedidos'] >= 20]
    if len(mensal) >= 2:
        fig_tempo = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35], vertical_spacing=0.08)
        fig_tempo.add_trace(go.Scatter(x=mensal.index, y=mensal['nota'], mode='lines+markers', line=dict(color=CATEGORICO_ORDEM[0], width=3), marker=dict(size=6), hovertemplate='%{x}: nota %{y:.2f}<extra></extra>'), row=1, col=1)
        fig_tempo.add_trace(go.Bar(x=mensal.index, y=mensal['pedidos'], marker_color=GRADE, hovertemplate='%{x}: %{y:,} pedidos<extra></extra>'), row=2, col=1)
        fig_tempo.update_layout(title='Nota média e volume de pedidos ao longo do tempo', showlegend=False, height=460, **TEMPLATE_PLOTLY)
        fig_tempo.update_yaxes(title_text='Nota média', gridcolor=GRADE, row=1, col=1)
        fig_tempo.update_yaxes(title_text='Pedidos', gridcolor=GRADE, row=2, col=1)
        st.plotly_chart(fig_tempo, width='stretch')
    else:
        st.info('Poucos meses no recorte atual para exibir a tendência temporal.')

with aba_texto:
    detratores_texto = df[(df['faixa_satisfacao'] == 'Detrator') & df['review_comment_message'].notna()]

    if len(detratores_texto) < 20:
        st.info('Poucos comentários de detratores no recorte atual para uma contagem de palavras confiável.')
    else:
        contador = Counter()
        for msg in detratores_texto['review_comment_message']:
            contador.update(set(tokeniza(msg)))
        top15 = pd.DataFrame(contador.most_common(15), columns=['palavra', 'qtd'])
        top15['pct'] = top15['qtd'] / len(detratores_texto) * 100

        col_a, col_b = st.columns([3, 2])
        fig_palavras = go.Figure(go.Bar(
            y=top15['palavra'][::-1], x=top15['pct'][::-1], orientation='h', marker_color=COR_DETRATOR,
            text=[f'{v:.0f}%' for v in top15['pct'][::-1]], textposition='outside',
        ))
        fig_palavras.update_layout(
            title=f'Palavras mais citadas por Detratores (n={len(detratores_texto):,} comentários)',
            xaxis=dict(title='% dos comentários', gridcolor=GRADE), height=460, **TEMPLATE_PLOTLY,
        )
        col_a.plotly_chart(fig_palavras, width='stretch')

        with col_b:
            st.markdown('**Alguns comentários (amostra aleatória):**')
            amostra = detratores_texto['review_comment_message'].dropna().sample(min(5, len(detratores_texto)), random_state=42)
            for texto in amostra:
                st.markdown(f'> {corrige_texto(texto)[:220]}{"…" if len(texto) > 220 else ""}')

    with st.expander('Nota sobre a mineração de texto'):
        st.markdown(
            '''
Contagem simples de palavras (não é um modelo de NLP/sentimento) nos
comentários de pedidos com nota Detratora (1-2). Cada comentário conta no
máximo 1 vez por palavra. Duas limpezas aplicadas: correção de um problema
de codificação de caracteres que já vem do dataset original da Olist, e
remoção de um apelido fictício ("lannister") que o dataset usa pra
anonimizar o nome da loja/marketplace no texto.
            '''
        )

st.divider()
st.caption(
    'Dados: Brazilian E-Commerce Public Dataset by Olist (Kaggle) · '
    'Pipeline e análise completa em `codigo/etl_pipeline.py` e `notebooks/analise_exploratoria.ipynb`'
)
