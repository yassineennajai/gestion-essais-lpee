import uuid           # Pour générer des noms de fichiers uniques pour les charts
import os             # Pour manipuler les fichiers et chemins
import pandas as pd   # Pour la manipulation et l'analyse des données
import json           # Pour convertir DataFrame en JSON
import numpy as np    # Pour les calculs numériques
import matplotlib     # Librairie pour tracer des graphiques
matplotlib.use("Agg") # Backend pour générer des images sans affichage graphique
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from config import CHART_DIR, CSV_PATH, PALETTE  # Paramètres de config (dossier charts, CSV, couleurs)

# ── Fonction pour charger le dataset ────────────────────────────────
def _load_df(path: str) -> pd.DataFrame:
    """
    Charge le CSV en DataFrame et normalise les noms de colonnes.
    """
    if not os.path.exists(path):  # Vérifie si le fichier existe
        raise FileNotFoundError(
            f"❌ Sales_Data.csv not found at: {path}\n"
            "   Place it inside the KnowledgeBase/ folder."
        )
    frame = pd.read_csv(path)  # Lit le CSV
    # Normalise les noms de colonnes : minuscules, underscores à la place des espaces
    frame.columns = (frame.columns
                     .str.strip()
                     .str.lower()
                     .str.replace(" ", "_"))
    return frame

df = _load_df(CSV_PATH)  # Charge le dataset

# ── Gestion des colonnes de dates ────────────────────────────────
date_col = next((c for c in df.columns if "date" in c), None)  # Cherche la colonne contenant "date"
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")  # Convertit en datetime
    # Crée des colonnes utiles pour l'analyse temporelle
    df["order_year"]       = df[date_col].dt.year
    df["order_month"]      = df[date_col].dt.month
    df["order_month_name"] = df[date_col].dt.strftime("%b")  # Nom du mois (Jan, Feb...)

# ── Regroupement des colonnes par type ───────────────────────────────
NUMERIC_COLS     = df.select_dtypes(include="number").columns.tolist()   # Colonnes numériques
CATEGORICAL_COLS = df.select_dtypes(include="object").columns.tolist()   # Colonnes catégorielles
DATE_COLS        = [c for c in df.columns if "date" in c]                # Colonnes date
ALL_COLS         = list(df.columns)                                      # Toutes les colonnes

SAMPLE_ROWS = json.loads(df.head(3).to_json(orient="records", date_format="iso"))
# On stocke les 3 premières lignes en JSON pour tests ou affichage rapide

print(f"✅ Dataset: {len(df)} rows | columns: {ALL_COLS}")

# ── Fonctions utilitaires pour choisir les meilleures colonnes ───────────────
def best_cat_col() -> str:
    """Retourne la colonne catégorielle la plus pertinente (2–50 valeurs uniques)."""
    for c in CATEGORICAL_COLS:
        if 2 <= df[c].nunique() <= 50:
            return c
    return CATEGORICAL_COLS[0] if CATEGORICAL_COLS else ALL_COLS[0]

def best_num_col() -> str | None:
    """Retourne la colonne numérique la plus probable pour 'sales' ou 'revenue'."""
    preferred = ["sales", "revenue", "profit", "quantity", "amount", "total", "price"]
    for p in preferred:
        for c in NUMERIC_COLS:
            if p in c:
                return c
    return NUMERIC_COLS[0] if NUMERIC_COLS else None

# ── Fonction pour sauvegarder un graphique matplotlib ───────────────
def _save_fig() -> str:
    """
    Sauvegarde la figure matplotlib courante dans CHART_DIR et retourne son chemin relatif.
    """
    fname = f"{uuid.uuid4().hex}.png"  # Nom unique
    fpath = os.path.join(CHART_DIR, fname)
    plt.savefig(fpath, dpi=130, bbox_inches="tight", facecolor="#0f1117")  # Sauvegarde image
    plt.close("all")  # Ferme la figure pour libérer la mémoire
    return f"/static/charts/{fname}"

