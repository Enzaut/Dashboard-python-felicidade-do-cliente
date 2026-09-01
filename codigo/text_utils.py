"""Limpeza de texto usada na contagem de palavras dos comentários dos clientes."""

import re

STOP_PT = set('''a ao aos as com como da das de dela dele deles depois do dos e ela elas ele eles em entre era essa
essas esse esses esta estas este estes eu foi for foram isso isto ja la lhe mais mas me mesmo meu meus minha minhas
muito na nao nas nem no nos nossa nossas nosso nossos num numa o os ou para pela pelas pelo pelos por pra pro qual
quando que quem se sem ser seu seus sua suas so tal tambem te tem tera teu teus teve tinha tive tu tua tuas um uma
umas uns vc voce voces era sao vai vou fica ficou tao ate onde outra outro pois ainda apenas agora dia'''.split())

# nome ficticio que a Olist usa pra anonimizar a loja/marketplace no texto -
# nao e uma palavra real do cliente, entao fica fora da contagem
PLACEHOLDER_ANONIMIZACAO = {'lannister'}


def corrige_palavra(palavra):
    """Reverte texto corrompido (UTF-8 lido como cp1252 em algum ponto do
    pipeline original da Olist); quando não dá pra reverter, devolve como veio."""
    try:
        return palavra.encode('cp1252').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return palavra


def corrige_texto(texto):
    """corrige_palavra preservando maiúsculas/espaços, pra exibir uma citação."""
    return ' '.join(corrige_palavra(p) for p in texto.split())


def tokeniza(texto):
    texto = texto.lower()
    texto = ' '.join(corrige_palavra(p) for p in texto.split())
    texto = re.sub(r'[^a-zà-ÿ\s]', ' ', texto)
    tokens = [t for t in texto.split() if len(t) > 2]
    return [t for t in tokens if t not in STOP_PT and t not in PLACEHOLDER_ANONIMIZACAO]
