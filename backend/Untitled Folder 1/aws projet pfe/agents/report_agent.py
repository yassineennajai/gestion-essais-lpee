import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class ReportType(Enum):
    """Types de rapports supportés"""
    GLOBAL = "global"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    PRODUCT = "product"
    CATEGORY = "category"
    CUSTOM = "custom"

@dataclass
class ReportConfig:
    """Configuration pour la génération de rapports"""
    show_trends: bool = True
    show_comparisons: bool = True
    decimals: int = 2
    currency: str = "XOF"
    locale: str = "fr_FR"

class ReportAgent:
    """
    Agent spécialisé dans la génération de rapports d'analyse commerciale.
    Version premium avec analyses approfondies et visualisations textuelles.
    """
    
    # Configuration des colonnes numériques
    NUMERIC_COLUMNS = {
        "Total": "Chiffre d'affaires",
        "Quantity": "Quantité",
        "Gross Income": "Revenu brut",
        "Cost of Goods Sold": "Coût des marchandises",
        "Rating": "Note",
        "Unit Price": "Prix unitaire",
        "Tax": "Taxe"
    }
    
    # Colonnes de date
    DATE_COLUMNS = ["Date", "Invoice Date", "Transaction Date"]
    
    # Colonnes catégorielles importantes
    CATEGORICAL_COLUMNS = [
        "Product line", "Category", "City", "Branch", 
        "Customer Type", "Gender", "Payment Method"
    ]

    def __init__(self, data: Dict[str, pd.DataFrame], config: Optional[ReportConfig] = None):
        """
        Initialise le ReportAgent avec les données et la configuration.
        
        Args:
            data: Dictionnaire contenant les DataFrames (doit contenir 'sales')
            config: Configuration optionnelle du rapport
        """
        logger.info("🚀 Initialisation du ReportAgent version premium...")
        
        self.config = config or ReportConfig()
        self.df = data.get("sales", pd.DataFrame()).copy()  # Copie pour éviter les modifications
        
        if self.df.empty:
            logger.warning("⚠️ Dataset sales vide")
        else:
            logger.info(f"📊 Dataset chargé: {len(self.df)} lignes, {len(self.df.columns)} colonnes")
            self._prepare_data()
            self._enrich_data()
            self._validate_data_quality()

    def _prepare_data(self) -> None:
        """Prépare et nettoie les données avec validation avancée."""
        try:
            if self.df.empty:
                return

            # 1️⃣ Gestion des dates
            for date_col in self.DATE_COLUMNS:
                if date_col in self.df.columns:
                    self.df[date_col] = pd.to_datetime(self.df[date_col], errors="coerce")
                    # Extraction des composantes de date
                    self.df[f"{date_col}_Year"] = self.df[date_col].dt.year
                    self.df[f"{date_col}_Month"] = self.df[date_col].dt.month
                    self.df[f"{date_col}_MonthName"] = self.df[date_col].dt.month_name()
                    self.df[f"{date_col}_Week"] = self.df[date_col].dt.isocalendar().week
                    self.df[f"{date_col}_DayOfWeek"] = self.df[date_col].dt.day_name()
                    logger.info(f"✅ Colonnes de date créées à partir de: {date_col}")
                    break  # On prend la première colonne date trouvée

            # 2️⃣ Conversion numérique robuste
            for col, label in self.NUMERIC_COLUMNS.items():
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                    
                    # Statistiques de qualité
                    null_pct = self.df[col].isnull().mean() * 100
                    if null_pct > 5:
                        logger.warning(f"⚠️ {col}: {null_pct:.1f}% valeurs manquantes")
                    
                    # Remplissage des NaN avec la médiane
                    self.df[col].fillna(self.df[col].median(), inplace=True)

            # 3️⃣ Détection automatique des colonnes catégorielles
            for col in self.CATEGORICAL_COLUMNS:
                if col in self.df.columns:
                    self.df[col] = self.df[col].astype('category')

            logger.info("✅ Données préparées avec succès")

        except Exception as e:
            logger.error(f"❌ Erreur préparation données: {e}")
            raise

    def _enrich_data(self) -> None:
        """Enrichit les données avec des métriques calculées."""
        try:
            if self.df.empty:
                return

            # Calcul des métriques dérivées
            if all(col in self.df.columns for col in ["Total", "Quantity"]):
                self.df["Unit_Price_Avg"] = self.df["Total"] / self.df["Quantity"].clip(lower=1)
            
            if all(col in self.df.columns for col in ["Gross Income", "Total"]):
                self.df["Margin_Rate"] = (self.df["Gross Income"] / self.df["Total"] * 100).round(2)
            
            # Segmentation des ventes
            if "Total" in self.df.columns:
                quantiles = self.df["Total"].quantile([0.33, 0.67])
                self.df["Ticket_Size"] = pd.cut(
                    self.df["Total"],
                    bins=[-np.inf, quantiles.iloc[0], quantiles.iloc[1], np.inf],
                    labels=["Petit", "Moyen", "Grand"]
                )

            logger.debug("✅ Données enrichies avec métriques calculées")

        except Exception as e:
            logger.error(f"❌ Erreur enrichissement données: {e}")

    def _validate_data_quality(self) -> Dict[str, Any]:
        """Valide la qualité des données et retourne un rapport."""
        quality_report = {
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "missing_values": self.df.isnull().sum().to_dict(),
            "data_types": self.df.dtypes.astype(str).to_dict(),
            "duplicates": self.df.duplicated().sum()
        }
        
        logger.info(f"📈 Qualité données: {quality_report['total_rows']} lignes, {quality_report['duplicates']} doublons")
        return quality_report

    def _format_number(self, value: float, is_currency: bool = True) -> str:
        """Formate les nombres avec séparateurs et devise."""
        if pd.isna(value) or value is None:
            return "N/A"
        
        try:
            if is_currency:
                if self.config.currency == "XOF":
                    return f"{value:,.0f} FCFA".replace(",", " ")
                else:
                    return f"{value:,.{self.config.decimals}f} {self.config.currency}"
            else:
                return f"{value:,.{self.config.decimals}f}".replace(",", " ")
        except:
            return str(value)

    def _generate_trend_analysis(self, df_grouped: pd.Series, period: str) -> str:
        """Génère une analyse de tendance."""
        if len(df_grouped) < 2:
            return ""
        
        try:
            first_value = df_grouped.iloc[0]
            last_value = df_grouped.iloc[-1]
            
            if first_value > 0:
                evolution = ((last_value - first_value) / first_value) * 100
                trend_icon = "📈" if evolution > 0 else "📉" if evolution < 0 else "➡️"
                
                return f"\n{trend_icon} Évolution sur la période: {evolution:+.1f}%"
        except:
            pass
        
        return ""

    def _generate_comparisons(self, df_grouped: pd.Series, period: str) -> str:
        """Génère des comparaisons utiles."""
        comparisons = []
        
        try:
            # Meilleure période
            best_period = df_grouped.idxmax()
            best_value = df_grouped.max()
            comparisons.append(f"🏆 Meilleur {period}: {best_period} ({self._format_number(best_value)})")
            
            # Pire période
            worst_period = df_grouped.idxmin()
            worst_value = df_grouped.min()
            comparisons.append(f"📉 Pire {period}: {worst_period} ({self._format_number(worst_value)})")
            
            # Moyenne
            avg_value = df_grouped.mean()
            comparisons.append(f"📊 Moyenne: {self._format_number(avg_value)}")
            
        except Exception as e:
            logger.error(f"Erreur comparaisons: {e}")
        
        return "\n".join(comparisons)

    def generate_global_report(self) -> str:
        """Génère un rapport global ultra-détaillé."""
        
        # Métriques principales
        total_revenue = self.df["Total"].sum()
        total_sales = self.df["Invoice ID"].nunique() if "Invoice ID" in self.df.columns else len(self.df)
        avg_basket = total_revenue / total_sales if total_sales > 0 else 0
        
        # Métriques avancées
        total_quantity = self.df["Quantity"].sum() if "Quantity" in self.df.columns else 0
        avg_rating = self.df["Rating"].mean() if "Rating" in self.df.columns else 0
        
        # Métriques de rentabilité
        gross_income = self.df["Gross Income"].sum() if "Gross Income" in self.df.columns else 0
        margin_rate = (gross_income / total_revenue * 100) if total_revenue > 0 else 0
        
        # Top produits/catégories
        top_products = ""
        if "Product line" in self.df.columns:
            top_products = self.df.groupby("Product line")["Total"].sum().nlargest(3)
            top_products_str = ", ".join([f"{p} ({self._format_number(v)})" for p, v in top_products.items()])
        
        # Période
        date_start = "N/A"
        date_end = "N/A"
        days_diff = 0
        
        if "Date" in self.df.columns:
            date_start = self.df['Date'].min().strftime('%d/%m/%Y')
            date_end = self.df['Date'].max().strftime('%d/%m/%Y')
            days_diff = (self.df['Date'].max() - self.df['Date'].min()).days
        
        # Construction du rapport
        report = f"""
{'='*60}
🏢 RAPPORT GLOBAL SUPERMARKET - VISION 360°
{'='*60}

📊 INDICATEURS CLÉS DE PERFORMANCE (KPI)
{'-'*40}
💰 Chiffre d'affaires total:      {self._format_number(total_revenue)}
🧾 Nombre de transactions:         {total_sales:,}
🛒 Panier moyen:                   {self._format_number(avg_basket)}
📦 Quantité totale vendue:         {total_quantity:,.0f}
⭐ Note moyenne clients:            {avg_rating:.2f}/10

💹 ANALYSE DE RENTABILITÉ
{'-'*40}
💵 Revenu brut:                    {self._format_number(gross_income)}
📈 Marge brute moyenne:             {margin_rate:.1f}%

🏆 TOP PERFORMANCES
{'-'*40}
{top_products_str if 'top_products_str' in locals() else "Données produits non disponibles"}

📅 INFORMATIONS GÉNÉRALES
{'-'*40}
📆 Période analysée:                {date_start} au {date_end}
⏱️  Durée:                           {days_diff} jours
🕒 Généré le:                        {datetime.now().strftime('%d/%m/%Y à %H:%M')}

{'='*60}
"""
        return report

    def generate_monthly_report(self) -> str:
        """Génère un rapport mensuel détaillé avec analyses."""
        
        # Déterminer la colonne de mois
        month_col = None
        for col in self.df.columns:
            if 'Month' in col or 'month' in col:
                month_col = col
                break
        
        if month_col is None:
            # Chercher une colonne de date pour extraire le mois
            for date_col in self.DATE_COLUMNS:
                if date_col in self.df.columns:
                    month_col = f"{date_col}_Month"
                    if month_col in self.df.columns:
                        break
            
            if month_col is None or month_col not in self.df.columns:
                return "❌ Impossible de générer le rapport mensuel: données de mois non trouvées"
        
        # Agrégation mensuelle
        monthly_data = self.df.groupby(month_col).agg({
            'Total': ['sum', 'mean', 'count'],
            'Rating': 'mean' if 'Rating' in self.df.columns else lambda x: 0
        }).round(2)
        
        monthly_data.columns = ['CA_Total', 'CA_Moyen', 'Nb_Transactions', 'Note_Moyenne']
        
        # Construction du rapport
        report = f"""
{'='*60}
📅 RAPPORT MENSUEL DÉTAILLÉ
{'='*60}

{'MOIS':<15} {'CA TOTAL':>15} {'PANIER':>12} {'TRANSACTIONS':>15} {'NOTE':>10}
{'-'*67}
"""
        
        for month, row in monthly_data.iterrows():
            report += f"{month:<15} {self._format_number(row['CA_Total']):>15} {self._format_number(row['CA_Moyen']):>12} {row['Nb_Transactions']:>15,.0f} {row['Note_Moyenne']:>10.1f}\n"
        
        # Ajouter les analyses
        if self.config.show_trends:
            trend = self._generate_trend_analysis(monthly_data['CA_Total'], "mois")
            report += f"\n{trend}"
        
        if self.config.show_comparisons:
            comparisons = self._generate_comparisons(monthly_data['CA_Total'], "mois")
            report += f"\n\n{comparisons}"
        
        report += f"\n{'='*60}"
        
        return report

    def generate_yearly_report(self) -> str:
        """Génère un rapport annuel complet."""
        
        # Déterminer la colonne d'année
        year_col = None
        for col in self.df.columns:
            if 'Year' in col or 'year' in col:
                year_col = col
                break
        
        if year_col is None:
            # Chercher une colonne de date pour extraire l'année
            for date_col in self.DATE_COLUMNS:
                if date_col in self.df.columns:
                    year_col = f"{date_col}_Year"
                    if year_col in self.df.columns:
                        break
            
            if year_col is None or year_col not in self.df.columns:
                return "❌ Impossible de générer le rapport annuel: données d'année non trouvées"
        
        # Agrégation annuelle
        yearly_data = self.df.groupby(year_col).agg({
            'Total': ['sum', 'mean', 'count', 'std'],
            'Rating': 'mean' if 'Rating' in self.df.columns else lambda x: 0
        }).round(2)
        
        # Construction du rapport
        report = f"""
{'='*60}
📊 RAPPORT ANNUEL - ANALYSE COMPLÈTE
{'='*60}

{'ANNÉE':<15} {'CA TOTAL':>15} {'MOYENNE':>12} {'VOLUME':>10} {'ÉCART-TYPE':>12} {'NOTE':>8}
{'-'*72}
"""
        
        for year, row in yearly_data.iterrows():
            ca_total = row['Total']['sum'] if isinstance(row['Total'], dict) else row['Total']
            ca_mean = row['Total']['mean'] if isinstance(row['Total'], dict) else 0
            count = row['Total']['count'] if isinstance(row['Total'], dict) else 0
            std = row['Total']['std'] if isinstance(row['Total'], dict) else 0
            rating = row['Rating'] if isinstance(row, pd.Series) and 'Rating' in row else 0
            
            report += f"{year:<15} {self._format_number(ca_total):>15} {self._format_number(ca_mean):>12} {count:>10,.0f} {self._format_number(std, False):>12} {rating:>8.1f}\n"
        
        # Métriques additionnelles
        if len(yearly_data) > 0:
            best_year = yearly_data['Total']['sum'].idxmax() if isinstance(yearly_data['Total'], pd.DataFrame) else yearly_data.index[0]
            best_value = yearly_data['Total']['sum'].max() if isinstance(yearly_data['Total'], pd.DataFrame) else yearly_data['Total'].iloc[0]
            
            if len(yearly_data) > 1:
                first_value = yearly_data['Total']['sum'].iloc[0] if isinstance(yearly_data['Total'], pd.DataFrame) else yearly_data['Total'].iloc[0]
                last_value = yearly_data['Total']['sum'].iloc[-1] if isinstance(yearly_data['Total'], pd.DataFrame) else yearly_data['Total'].iloc[-1]
                growth_rate = ((last_value / first_value) - 1) * 100 if first_value > 0 else 0
            else:
                growth_rate = 0
            
            total_period = yearly_data['Total']['sum'].sum() if isinstance(yearly_data['Total'], pd.DataFrame) else yearly_data['Total'].sum()
            
            report += f"""
{'-'*40}
🏆 Meilleure année: {best_year} ({self._format_number(best_value)})
📈 Taux de croissance: {growth_rate:+.1f}%
📊 Total sur la période: {self._format_number(total_period)}
{'='*60}
"""
        
        return report

    def generate_product_report(self, product_name: Optional[str] = None) -> str:
        """Génère un rapport par produit ou catégorie."""
        
        product_col = "Product line" if "Product line" in self.df.columns else None
        if product_col is None:
            for col in self.df.columns:
                if "product" in col.lower() or "category" in col.lower():
                    product_col = col
                    break
        
        if product_col is None:
            return "❌ Données produits non disponibles"
        
        if product_name:
            # Rapport pour un produit spécifique
            product_data = self.df[self.df[product_col].str.contains(product_name, case=False, na=False)]
            if product_data.empty:
                return f"❌ Produit '{product_name}' non trouvé"
        else:
            # Rapport pour tous les produits
            product_data = self.df
        
        # Agrégation par produit
        agg_dict = {
            'Total': ['sum', 'mean', 'count'],
        }
        
        if 'Quantity' in product_data.columns:
            agg_dict['Quantity'] = 'sum'
        if 'Rating' in product_data.columns:
            agg_dict['Rating'] = 'mean'
            
        product_stats = product_data.groupby(product_col).agg(agg_dict).round(2)
        
        # Construction du rapport
        report = f"""
{'='*60}
📦 RAPPORT PRODUITS - PERFORMANCE COMMERCIALE
{'='*60}

{'PRODUIT':<25} {'CA TOTAL':>15} {'VENTES':>10} {'QTÉ':>8} {'NOTE':>8}
{'-'*66}
"""
        
        for product, row in product_stats.iterrows():
            ca_total = row['Total']['sum'] if isinstance(row['Total'], dict) else row['Total']
            ventes = row['Total']['count'] if isinstance(row['Total'], dict) else 1
            quantite = row['Quantity'] if 'Quantity' in row and not pd.isna(row['Quantity']) else 0
            note = row['Rating'] if 'Rating' in row and not pd.isna(row['Rating']) else 0
            
            report += f"{product[:25]:<25} {self._format_number(ca_total):>15} {ventes:>10,.0f} {quantite:>8,.0f} {note:>8.1f}\n"
        
        # Produit phare
        if len(product_stats) > 0:
            if isinstance(product_stats['Total'], pd.DataFrame):
                top_product = product_stats['Total']['sum'].idxmax()
                top_value = product_stats['Total']['sum'].max()
            else:
                top_product = product_stats.index[0]
                top_value = product_stats['Total'].iloc[0]
            
            total_revenue = self.df['Total'].sum()
            contribution = (top_value / total_revenue * 100) if total_revenue > 0 else 0
            
            report += f"""
{'-'*40}
🏆 Produit phare: {top_product} ({self._format_number(top_value)})
📊 Contribution au CA total: {contribution:.1f}%
{'='*60}
"""
        
        return report

    def run(self, message: str) -> str:
        """
        Point d'entrée principal - route la demande vers le rapport approprié.
        
        Args:
            message: Requête utilisateur
            
        Returns:
            Rapport formaté
        """
        logger.info(f"📝 Traitement de la demande: {message[:100]}...")
        
        if self.df.empty:
            return "❌ Aucune donnée disponible pour générer un rapport."
        
        msg = message.lower()
        
        # Détection intelligente du type de rapport
        if any(word in msg for word in ["produit", "product", "article", "catégorie", "category"]):
            # Extraction du nom de produit si spécifié
            words = msg.split()
            for i, word in enumerate(words):
                if word in ["produit", "product", "article"] and i + 1 < len(words):
                    return self.generate_product_report(words[i + 1])
            return self.generate_product_report()
        
        elif any(word in msg for word in ["mois", "month", "mensuel", "février", "janvier", "mars"]):
            return self.generate_monthly_report()
        
        elif any(word in msg for word in ["année", "year", "annuel", "2023", "2024"]):
            return self.generate_yearly_report()
        
        elif any(word in msg for word in ["global", "général", "general", "complet", "total"]):
            return self.generate_global_report()
        
        else:
            # Par défaut, rapport global avec suggestion
            return self.generate_global_report() + "\n\n💡 Pour plus de détails, précisez: 'mensuel', 'annuel', ou 'produit [nom]'"

    def export_to_dict(self) -> Dict[str, Any]:
        """Exporte les métriques clés sous forme de dictionnaire."""
        result = {
            "total_revenue": float(self.df["Total"].sum()),
            "total_transactions": int(len(self.df)),
            "average_basket": float(self.df["Total"].mean()),
            "average_rating": float(self.df["Rating"].mean()) if "Rating" in self.df.columns else 0,
        }
        
        if "Date" in self.df.columns:
            result["date_range"] = {
                "start": self.df["Date"].min().isoformat() if not pd.isna(self.df["Date"].min()) else None,
                "end": self.df["Date"].max().isoformat() if not pd.isna(self.df["Date"].max()) else None
            }
        
        if "Product line" in self.df.columns:
            result["top_products"] = self.df.groupby("Product line")["Total"].sum().nlargest(3).to_dict()
        
        return result