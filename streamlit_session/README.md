# Chatbot Othello

Chatbot basé sur un LLM pour répondre aux questions sur la pièce Othello de Shakespeare.

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Créer un fichier `.env` avec votre clé API OpenAI :
```
OPENAI_API_KEY=votre_cle_api_ici
```

## Utilisation

1. Générer la base de données vectorielle :
```bash
python vector_db.py
```

2. Lancer l'application :
```bash
streamlit run app.py
```

3. Utiliser l'application dans le navigateur (http://localhost:8501)
