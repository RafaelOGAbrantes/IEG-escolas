import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Set page config
st.set_page_config(page_title="Comparador de IEG Escolar", layout="wide")

st.title("📊 Comparativo de Dados Escolares")

@st.cache_data
def load_data():
    try:
        df_ant = pd.read_excel('anteriores.xlsx')
        df_atu = pd.read_excel('atuais.xlsx')
        
        # Clean data
        df_ant = df_ant.dropna(subset=['Escola'])
        df_atu = df_atu.dropna(subset=['Escola'])
        
        # Ensure 'Escola' is string and strip
        df_ant['Escola'] = df_ant['Escola'].astype(str).str.strip()
        df_atu['Escola'] = df_atu['Escola'].astype(str).str.strip()
        
        return df_ant, df_atu
    except Exception as e:
        st.error(f"Erro ao carregar arquivos: {e}")
        return None, None

df_ant, df_atu = load_data()

if df_ant is not None and df_atu is not None:
    # Merge data
    # We merge on 'Escola', 'GRE', 'Municipio'
    # We keep all columns to allow dynamic selection of indices
    merged = pd.merge(df_ant, df_atu, on=['Escola', 'GRE', 'Municipio'], how='inner', suffixes=('_ant', '_atu'))
    
    # Sidebar Navigation
    st.sidebar.title("Navegação")
    page = st.sidebar.radio("Ir para", ["Comparativo IEG", "Comparativo Detalhado"])

    # Common Filters (applied to both pages)
    st.sidebar.header("Filtros")
    
    # GRE Filter
    all_gres = sorted(merged['GRE'].unique())
    selected_gre = st.sidebar.multiselect("Selecione a GRE", all_gres, default=all_gres)
    
    # Filter by GRE
    filtered_df = merged[merged['GRE'].isin(selected_gre)]
    
    # Municipio Filter
    all_municipios = sorted(filtered_df['Municipio'].unique())
    selected_municipio = st.sidebar.multiselect("Selecione o Município", all_municipios, default=all_municipios)
    
    # Final Filter
    filtered_df = filtered_df[filtered_df['Municipio'].isin(selected_municipio)]

    if page == "Comparativo IEG":
        st.header("Comparativo de IEG")
        
        if 'IEG_ant' in filtered_df.columns and 'IEG_atu' in filtered_df.columns:
            # Metrics
            col1, col2, col3 = st.columns(3)
            avg_ant = filtered_df['IEG_ant'].mean()
            avg_atu = filtered_df['IEG_atu'].mean()
            delta = avg_atu - avg_ant
            
            col1.metric("Média IEG Anterior", f"{avg_ant:.2f}")
            col2.metric("Média IEG Atual", f"{avg_atu:.2f}", delta=f"{delta:.2f}")
            col3.metric("Total de Escolas", len(filtered_df))
            
            # Chart
            st.subheader("Comparação Visual")
            
            # Melt for bar chart
            melted = filtered_df.melt(id_vars=['Escola'], value_vars=['IEG_ant', 'IEG_atu'], var_name='Versão', value_name='IEG')
            melted['Versão'] = melted['Versão'].map({'IEG_ant': 'Anterior', 'IEG_atu': 'Atual'})
            
            fig = px.bar(melted, x='Escola', y='IEG', color='Versão', barmode='group', title="IEG por Escola (Anterior vs Atual)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Data Table
            st.subheader("Dados Detalhados")
            filtered_df['Diferenca_IEG'] = filtered_df['IEG_atu'] - filtered_df['IEG_ant']
            st.dataframe(filtered_df[['Escola', 'GRE', 'Municipio', 'IEG_ant', 'IEG_atu', 'Diferenca_IEG']].sort_values(by='Diferenca_IEG', ascending=False))
        else:
            st.error("Colunas de IEG não encontradas.")

    elif page == "Comparativo Detalhado":
        st.header("Comparativo Detalhado de Índices")
        
        # Identify Index columns (I1, I2, ... I17) and their related columns
        # We rely on the column order in df_atu
        all_cols = df_atu.columns.tolist()
        
        # Map indices to related columns
        index_map = {}
        
        # Find all I columns
        possible_indices = [c for c in all_cols if c.startswith('I') and c[1:].isdigit()]
        
        # Sort indices numerically
        try:
            possible_indices.sort(key=lambda x: int(x[1:]))
        except:
            possible_indices.sort()
            
        for idx in possible_indices:
            try:
                idx_num = int(idx[1:])
                idx_pos = all_cols.index(idx)
                
                related = []
                if idx_num in [1, 2]:
                    # Get 2 preceding columns
                    if idx_pos >= 2:
                        related = all_cols[idx_pos-2:idx_pos]
                else:
                    # Get 1 preceding column
                    if idx_pos >= 1:
                        related = [all_cols[idx_pos-1]]
                
                index_map[idx] = related
            except ValueError:
                continue

        # View by School (Report Card)
        st.subheader("Boletim Individual")
        
        school_list = sorted(filtered_df['Escola'].unique())
        selected_school = st.selectbox("Selecione a Escola", school_list)
        
        if selected_school:
            school_data = filtered_df[filtered_df['Escola'] == selected_school].iloc[0]
            
            # Create a report dataframe
            report_data = []
            for idx in possible_indices:
                # Get related data
                related_cols = index_map.get(idx, [])
                related_info = ""
                
                for rc in related_cols:
                    rc_ant = f"{rc}_ant"
                    rc_atu = f"{rc}_atu"
                    val_ant = school_data.get(rc_ant, '-')
                    val_atu = school_data.get(rc_atu, '-')
                    related_info += f"{rc}: {val_ant} -> {val_atu}\n"
                
                col_ant = f"{idx}_ant"
                col_atu = f"{idx}_atu"
                
                val_ant = school_data.get(col_ant, None)
                val_atu = school_data.get(col_atu, None)
                
                diff = None
                if isinstance(val_ant, (int, float)) and isinstance(val_atu, (int, float)):
                    diff = val_atu - val_ant
                
                report_data.append({
                    'Índice': idx,
                    'Dados Relacionados': related_info.strip(),
                    'Anterior': val_ant,
                    'Atual': val_atu,
                    'Diferença': diff
                })
            
            df_report = pd.DataFrame(report_data)
            
            # Display metrics for IEG if available
            if 'IEG_ant' in school_data and 'IEG_atu' in school_data:
                col1, col2, col3 = st.columns(3)
                col1.metric("IEG Anterior", f"{school_data['IEG_ant']:.2f}")
                col2.metric("IEG Atual", f"{school_data['IEG_atu']:.2f}", delta=f"{school_data['IEG_atu'] - school_data['IEG_ant']:.2f}")
            
            st.table(df_report)
            
            # Visual Chart for this school
            st.write("### Gráfico de Evolução")
            melted_report = df_report.melt(id_vars=['Índice', 'Dados Relacionados'], value_vars=['Anterior', 'Atual'], var_name='Versão', value_name='Valor')
            fig = px.bar(melted_report, x='Índice', y='Valor', color='Versão', barmode='group', title=f"Índices da Escola {selected_school}", hover_data=['Dados Relacionados'])
            st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Certifique-se de que 'anteriores.xlsx' e 'atuais.xlsx' estão na mesma pasta.")
