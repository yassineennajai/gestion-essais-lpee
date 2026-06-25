from services.bedrock_client import ask_bedrock
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class AnalyticsAgent:

    def __init__(self, data):
        # data = {"sales": df}
        self.df = data.get("sales")
        
        if self.df is not None:
            logger.info(f"AnalyticsAgent initialisé avec {len(self.df)} lignes")
            logger.info(f"Colonnes disponibles: {self.df.columns.tolist()}")

    def _analyze_top_products(self, n=4):
        """Méthode spéciale pour l'analyse des top produits"""
        try:
            # Vérifier les colonnes disponibles
            product_col = None
            price_col = None
            
            # Détection automatique des colonnes
            for col in self.df.columns:
                if 'product' in col.lower() or 'line' in col.lower():
                    product_col = col
                if 'price' in col.lower() or 'unit' in col.lower():
                    price_col = col
            
            if not product_col:
                return "Colonne produit non trouvée"
            
            if not price_col:
                price_col = 'Unit Price' if 'Unit Price' in self.df.columns else 'Total'
            
            # Analyse des top produits par prix moyen
            top_products = self.df.groupby(product_col)[price_col].mean().sort_values(ascending=False).head(n)
            
            # Formatage du résultat
            result = f"\n🏆 TOP {n} PRODUITS PAR PRIX MOYEN\n"
            result += "="*40 + "\n"
            
            for i, (product, price) in enumerate(top_products.items(), 1):
                result += f"{i}. {product:<25} {price:>10,.2f} FCFA\n"
            
            # Ajouter les stats de volume
            result += "\n📊 DÉTAIL DES VENTES\n"
            result += "="*40 + "\n"
            
            for product in top_products.index:
                product_data = self.df[self.df[product_col] == product]
                total_rev = product_data['Total'].sum() if 'Total' in product_data.columns else 0
                quantity = product_data['Quantity'].sum() if 'Quantity' in product_data.columns else len(product_data)
                
                result += f"\n📦 {product}:\n"
                result += f"   💰 CA Total: {total_rev:,.0f} FCFA\n"
                result += f"   📦 Quantité: {quantity:,.0f}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur dans _analyze_top_products: {e}")
            return None

    def run(self, user_message):
        """Point d'entrée principal avec routage intelligent"""

        if self.df is None:
            return "Erreur: Dataset 'sales' not found."

        # Vérifier si la question concerne les top produits
        msg_lower = user_message.lower()
        
        # Détection des questions sur les top produits
        if any(word in msg_lower for word in ['top', 'meilleur', 'produit', 'product', 'prix', 'price']):
            
            # Extraire le nombre demandé (4 par défaut)
            n = 4
            words = msg_lower.split()
            for i, word in enumerate(words):
                if word.isdigit() and i > 0:
                    n = int(word)
                    break
            
            result = self._analyze_top_products(n)
            if result:
                return result

        # Si ce n'est pas une question top produits, utiliser Bedrock
        prompt = f"""
You are a professional Python data analyst.

You have ONE pandas dataframe called df with these columns:
{self.df.columns.tolist()}

First 5 rows of data:
{self.df.head().to_string()}

User question: {user_message}

RULES:
- Use pandas only
- The dataframe name is df
- Save final output in a variable called result
- Return only raw Python code
"""

        code = ask_bedrock(prompt)
        logger.debug(f"Code généré: {code}")

        try:
            local_vars = {"df": self.df, "pd": pd}
            exec(code, {"__builtins__": __builtins__}, local_vars)

            if "result" in local_vars:
                result = local_vars["result"]
                
                # Formatage intelligent du résultat
                if isinstance(result, pd.DataFrame):
                    if len(result) > 20:
                        return str(result.head(20)) + f"\n... et {len(result)-20} lignes supplémentaires"
                    else:
                        return str(result)
                else:
                    return str(result)
            else:
                return "No result generated."

        except Exception as e:
            logger.error(f"Erreur d'exécution: {e}")
            return f"Erreur during execution: {e}"