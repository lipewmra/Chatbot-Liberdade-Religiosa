import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq
from database import init_db, log_message

# Load environment variables
load_dotenv()

# Configure page settings
st.set_page_config(
    page_title="Chatbot Liberdade Religiosa",
    page_icon="🕊️",
    layout="wide"
)

# Hide Streamlit's default elements
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            [data-testid="stToolbar"] {visibility: hidden;}
            [data-testid="stSidebarNav"] {display: none;}
            [data-testid="stSidebar"] {
                background-color: #f0f2f6;
            }
            [data-testid="stSidebar"] * {
                color: #333333 !important;
            }
            /* Specific overrides for elements that might need different colors if necessary,
               but for now forcing dark gray/black on the light sidebar background. */
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Initialize database
init_db()

# Sidebar removed as per requirement


# Main Chat Interface
# Center the image using columns
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if os.path.exists("logowhite.png"):
        st.image("logowhite.png", use_container_width=True)

st.markdown("<h1 style='text-align: center;'>Assistente Pessoal de Assuntos sobre Liberdade Religiosa, da IASD Central de Campina Grande, PB</h1>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; margin-bottom: 20px;'>
Olá usuário/a, como seu assistente pessoal estou habilitado a trazer orientações sobre o assunto de liberdade religiosa, posso lhe ajudar com problemas na escola, na universidade, no trabalho, empregador e outros.<br>
Para iniciar me fale abaixo o que você deseja saber
</div>
""", unsafe_allow_html=True)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []



# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Digite sua pergunta sobre liberdade religiosa..."):

    # Normal Chat Flow
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Check for API Key before processing
    # Try st.secrets first (Streamlit Cloud), then fallback to .env (local)
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except (KeyError, FileNotFoundError):
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        st.error("Erro: Chave de API não configurada.")
        st.stop()

    try:
        # Configure Groq Client
        client = Groq(api_key=api_key)
        
        # Get Context from Knowledge Base
        from knowledge_base import get_combined_context_truncated, get_available_models, DOCS_DIR
        kb_context = get_combined_context_truncated()
        available_models = get_available_models()
        
        models_list_text = "\n".join(available_models) if available_models else "Nenhum modelo disponível no momento."
        
        # Constructing system instruction
        base_instruction = f"""Você é um especialista em Liberdade Religiosa da Igreja Adventista do Sétimo Dia (IASD). 
Responda as perguntas com base nos regulamentos e princípios da igreja. Seja cortês e direto.

CONTEXTO DE MODELOS DE DOCUMENTOS:
Você tem acesso aos seguintes modelos de documentos na pasta 'docs/modelos':
{models_list_text}

SE O USUÁRIO SOLICITAR UM MODELO:
1. Verifique se o modelo solicitado (ou algo similar) está na lista acima.
2. Se estiver, responda EXATAMENTE: "Aqui está o modelo solicitado: [NOME_DO_ARQUIVO_EXATO]".
3. Se não estiver, diga que não encontrou o modelo específico, mas liste os que estão disponíveis.
"""
        
        system_content = base_instruction
        if kb_context:
            system_content += f"\n\nUse o seguinte contexto adicional para responder à pergunta (se relevante):\n{kb_context}\n"
        
        # Prepare messages for Groq (OpenAI format)
        # System message first
        messages = [{"role": "system", "content": system_content}]
        
        # Add chat history (limit to last 4 messages to save context for Llama 3)
        # Note: Groq/OpenAI format uses 'content', not 'parts'
        for msg in st.session_state.messages[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile", # Using Llama 3.3 70B for high quality
        )
        
        bot_response = chat_completion.choices[0].message.content

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(bot_response)
            
            # Check if bot offered a file
            import re
            match = re.search(r"Aqui está o modelo solicitado: (.+)", bot_response)
            if match:
                filename = match.group(1).strip()
                if filename.endswith("."):
                    filename = filename[:-1]
                
                file_path = os.path.join(DOCS_DIR, "modelos", filename)
                if os.path.exists(file_path):
                    with open(file_path, "rb") as file:
                        st.download_button(
                            label=f"📥 Baixar {filename}",
                            data=file,
                            file_name=filename,
                            mime="application/octet-stream"
                        )
                else:
                    st.warning(f"Arquivo '{filename}' mencionado não encontrado no servidor.")
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        
        # Log to database
        log_message(prompt, bot_response)

    except Exception as e:
        st.error(f"Erro ao processar sua solicitação: {e}")
