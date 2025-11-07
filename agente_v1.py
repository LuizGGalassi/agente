import google.generativeai as genai
import feedparser # <-- Nossa nova biblioteca (Módulo 1)
import os
from typing import Tuple, Union
from datetime import datetime # Para pegar a data de hoje

# --- CONFIGURAÇÃO (API KEY) ---
# Pega a API Key do "cofre" do GitHub Actions (Environment Variable)
API_KEY = os.environ.get("GOOGLE_API_KEY")

if not API_KEY:
    print("Erro: A API Key 'GOOGLE_API_KEY' não foi encontrada.") 
genai.configure(api_key=API_KEY)


# --- MÓDULO 1: O MONITOR (Coleta de Dados) ---

def buscar_ultima_noticia() -> Tuple[Union[str, None], Union[str, None]]:
    """
    Busca a notícia mais recente de uma fonte RSS (Shopify).
    Retorna (titulo, resumo) ou (None, None) se falhar.
    """
    URL_RSS_REDDIT_SHOPIFY = "https://www.reddit.com/r/shopify/.rss"
    
    # --- A CORREÇÃO: "Disfarce" de Navegador ---
    # Este é um User-Agent comum de um navegador Chrome.
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    
    print(f"Buscando dados em: {URL_RSS_REDDIT_SHOPIFY}")
    
    try:
        # Passamos o 'agent' para o feedparser
        feed = feedparser.parse(URL_RSS_REDDIT_SHOPIFY, agent=USER_AGENT)
        
        # --- VERIFICAÇÃO DE ROBUSTEZ ---
        # 1. O feed.bozo é 1 (True) se o feedparser não conseguiu ler o RSS
        if feed.bozo:
            print(f"Erro de parsing: O feed RSS está mal formatado ou inacessível.")
            print(f"Causa: {feed.bozo_exception}")
            return None, None

        # 2. Verificamos se a lista de 'entries' NÃO está vazia
        if not feed.entries:
            print("Erro: O feed foi lido, mas não contém nenhum post (entries).")
            print("Isso pode ser um bloqueio do servidor ou o feed está vazio.")
            return None, None
            
        # SÓ AGORA (após verificar) podemos acessar o [0] com segurança
        post_mais_recente = feed.entries[0]
        
        titulo = post_mais_recente.title
        resumo = post_mais_recente.get('summary', post_mais_recente.get('description', ''))
        
        if not titulo or not resumo:
            print("Erro: Post do RSS veio sem título ou resumo.")
            return None, None
            
        return titulo, resumo

    except Exception as e:
        print(f"Erro inesperado ao buscar dados do RSS: {e}")
        return None, None

# --- MÓDULO 2: O CÉREBRO (Processamento IA) ---
# (Esta é a sua função que já validamos)

def gerar_insight_acionavel(titulo_artigo: str, resumo_artigo: str) -> str:
    """
    Usa a IA para transformar dados brutos em um insight acionável.
    """
    
    prompt_template = f"""
    Objetivo: Atue como um especialista em e-commerce focado em Shopify e Shopee.
    Sua tarefa é ler o material de origem e gerar um "insight acionável" para 
    donos de pequenos negócios.

    Regras de Saída:
    1.  Crie um título curto e magnético (máx. 10 palavras).
    2.  Escreva um insight de 2 a 3 frases (máx. 50 palavras).
    3.  A linguagem deve ser direta, clara e focada na ação.

    Material de Origem:
    - Título: "{titulo_artigo}"
    - Resumo: "{resumo_artigo}"

    Insight Gerado:
    """

    try:
        # O modelo que descobrimos que funciona para você
        model = genai.GenerativeModel('models/gemini-2.5-flash') 
        response = model.generate_content(prompt_template)
        
        insight_limpo = response.text.strip()
        return insight_limpo
    
    except Exception as e:
        print(f"Erro ao chamar a API de IA: {e}")
        return None

# --- MÓDULO 3: O PUBLICADOR (Salva o Post) ---

def salvar_post_jekyll(insight_completo: str):
    """
    Pega o insight gerado pela IA, formata-o como um post
    Jekyll e o salva como um arquivo .md.
    """
    print("Iniciando Módulo 3: Publicador Estático...")
    
    try:
        # 1. Separar o Título do Corpo
        # O formato da IA é: **Título**\n\nCorpo...
        partes = insight_completo.split('\n\n', 1)
        if len(partes) < 2:
            print("Erro: Insight da IA não está no formato Título/Corpo esperado.")
            return

        titulo_raw = partes[0]
        corpo = partes[1].strip()
        
        # Limpa o título (remove os ** do Markdown)
        titulo_limpo = titulo_raw.replace("**", "").strip()

        # 2. Preparar o Nome do Arquivo (Formato Jekyll)
        # Formato: YYYY-MM-DD-titulo-do-post.md
        
        hoje_str = datetime.now().strftime('%Y-%m-%d')
        
        # Cria um "slug": "Meu Título" -> "meu-titulo"
        # Esta é uma versão simples e "low-maintenance"
        slug = titulo_limpo.lower().replace(' ', '-')
        # Remove caracteres problemáticos para nomes de arquivo
        slug = "".join(c for c in slug if c.isalnum() or c in ['-']) 
        
        nome_arquivo = f"{hoje_str}-{slug}.md"
        
        # 3. Criar o "Front Matter" do Jekyll
        # Este é o cabeçalho que o Jekyll usa para construir a página
        conteudo_front_matter = f"""---
layout: post
title: "{titulo_limpo}"
---

"""
        conteudo_completo = conteudo_front_matter + corpo

        # 4. Salvar o Arquivo
        # Salva tudo na pasta '_posts' (o padrão do Jekyll)
        pasta_posts = "_posts"
        os.makedirs(pasta_posts, exist_ok=True) # Cria a pasta se ela não existir
        
        caminho_arquivo = os.path.join(pasta_posts, nome_arquivo)
        
        with open(caminho_arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo_completo)
            
        print(f"--- SUCESSO: Post salvo em '{caminho_arquivo}' ---")

    except Exception as e:
        print(f"Erro ao salvar o arquivo do post: {e}")

# --- ORQUESTRADOR PRINCIPAL ---

# ... (outras funções acima) ...

def executar_agente():
    print("--- INICIANDO AGENTE DE INTELIGÊNCIA V1 ---")
    
    # 1. Módulo 1 executa
    titulo, resumo = buscar_ultima_noticia()
    
    if titulo and resumo:
        print(f"\nDados Brutos Coletados:\n  Título: {titulo[:50]}...")
        print(f"  Resumo: {resumo[:70]}...")
        
        # 2. Módulo 2 executa
        print("\nEnviando para o Cérebro de IA (Módulo 2)...")
        insight = gerar_insight_acionavel(titulo, resumo)
        
        if insight:
            print("\n--- INSIGHT GERADO COM SUCESSO ---")
            print(insight)
            
            # --- ESTE É O LUGAR CORRETO ---
            # O 'insight' é passado como argumento
            salvar_post_jekyll(insight) 
            
        else:
            print("\nFalha ao gerar insight com os dados reais.")
    else:
        print("Falha ao coletar dados reais. Abortando.")
        
    print("\n--- AGENTE FINALIZADO ---")


# --- Ponto de Entrada do Script ---
if __name__ == "__main__":
    executar_agente() # Esta deve ser a ÚLTIMA chamada no seu script