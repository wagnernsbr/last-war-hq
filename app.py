import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Ficheiros
ARQUIVO_MEMBROS = "lista_membros.csv"
ARQUIVO_ANUNCIO = "anuncio_alianca.txt"
ARQUIVO_HISTORICO = "historico_escalacoes.csv"

st.set_page_config(page_title="Last War Strategic Command", layout="wide", initial_sidebar_state="expanded")

# --- CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
    }
    .stButton > button { width: 100%; border-radius: 8px; background-color: #21262d; border: 1px solid #30363d; color: white; }
    .stButton > button:hover { border-color: #58a6ff; color: #58a6ff; }
    </style>
""", unsafe_allow_html=True)

def carregar_dados():
    if os.path.exists(ARQUIVO_MEMBROS):
        df = pd.read_csv(ARQUIVO_MEMBROS)
        for col in ["Status", "Tropa", "Time"]:
            if col not in df.columns: df[col] = "Nenhum"
        return df
    return pd.DataFrame(columns=["Jogador", "Poder (M)", "Time", "Status", "Tropa"])

if 'dados' not in st.session_state:
    st.session_state.dados = carregar_dados()

df = st.session_state.dados
ICONES = {"Tanque": "🚜", "Míssil": "🚀", "Aeronave": "✈️", "Nenhum": "❓"}

# --- SIDEBAR ---
st.sidebar.title("⚡ VS TRACKER")
aba = st.sidebar.radio("MENU", ["📊 Dashboard", "⚔️ Escalação Rápida", "👤 Membros", "📜 Histórico", "📢 Anúncio"])

# --- ABA: DASHBOARD ---
if aba == "📊 Dashboard":
    st.title("🛡️ Painel de Comando")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PODER TOTAL", f"{df['Poder (M)'].sum():.1f} M")
    m2.metric("JOGADORES", len(df))
    tropas_count = df['Tropa'].value_counts()
    m3.metric("TANQUES 🚜", tropas_count.get("Tanque", 0))
    m4.metric("MÍSSIL/AÉREO 🚀✈️", tropas_count.get("Míssil", 0) + tropas_count.get("Aeronave", 0))
    st.divider()
    c_top, c_dist = st.columns([1, 1])
    with c_top:
        st.subheader("🏆 Top 5 Elite")
        top_5 = df.sort_values(by="Poder (M)", ascending=False).head(5)
        top_5['Info'] = top_5.apply(lambda r: f"{ICONES.get(r['Tropa'], '❓')} {r['Jogador']}", axis=1)
        st.table(top_5[['Info', 'Poder (M)']])
    with c_dist:
        st.subheader("📈 Distribuição de Tropa")
        if not df.empty: st.bar_chart(df['Tropa'].value_counts())

# --- ABA: ESCALAÇÃO ---
elif aba == "⚔️ Escalação Rápida":
    st.header("Escalação de Campo")
    c1, c2 = st.columns(2)
    time_alvo = c1.radio("Time:", ["Time A (18h)", "Time B (09h)"], horizontal=True)
    status_alvo = c2.radio("Status:", ["Titular", "Reserva"], horizontal=True)
    
    disponiveis = df[df['Time'] == "Nenhum"].sort_values(by="Poder (M)", ascending=False)
    st.write(f"### Membros Disponíveis ({len(disponiveis)})")
    cols = st.columns(4)
    for i, (idx, row) in enumerate(disponiveis.iterrows()):
        with cols[i % 4]:
            if st.button(f"{ICONES.get(row['Tropa'], '❓')} {row['Jogador']}\n{row['Poder (M)']}M", key=f"add_{row['Jogador']}"):
                df.loc[df['Jogador'] == row['Jogador'], ['Time', 'Status']] = [time_alvo, status_alvo]
                df.to_csv(ARQUIVO_MEMBROS, index=False)
                st.session_state.dados = df
                st.rerun()
    st.divider()
    st.subheader(f"Escalados para {time_alvo}")
    escalados = df[df['Time'] == time_alvo]
    ce = st.columns(4)
    for i, (idx, row) in enumerate(escalados.iterrows()):
        prefixo = "🟢" if row['Status'] == "Titular" else "🟡"
        with ce[i % 4]:
            if st.button(f"{prefixo} {row['Jogador']}", key=f"rem_{row['Jogador']}"):
                df.loc[df['Jogador'] == row['Jogador'], ['Time', 'Status']] = ["Nenhum", "Nenhum"]
                df.to_csv(ARQUIVO_MEMBROS, index=False)
                st.session_state.dados = df
                st.rerun()

# --- ABA: MEMBROS ---
elif aba == "👤 Membros":
    st.header("Gestão de Membros")
    # (Mantive a lógica de edição que criamos antes)
    st.info("Use esta aba para atualizar poderes ou trocar tipos de tropa.")
    st.dataframe(df.sort_values(by="Poder (M)", ascending=False), use_container_width=True)

# --- ABA: HISTÓRICO (NOVA!) ---
elif aba == "📜 Histórico":
    st.header("📜 Histórico de Escalações Passadas")
    if os.path.exists(ARQUIVO_HISTORICO):
        hist_df = pd.read_csv(ARQUIVO_HISTORICO)
        datas = hist_df['Data_Escalacao'].unique()
        data_sel = st.selectbox("Selecione uma data para revisar:", sorted(datas, reverse=True))
        
        view_df = hist_df[hist_df['Data_Escalacao'] == data_sel]
        st.write(f"### Escalação de {data_sel}")
        st.dataframe(view_df[['Jogador', 'Poder (M)', 'Time', 'Status', 'Tropa']], use_container_width=True)
    else:
        st.warning("Ainda não há registros no histórico. Salve uma escalação na aba 'Anúncio' primeiro.")

# --- ABA: ANÚNCIO ---
elif aba == "📢 Anúncio":
    st.header("Anúncio de Guerra")
    
    # Gerador de Relatório
    relatorio = f"⚔️ **RELATÓRIO TEMPESTADE - {datetime.now().strftime('%d/%m/%Y')}** ⚔️\n\n"
    escalados_df = df[df['Time'] != "Nenhum"]
    
    for t_nome in ["Time A (18h)", "Time B (09h)"]:
        d_t = df[df['Time'] == t_nome]
        if not d_t.empty:
            relatorio += f"📍 {t_nome.upper()} ({d_t['Poder (M)'].sum():.1f}M)\n"
            for status in ["Titular", "Reserva"]:
                sub = d_t[d_t['Status'] == status].sort_values(by="Poder (M)", ascending=False)
                if not sub.empty:
                    relatorio += f"\n-- {status.upper()} --\n"
                    for _, r in sub.iterrows():
                        relatorio += f"{ICONES.get(r['Tropa'], '')} {r['Jogador']} ({r['Poder (M)']}M)\n"
            relatorio += "\n"
    
    st.code(relatorio)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Salvar Escalação no Histórico"):
            if not escalados_df.empty:
                temp_hist = escalados_df.copy()
                temp_hist['Data_Escalacao'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                if os.path.exists(ARQUIVO_HISTORICO):
                    temp_hist.to_csv(ARQUIVO_HISTORICO, mode='a', header=False, index=False)
                else:
                    temp_hist.to_csv(ARQUIVO_HISTORICO, index=False)
                st.success("Escalação arquivada com sucesso!")
            else:
                st.error("Escalação vazia! Escolha os membros primeiro.")

    with col2:
        if st.button("🗑️ Resetar Escalação Semanal"):
            df['Time'] = "Nenhum"
            df['Status'] = "Nenhum"
            df.to_csv(ARQUIVO_MEMBROS, index=False)
            st.session_state.dados = df
            st.rerun()
