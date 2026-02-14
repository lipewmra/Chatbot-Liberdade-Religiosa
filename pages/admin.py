import sys
import os

# Add parent directory to path to allow importing database
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from database import get_logs, get_stats

load_dotenv()

st.set_page_config(page_title="Admin - Chatbot", page_icon="🔒")

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

st.title("🔒 Área Administrativa")

with st.sidebar:
    if os.path.exists("libreligiosa.png"):
        st.image("libreligiosa.png", use_container_width=True)
    st.page_link("main.py", label="Voltar ao Chat", icon="🏠")

# Simple Authentication
password = st.text_input("Senha de Administrador", type="password")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

if password == ADMIN_PASSWORD:
    st.success("Acesso Permitido")
    
    # Tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["📊 Estatísticas", "📝 Logs de Conversa", "📚 Base de Conhecimento"])
    
    with tab1:
        st.header("Estatísticas Gerais")
        stats = get_stats()
        col1, col2 = st.columns(2)
        col1.metric("Total de Mensagens", stats.get("total_messages", 0))
        # Add more stats here later
        
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

elif password:
    st.error("Senha incorreta.")
else:
    st.warning("Por favor, insira a senha para acessar.")
