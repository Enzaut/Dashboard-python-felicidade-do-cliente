"""
Utilitários de texto compartilhados entre o notebook de análise e o
dashboard, usados na mineração simples de palavras dos comentários de
clientes Detratores.
"""

import re

STOP_PT = set('''a ao aos as com como da das de dela dele deles depois do dos e ela elas ele eles em entre era essa
essas esse esses esta estas este estes eu foi for foram isso isto ja la lhe mais mas me mesmo meu meus minha minhas
muito na nao nas nem no nos nossa nossas nosso nossos num numa o os ou para pela pelas pelo pelos por pra pro qual
quando que quem se sem ser seu seus sua suas so tal tambem te tem tera teu teus teve tinha tive tu tua tuas um uma
umas uns vc voce voces era sao vai vou fica ficou tao ate onde outra outro pois ainda apenas agora dia'''.split())

# Nome fictício usado no dataset público da Olist para anonimizar a
# loja/marketplace dentro do texto dos comentários - não é uma palavra
# real do cliente, então é removido da contagem.
PLACEHOLDER_ANONIMIZACAO = {'lannister'}


def corrige_palavra(palavra):
    """Reverte mojibake (texto UTF-8 originalmente lido/gravado como
    cp1252 em algum ponto do pipeline da Olist) palavra a palavra; quando
    não é reversível, devolve a palavra como veio."""
    try:
        return palavra.encode('cp1252').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return palavra


def corrige_texto(texto):
    """Igual a corrige_palavra, mas preservando maiúsculas/espaços - usado
    para exibir uma citação de comentário (não para tokenizar)."""
    return ' '.join(corrige_palavra(p) for p in texto.split())


def tokeniza(texto):
    """Quebra um comentário em tokens limpos: minúsculo, mojibake
    corrigido, só letras (com acentos), sem stopwords em pt-BR e sem o
    placeholder de anonimização."""
    texto = texto.lower()
    texto = ' '.join(corrige_palavra(p) for p in texto.split())
    texto = re.sub(r'[^a-zà-ÿ\s]', ' ', texto)
    tokens = [t for t in texto.split() if len(t) > 2]
    return [t for t in tokens if t not in STOP_PT and t not in PLACEHOLDER_ANONIMIZACAO]
