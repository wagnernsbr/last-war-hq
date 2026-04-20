import streamlit as st
import pandas as pd
import os

# Ficheiros
ARQUIVO_MEMBROS = "lista_membros.csv"
ARQUIVO_ANUNCIO = "anuncio_alianca.txt"

st.set_page_config(page_title="Last War Strategic Command", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO ---
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

# Variáveis para controle de edição
if 'edit_nome' not in st.session_state: st.session_state.edit_nome = ""
if 'edit_poder' not in st.session_state: st.session_state.edit_poder = 0.0
if 'edit_tropa' not in st.session_state: st.session_state.edit_tropa = "Tanque"

df = st.session_state.dados
ICONES = {"Tanque": "🚜", "Míssil": "🚀", "Aeronave": "✈️", "Nenhum": "❓"}

# --- SIDEBAR ---
st.sidebar.title("⚡ VS TRACKER")
aba = st.sidebar.radio("MENU", ["📊 Dashboard", "⚔️ Escalação Rápida", "👤 Membros", "📢 Anúncio"])

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
    cols = st.columns(4)
    for i, (idx, row) in enumerate(disponiveis.iterrows()):
        with cols[i % 4]:
            if st.button(f"{ICONES.get(row['Tropa'], '❓')} {row['Jogador']}\n{row['Poder (M)']}M", key=f"add_{row['Jogador']}"):
                df.loc[df['Jogador'] == row['Jogador'], ['Time', 'Status']] = [time_alvo, status_alvo]
                df.to_csv(ARQUIVO_MEMBROS, index=False)
                st.session_state.dados = df
                st.rerun()
    st.divider()
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

# --- ABA: MEMBROS (COM FUNÇÃO EDITAR) ---
elif aba == "👤 Membros":
    st.header("Gestão de Membros")
    
    with st.form("form_membros"):
        st.write("### Cadastrar / Editar")
        c1, c2, c3 = st.columns([2, 1, 1])
        nome_input = c1.text_input("Nick:", value=st.session_state.edit_nome)
        poder_input = c2.number_input("Poder (M):", min_value=0.0, value=st.session_state.edit_poder)
        # Tenta selecionar a tropa que já estava salva ao editar
        tropa_lista = ["Tanque", "Míssil", "Aeronave"]
        idx_tropa = tropa_lista.index(st.session_state.edit_tropa) if st.session_state.edit_tropa in tropa_lista else 0
        tropa_input = c3.selectbox("Tropa:", tropa_lista, index=idx_tropa)
        
        if st.form_submit_button("Confirmar Dados"):
            if nome_input:
                # Se for edição, mantém o Time e Status que ele já tinha
                time_atual = "Nenhum"
                status_atual = "Nenhum"
                if nome_input in df['Jogador'].values:
                    time_atual = df.loc[df['Jogador'] == nome_input, 'Time'].values[0]
                    status_atual = df.loc[df['Jogador'] == nome_input, 'Status'].values[0]
                
                df = df[df['Jogador'] != nome_input]
                novo = pd.DataFrame([[nome_input, poder_input, time_atual, status_atual, tropa_input]], 
                                    columns=["Jogador", "Poder (M)", "Time", "Status", "Tropa"])
                df = pd.concat([df, novo], ignore_index=True)
                df.to_csv(ARQUIVO_MEMBROS, index=False)
                st.session_state.dados = df
                # Limpa campos de edição
                st.session_state.edit_nome = ""
                st.session_state.edit_poder = 0.0
                st.session_state.edit_tropa = "Tanque"
                st.success("Membro atualizado!")
                st.rerun()

    st.divider()
    st.write("### Lista de Membros")
    
    # Criando uma lista com botões de editar e excluir
    for i, row in df.sort_values(by="Poder (M)", ascending=False).iterrows():
        col_n, col_p, col_t, col_ed, col_ex = st.columns([2, 1, 1, 1, 1])
        col_n.write(f"**{row['Jogador']}**")
        col_p.write(f"{row['Poder (M)']}M")
        col_t.write(f"{ICONES.get(row['Tropa'], '❓')} {row['Tropa']}")
        
        if col_ed.button("📝 Editar", key=f"ed_{row['Jogador']}"):
            st.session_state.edit_nome = row['Jogador']
            st.session_state.edit_poder = float(row['Poder (M)'])
            st.session_state.edit_tropa = row['Tropa']
            st.rerun()
            
        if col_ex.button("🗑️ Excluir", key=f"ex_{row['Jogador']}"):
            df = df[df['Jogador'] != row['Jogador']]
            df.to_csv(ARQUIVO_MEMBROS, index=False)
            st.session_state.dados = df
            st.rerun()

# --- ABA 4: ANÚNCIO (Versão Reforçada) ---
elif aba == "📢 Anúncio":
    st.header("Anúncio de Guerra")
    
    # Tenta ler o arquivo do GitHub, se não existir ou falhar, começa vazio
    txt_atual = ""
    if os.path.exists(ARQUIVO_ANUNCIO):
        try:
            with open(ARQUIVO_ANUNCIO, "r", encoding="utf-8") as f:
                txt_atual = f.read()
        except:
            txt_atual = "Erro ao ler arquivo. Verifique o GitHub."

    # Campo para ver o anúncio salvo
    st.subheader("📢 Convocação Atual")
    if txt_atual:
        st.code(txt_atual)
    else:
        st.info("Nenhum anúncio fixo encontrado no arquivo 'anuncio_alianca.txt' do GitHub.")

    st.divider()
    
    # Gerador de Relatório (Aquele que você copia para o jogo)
    st.subheader("📝 Relatório para Copiar")
    relatorio = "⚔️ **RELATÓRIO TEMPESTADE** ⚔️\n\n"
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
    
    if st.button("🗑️ Resetar Escalação Semanal"):
        df['Time'] = "Nenhum"
        df['Status'] = "Nenhum"
        df.to_csv(ARQUIVO_MEMBROS, index=False)
        st.session_state.dados = df
        st.rerun()
