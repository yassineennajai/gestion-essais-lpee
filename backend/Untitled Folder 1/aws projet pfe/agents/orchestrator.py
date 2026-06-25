import logging
import pandas as pd
from agents.analytics_agent import AnalyticsAgent
from agents.report_agent import ReportAgent
from agents.faq_agent import FAQAgent
from services.bedrock_client import ask_bedrock

logger = logging.getLogger(__name__)

class SuperOrchestrator:
    """
    Orchestrateur intelligent version ULTIME
    Capable de répondre à TOUTES les questions en utilisant le dataset
    """
    
    def __init__(self, data):
        logger.info("🚀 Initialisation du SuperOrchestrator...")
        
        # Sauvegarde des données brutes pour référence
        self.raw_data = data
        
        # Initialisation de tous les agents
        self.analytics_agent = AnalyticsAgent(data)
        self.report_agent = ReportAgent(data)
        
        # FAQ Agent avec son propre dataframe
        faq_df = data.get("faq")
        self.faq_agent = FAQAgent(faq_df)
        
        # Extraction du dataframe principal (sales)
        self.df = data.get("sales")
        
        if self.df is not None:
            logger.info(f"📊 Dataset principal chargé: {len(self.df)} lignes")
            logger.info(f"📋 Colonnes disponibles: {self.df.columns.tolist()}")
            
            # Pré-calculer quelques statistiques pour les questions rapides
            self._precompute_stats()
    
    def _precompute_stats(self):
        """Pré-calcule les statistiques courantes pour des réponses instantanées"""
        self.stats = {}
        
        try:
            if self.df is not None and not self.df.empty:
                # Statistiques générales
                self.stats['total_revenue'] = self.df['Total'].sum() if 'Total' in self.df.columns else 0
                self.stats['avg_basket'] = self.df['Total'].mean() if 'Total' in self.df.columns else 0
                self.stats['total_transactions'] = len(self.df)
                
                # Statistiques produits
                if 'Product line' in self.df.columns:
                    # Top produits par CA
                    self.stats['top_products_by_revenue'] = self.df.groupby('Product line')['Total'].sum().nlargest(5).to_dict()
                    
                    # Top produits par quantité
                    if 'Quantity' in self.df.columns:
                        self.stats['top_products_by_quantity'] = self.df.groupby('Product line')['Quantity'].sum().nlargest(5).to_dict()
                    
                    # Prix moyens par produit
                    if 'Unit Price' in self.df.columns:
                        self.stats['avg_price_by_product'] = self.df.groupby('Product line')['Unit Price'].mean().to_dict()
                    else:
                        # Estimer le prix unitaire moyen
                        if 'Total' in self.df.columns and 'Quantity' in self.df.columns:
                            self.df['estimated_unit_price'] = self.df['Total'] / self.df['Quantity'].clip(lower=1)
                            self.stats['avg_price_by_product'] = self.df.groupby('Product line')['estimated_unit_price'].mean().to_dict()
                
                logger.info("✅ Statistiques pré-calculées avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur pré-calcul stats: {e}")
    
    def _extract_number(self, text):
        """Extrait un nombre du texte (ex: '3 produits' -> 3)"""
        import re
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else None
    
    def _handle_product_question(self, message):
        """Gère spécifiquement les questions sur les produits"""
        
        msg_lower = message.lower()
        
        # Déterminer le nombre de produits demandés
        n = self._extract_number(message)
        if n is None:
            if 'top' in msg_lower or 'meilleur' in msg_lower:
                n = 5  # Default top 5
            else:
                n = 10  # Default all
        
        # Vérifier si on a les données nécessaires
        if 'Product line' not in self.df.columns:
            return None
        
        try:
            # Construction de la réponse selon la question
            response = []
            
            # Question sur les prix
            if 'prix' in msg_lower or 'price' in msg_lower or 'tarif' in msg_lower:
                if 'avg_price_by_product' in self.stats:
                    top_products = sorted(self.stats['avg_price_by_product'].items(), 
                                         key=lambda x: x[1], reverse=True)[:n]
                    
                    response.append(f"\n🏆 TOP {n} PRODUITS PAR PRIX MOYEN")
                    response.append("="*45)
                    
                    for i, (product, price) in enumerate(top_products, 1):
                        response.append(f"{i}. {product:<30} {price:>10,.2f} FCFA")
                    
                    # Ajouter les stats de vente
                    response.append(f"\n📊 DÉTAIL DES VENTES (TOP {n})")
                    response.append("="*45)
                    
                    for product, _ in top_products:
                        product_data = self.df[self.df['Product line'] == product]
                        total_qty = product_data['Quantity'].sum() if 'Quantity' in product_data.columns else len(product_data)
                        total_rev = product_data['Total'].sum() if 'Total' in product_data.columns else 0
                        
                        response.append(f"\n📦 {product}:")
                        response.append(f"   💰 CA: {total_rev:,.0f} FCFA")
                        response.append(f"   📦 Quantité: {total_qty:,.0f}")
            
            # Question sur les meilleures ventes
            elif 'vente' in msg_lower or 'vend' in msg_lower or 'quantity' in msg_lower:
                if 'top_products_by_quantity' in self.stats:
                    top_products = list(self.stats['top_products_by_quantity'].items())[:n]
                    
                    response.append(f"\n🏆 TOP {n} PRODUITS LES PLUS VENDUS")
                    response.append("="*45)
                    
                    for i, (product, qty) in enumerate(top_products, 1):
                        response.append(f"{i}. {product:<30} {qty:>10,.0f} unités")
            
            # Question sur le chiffre d'affaires
            elif 'chiffre' in msg_lower or 'ca' in msg_lower or 'revenu' in msg_lower or 'revenue' in msg_lower:
                if 'top_products_by_revenue' in self.stats:
                    top_products = list(self.stats['top_products_by_revenue'].items())[:n]
                    
                    response.append(f"\n🏆 TOP {n} PRODUITS PAR CHIFFRE D'AFFAIRES")
                    response.append("="*45)
                    
                    for i, (product, revenue) in enumerate(top_products, 1):
                        response.append(f"{i}. {product:<30} {revenue:>10,.0f} FCFA")
            
            # Question générale sur les produits
            else:
                if 'avg_price_by_product' in self.stats:
                    # Mélanger les infos
                    products_info = []
                    for product in list(self.stats['avg_price_by_product'].keys())[:n]:
                        price = self.stats['avg_price_by_product'].get(product, 0)
                        qty = self.stats['top_products_by_quantity'].get(product, 0) if 'top_products_by_quantity' in self.stats else 0
                        revenue = self.stats['top_products_by_revenue'].get(product, 0) if 'top_products_by_revenue' in self.stats else 0
                        
                        products_info.append({
                            'name': product,
                            'price': price,
                            'quantity': qty,
                            'revenue': revenue
                        })
                    
                    response.append(f"\n📋 INFORMATIONS PRODUITS (TOP {n})")
                    response.append("="*60)
                    response.append(f"{'PRODUIT':<25} {'PRIX':>10} {'VENTES':>10} {'CA':>12}")
                    response.append("-"*60)
                    
                    for p in products_info:
                        response.append(f"{p['name']:<25} {p['price']:>10,.0f} {p['quantity']:>10,.0f} {p['revenue']:>12,.0f} FCFA")
            
            if response:
                return "\n".join(response)
                
        except Exception as e:
            logger.error(f"Erreur dans _handle_product_question: {e}")
        
        return None
    
    def _handle_sales_question(self, message):
        """Gère les questions sur les ventes"""
        
        msg_lower = message.lower()
        
        try:
            # Questions simples sur les ventes
            if 'total' in msg_lower and ('vente' in msg_lower or 'ca' in msg_lower):
                return f"💰 Chiffre d'affaires total: {self.stats.get('total_revenue', 0):,.0f} FCFA"
            
            elif 'moyen' in msg_lower and ('panier' in msg_lower or 'basket' in msg_lower):
                return f"🛒 Panier moyen: {self.stats.get('avg_basket', 0):,.0f} FCFA"
            
            elif 'nombre' in msg_lower and ('transaction' in msg_lower or 'vente' in msg_lower):
                return f"🧾 Nombre total de transactions: {self.stats.get('total_transactions', 0):,}"
            
            elif 'moyenne' in msg_lower and ('note' in msg_lower or 'rating' in msg_lower):
                if 'Rating' in self.df.columns:
                    avg_rating = self.df['Rating'].mean()
                    return f"⭐ Note moyenne: {avg_rating:.2f}/10"
            
        except Exception as e:
            logger.error(f"Erreur dans _handle_sales_question: {e}")
        
        return None
    
    def route(self, message):
        """
        Route intelligent qui répond à TOUTES les questions
        """
        
        logger.info(f"📝 Traitement de: {message[:100]}...")
        
        # 1️⃣ Vérifier si le dataset est chargé
        if self.df is None or self.df.empty:
            return "❌ Désolé, le dataset n'est pas disponible pour le moment."
        
        # 2️⃣ Gestion des questions simples sur les ventes
        sales_response = self._handle_sales_question(message)
        if sales_response:
            return sales_response
        
        # 3️⃣ Gestion des questions sur les produits
        product_response = self._handle_product_question(message)
        if product_response:
            return product_response
        
        # 4️⃣ Utilisation des agents spécialisés
        # Analytics Agent pour les analyses complexes
        if any(word in message.lower() for word in ['analyse', 'compar', 'stat', 'trend', 'évolution']):
            result = self.analytics_agent.run(message)
            if result and "Erreur" not in result:
                return result
        
        # Report Agent pour les rapports
        if any(word in message.lower() for word in ['rapport', 'report', 'mois', 'année', 'global']):
            result = self.report_agent.run(message)
            if result and "Erreur" not in result:
                return result
        
        # FAQ Agent pour les questions générales
        faq_result = self.faq_agent.run(message)
        if faq_result and "🤖" not in faq_result:  # Si FAQ a trouvé une réponse
            return faq_result
        
        # 5️⃣ Fallback intelligent avec contexte du dataset
        context = self._build_dynamic_context(message)
        
        prompt = f"""
Tu es un assistant d'entreprise SUPER INTELLIGENT qui a ACCÈS COMPLET aux données.

CONTEXTE DISPONIBLE:
- Dataset avec {len(self.df)} lignes de ventes
- Colonnes: {self.df.columns.tolist()}
- Période: du {self.df['Date'].min() if 'Date' in self.df.columns else 'N/A'} au {self.df['Date'].max() if 'Date' in self.df.columns else 'N/A'}
- Chiffre d'affaires total: {self.stats.get('total_revenue', 0):,.0f} FCFA
- Nombre de produits: {self.df['Product line'].nunique() if 'Product line' in self.df.columns else 'N/A'}

INSTRUCTIONS SPÉCIALES:
1. Utilise les données FOURNIES pour répondre
2. Sois PRÉCIS et donne des chiffres
3. Si la question demande une analyse, propose de l'aide
4. Réponds en français professionnel

QUESTION DE L'UTILISATEUR:
{message}

RÉPONSE (en utilisant les données disponibles):
"""
        
        try:
            bedrock_response = ask_bedrock(prompt)
            return bedrock_response
        except Exception as e:
            logger.error(f"Erreur Bedrock: {e}")
            return "❌ Désolé, je rencontre des difficultés techniques. Veuillez réessayer."
    
    def _build_dynamic_context(self, message):
        """Construit un contexte dynamique basé sur la question"""
        context = []
        
        # Ajouter des stats pertinentes selon la question
        msg_lower = message.lower()
        
        if 'produit' in msg_lower or 'product' in msg_lower:
            if 'Product line' in self.df.columns:
                products = self.df['Product line'].unique()[:5]
                context.append(f"Catégories de produits: {', '.join(products)}...")
        
        if 'prix' in msg_lower or 'price' in msg_lower:
            if 'Unit Price' in self.df.columns:
                context.append(f"Prix moyens par catégorie disponibles")
        
        return "\n".join(context) if context else "Données disponibles pour analyse"

# Exemple d'utilisation
if __name__ == "__main__":
    # Simulation des données
    data = {
        "sales": pd.DataFrame({
            'Product line': ['Sports', 'Home', 'Food', 'Sports', 'Health'],
            'Unit Price': [86.31, 73.56, 54.84, 92.15, 46.95],
            'Quantity': [10, 5, 8, 12, 6],
            'Total': [863.1, 367.8, 438.72, 1105.8, 281.7],
            'Rating': [8.5, 7.2, 9.1, 8.8, 6.9],
            'Date': pd.date_range('2024-01-01', periods=5)
        })
    }
    
    orchestrator = SuperOrchestrator(data)
    
    # Test de différentes questions
    questions = [
        "donne les 3 produits top avec le prix",
        "quel est le chiffre d'affaires total ?",
        "quels sont les produits les plus vendus ?",
        "donne-moi le top 4 des produits par CA",
        "quelle est la note moyenne ?"
    ]
    
    for q in questions:
        print(f"\n❓ {q}")
        print(orchestrator.route(q))
        print("-" * 50)