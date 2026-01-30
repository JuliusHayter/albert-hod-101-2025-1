import os
import pickle
import streamlit as st
import openai
from dotenv import load_dotenv
import faiss
import numpy as np
from typing import List, Dict

load_dotenv()

st.set_page_config(
    page_title="Chatbot Othello",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_vector_database(index_path: str, chunks_path: str) -> tuple:
    """Charge la base vectorielle et les chunks."""
    if not os.path.exists(index_path) or not os.path.exists(chunks_path):
        return None, None
    
    index = faiss.read_index(index_path)
    with open(chunks_path, 'rb') as f:
        chunks = pickle.load(f)
    
    return index, chunks


def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Génère un embedding pour un texte."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(model=model, input=text)
    return response.data[0].embedding


def search_similar_chunks(query: str, index: faiss.Index, 
                         chunks: List[str], k: int = 3) -> List[str]:
    """Trouve les chunks les plus similaires à la requête."""
    query_embedding = get_embedding(query)
    query_vector = np.array([query_embedding]).astype('float32')
    distances, indices = index.search(query_vector, k)
    return [chunks[i] for i in indices[0]]


def create_system_message(context: str) -> Dict:
    """Crée le message système avec le contexte."""
    return {
        "role": "system",
        "content": f"""Tu es un assistant expert sur la pièce Othello de Shakespeare.
        Utilise UNIQUEMENT le contexte suivant pour répondre aux questions de l'utilisateur.
        Cite toujours tes sources en mentionnant le numéro du passage (Passage 1, Passage 2, etc.).
        
        Contexte:
        {context}
        
        Réponds en français de manière claire et précise."""
    }


def get_chat_response(messages: List[Dict], model: str, 
                     context: str = "") -> str:
    """Obtient une réponse du LLM."""
    system_message = create_system_message(context)
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[system_message] + messages
    )
    return response.choices[0].message.content


def get_homepage_intro() -> str:
    return """## Bienvenue dans le Chatbot Othello

Cette application vous permet de discuter avec un assistant intelligent
spécialisé dans la pièce **Othello** de William Shakespeare."""


def get_homepage_features() -> str:
    return """### Fonctionnalités :
- 💬 **Chat interactif** : Posez vos questions sur Othello
- 📚 **Base de connaissances** : Réponses basées sur le texte complet de la pièce
- 🔍 **Citations** : Le chatbot cite toujours ses sources
- 📜 **Historique** : Consultez vos conversations précédentes
- 🤖 **Choix du modèle** : Sélectionnez le modèle OpenAI de votre choix"""


def get_homepage_content() -> str:
    intro = get_homepage_intro()
    features = get_homepage_features()
    usage = """### Comment utiliser :
1. Naviguez vers la page **Chat** dans le menu latéral
2. Sélectionnez votre modèle préféré
3. Commencez à poser vos questions sur Othello !"""
    footer = """*Cette application utilise l'API OpenAI et une base de données vectorielle
pour fournir des réponses précises et contextuelles.*"""
    return f"{intro}\n\n{features}\n\n{usage}\n\n---\n\n{footer}"


def display_homepage():
    st.title("🎭 Chatbot Othello")
    st.markdown("---")
    st.markdown(get_homepage_content())


def setup_sidebar() -> tuple:
    st.header("⚙️ Paramètres")
    model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    selected_model = st.selectbox("Modèle OpenAI", model_options, index=0)
    num_chunks = st.slider(
        "Nombre de passages à utiliser", min_value=1, max_value=5, value=3
    )
    if st.button("🗑️ Effacer l'historique"):
        st.session_state.messages = []
        st.rerun()
    return selected_model, num_chunks


def display_message_history():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message:
                with st.expander("📚 Sources"):
                    for i, source in enumerate(message["sources"], 1):
                        st.text(f"Passage {i}:")
                        st.text(source)


def add_user_message(prompt: str):
    st.session_state.messages.append({"role": "user", "content": prompt})


def get_context_from_query(prompt: str, index: faiss.Index, 
                          chunks: List[str], num_chunks: int) -> tuple:
    with st.spinner("Recherche dans la base de connaissances..."):
        similar_chunks = search_similar_chunks(prompt, index, chunks, k=num_chunks)
        context = "\n\n".join([f"Passage {i+1}:\n{chunk}" 
                              for i, chunk in enumerate(similar_chunks)])
    return similar_chunks, context


def generate_assistant_response(messages: List[Dict], model: str, 
                                context: str) -> str:
    with st.spinner("Génération de la réponse..."):
        return get_chat_response(messages, model, context)


