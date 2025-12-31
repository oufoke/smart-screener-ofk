import streamlit as st
import json
from PyPDF2 import PdfReader
from openai import OpenAI

#Configuration de la page (doit être la première commande Streamlit)
st.set_page_config(
    page_title="Assistant RH - PME",
    page_icon="👔",
    layout="wide"
)

# --- 1. LE CERVEAU (LE PROMPT) ---
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

# --- 2. FONCTIONS UTILITAIRES ---

def extract_text_from_pdf(pdf_file):
    """Extrait le texte brut d'un fichier PDF uploadé."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Erreur de lecture du PDF : {e}")
        return None

def analyze_cv_with_ai(api_key, cv_text, job_desc):
    """Envoie les données à l'API OpenAI pour analyse."""
    client = OpenAI(api_key=api_key)
    
    user_message = f"""
    --- OFFRE D'EMPLOI ---
    {job_desc}
    
    --- CV CANDIDAT ---
    {cv_text}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Modèle rapide et économique
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Erreur API : {e}")
        return None

# --- 3. INTERFACE UTILISATEUR (UI) ---

# Barre latérale pour la configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Clé API OpenAI", type="password", help="Nécessaire pour faire fonctionner l'IA")
    st.info("💡 Astuce Portfolio : Pour la démo, utilisez une clé temporaire.")
    st.markdown("---")
    st.write("Developed by **[Votre Nom]**")

# Titre Principal
st.title("🤖 Smart-Screener PME")
st.markdown("### L'Assistant de pré-qualification pour recruteurs pressés")
st.markdown("---")

# Création de deux colonnes
col_input, col_result = st.columns([1, 1])

# COLONNE DE GAUCHE : LES ENTRÉES
with col_input:
    st.subheader("1. Les Données")
    
    # Zone de texte pour l'offre
    job_desc = st.text_area(
        "Description du poste (Job Description)", 
        height=200, 
        placeholder="Collez ici l'offre d'emploi..."
    )
    
    # Upload du CV
    uploaded_file = st.file_uploader("CV du candidat (PDF uniquement)", type="pdf")

    # Bouton d'action
    analyze_btn = st.button("Lancer l'analyse 🚀", type="primary", use_container_width=True)

# COLONNE DE DROITE : LES RÉSULTATS
with col_result:
    st.subheader("2. L'Analyse IA")

    if analyze_btn:
        if not api_key:
            st.warning("⚠️ Veuillez entrer votre clé API OpenAI dans la barre latérale.")
        elif not job_desc or not uploaded_file:
            st.warning("⚠️ Veuillez remplir l'offre ET uploader un CV.")
        else:
            with st.spinner("Le DRH virtuel analyse le document..."):
                # 1. Extraction du texte
                cv_text = extract_text_from_pdf(uploaded_file)
                
                if cv_text:
                    # 2. Appel IA
                    result = analyze_cv_with_ai(api_key, cv_text, job_desc)
                    
                    if result:
                        # --- AFFICHAGE DU SCORE ---
                        score = result.get("score_match", 0)
                        
                        # Couleur dynamique selon le score
                        score_color = "green" if score >= 70 else "orange" if score >= 50 else "red"
                        
                        st.markdown(f"""
                        <div style="text-align: center; border: 2px solid #f0f2f6; padding: 20px; border-radius: 10px;">
                            <h2 style="margin:0;">Compatibilité</h2>
                            <h1 style="color:{score_color}; font-size: 60px; margin:0;">{score}/100</h1>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.success(f"📝 **Synthèse :** {result['synthese']}")

                        # --- ONGLETS POUR LES DÉTAILS ---
                        tab1, tab2, tab3 = st.tabs(["✅ Points Forts", "⚠️ Vigilance", "🎤 Entretien"])
                        
                        with tab1:
                            for point in result['points_forts']:
                                st.markdown(f"- {point}")
                                
                        with tab2:
                            for point in result['points_vigilance']:
                                st.markdown(f"- {point}")
                                
                        with tab3:
                            st.info("Posez ces questions pour vérifier les compétences :")
                            for q in result['questions_entretien']:
                                st.markdown(f"❓ **{q}**")
                        
                        # Debug (optionnel, pour montrer au recruteur qu'on maîtrise la data brute)
                        with st.expander("Voir le JSON brut (Données techniques)"):
                            st.json(result)