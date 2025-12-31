import streamlit as st
import json
from typing import Optional, Dict, Any
from PyPDF2 import PdfReader
from openai import OpenAI

# --- CONSTANTES DE CONFIGURATION ---
PAGE_TITLE = "Assistant RH - PME"
PAGE_ICON = "👔"
MODEL_NAME = "gpt-4o-mini"
SYSTEM_PROMPT = """
Tu es un Expert en Recrutement (DRH) avec 15 ans d'expérience.
Ta mission est d'analyser un candidat par rapport à une offre d'emploi.

Tu dois répondre UNIQUEMENT au format JSON strict avec la structure suivante :
{
    "score_match": (entier de 0 à 100, sois sévère),
    "synthese": "Un résumé en 2 phrases du profil par rapport au besoin",
    "points_forts": ["Point 1", "Point 2", "Point 3"],
    "points_vigilance": ["Attention 1", "Lacune 2", "Incohérence 3"],
    "questions_entretien": [
        "Question 1 (précise)",
        "Question 2 (technique)",
        "Question 3 (culture)"
    ]
}
"""

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide"
)

# --- FONCTIONS MÉTIER ---

def extract_text_from_pdf(pdf_file) -> Optional[str]:
    """
    Extrait le texte brut d'un fichier PDF.
    
    Args:
        pdf_file: Le fichier binaire uploadé via Streamlit.
        
    Returns:
        str: Le texte extrait ou None en cas d'erreur.
    """
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Erreur lors de la lecture du PDF : {str(e)}")
        return None

def analyze_cv_with_ai(api_key: str, cv_text: str, job_desc: str) -> Optional[Dict[str, Any]]:
    """
    Interroge l'API OpenAI pour analyser le CV par rapport à l'offre.
    
    Args:
        api_key (str): La clé API OpenAI.
        cv_text (str): Le contenu textuel du CV.
        job_desc (str): La description du poste.
        
    Returns:
        dict: La réponse JSON parsée ou None en cas d'échec.
    """
    client = OpenAI(api_key=api_key)
    
    user_message = f"""
    --- OFFRE D'EMPLOI ---
    {job_desc}
    
    --- CV CANDIDAT ---
    {cv_text}
    """

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2, # Température basse pour garantir la cohérence
            response_format={"type": "json_object"}
        )
        # Parsing de la réponse JSON
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Erreur lors de l'appel API : {str(e)}")
        return None

# --- FONCTION PRINCIPALE (MAIN) ---

def main():
    """Fonction principale gérant l'interface utilisateur."""
    
    # --- SIDEBAR : CONFIGURATION ---
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Gestion sécurisée de la clé API
        api_key = st.secrets.get("OPENAI_API_KEY")
        if api_key:
            st.success("✅ Clé API chargée du serveur")
        else:
            api_key = st.text_input(
                "Clé API OpenAI", 
                type="password", 
                help="Entrez votre clé API OpenAI pour tester l'application."
            )
            if not api_key:
                st.info("Veuillez renseigner une clé API pour continuer.")

        st.markdown("---")
        st.write("Developed by **Oumar F. KEBE**")

    # --- MAIN CONTENT : INTERFACE ---
    st.title("🤖 Smart-Screener PME")
    st.markdown("### L'Assistant de pré-qualification pour recruteurs pressés")
    st.markdown("---")

    col_input, col_result = st.columns([1, 1])

    # Colonne de Gauche : Inputs
    with col_input:
        st.subheader("1. Les Données")
        job_desc = st.text_area(
            "Description du poste", 
            height=250, 
            placeholder="Copiez-collez l'offre d'emploi ici..."
        )
        uploaded_file = st.file_uploader("CV du candidat (PDF)", type="pdf")
        
        analyze_btn = st.button("Lancer l'analyse 🚀", type="primary", use_container_width=True)

    # Colonne de Droite : Résultats
    with col_result:
        st.subheader("2. L'Analyse IA")

        if analyze_btn:
            # Vérifications préliminaires
            if not api_key:
                st.warning("⚠️ Clé API manquante.")
            elif not job_desc:
                st.warning("⚠️ Veuillez saisir une description de poste.")
            elif not uploaded_file:
                st.warning("⚠️ Veuillez uploader un CV.")
            else:
                # Traitement
                with st.spinner("Analyse du profil en cours..."):
                    cv_text = extract_text_from_pdf(uploaded_file)
                    
                    if cv_text:
                        result = analyze_cv_with_ai(api_key, cv_text, job_desc)
                        
                        if result:
                            # Affichage du Score
                            score = result.get("score_match", 0)
                            color = "green" if score >= 70 else "orange" if score >= 50 else "red"
                            
                            st.markdown(f"""
                            <div style="text-align: center; border: 2px solid #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                <h3 style="margin:0; color: #555;">Compatibilité</h3>
                                <h1 style="color:{color}; font-size: 60px; margin:0;">{score}/100</h1>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.success(f"**Synthèse :** {result.get('synthese', 'Pas de synthèse disponible.')}")

                            # Affichage détaillé via Onglets
                            tab1, tab2, tab3 = st.tabs(["✅ Points Forts", "⚠️ Vigilance", "🎤 Entretien"])
                            
                            with tab1:
                                for point in result.get('points_forts', []):
                                    st.markdown(f"- {point}")
                            
                            with tab2:
                                for point in result.get('points_vigilance', []):
                                    st.markdown(f"- {point}")
                                    
                            with tab3:
                                st.info("Questions suggérées :")
                                for q in result.get('questions_entretien', []):
                                    st.markdown(f"❓ **{q}**")
                            
                            # Zone technique (Debug)
                            with st.expander("Voir les données brutes (JSON)"):
                                st.json(result)

# Point d'entrée du script
if __name__ == "__main__":
    main()