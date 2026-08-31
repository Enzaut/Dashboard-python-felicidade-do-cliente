"""
Cores e estilo compartilhados entre o notebook (matplotlib) e o painel
(plotly), pra manter a mesma identidade visual no projeto todo.

Paleta validada pra daltonismo e contraste - a ordem das cores abaixo
faz parte dessa validacao, entao evite reordenar.
"""

# categorica (ordem fixa - nunca reordenar nem "ciclar" as cores)
CATEGORICO_ORDEM = [
    '#2a78d6',  # azul
    '#eb6834',  # laranja
    '#1baf7a',  # agua
    '#eda100',  # amarelo
    '#e87ba4',  # magenta
    '#008300',  # verde
    '#4a3aa7',  # violeta
    '#e34948',  # vermelho
]

# satisfacao (Promotor / Neutro / Detrator)
COR_PROMOTOR = '#0ca30c'
COR_NEUTRO = '#fab219'
COR_DETRATOR = '#d03b3b'
CORES_SATISFACAO = {
    'Promotor': COR_PROMOTOR,
    'Neutro': COR_NEUTRO,
    'Detrator': COR_DETRATOR,
}
ORDEM_SATISFACAO = ['Detrator', 'Neutro', 'Promotor']

# atraso x adiantamento na entrega
COR_ADIANTADO = '#2a78d6'
COR_ATRASADO = '#e34948'
COR_NEUTRO_DIVERGENTE = '#c3c2b7'

# azul claro -> escuro, pra magnitude (valor, volume)
SEQUENCIAL_AZUL = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']

SUPERFICIE = '#fcfcfb'
TINTA_PRIMARIA = '#0b0b0b'
TINTA_SECUNDARIA = '#52514e'
TINTA_MUTED = '#898781'
GRADE = '#e1e0d9'
FONTE = 'Segoe UI, system-ui, sans-serif'


def aplicar_estilo_matplotlib():
    """Aplica o tema do projeto ao matplotlib (notebook e imagens exportadas)."""
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        'figure.facecolor': SUPERFICIE,
        'axes.facecolor': SUPERFICIE,
        'savefig.facecolor': SUPERFICIE,
        'axes.edgecolor': GRADE,
        'axes.labelcolor': TINTA_SECUNDARIA,
        'axes.grid': True,
        'axes.axisbelow': True,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.spines.left': False,
        'grid.color': GRADE,
        'grid.linewidth': 0.8,
        'text.color': TINTA_PRIMARIA,
        'xtick.color': TINTA_SECUNDARIA,
        'ytick.color': TINTA_SECUNDARIA,
        'font.family': 'sans-serif',
        'font.size': 11,
        'figure.dpi': 110,
        'savefig.dpi': 150,
        'legend.frameon': False,
    })