# ── Fonction pour appliquer un style sombre à un graphique ─────────────
def _style(ax, title: str, xlabel: str = "", ylabel: str = ""):
    """
    Applique un thème sombre et formate axes, titres et ticks.
    """
    ax.figure.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#1a1d27")
    ax.set_title(title, color="#e8eaf0", fontsize=13, pad=12, fontweight="bold")
    ax.set_xlabel(xlabel, color="#9ca3af", fontsize=10)
    ax.set_ylabel(ylabel, color="#9ca3af", fontsize=10)
    ax.tick_params(colors="#9ca3af", labelsize=9)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3047")
    # Formattage y-axis : nombres avec virgules ou 2 décimales si <1
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda x, _: f"{x:,.0f}" if abs(x) >= 1 else f"{x:.2f}"
        )
    )
    ax.grid(axis="y", color="#2d3047", linewidth=0.6, linestyle="--", alpha=0.7)

# ── Fonction de traduction simple ─────────────
def _t(lang: str, en: str, fr: str) -> str:
    """Retourne la version française si lang='fr', sinon anglais."""
    return fr if lang == "fr" else en

# ── Fonction principale pour gérer l'analyse ───────────────────────
def handle_analytics(parsed: dict, lang: str = "en") -> dict:
    """
    Exécute l'analyse demandée et retourne le texte descriptif et le chemin du graphique.
    parsed: {
        metric: str,          # 'sum', 'average', 'distribution', 'trend', 'top_n', ...
        columns: [str],       # Colonnes à analyser
        filters: dict,        # Filtres à appliquer
        group_by: [str],      # Colonnes pour group_by
        top_n: int,           # Nombre de top éléments
        chart_type: str,      # 'hist', 'line', 'pie'
        time_period: str      # 'daily', 'monthly', 'yearly'
    }
    """
    # ── Préparation des paramètres ─────────────────────────────
    metric      = parsed.get("metric") or "sum"
    columns     = parsed.get("columns") or []
    filters     = parsed.get("filters") or {}
    group_by    = parsed.get("group_by") or []
    top_n       = int(parsed.get("top_n") or 5)
    chart_type  = parsed.get("chart_type")
    time_period = parsed.get("time_period")

    data = df.copy()  # Copie du dataset pour ne pas le modifier

    # ── Choisir la colonne numérique à analyser ─────────────
    col = next(
        (c for c in columns if c in data.columns and c in NUMERIC_COLS),
        best_num_col()
    )
    if col is None:
        return {"text": _t(lang,
            "❌ No numeric column found in the dataset.",
            "❌ Aucune colonne numérique trouvée dans le dataset."), "chart": None}

    # ── Vérifie que les colonnes group_by existent ─────────────
    group_by = [g for g in group_by if g in data.columns]

    # ── Application des filtres ─────────────
    for fc, fv in filters.items():
        if fc in data.columns:
            try:
                # Comparaison insensible à la casse
                data = data[data[fc].astype(str).str.lower() == str(fv).lower()]
            except Exception as fe:
                print(f"[filter error] {fe}")

    if data.empty:  # Si pas de données après filtrage
        return {"text": _t(lang,
            f"⚠️ No data after applying filters: {filters}",
            f"⚠️ Aucune donnée après filtrage : {filters}"), "chart": None}

    # ── Différentes métriques possibles ─────────────
    # Distribution (histogramme)
    if metric == "distribution" or chart_type == "hist":
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.hist(data[col].dropna(), bins=25, color=PALETTE[0],
                edgecolor="#0f1117", alpha=0.9)
        _style(ax, f"Distribution of {col}", col, "Frequency")
        fig.tight_layout()
        text = _t(lang,
            (f"Distribution of {col}:\n"
             f"  Mean   = {data[col].mean():,.2f}\n"
             f"  Median = {data[col].median():,.2f}\n"
             f"  Std    = {data[col].std():,.2f}\n"
             f"  Min    = {data[col].min():,.2f} | Max = {data[col].max():,.2f}"),
            (f"Distribution de {col} :\n"
             f"  Moyenne  = {data[col].mean():,.2f}\n"
             f"  Médiane  = {data[col].median():,.2f}\n"
             f"  Écart-type = {data[col].std():,.2f}\n"
             f"  Min = {data[col].min():,.2f} | Max = {data[col].max():,.2f}")
        )
        return {"text": text, "chart": _save_fig()}

    # D’autres métriques comme correlation, trend, top_n, pie, sum/average/max/min
    # suivent le même principe : préparer les données, créer un graphique si nécessaire
    # et retourner un dictionnaire {"text": ..., "chart": ...}
