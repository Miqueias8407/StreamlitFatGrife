import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import glob

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Faturas",
    page_icon="💳",
    layout="wide"
)

# Paleta de cores
COLORS = {
    "background": "#121212",
    "secondary": "#1E1E1E",
    "text": "#E0E0E0",
    "paid": "#2E86AB",
    "unpaid": "#FF6B6B",
    "highlight": "#4ECDC4",
    "card_bg": "#1E1E1E",
    "sidebar": "#253644"  # Nova cor adicionada para o sidebar
}

# Função para formatar números com ponto nos milhares e vírgula nos decimais
def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Estilos CSS personalizados
def local_css():
    st.markdown(f"""
    <style>
        /* Estilo geral */
        .stApp {{
            background-color: {COLORS['background']};
            color: {COLORS['text']};
        }}
        
        /* Sidebar - Estilo personalizado */
        section[data-testid="stSidebar"] > div {{
            background-color: {COLORS['sidebar']} !important;
        }}
        
        /* Elementos do sidebar */
        .css-1d391kg, .css-1y4p8pa {{
            background-color: {COLORS['sidebar']} !important;
        }}
        
        /* Texto do sidebar */
        .stSidebar .css-10trblm {{
            color: {COLORS['text']} !important;
        }}
        
        /* Restante dos estilos */
        .st-bb, .st-at, .st-ar, .st-as {{
            background-color: {COLORS['secondary']};
        }}
        .css-10trblm {{
            color: {COLORS['text']};
        }}
        .card {{
            background-color: {COLORS['card_bg']};
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }}
        .card-title {{
            font-size: 14px;
            color: {COLORS['text']};
            opacity: 0.8;
            margin-bottom: 10px;
        }}
        .card-value {{
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['highlight']};
        }}
        .css-1cpxqw2 {{
            border: 1px solid {COLORS['secondary']};
        }}
        .stDataFrame {{
            background-color: {COLORS['secondary']};
        }}
        .st-b7 {{
            background-color: {COLORS['highlight']};
        }}
        .stSlider>div>div>div>div {{
            background-color: {COLORS['highlight']} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

local_css()

# Função para carregar dados das planilhas
@st.cache_data
def load_data():
    # Caminho para as planilhas
    path = r"K:\RelatoriosFinanceiros\Rel_441\*.xlsx"  # Assumindo arquivos Excel
    
    all_files = glob.glob(path)
    dfs = []
    
    for file in all_files:
        try:
            df = pd.read_excel(file)
            # Padronizar nomes de colunas (caso haja variações)
            df.columns = df.columns.str.upper()
            dfs.append(df)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo {file}: {e}")
    
    if not dfs:
        st.error("Nenhuma planilha encontrada ou foi possível ler.")
        return pd.DataFrame()
    
    # Concatenar todos os DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Renomear colunas conforme solicitado
    combined_df = combined_df.rename(columns={
        'FATURA': 'ID',
        'CLIENTE': 'Cliente',
        'VLR FATUR': 'Valor',
        'VENCIMEN': 'Vencimento',
        'LIQUIDADA/ATRASADA': 'Status'
    })
    
    # Converter status para valores padronizados
    combined_df['Status'] = combined_df['Status'].apply(
        lambda x: 'Paga' if str(x).strip().upper() == 'LIQUIDADO' else 'Em aberto'
    )
    
    # Converter datas se necessário
    if 'Vencimento' in combined_df.columns:
        combined_df['Vencimento'] = pd.to_datetime(combined_df['Vencimento'], errors='coerce')
    
    return combined_df.dropna(subset=['ID', 'Valor', 'Vencimento'])

# Carregar dados
df = load_data()

if df.empty:
    st.error("Não foi possível carregar os dados. Verifique os arquivos na pasta.")
    st.stop()

# Filtros
st.sidebar.title("Filtros")

# Seletor de intervalo de datas
min_date = df['Vencimento'].min().date()
max_date = df['Vencimento'].max().date()

date_range = st.sidebar.date_input(
    "Selecione o intervalo de datas:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Verificar se selecionou um intervalo válido
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Outros filtros
status_filter = st.sidebar.multiselect(
    "Status", 
    options=['Paga', 'Em aberto'], 
    default=['Paga', 'Em aberto']
)

client_filter = st.sidebar.multiselect(
    "Cliente", 
    options=df['Cliente'].unique()
)

# Aplicar filtros
filtered_df = df.copy()
filtered_df = filtered_df[
    (filtered_df['Vencimento'].dt.date >= start_date) & 
    (filtered_df['Vencimento'].dt.date <= end_date)
]

if status_filter:
    filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
if client_filter:
    filtered_df = filtered_df[filtered_df['Cliente'].isin(client_filter)]

# Cards de resumo
st.title("📊 Dashboard de Faturas")

# Linha do tempo interativa
st.subheader(f"Período selecionado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Total de Faturas</div>
        <div class="card-value">{len(filtered_df)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    unpaid = filtered_df[filtered_df['Status'] == 'Em aberto']['Valor'].sum()
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Valor em Aberto</div>
        <div class="card-value">{format_brl(unpaid)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    paid = filtered_df[filtered_df['Status'] == 'Paga']['Valor'].sum()
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Valor Pago</div>
        <div class="card-value">{format_brl(paid)}</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    total_value = filtered_df['Valor'].sum()
    st.markdown(f"""
    <div class="card">
        <div class="card-title">Valor Total</div>
        <div class="card-value">{format_brl(total_value)}</div>
    </div>
    """, unsafe_allow_html=True)

# Gráficos
st.markdown("---")
col5, col6 = st.columns([6, 4])

with col5:
    # Agrupar por período selecionado
    if (end_date - start_date).days <= 31:  # Se intervalo menor que 1 mês, agrupar por dia
        filtered_df['Periodo'] = filtered_df['Vencimento'].dt.strftime('%d/%m')
        title = 'Faturas por Dia'
    elif (end_date - start_date).days <= 365:  # Se intervalo menor que 1 ano, agrupar por mês
        filtered_df['Periodo'] = filtered_df['Vencimento'].dt.strftime('%m/%Y')
        title = 'Faturas por Mês'
    else:  # Para intervalos maiores, agrupar por ano
        filtered_df['Periodo'] = filtered_df['Vencimento'].dt.strftime('%Y')
        title = 'Faturas por Ano'
    
    # Gráfico de barras
    period_summary = filtered_df.groupby(['Periodo', 'Status'])['Valor'].sum().unstack().fillna(0)
    
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=period_summary.index,
        y=period_summary['Paga'],
        name='Pagas',
        marker_color=COLORS['paid']
    ))
    fig_bar.add_trace(go.Bar(
        x=period_summary.index,
        y=period_summary['Em aberto'],
        name='Em aberto',
        marker_color=COLORS['unpaid']
    ))
    
    fig_bar.update_layout(
        title=title,
        plot_bgcolor=COLORS['secondary'],
        paper_bgcolor=COLORS['secondary'],
        font_color=COLORS['text'],
        barmode='group',
        hovermode="x unified",
        xaxis_title="Período",
        yaxis_title="Valor (R$)"
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

with col6:
    # Gráfico de pizza
    status_counts = filtered_df['Status'].value_counts()
    fig_pie = go.Figure(go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        hole=.4,
        marker_colors=[COLORS['paid'], COLORS['unpaid']],
        textinfo='percent+value'
    ))
    
    fig_pie.update_layout(
        title='Proporção de Status',
        plot_bgcolor=COLORS['secondary'],
        paper_bgcolor=COLORS['secondary'],
        font_color=COLORS['text'],
        showlegend=True
    )
    
    st.plotly_chart(fig_pie, use_container_width=True)

# Tabela de faturas recentes
st.markdown("---")

# Cria duas colunas para o título e o campo de busca
col_title, col_search = st.columns([4, 2])

with col_title:
    st.subheader(f"Faturas ({len(filtered_df)} no total)")

with col_search:
    # Adiciona um campo de texto para filtrar
    search_term = st.text_input("Filtrar faturas:", placeholder="Digite ID, Cliente, Valor...", label_visibility="collapsed")

# Aplica o filtro de texto se algo foi digitado
if search_term:
    search_lower = search_term.lower()
    filtered_df = filtered_df[
        filtered_df['ID'].astype(str).str.lower().str.contains(search_lower) |
        filtered_df['Cliente'].astype(str).str.lower().str.contains(search_lower) |
        filtered_df['Valor'].astype(str).str.lower().str.contains(search_lower) |
        filtered_df['Vencimento'].astype(str).str.lower().str.contains(search_lower) |
        filtered_df['Status'].astype(str).str.lower().str.contains(search_lower)
    ]

# Adicionar ícones de status
def status_icon(status):
    return "✅" if status == "Paga" else "⚠️"

display_df = filtered_df.copy()
display_df['Status'] = display_df['Status'].apply(status_icon)
display_df = display_df.sort_values('Vencimento', ascending=False)

# Formatar a coluna Valor na tabela
display_df['Valor'] = display_df['Valor'].apply(lambda x: format_brl(x))

st.dataframe(
    display_df[['ID', 'Cliente', 'Valor', 'Vencimento', 'Status']],
    column_config={
        "Vencimento": st.column_config.DateColumn(format="DD/MM/YYYY")
    },
    use_container_width=True,
    height=400
)

# Botão de exportação
st.sidebar.markdown("---")
if st.sidebar.button("Exportar para CSV"):
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="Baixar CSV",
        data=csv,
        file_name="faturas.csv",
        mime="text/csv"
    )
