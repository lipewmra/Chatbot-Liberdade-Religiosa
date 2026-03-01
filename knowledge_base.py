import os
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import pandas as pd
import sqlite3
from database import DB_NAME

DOCS_DIR = "docs"

def get_pdf_text(pdf_path):
    text = ""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def get_txt_text(txt_path):
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT {txt_path}: {e}")
        return ""

def load_local_documents():
    context = ""
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
        return ""
    
    for filename in os.listdir(DOCS_DIR):
        file_path = os.path.join(DOCS_DIR, filename)
        if filename.endswith(".pdf"):
            context += f"\n--- Document: {filename} ---\n"
            context += get_pdf_text(file_path)
        elif filename.endswith(".txt") or filename.endswith(".md"):
             context += f"\n--- Document: {filename} ---\n"
             context += get_txt_text(file_path)
    return context

import io

def fetch_url_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Check if it's a PDF by URL extension or Content-Type
        content_type = response.headers.get('Content-Type', '').lower()
        if url.lower().endswith('.pdf') or 'application/pdf' in content_type:
            try:
                # Read PDF from bytes
                pdf_file = io.BytesIO(response.content)
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return text if text else "Nenhum texto pôde ser extraído deste PDF."
            except Exception as pdf_err:
                return f"Erro ao processar PDF: {pdf_err}"
        
        # Fallback to HTML parsing
        soup = BeautifulSoup(response.content, 'html.parser')
        # Simple extraction: get all paragraph text
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text() for p in paragraphs])
        return text
    except Exception as e:
        return f"Error fetching {url}: {e}"

def add_reference_link(url, title):
    content = fetch_url_content(url)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO reference_links (url, title, content) VALUES (?, ?, ?)", (url, title, content))
    conn.commit()
    conn.close()

def get_reference_links():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM reference_links ORDER BY added_at DESC", conn)
    conn.close()
    return df

def delete_reference_link(link_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM reference_links WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()

def get_combined_context():
    local_context = load_local_documents()
    
    conn = sqlite3.connect(DB_NAME)
    links_df = pd.read_sql("SELECT title, content FROM reference_links", conn)
    conn.close()
    
    link_context = ""
    for _, row in links_df.iterrows():
        link_context += f"\n--- Reference Link: {row['title']} ---\n{row['content']}\n"
        
    return local_context + "\n" + link_context

def get_combined_context_truncated(max_chars=6000):
    full_context = get_combined_context()
    if len(full_context) > max_chars:
        return full_context[:max_chars] + "... [TRUNCATED]"
    return full_context

def get_available_models():
    models_dir = os.path.join(DOCS_DIR, "modelos")
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        return []
    
    models = []
    for filename in os.listdir(models_dir):
        if filename.endswith((".pdf", ".docx", ".doc", ".txt", ".md")):
            models.append(filename)
    return models
