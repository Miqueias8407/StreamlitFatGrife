{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "be847b13-edef-45a1-91b2-a2452fb1f5bb",
   "metadata": {},
   "outputs": [],
   "source": [
    "%%writefile fatura_dashboard.py\n",
    "import streamlit as st\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import plotly.express as px\n",
    "import plotly.graph_objects as go\n",
    "from datetime import datetime, timedelta\n",
    "import os\n",
    "import glob\n",
    "\n",
    "# Configuração da página\n",
    "st.set_page_config(\n",
    "    page_title=\"Dashboard de Faturas\",\n",
    "    page_icon=\"💳\",\n",
    "    layout=\"wide\"\n",
    ")\n",
    "\n",
    "# Paleta de cores\n",
    "COLORS = {\n",
    "    \"background\": \"#121212\",\n",
    "    \"secondary\": \"#1E1E1E\",\n",
    "    \"text\": \"#E0E0E0\",\n",
    "    \"paid\": \"#2E86AB\",\n",
    "    \"unpaid\": \"#FF6B6B\",\n",
    "    \"highlight\": \"#4ECDC4\",\n",
    "    \"card_bg\": \"#1E1E1E\"\n",
    "}\n",
    "\n",
    "# Função para formatar números com ponto nos milhares e vírgula nos decimais\n",
    "def format_brl(value):\n",
    "    return f\"R$ {value:,.2f}\".replace(\",\", \"X\").replace(\".\", \",\").replace(\"X\", \".\")\n",
    "\n",
    "# Estilos CSS personalizados\n",
    "def local_css():\n",
    "    st.markdown(f\"\"\"\n",
    "    <style>\n",
    "        .stApp {{\n",
    "            background-color: {COLORS['background']};\n",
    "            color: {COLORS['text']};\n",
    "        }}\n",
    "        .css-1d391kg, .css-1y4p8pa {{\n",
    "            background-color: {COLORS['secondary']};\n",
    "        }}\n",
    "        .st-bb, .st-at, .st-ar, .st-as {{\n",
    "            background-color: {COLORS['secondary']};\n",
    "        }}\n",
    "        .css-10trblm {{\n",
    "            color: {COLORS['text']};\n",
    "        }}\n",
    "        .card {{\n",
    "            background-color: {COLORS['card_bg']};\n",
    "            border-radius: 10px;\n",
    "            padding: 15px;\n",
    "            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);\n",
    "            transition: transform 0.3s ease;\n",
    "        }}\n",
    "        .card:hover {{\n",
    "            transform: translateY(-5px);\n",
    "            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);\n",
    "        }}\n",
    "        .card-title {{\n",
    "            font-size: 14px;\n",
    "            color: {COLORS['text']};\n",
    "            opacity: 0.8;\n",
    "            margin-bottom: 10px;\n",
    "        }}\n",
    "        .card-value {{\n",
    "            font-size: 24px;\n",
    "            font-weight: bold;\n",
    "            color: {COLORS['highlight']};\n",
    "        }}\n",
    "        .css-1cpxqw2 {{\n",
    "            border: 1px solid {COLORS['secondary']};\n",
    "        }}\n",
    "        .stDataFrame {{\n",
    "            background-color: {COLORS['secondary']};\n",
    "        }}\n",
    "        .st-b7 {{\n",
    "            background-color: {COLORS['highlight']};\n",
    "        }}\n",
    "        .stSlider>div>div>div>div {{\n",
    "            background-color: {COLORS['highlight']} !important;\n",
    "        }}\n",
    "    </style>\n",
    "    \"\"\", unsafe_allow_html=True)\n",
    "\n",
    "local_css()\n",
    "\n",
    "# Função para carregar dados das planilhas\n",
    "@st.cache_data\n",
    "def load_data():\n",
    "    # Caminho para as planilhas\n",
    "    path = r\"K:\\RelatoriosFinanceiros\\Rel_441\\*.xlsx\"  # Assumindo arquivos Excel\n",
    "    \n",
    "    all_files = glob.glob(path)\n",
    "    dfs = []\n",
    "    \n",
    "    for file in all_files:\n",
    "        try:\n",
    "            df = pd.read_excel(file)\n",
    "            # Padronizar nomes de colunas (caso haja variações)\n",
    "            df.columns = df.columns.str.upper()\n",
    "            dfs.append(df)\n",
    "        except Exception as e:\n",
    "            st.error(f\"Erro ao ler o arquivo {file}: {e}\")\n",
    "    \n",
    "    if not dfs:\n",
    "        st.error(\"Nenhuma planilha encontrada ou foi possível ler.\")\n",
    "        return pd.DataFrame()\n",
    "    \n",
    "    # Concatenar todos os DataFrames\n",
    "    combined_df = pd.concat(dfs, ignore_index=True)\n",
    "    \n",
    "    # Renomear colunas conforme solicitado\n",
    "    combined_df = combined_df.rename(columns={\n",
    "        'FATURA': 'ID',\n",
    "        'CLIENTE': 'Cliente',\n",
    "        'VLR FATUR': 'Valor',\n",
    "        'VENCIMEN': 'Vencimento',\n",
    "        'LIQUIDADA/ATRASADA': 'Status'\n",
    "    })\n",
    "    \n",
    "    # Converter status para valores padronizados\n",
    "    combined_df['Status'] = combined_df['Status'].apply(\n",
    "        lambda x: 'Paga' if str(x).strip().upper() == 'LIQUIDADO' else 'Em aberto'\n",
    "    )\n",
    "    \n",
    "    # Converter datas se necessário\n",
    "    if 'Vencimento' in combined_df.columns:\n",
    "        combined_df['Vencimento'] = pd.to_datetime(combined_df['Vencimento'], errors='coerce')\n",
    "    \n",
    "    return combined_df.dropna(subset=['ID', 'Valor', 'Vencimento'])\n",
    "\n",
    "# Carregar dados\n",
    "df = load_data()\n",
    "\n",
    "if df.empty:\n",
    "    st.error(\"Não foi possível carregar os dados. Verifique os arquivos na pasta.\")\n",
    "    st.stop()\n",
    "\n",
    "# Filtros\n",
    "st.sidebar.title(\"Filtros\")\n",
    "\n",
    "# Seletor de intervalo de datas\n",
    "min_date = df['Vencimento'].min().date()\n",
    "max_date = df['Vencimento'].max().date()\n",
    "\n",
    "date_range = st.sidebar.date_input(\n",
    "    \"Selecione o intervalo de datas:\",\n",
    "    value=(min_date, max_date),\n",
    "    min_value=min_date,\n",
    "    max_value=max_date\n",
    ")\n",
    "\n",
    "# Verificar se selecionou um intervalo válido\n",
    "if len(date_range) == 2:\n",
    "    start_date, end_date = date_range\n",
    "else:\n",
    "    start_date, end_date = min_date, max_date\n",
    "\n",
    "# Outros filtros\n",
    "status_filter = st.sidebar.multiselect(\n",
    "    \"Status\", \n",
    "    options=['Paga', 'Em aberto'], \n",
    "    default=['Paga', 'Em aberto']\n",
    ")\n",
    "\n",
    "client_filter = st.sidebar.multiselect(\n",
    "    \"Cliente\", \n",
    "    options=df['Cliente'].unique()\n",
    ")\n",
    "\n",
    "# Aplicar filtros\n",
    "filtered_df = df.copy()\n",
    "filtered_df = filtered_df[\n",
    "    (filtered_df['Vencimento'].dt.date >= start_date) & \n",
    "    (filtered_df['Vencimento'].dt.date <= end_date)\n",
    "]\n",
    "\n",
    "if status_filter:\n",
    "    filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]\n",
    "if client_filter:\n",
    "    filtered_df = filtered_df[filtered_df['Cliente'].isin(client_filter)]\n",
    "\n",
    "# Cards de resumo\n",
    "st.title(\"📊 Dashboard de Faturas\")\n",
    "\n",
    "# Linha do tempo interativa\n",
    "st.subheader(f\"Período selecionado: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}\")\n",
    "\n",
    "col1, col2, col3, col4 = st.columns(4)\n",
    "\n",
    "with col1:\n",
    "    st.markdown(f\"\"\"\n",
    "    <div class=\"card\">\n",
    "        <div class=\"card-title\">Total de Faturas</div>\n",
    "        <div class=\"card-value\">{len(filtered_df)}</div>\n",
    "    </div>\n",
    "    \"\"\", unsafe_allow_html=True)\n",
    "\n",
    "with col2:\n",
    "    unpaid = filtered_df[filtered_df['Status'] == 'Em aberto']['Valor'].sum()\n",
    "    st.markdown(f\"\"\"\n",
    "    <div class=\"card\">\n",
    "        <div class=\"card-title\">Valor em Aberto</div>\n",
    "        <div class=\"card-value\">{format_brl(unpaid)}</div>\n",
    "    </div>\n",
    "    \"\"\", unsafe_allow_html=True)\n",
    "\n",
    "with col3:\n",
    "    paid = filtered_df[filtered_df['Status'] == 'Paga']['Valor'].sum()\n",
    "    st.markdown(f\"\"\"\n",
    "    <div class=\"card\">\n",
    "        <div class=\"card-title\">Valor Pago</div>\n",
    "        <div class=\"card-value\">{format_brl(paid)}</div>\n",
    "    </div>\n",
    "    \"\"\", unsafe_allow_html=True)\n",
    "\n",
    "with col4:\n",
    "    total_value = filtered_df['Valor'].sum()\n",
    "    st.markdown(f\"\"\"\n",
    "    <div class=\"card\">\n",
    "        <div class=\"card-title\">Valor Total</div>\n",
    "        <div class=\"card-value\">{format_brl(total_value)}</div>\n",
    "    </div>\n",
    "    \"\"\", unsafe_allow_html=True)\n",
    "\n",
    "# Gráficos\n",
    "st.markdown(\"---\")\n",
    "col5, col6 = st.columns([6, 4])\n",
    "\n",
    "with col5:\n",
    "    # Agrupar por período selecionado\n",
    "    if (end_date - start_date).days <= 31:  # Se intervalo menor que 1 mês, agrupar por dia\n",
    "        filtered_df['Periodo'] = filtered_df['Vencimento'].dt.strftime('%d/%m')\n",
    "        title = 'Faturas por Dia'\n",
    "    elif (end_date - start_date).days <= 365:  # Se intervalo menor que 1 ano, agrupar por mês\n",
    "        filtered_df['Periodo'] = filtered_df['Vencimento'].dt.strftime('%m/%Y')\n",
    "        title = 'Faturas por Mês'\n",
    "    else:  # Para intervalos maiores, agrupar por ano\n",
    "        filtered_df['Periodo'] = filtered_df['Vencimento'].dt.strftime('%Y')\n",
    "        title = 'Faturas por Ano'\n",
    "    \n",
    "    # Gráfico de barras\n",
    "    period_summary = filtered_df.groupby(['Periodo', 'Status'])['Valor'].sum().unstack().fillna(0)\n",
    "    \n",
    "    fig_bar = go.Figure()\n",
    "    fig_bar.add_trace(go.Bar(\n",
    "        x=period_summary.index,\n",
    "        y=period_summary['Paga'],\n",
    "        name='Pagas',\n",
    "        marker_color=COLORS['paid']\n",
    "    ))\n",
    "    fig_bar.add_trace(go.Bar(\n",
    "        x=period_summary.index,\n",
    "        y=period_summary['Em aberto'],\n",
    "        name='Em aberto',\n",
    "        marker_color=COLORS['unpaid']\n",
    "    ))\n",
    "    \n",
    "    fig_bar.update_layout(\n",
    "        title=title,\n",
    "        plot_bgcolor=COLORS['secondary'],\n",
    "        paper_bgcolor=COLORS['secondary'],\n",
    "        font_color=COLORS['text'],\n",
    "        barmode='group',\n",
    "        hovermode=\"x unified\",\n",
    "        xaxis_title=\"Período\",\n",
    "        yaxis_title=\"Valor (R$)\"\n",
    "    )\n",
    "    \n",
    "    st.plotly_chart(fig_bar, use_container_width=True)\n",
    "\n",
    "with col6:\n",
    "    # Gráfico de pizza\n",
    "    status_counts = filtered_df['Status'].value_counts()\n",
    "    fig_pie = go.Figure(go.Pie(\n",
    "        labels=status_counts.index,\n",
    "        values=status_counts.values,\n",
    "        hole=.4,\n",
    "        marker_colors=[COLORS['paid'], COLORS['unpaid']],\n",
    "        textinfo='percent+value'\n",
    "    ))\n",
    "    \n",
    "    fig_pie.update_layout(\n",
    "        title='Proporção de Status',\n",
    "        plot_bgcolor=COLORS['secondary'],\n",
    "        paper_bgcolor=COLORS['secondary'],\n",
    "        font_color=COLORS['text'],\n",
    "        showlegend=True\n",
    "    )\n",
    "    \n",
    "    st.plotly_chart(fig_pie, use_container_width=True)\n",
    "\n",
    "# Tabela de faturas recentes\n",
    "st.markdown(\"---\")\n",
    "\n",
    "# Cria duas colunas para o título e o campo de busca\n",
    "col_title, col_search = st.columns([4, 2])\n",
    "\n",
    "with col_title:\n",
    "    st.subheader(f\"Faturas ({len(filtered_df)} no total)\")\n",
    "\n",
    "with col_search:\n",
    "    # Adiciona um campo de texto para filtrar\n",
    "    search_term = st.text_input(\"Filtrar faturas:\", placeholder=\"Digite ID, Cliente, Valor...\", label_visibility=\"collapsed\")\n",
    "\n",
    "# Aplica o filtro de texto se algo foi digitado\n",
    "if search_term:\n",
    "    search_lower = search_term.lower()\n",
    "    filtered_df = filtered_df[\n",
    "        filtered_df['ID'].astype(str).str.lower().str.contains(search_lower) |\n",
    "        filtered_df['Cliente'].astype(str).str.lower().str.contains(search_lower) |\n",
    "        filtered_df['Valor'].astype(str).str.lower().str.contains(search_lower) |\n",
    "        filtered_df['Vencimento'].astype(str).str.lower().str.contains(search_lower) |\n",
    "        filtered_df['Status'].astype(str).str.lower().str.contains(search_lower)\n",
    "    ]\n",
    "\n",
    "# Adicionar ícones de status\n",
    "def status_icon(status):\n",
    "    return \"✅\" if status == \"Paga\" else \"⚠️\"\n",
    "\n",
    "display_df = filtered_df.copy()\n",
    "display_df['Status'] = display_df['Status'].apply(status_icon)\n",
    "display_df = display_df.sort_values('Vencimento', ascending=False)\n",
    "\n",
    "# Formatar a coluna Valor na tabela\n",
    "display_df['Valor'] = display_df['Valor'].apply(lambda x: format_brl(x))\n",
    "\n",
    "st.dataframe(\n",
    "    display_df[['ID', 'Cliente', 'Valor', 'Vencimento', 'Status']],\n",
    "    column_config={\n",
    "        \"Vencimento\": st.column_config.DateColumn(format=\"DD/MM/YYYY\")\n",
    "    },\n",
    "    use_container_width=True,\n",
    "    height=400\n",
    ")\n",
    "\n",
    "# Botão de exportação\n",
    "st.sidebar.markdown(\"---\")\n",
    "if st.sidebar.button(\"Exportar para CSV\"):\n",
    "    csv = filtered_df.to_csv(index=False).encode('utf-8')\n",
    "    st.sidebar.download_button(\n",
    "        label=\"Baixar CSV\",\n",
    "        data=csv,\n",
    "        file_name=\"faturas.csv\",\n",
    "        mime=\"text/csv\"\n",
    "    )"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "29f8fbab-cb6c-4530-8a75-3742dd9fbd67",
   "metadata": {},
   "outputs": [],
   "source": [
    "!streamlit run fatura_dashboard.py"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.7"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
