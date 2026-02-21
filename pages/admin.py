import sys
import os

# Add parent directory to path to allow importing database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from database import get_logs, get_stats, verify_password, update_password, get_monthly_stats, get_keyword_stats, init_db

load_dotenv()

st.set_page_config(page_title="Admin - Chatbot", page_icon="🔒", layout="wide")

# Hide Streamlit's default elements
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stToolbar"] {visibility: hidden;}
            [data-testid="stSidebarNav"] {display: none;}
            [data-testid="stSidebar"] {background-color: #f0f2f6;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Ensure database is initialized
init_db()

st.title("🔒 Área Administrativa")

# Check Authentication
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# If not authenticated, show login
if not st.session_state.admin_authenticated:
    st.title("🔒 Login Administrativo")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        if verify_password(password):
            st.session_state.admin_authenticated = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    
    if st.button("Voltar ao Chat"):
        st.switch_page("main.py")
    
    st.stop() # Prevent showing the rest of the page

# If authenticated
# Logout/Back button in main area
col_back, col_title = st.columns([1, 5])
with col_back:
    if st.button("⬅️ Sair"):
        st.session_state.admin_authenticated = False
        st.switch_page("main.py")

# Change Password Section (Expander)
with st.expander("🔑 Alterar Senha de Administrador"):
    with st.form("change_password_form"):
        new_pass = st.text_input("Nova Senha", type="password")
        confirm_pass = st.text_input("Confirmar Nova Senha", type="password")
        submit_pass = st.form_submit_button("Atualizar Senha")
        
        if submit_pass:
            if new_pass and new_pass == confirm_pass:
                update_password(new_pass)
                st.success("Senha atualizada com sucesso! Por favor, faça login novamente.")
                st.session_state.admin_authenticated = False
                st.rerun()
            elif new_pass != confirm_pass:
                st.error("As senhas não coincidem.")
            else:
                st.error("A senha não pode estar vazia.")

    
# Tabs for different admin functions
tab1, tab2, tab3, tab4 = st.tabs(["📊 Estatísticas", "📝 Logs de Conversa", "📚 Base de Conhecimento", "⚙️ Manutenção"])

with tab1:
    st.header("Estatísticas Gerais")
    stats = get_stats()
    col1, col2 = st.columns(2)
    col1.metric("Total de Mensagens", stats.get("total_messages", 0))
    # Add more stats here later
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Postagens por Mês")
        monthly_df = get_monthly_stats()
        if not monthly_df.empty:
            st.bar_chart(monthly_df.set_index('month'))
        else:
            st.info("Sem dados suficientes para o gráfico.")

    with col_chart2:
        st.subheader("Ranking de Palavras-Chave")
        keyword_df = get_keyword_stats()
        if not keyword_df.empty:
            # Horizontal bar chart for readable keywords
            st.bar_chart(keyword_df.set_index('keyword'), horizontal=True)
        else:
            st.info("Sem dados suficientes para o gráfico.")

with tab2:
    st.header("Histórico de Conversas")
    df = get_logs()
    st.dataframe(df, use_container_width=True)
    
    if st.button("Atualizar Logs"):
        st.rerun()

with tab3:
    st.header("Gerenciar Links de Referência")
    
    # Form to add new link
    with st.form("add_link_form"):
        new_url = st.text_input("URL da Referência")
        new_title = st.text_input("Título da Referência")
        submitted = st.form_submit_button("Adicionar Link")
        
        if submitted and new_url and new_title:
            try:
                from knowledge_base import add_reference_link
                add_reference_link(new_url, new_title)
                st.success("Link adicionado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao adicionar link: {e}")

    st.divider()
    st.subheader("Links Cadastrados")
    try:
        from knowledge_base import get_reference_links, delete_reference_link
        links_df = get_reference_links()
        
        if not links_df.empty:
            for index, row in links_df.iterrows():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{row['title']}**\n{row['url']}")
                with col2:
                    if st.button("Excluir", key=f"del_{row['id']}"):
                        delete_reference_link(row['id'])
                        st.rerun()
                st.divider()
        else:
            st.info("Nenhum link cadastrado.")
    except Exception as e:
            st.error(f"Erro ao carregar links: {e}")

with tab4:
    st.header("Manutenção do Sistema")
    
    st.subheader("Backup de Dados")
    st.write("Faça o download do banco de dados completo antes de realizar operações de risco.")
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chatbot.db")
    if os.path.exists(db_path):
        with open(db_path, "rb") as fp:
            btn = st.download_button(
                label="📥 Baixar Banco de Dados (Backup)",
                data=fp,
                file_name="chatbot_backup.db",
                mime="application/x-sqlite3"
            )
    else:
        st.info("Banco de dados ainda não foi criado.")
        
    st.divider()
    st.subheader("🚨 Zona de Perigo")
    
    col_danger1, col_danger2 = st.columns(2)
    
    with col_danger1:
        st.error("Resetar Banco de Dados")
        st.write("Isso apagará TODOS os logs, conversas e links cadastrados. A senha de admin será mantida.")
        if st.checkbox("Entendo que esta ação é irreversível", key="confirm_reset_db"):
            if st.button("🗑️ Executar Reset Completo", type="primary"):
                try:
                    from database import reset_database
                    reset_database()
                    st.success("Banco de dados resetado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao resetar: {e}")
                    
    with col_danger2:
        st.error("Resetar Senha de Admin")
        st.write("Isso restaurará a senha do administrador para o padrão: 'admin'.")
        if st.checkbox("Confirmar reset de senha", key="confirm_reset_pass"):
            if st.button("🔄 Restaurar Senha Padrão", type="primary"):
                try:
                    from database import reset_admin_password
                    reset_admin_password()
                    st.success("Senha restaurada para 'admin'. Faça login novamente.")
                    st.session_state.admin_authenticated = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao resetar senha: {e}")