def display_assistant_response(response: str, similar_chunks: List[str]):
    with st.chat_message("assistant"):
        st.markdown(response)
        with st.expander("📚 Sources utilisées"):
            for i, chunk in enumerate(similar_chunks, 1):
                st.text(f"Source {i}:")
                truncated = chunk[:500] + "..." if len(chunk) > 500 else chunk
                st.text(truncated)


def display_user_message(prompt: str):
    with st.chat_message("user"):
        st.markdown(prompt)


def get_response_for_query(prompt: str, index: faiss.Index, 
                          chunks: List[str], num_chunks: int, 
                          selected_model: str) -> tuple:
    similar_chunks, context = get_context_from_query(
        prompt, index, chunks, num_chunks
    )
    messages_for_llm = st.session_state.messages[:-1]
    response = generate_assistant_response(
        messages_for_llm, selected_model, context
    )
    return response, similar_chunks


def generate_and_display_response(prompt: str, index: faiss.Index, 
                                 chunks: List[str], num_chunks: int, 
                                 selected_model: str) -> tuple:
    response, similar_chunks = get_response_for_query(
        prompt, index, chunks, num_chunks, selected_model
    )
    display_assistant_response(response, similar_chunks)
    return response, similar_chunks


def save_assistant_message(response: str, similar_chunks: List[str]):
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "sources": similar_chunks
    })


def display_user_prompt(prompt: str):
    with st.chat_message("user"):
        st.markdown(prompt)


def display_response_with_sources(response: str, similar_chunks: List[str]):
    st.markdown(response)
    with st.expander("📚 Sources utilisées"):
        for i, chunk in enumerate(similar_chunks, 1):
            st.text(f"Passage {i}:")
            st.text(chunk)


def get_context_and_response(prompt: str, index: faiss.Index, 
                            chunks: List[str], num_chunks: int, 
                            selected_model: str) -> tuple:
    with st.spinner("Recherche dans la base de connaissances..."):
        similar_chunks, context = get_context_from_query(
            prompt, index, chunks, num_chunks
        )
    with st.spinner("Génération de la réponse..."):
        user_msg = {"role": "user", "content": prompt}
        response = generate_assistant_response(
            st.session_state.messages + [user_msg], selected_model, context
        )
    return response, similar_chunks


def process_user_query(prompt: str, index: faiss.Index, 
                       chunks: List[str], num_chunks: int, 
                       selected_model: str):
    display_user_prompt(prompt)
    
    with st.chat_message("assistant"):
        response, similar_chunks = get_context_and_response(
            prompt, index, chunks, num_chunks, selected_model
        )
        display_response_with_sources(response, similar_chunks)
    
    add_user_message(prompt)
    save_assistant_message(response, similar_chunks)


def display_chat_page():
    st.title("💬 Chat avec Othello")
    
    index, chunks = load_vector_database("othello_index.faiss", "othello_chunks.pkl")
    
    if index is None or chunks is None:
        st.error("⚠️ Base de données vectorielle non trouvée. "
                "Veuillez d'abord exécuter vector_db.py pour la créer.")
        return
    
    with st.sidebar:
        selected_model, num_chunks = setup_sidebar()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    display_message_history()
    
    if prompt := st.chat_input("Posez votre question sur Othello..."):
        process_user_query(prompt, index, chunks, num_chunks, selected_model)


def load_othello_text() -> str:
    try:
        with open("othello.txt", 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Fichier othello.txt non trouvé."


def display_othello_text():
    st.title("📖 Othello - Texte complet")
    st.markdown("---")
    
    text = load_othello_text()
    
    if text == "Fichier othello.txt non trouvé.":
        st.error(text)
        return
    
    st.markdown("### Lisez la pièce complète d'Othello de William Shakespeare")
    st.markdown("---")
    
    st.text_area(
        "Texte complet",
        value=text,
        height=600,
        disabled=True,
        label_visibility="collapsed"
    )


def main():
    if not os.getenv("OPENAI_API_KEY"):
        st.error("⚠️ OPENAI_API_KEY n'est pas définie dans le fichier .env")
        st.stop()
    
    page = st.sidebar.selectbox(
        "Navigation",
        ["🏠 Accueil", "💬 Chat", "📖 Othello"]
    )
    
    if page == "🏠 Accueil":
        display_homepage()
    elif page == "💬 Chat":
        display_chat_page()
    elif page == "📖 Othello":
        display_othello_text()


if __name__ == "__main__":
    main()
