import logging
import pandas as pd
from typing import Optional, Dict, Any, List
from difflib import SequenceMatcher
from services.bedrock_client import ask_bedrock

logger = logging.getLogger(__name__)

class FAQAgent:
    """
    Agent spécialisé dans la réponse aux questions fréquentes (FAQ).
    Recherche d'abord dans une base de connaissances locale, puis utilise Bedrock en fallback.
    """
    
    # Seuil de similarité pour les correspondances floues
    SIMILARITY_THRESHOLD = 0.6
    
    def __init__(self, df: Optional[pd.DataFrame] = None):
        """
        Initialise l'agent FAQ avec un DataFrame contenant les paires instruction/réponse.
        
        Args:
            df: DataFrame avec colonnes 'instruction' et 'response'
        """
        logger.info("Initialisation de FAQAgent...")
        
        self.df = df
        self._validate_dataframe()
        
        if self.df is not None and not self.df.empty:
            # Prétraitement des instructions pour une recherche plus efficace
            self._preprocess_instructions()
            logger.info(f"FAQAgent initialisé avec {len(self.df)} entrées")
        else:
            logger.warning("Aucune donnée FAQ fournie ou DataFrame vide")

    def _validate_dataframe(self) -> None:
        """Valide la structure du DataFrame FAQ."""
        if self.df is None:
            return
        
        if not isinstance(self.df, pd.DataFrame):
            logger.error(f"Type incorrect pour le DataFrame: {type(self.df)}")
            self.df = None
            return
        
        # Vérification des colonnes requises
        required_columns = ['instruction', 'response']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            logger.error(f"Colonnes manquantes dans le DataFrame FAQ: {missing_columns}")
            self.df = None
            return
        
        # Nettoyage des données
        self.df = self.df.dropna(subset=['instruction', 'response']).reset_index(drop=True)
        
        if self.df.empty:
            logger.warning("DataFrame FAQ vide après nettoyage")

    def _preprocess_instructions(self) -> None:
        """Prétraite les instructions pour une recherche plus efficace."""
        if self.df is None or self.df.empty:
            return
        
        try:
            # Création d'une version normalisée des instructions
            self.df['instruction_lower'] = self.df['instruction'].str.lower().str.strip()
            self.df['instruction_words'] = self.df['instruction_lower'].str.split()
            
            # Création d'un index pour la recherche rapide
            self.keywords_index = {}
            for idx, words in enumerate(self.df['instruction_words']):
                for word in words:
                    if len(word) > 2:  # Ignorer les mots trop courts
                        if word not in self.keywords_index:
                            self.keywords_index[word] = []
                        self.keywords_index[word].append(idx)
            
            logger.debug(f"Index de mots-clés créé avec {len(self.keywords_index)} entrées")
            
        except Exception as e:
            logger.error(f"Erreur lors du prétraitement des instructions: {e}")

    def _exact_match(self, msg: str) -> Optional[pd.Series]:
        """
        Recherche une correspondance exacte dans les instructions.
        
        Args:
            msg: Message utilisateur normalisé
            
        Returns:
            La première correspondance exacte ou None
        """
        if self.df is None or self.df.empty:
            return None
        
        try:
            match = self.df[self.df['instruction_lower'].str.contains(msg, na=False)]
            if not match.empty:
                logger.info(f"Correspondance exacte trouvée pour: {msg[:50]}...")
                return match.iloc[0]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche exacte: {e}")
        
        return None

    def _fuzzy_match(self, msg: str) -> Optional[pd.Series]:
        """
        Recherche une correspondance floue basée sur les mots-clés.
        
        Args:
            msg: Message utilisateur normalisé
            
        Returns:
            La meilleure correspondance ou None
        """
        if self.df is None or self.df.empty or not hasattr(self, 'keywords_index'):
            return None
        
        try:
            words = set(msg.split())
            scores = {}
            
            # Trouver les instructions pertinentes via l'index
            relevant_indices = set()
            for word in words:
                if len(word) > 2 and word in self.keywords_index:
                    relevant_indices.update(self.keywords_index[word])
            
            if not relevant_indices:
                return None
            
            # Calculer le score de similarité pour chaque instruction pertinente
            for idx in relevant_indices:
                instruction = self.df.iloc[idx]['instruction_lower']
                # Similarité basée sur le ratio de mots communs
                common_words = len(set(words) & set(self.df.iloc[idx]['instruction_words']))
                total_words = max(len(words), len(self.df.iloc[idx]['instruction_words']))
                
                if total_words > 0:
                    score = common_words / total_words
                    
                    # Bonus pour les correspondances exactes de phrases
                    if msg in instruction:
                        score += 0.2
                    
                    scores[idx] = min(score, 1.0)
            
            if scores:
                best_idx = max(scores, key=scores.get)
                best_score = scores[best_idx]
                
                if best_score >= self.SIMILARITY_THRESHOLD:
                    logger.info(f"Correspondance floue trouvée avec score {best_score:.2f}")
                    return self.df.iloc[best_idx]
        
        except Exception as e:
            logger.error(f"Erreur lors de la recherche floue: {e}")
        
        return None

    def _get_relevant_context(self, msg: str) -> str:
        """
        Récupère le contexte pertinent pour le prompt Bedrock.
        
        Args:
            msg: Message utilisateur
            
        Returns:
            Contexte formaté
        """
        if self.df is None or self.df.empty:
            return "Aucune FAQ disponible."
        
        try:
            # Récupérer quelques instructions similaires pour le contexte
            similar = []
            msg_lower = msg.lower()
            
            for _, row in self.df.head(5).iterrows():
                similarity = SequenceMatcher(None, msg_lower, row['instruction'].lower()).ratio()
                if similarity > 0.3:
                    similar.append(f"- Question: {row['instruction']}\n  Réponse: {row['response'][:100]}...")
            
            if similar:
                return "Questions similaires dans la base FAQ:\n" + "\n".join(similar)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contexte: {e}")
        
        return "Aucune question similaire trouvée dans la base FAQ."

    def run(self, message: str) -> str:
        """
        Traite une question utilisateur en cherchant d'abord dans la FAQ,
        puis en utilisant Bedrock en fallback.
        
        Args:
            message: Question de l'utilisateur
            
        Returns:
            Réponse de la FAQ ou de Bedrock
        """
        logger.info(f"Traitement de la question FAQ: {message[:100]}...")
        
        if not message or not isinstance(message, str):
            logger.warning("Message vide ou invalide")
            return "Veuillez poser une question valide."
        
        # Normalisation du message
        msg_lower = message.lower().strip()
        
        # Étape 1: Recherche exacte
        match = self._exact_match(msg_lower)
        if match is not None:
            logger.info("Réponse trouvée dans la FAQ (correspondance exacte)")
            return f"📚 D'après notre base de connaissances:\n\n{match['response']}"
        
        # Étape 2: Recherche floue
        match = self._fuzzy_match(msg_lower)
        if match is not None:
            logger.info("Réponse trouvée dans la FAQ (correspondance floue)")
            return f"📚 J'ai trouvé une réponse similaire dans notre FAQ:\n\n{match['response']}\n\n💡 Cette réponse correspond-elle à votre question ?"
        
        # Étape 3: Fallback vers Bedrock avec contexte
        logger.info("Aucune correspondance trouvée dans la FAQ, utilisation de Bedrock")
        
        context = self._get_relevant_context(message)
        
        prompt = f"""
Tu es un assistant d'entreprise spécialisé dans les questions fréquentes.

CONTEXTE:
{context}

INSTRUCTIONS:
- Réponds de manière professionnelle et concise
- Si la question concerne des informations non disponibles dans la FAQ, sois honnête
- Propose de rediriger vers un humain si nécessaire
- Utilise un ton amical mais professionnel

QUESTION DE L'UTILISATEUR:
{message}

RÉPONSE:
"""
        
        try:
            bedrock_response = ask_bedrock(prompt)
            return f"🤖 {bedrock_response}\n\n💡 Pour des questions plus précises, n'hésitez pas à consulter notre FAQ ou contacter le support."
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à Bedrock: {e}")
            return "❌ Désolé, je rencontre des difficultés techniques. Veuillez réessayer ou contacter le support."

    def add_faq_entry(self, instruction: str, response: str) -> bool:
        """
        Ajoute une nouvelle entrée à la FAQ.
        
        Args:
            instruction: La question/instruction
            response: La réponse associée
            
        Returns:
            True si l'ajout a réussi
        """
        if not instruction or not response:
            logger.warning("Instruction ou réponse vide")
            return False
        
        try:
            new_entry = pd.DataFrame({
                'instruction': [instruction],
                'response': [response]
            })
            
            if self.df is None:
                self.df = new_entry
            else:
                self.df = pd.concat([self.df, new_entry], ignore_index=True)
            
            # Refaire le prétraitement
            self._preprocess_instructions()
            
            logger.info(f"Nouvelle entrée FAQ ajoutée: {instruction[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout à la FAQ: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne des statistiques sur la FAQ.
        
        Returns:
            Dictionnaire avec les statistiques
        """
        if self.df is None or self.df.empty:
            return {
                "total_entries": 0,
                "status": "empty"
            }
        
        try:
            return {
                "total_entries": len(self.df),
                "status": "active",
                "avg_response_length": int(self.df['response'].str.len().mean()),
                "topics": self.df['instruction'].str.extract(r'(\b\w+\b)')[0].value_counts().head(5).to_dict()
            }
        except Exception as e:
            logger.error(f"Erreur lors de la génération des statistiques: {e}")
            return {
                "total_entries": len(self.df),
                "status": "error",
                "error": str(e)
            }