"""
╔══════════════════════════════════════════════════════════════════╗
║         Bilansia — Portail Audit Financier                       ║
║         Expert Forensic Accounting | FinTech Dashboard           ║
╚══════════════════════════════════════════════════════════════════╝
Dépendances : pip install streamlit pandas plotly numpy scipy google-generativeai fpdf
Lancement   : streamlit run scanner_gestion.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats
import math
from datetime import datetime
import io
import json
import base64
import os
import re
import csv

# ── Google Gemini (optionnel — requis pour l'import PDF) ──────────
try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

# Clé API Gemini
_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if _GEMINI_AVAILABLE and _GEMINI_API_KEY:
    genai.configure(api_key=_GEMINI_API_KEY)

# ── FPDF (requis pour l'export PDF) ──────────
try:
    from fpdf import FPDF
    _FPDF_AVAILABLE = True
except ImportError:
    _FPDF_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────
#  CONFIG GLOBALE & CSS
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bilansia — Audit Forensic",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# INITIALISATION DU COFFRE-FORT MÉMOIRE
if "data_store" not in st.session_state:
    st.session_state.data_store = {}
if "file_signatures" not in st.session_state:
    st.session_state.file_signatures = {}
if "file_names_store" not in st.session_state:
    st.session_state.file_names_store = {}

CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');

  :root {
    --night:    #0F172A;
    --deep:     #1E293B;
    --panel:    #1A2744;
    --border:   #2D3F5E;
    --steel:    #94A3B8;
    --muted:    #64748B;
    --emerald: #10B981;
    --amber:    #F59E0B;
    --rose:     #F43F5E;
    --sky:      #38BDF8;
    --white:    #F1F5F9;
    --font-display: 'Syne', sans-serif;
    --font-body: 'Inter', sans-serif;
    --font-mono: 'DM Mono', monospace;
  }

  html, body, [class*="css"] { background-color: var(--night) !important; color: var(--white) !important; font-family: var(--font-body) !important; }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--night); }
  ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

  .secure-banner { background: linear-gradient(90deg, #0d2137 0%, #0f2d4a 50%, #0d2137 100%); border: 1px solid #1d4ed8; border-radius: 6px; padding: 8px 18px; font-family: var(--font-mono); font-size: 12px; color: #93c5fd; display: flex; align-items: center; gap: 10px; letter-spacing: 0.04em; margin-bottom: 6px; }
  .secure-banner .dot { width:7px; height:7px; border-radius:50%; background:#10B981; animation: blink 2s infinite; }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

  .page-title { font-family: var(--font-display); font-size: 2.4rem; font-weight: 800; letter-spacing: -0.03em; color: var(--white); line-height: 1.1; }
  .page-subtitle { font-family: var(--font-mono); font-size: 11px; color: var(--muted); letter-spacing: 0.12em; text-transform: uppercase; margin-top: 4px; }

  .kpi-card { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 18px 18px; position: relative; overflow: hidden; }
  .kpi-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, var(--emerald), var(--sky)); }
  .kpi-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
  .kpi-value { font-family: var(--font-display); font-size: 1.8rem; font-weight: 700; color: var(--white); }
  .kpi-delta { font-size: 12px; margin-top: 4px; }
  .delta-up   { color: var(--emerald); }
  .delta-down { color: var(--rose); }

  .section-header { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: var(--white); letter-spacing: -0.01em; padding-bottom: 10px; border-bottom: 1px solid var(--border); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }

  .alert-card { border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; display: flex; align-items: flex-start; gap: 16px; border-left: 4px solid; }
  .alert-critical { background: rgba(244,63,94,.08); border-color: var(--rose); }
  .alert-warning  { background: rgba(245,158,11,.08); border-color: var(--amber); }
  .alert-info     { background: rgba(56,189,248,.08); border-color: var(--sky); }
  .alert-ok       { background: rgba(16,185,129,.08); border-color: var(--emerald); }
  .alert-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }
  .alert-title { font-family: var(--font-display); font-size: 14px; font-weight: 700; color: var(--white); margin-bottom: 6px;}
  .alert-body  { font-size: 13px; color: var(--steel); line-height: 1.6; }
  .alert-badge { display: inline-block; font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; padding: 2px 7px; border-radius: 3px; margin-top: 8px; }
  .badge-critical { background: rgba(244,63,94,.2); color: var(--rose); }
  .badge-warning  { background: rgba(245,158,11,.2); color: var(--amber); }
  .badge-info     { background: rgba(56,189,248,.2); color: var(--sky); }

  /* ── ONGLET CHAT ── */
  .chat-container { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 0; overflow: hidden; }
  .chat-header { background: linear-gradient(90deg, #0f2d4a, #0d2137); padding: 14px 18px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--border); }
  .chat-title { font-family: var(--font-display); font-size: 14px; font-weight: 700; color: var(--white); }
  .chat-body  { padding: 16px 18px; max-height: 480px; overflow-y: auto; display: flex; flex-direction: column; }
  .msg-user, .msg-ai { margin-bottom: 16px; max-width: 85%; display: flex; flex-direction: column; }
  .msg-user { align-self: flex-end; align-items: flex-end; }
  .msg-ai { align-self: flex-start; align-items: flex-start; }
  .msg-bubble { padding: 11px 15px; border-radius: 12px; font-size: 13px; line-height: 1.6; display: inline-block; text-align: left; }
  .msg-user .msg-bubble { background: #1d4ed8; color: #e0f2fe; border-bottom-right-radius: 3px; }
  .msg-ai .msg-bubble { background: #1A2744; border: 1px solid var(--border); color: var(--steel); border-bottom-left-radius: 3px; }
  .msg-meta { font-family: var(--font-mono); font-size: 10px; color: var(--muted); margin-top: 4px; padding: 0 4px; }

  /* Utilitaires Streamlit */
  .empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; text-align: center; gap: 16px; }
  .stTextInput > div > div { background: var(--deep) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; color: var(--white) !important; }
  .stButton > button { background: linear-gradient(135deg, #1d4ed8, #0f172a) !important; color: white !important; border: 1px solid #2563eb !important; border-radius: 8px !important; font-family: var(--font-display) !important; font-weight: 600 !important; letter-spacing: 0.02em !important; transition: all 0.2s; font-size: 12px !important; }
  .stButton > button:hover { background: linear-gradient(135deg, #2563eb, #1e293b) !important; }
  .stFileUploader > div { background: var(--panel) !important; border: 1px dashed var(--border) !important; border-radius: 12px !important; }
  .stSelectbox > div { background: var(--deep) !important; }
  div[data-testid="metric-container"] { background: var(--panel) !important; border: 1px solid var(--border) !important; border-radius: 12px !important; padding: 14px !important; }
  .stTabs [data-baseweb="tab-list"] { background: var(--deep) !important; border-radius: 10px !important; padding: 4px !important; }
  .stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--muted) !important; border-radius: 7px !important; }
  .stTabs [aria-selected="true"] { background: var(--panel) !important; color: var(--white) !important; }
  .stSidebar { background: var(--deep) !important; border-right: 1px solid var(--border) !important; }
  .stExpander { background: var(--panel) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; }
  .stDataFrame { background: var(--panel) !important; }
  [data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 10px !important; overflow: hidden !important; }
  .upload-hint { font-family: var(--font-mono); font-size: 11px; color: var(--muted); text-align: center; margin-top: 6px; }
</style>
"""

# ─────────────────────────────────────────────────────────────────
#  UTILITAIRES DE FORMATAGE
# ─────────────────────────────────────────────────────────────────
def fmt_eur(value: float, short: bool = False) -> str:
    try: value = float(value)
    except (TypeError, ValueError): return "— €"
    if short and abs(value) >= 10_000:
        return f"{value / 1_000:,.0f} K€".replace(",", "\u202f")
    return f"{value:,.0f} €".replace(",", "\u202f")

def empty_cr() -> pd.DataFrame:
    months = pd.date_range(datetime.now().strftime("%Y-01-01"), periods=12, freq="MS")
    return pd.DataFrame({"Mois": months, "CA": [0.0]*12, "Achats": [0.0]*12, "Charges_Ext": [0.0]*12, "Salaires": [0.0]*12, "Amortissements": [0.0]*12, "EBIT": [0.0]*12, "Interets": [0.0]*12, "Resultat_Net": [0.0]*12, "BFR": [0.0]*12})

def empty_bilan() -> pd.DataFrame:
    return pd.DataFrame({"Poste": pd.Series([], dtype=str), "Montant": pd.Series([], dtype=float), "Variation_N1": pd.Series([], dtype=float)})

def empty_fec() -> pd.DataFrame:
    return pd.DataFrame({"Date": pd.Series([], dtype="datetime64[ns]"), "Journal": pd.Series([], dtype=str), "Compte": pd.Series([], dtype=str), "Libelle": pd.Series([], dtype=str), "Debit": pd.Series([], dtype=float), "Credit": pd.Series([], dtype=float), "Montant": pd.Series([], dtype=float)})

def empty_ndf() -> pd.DataFrame:
    return pd.DataFrame({"Date": pd.Series([], dtype="datetime64[ns]"), "Collaborateur": pd.Series([], dtype=str), "Nature": pd.Series([], dtype=str), "Montant": pd.Series([], dtype=float)})

# ─────────────────────────────────────────────────────────────────
#  NOUVEAU CALCUL DES SCORES FINANCIERS (AVEC MALUS FORENSIC)
# ─────────────────────────────────────────────────────────────────
def compute_scores(cr: pd.DataFrame, bilan: pd.DataFrame, alerts: list) -> dict:
    bilan_dict = dict(zip(bilan["Poste"], bilan["Montant"])) if not bilan.empty else {}
    
    ca_total = cr["CA"].sum() if len(cr) > 0 else 0.0
    res_net_total = cr["Resultat_Net"].sum() if len(cr) > 0 and "Resultat_Net" in cr.columns else 0.0

    marge_nette = (res_net_total / ca_total * 100) if ca_total > 0 else 0.0

    # BFR Global
    stocks   = bilan_dict.get("Stocks", 0)
    creances = bilan_dict.get("Créances clients", 0) + bilan_dict.get("Créances clients et comptes rattachés", 0)
    dettes_fourn = bilan_dict.get("Dettes fournisseurs", 0)
    dettes_salaires = bilan_dict.get("Dettes salariales", 0)
    dettes_fisc = bilan_dict.get("Dettes fiscales/soc.", 0)
    bfr_total = (stocks + creances) - (dettes_fourn + dettes_salaires + dettes_fisc)
    
    # Seuil de Rentabilité
    achats_total = cr["Achats"].sum() if len(cr) > 0 and "Achats" in cr.columns else 0.0
    mcv = ca_total - achats_total
    tmcv = mcv / ca_total if ca_total > 0 else 0.0
    
    cf_total = 0.0
    if len(cr) > 0:
        for col in ["Charges_Ext", "Salaires", "Amortissements", "Interets"]:
            if col in cr.columns:
                cf_total += cr[col].sum()
                
    seuil_rentabilite = (cf_total / tmcv) if tmcv > 0 else 0.0

    # ── CALCUL DU NOUVEAU SCORE DE SANTÉ ──
    score_ca = 15 if ca_total > 0 else 0
    if marge_nette >= 10: score_rent = 40
    elif marge_nette >= 5: score_rent = 30
    elif marge_nette >= 0: score_rent = 15
    else: score_rent = 0
    
    if seuil_rentabilite > 0 and ca_total >= seuil_rentabilite: score_seuil = 25
    elif seuil_rentabilite > 0 and ca_total >= (seuil_rentabilite * 0.8): score_seuil = 10
    else: score_seuil = 0
    if seuil_rentabilite == 0 and ca_total > 0: score_seuil = 25
    
    if ca_total > 0:
        bfr_ratio = bfr_total / ca_total
        if bfr_total <= 0: score_bfr = 20
        elif bfr_ratio < 0.2: score_bfr = 10
        else: score_bfr = 0
    else:
        score_bfr = 0
        
    base_score = score_ca + score_rent + score_seuil + score_bfr
    
    nb_crit = sum(1 for a in alerts if a["level"] == "critical")
    nb_warn = sum(1 for a in alerts if a["level"] == "warning")
    malus = (nb_crit * 2) + (nb_warn * 1)
    final_score = max(0, min(100, base_score - malus))

    return {
        "global":            round(final_score),
        "ca_total":          ca_total,
        "resultat_net":      res_net_total,
        "marge_nette":       marge_nette,
        "seuil_rentabilite": seuil_rentabilite,
        "bfr":               bfr_total,
        "malus_applique":    malus
    }

# ─────────────────────────────────────────────────────────────────
#  MOTEUR FORENSIC DÉTERMINISTE (RÈGLES FUSIONNÉES ET AJUSTÉES)
# ─────────────────────────────────────────────────────────────────
def detect_anomalies(cr: pd.DataFrame, fec: pd.DataFrame, ndf: pd.DataFrame, bilan: pd.DataFrame = None, mode: str = "full") -> list:
    alerts = []
    if mode == "empty": return alerts

    _MODE_BANNERS = {
        "fec_autogen": {"level": "ok", "icon": "🟢", "title": "Mode Autonome — PCG Mapping", "body": "Le Compte de Résultat et le Bilan ont été reconstruits automatiquement à partir de la balance du FEC. Analyse 360° activée.", "badge": "FEC 100%", "tag": "badge-info"},
        "fec_only": {"level": "info", "icon": "🔵", "title": "Mode FEC — Périmètre d'analyse restreint", "body": "Alertes calculées uniquement sur les soldes comptables.", "badge": "FEC uniquement", "tag": "badge-info"},
        "pdf": {"level": "info", "icon": "🔵", "title": "Mode PDF — Périmètre d'analyse restreint", "body": "Données extraites d'une liasse fiscale PDF. Le FEC réel est absent.", "badge": "PDF — IA", "tag": "badge-info"},
        "hybride": {"level": "ok", "icon": "🟢", "title": "Mode Hybride — Analyse 360° (PDF + FEC)", "body": "Liasse fiscale PDF et FEC réel importés simultanément. Contrôles complets actifs.", "badge": "360°", "tag": "badge-info"},
    }
    if mode in _MODE_BANNERS: alerts.append(_MODE_BANNERS[mode])

    # 1. Chutes de CA (Valable FEC & PDF)
    if mode in ("full", "pdf", "hybride", "fec_autogen"):
        ca_mean = cr["CA"].mean() if len(cr) > 0 and cr["CA"].sum() > 0 else 0.0
        if ca_mean > 0:
            ca_mom = cr["CA"].pct_change() * 100
            for i, v in enumerate(ca_mom):
                if pd.notna(v) and v < -18 and i > 0:
                    m = cr.loc[i, "Mois"].strftime("%B %Y")
                    alerts.append({"level": "warning", "icon": "🟡", "title": f"Chute de CA anormale — {m}", "body": f"Le CA a chuté de {abs(v):.1f}% par rapport au mois précédent.", "badge": "Gestion", "tag": "badge-warning"})

    # 2. ALERTES STRUCTURELLES (Valable PDF & Excel/FEC si Bilan est présent)
    if bilan is not None and not bilan.empty and cr is not None and len(cr) > 0:
        bilan_dict = dict(zip(bilan["Poste"], bilan["Montant"]))
        ca_total = cr["CA"].sum()

        # A. Capitaux Propres Négatifs
        capitaux_propres = bilan_dict.get("Capitaux propres", 0)
        if capitaux_propres < 0:
            alerts.append({
                "level": "critical", "icon": "🔴", "title": "Capitaux Propres Négatifs", 
                "body": f"Les capitaux propres sont négatifs (<b>{fmt_eur(capitaux_propres)}</b>).<br><br><b>Analyse :</b> Les pertes accumulées ont absorbé le capital social. La situation financière est structurellement très compromise.<br><b>Action :</b> Vérifier l'obligation légale de reconstitution des capitaux propres et évaluer le risque immédiat de cessation des paiements.", 
                "badge": "Structurel", "tag": "badge-critical"
            })

        # B. Dettes Fiscales et Sociales Alarmantes (> 20% du CA)
        dettes_fisc_soc = bilan_dict.get("Dettes fiscales/soc.", 0) + bilan_dict.get("Dettes salariales", 0)
        if ca_total > 0 and (dettes_fisc_soc / ca_total) > 0.20:
            alerts.append({
                "level": "critical", "icon": "🔴", "title": "Dettes Urssaf / Fiscales Alarmantes", 
                "body": f"Le passif fiscal et social (<b>{fmt_eur(dettes_fisc_soc)}</b>) représente plus de 20% du CA annuel.<br><br><b>Analyse :</b> L'entreprise semble utiliser l'État comme 'banquier' pour pallier un manque de trésorerie critique.<br><b>Action :</b> Demander d'urgence un état détaillé des dettes privilégiées (privilège Urssaf/Trésor) et vérifier l'existence de moratoires.", 
                "badge": "Passif Privilégié", "tag": "badge-critical"
            })

        # C. BFR Toxique / Consommateur de trésorerie
        bfr_calc = (bilan_dict.get("Stocks", 0) + bilan_dict.get("Créances clients", 0)) - (bilan_dict.get("Dettes fournisseurs", 0) + bilan_dict.get("Dettes salariales", 0) + bilan_dict.get("Dettes fiscales/soc.", 0))
        if ca_total > 0 and (bfr_calc / ca_total) > 0.25:
            alerts.append({
                "level": "warning", "icon": "🟡", "title": "Besoin en Fonds de Roulement (BFR) excessivement lourd", 
                "body": f"Le BFR (<b>{fmt_eur(bfr_calc)}</b>) absorbe une part très importante du Chiffre d'Affaires (> 25%).<br><br><b>Analyse :</b> L'entreprise est étouffée par son cycle d'exploitation. Soit les clients paient très en retard, soit les stocks tournent trop lentement (risque de stocks morts).<br><b>Action :</b> Analyser la balance âgée clients et auditer la rotation réelle des stocks.", 
                "badge": "Structurel", "tag": "badge-warning"
            })
            
        # D. Trésorerie Négative au Bilan
        treso = bilan_dict.get("Trésorerie", 0)
        if treso < 0:
            alerts.append({
                "level": "critical", "icon": "🔴", "title": "Trésorerie Nette Négative à la Clôture", 
                "body": f"La trésorerie affichée au bilan est dans le rouge (<b>{fmt_eur(treso)}</b>).<br><br><b>Analyse :</b> L'entreprise clôture son exercice à découvert. C'est un signal de très forte tension financière.<br><b>Action :</b> Contrôler les lignes de découvert autorisées par les banques pour évaluer le risque de rupture des concours bancaires.", 
                "badge": "Trésorerie", "tag": "badge-critical"
            })

    # 3. Analyse détaillée du FEC (Anomalies de flux)
    if mode in ("full", "fec_only", "hybride", "fec_autogen") and len(fec) > 0 and fec["Montant"].sum() > 0:
        
        # Déséquilibre FEC
        total_debit = fec["Debit"].sum() if "Debit" in fec.columns else 0.0
        total_credit = fec["Credit"].sum() if "Credit" in fec.columns else 0.0
        diff = abs(total_debit - total_credit)
        if diff >= 0.01:
            alerts.append({"level": "critical", "icon": "🔴", "title": "Déséquilibre fondamental du FEC", "body": f"Total Débit : <b>{fmt_eur(total_debit)}</b> / Total Crédit : <b>{fmt_eur(total_credit)}</b> (Écart : {fmt_eur(diff)}).<br><br><b>Action recommandée :</b> Rejeter ce fichier et demander un export équilibré.<br><b>Impact :</b> Les soldes peuvent être faux.", "badge": "Rejet Fichier", "tag": "badge-critical"})

        f_run = fec.copy()
        f_run["CompteStr"] = f_run["Compte"].astype(str).str.replace(" ", "").str.lstrip("0")
        f_run["Solde_Mvmt"] = f_run["Debit"].fillna(0) - f_run["Credit"].fillna(0)
        f_run = f_run.sort_values(by=["CompteStr", "Date"])

        balance_finale = f_run.groupby("CompteStr")["Solde_Mvmt"].sum()
        
        stock_initial = 0.0
        stock_final = 0.0
        
        fournisseurs_debiteurs = 0.0
        fournisseurs_crediteurs = 0.0
        fournisseurs_an = 0.0
        
        emballages_crediteurs = 0.0
        emballages_an = 0.0
        
        caisse_fin = 0.0
        caisse_min = 0.0
        caisse_max = 0.0
        
        banque_fin = 0.0
        banque_an = 0.0
        
        recettes_10 = 0.0
        tva_decaisser = 0.0
        dettes_salariales = 0.0
        
        alerte_51121_active = False
        alerte_51123_active = False

        for cpt_str, group in f_run.groupby("CompteStr"):
            solde_fin = balance_finale.get(cpt_str, 0)
            group["Solde_Cumul"] = group["Solde_Mvmt"].cumsum()
            min_solde = group["Solde_Cumul"].min()
            max_solde = group["Solde_Cumul"].max()
            
            # Extraction des soldes à-nouveaux (Journal AN / OUV)
            is_an = group["Journal"].astype(str).str.upper().str.contains("AN|A-NOUV|RAN|OUV")
            an_solde = group.loc[is_an, "Solde_Mvmt"].sum()

            # Stocks (370)
            if cpt_str.startswith("370") or cpt_str.startswith("3"):
                stock_final += solde_fin
                if an_solde > 0: stock_initial += an_solde

            # Fournisseurs (401)
            if cpt_str.startswith("401"):
                fournisseurs_an += an_solde
                if solde_fin > 0.01: fournisseurs_debiteurs += solde_fin
                elif solde_fin < -0.01: fournisseurs_crediteurs += abs(solde_fin)

            # Fournisseurs - Emballages (4096)
            if cpt_str.startswith("4096"):
                emballages_an += an_solde
                if solde_fin < -0.01: emballages_crediteurs += abs(solde_fin)

            # Caisse (530)
            if cpt_str.startswith("530"):
                caisse_fin += solde_fin
                if min_solde < caisse_min: caisse_min = min_solde
                if max_solde > caisse_max: caisse_max = max_solde

            # Banque (512)
            if cpt_str.startswith("512"):
                banque_fin += solde_fin
                banque_an += an_solde

            # PAYPAL+ CB (51121) 
            if cpt_str.startswith("51121") and not alerte_51121_active:
                if solde_fin < -0.01 or min_solde < -0.01:
                    val_err = min_solde if min_solde < -0.01 else solde_fin
                    alerts.append({"level": "critical", "icon": "🔴", "title": f"PAYPAL+ CB ({cpt_str}) : Balance anormale", "body": f"Solde créditeur détecté en cours d'exercice : <b>{fmt_eur(val_err)}</b>.<br><br><b>Hypothèse :</b> Inversement de transaction ou recettes mal enregistrées.<br><b>Action :</b> Vérifier les transactions pour s'assurer de la nature des mouvements.<br><b>Impact :</b> Possible distorsion significative de la situation bancaire réelle, affectant notamment les prévisions de trésorerie.", "badge": "Trésorerie", "tag": "badge-critical"})
                    alerte_51121_active = True

            # VIREMENTS (51123)
            if cpt_str.startswith("51123") and not alerte_51123_active:
                if solde_fin < -0.01 or min_solde < -0.01:
                    val_err = min_solde if min_solde < -0.01 else solde_fin
                    alerts.append({"level": "critical", "icon": "🔴", "title": f"VIREMENTS ({cpt_str}) : Balance anormale", "body": f"Solde créditeur détecté : <b>{fmt_eur(val_err)}</b>.<br><br><b>Hypothèse :</b> Omissions de frais de virement ou enregistrements incomplets.<br><b>Action :</b> Passer en revue les frais associés aux virements.<br><b>Impact :</b> Les frais omis peuvent entraîner une révision à la baisse du bénéfice courant.", "badge": "Trésorerie", "tag": "badge-critical"})
                    alerte_51123_active = True

            # Recettes 10% (7011)
            if cpt_str.startswith("7011"):
                recettes_10 += abs(solde_fin)

            # TVA à décaisser (4455)
            if cpt_str.startswith("4455"):
                tva_decaisser += abs(solde_fin)

            # Dettes salariales (421)
            if cpt_str.startswith("421") and solde_fin < -0.01:
                dettes_salariales += abs(solde_fin)

        # ── GÉNÉRATION DES ALERTES FEC FUSIONNÉES ──
        
        # Anomalie 1 : Stocks
        if stock_initial > 0 and abs(stock_final) < 0.01:
            alerts.append({"level": "warning", "icon": "🟡", "title": "Stocks de marchandises (370)", "body": f"<b>Anomalie :</b> Solde nul au lieu d'un stock positif. Disparition inhabituelle du stock initial de {fmt_eur(stock_initial)}.<br><br><b>Hypothèse :</b> Sortie du stock non enregistrée correctement ou erreur de saisie lors de la clôture du dernier exercice.<br><b>Action recommandée :</b> Vérifier les mouvements de stocks ; s'assurer que toute sortie ou destruction a été correctement passée en écriture comptable.<br><b>Impact :</b> Sous-évaluation potentielle des actifs de {fmt_eur(stock_initial)}. Risque de distorsion dans le calcul du coût des ventes et du résultat.", "badge": "Actif", "tag": "badge-warning"})

        # Anomalie 2 : Fournisseurs
        if fournisseurs_crediteurs > 1000:
            alerts.append({"level": "critical", "icon": "🔴", "title": "Fournisseurs (401)", "body": f"<b>Anomalie :</b> Solde anormalement créditeur (-{fmt_eur(fournisseurs_crediteurs)}) et inversion par rapport au solde précédent.<br><br><b>Hypothèse :</b> Paiements anticipés ou erreurs de lettrage provoquant un solde anormalement créditeur.<br><b>Action recommandée :</b> Lettrer et rapprocher le grand livre fournisseurs ; identifier les paiements non affectés ou les factures non saisies.<br><b>Impact :</b> Risque de sur-estimation des dettes fournisseurs de {fmt_eur(fournisseurs_crediteurs)}. Impact immédiat sur la trésorerie et le résultat.", "badge": "Passif", "tag": "badge-critical"})
        elif fournisseurs_debiteurs > 0.01:
            alerts.append({"level": "warning", "icon": "🟡", "title": "Fournisseurs (401)", "body": f"<b>Anomalie :</b> Solde anormalement débiteur identifié ({fmt_eur(fournisseurs_debiteurs)}).<br><br><b>Hypothèse :</b> Paiements anticipés à certains fournisseurs ou erreurs dans l'enregistrement des factures.<br><b>Action recommandée :</b> Contrôler les comptes fournisseurs pour vérifier la validité des soldes.<br><b>Impact :</b> Risque de mauvaise gestion des paiements anticipés, pouvant générer des déséquilibres de trésorerie.", "badge": "Tiers", "tag": "badge-warning"})

        # Anomalie 3 : Emballages
        if emballages_crediteurs > 0.01:
            an_txt = f" ({fmt_eur(abs(emballages_an))})" if emballages_an < -0.01 else ""
            alerts.append({"level": "warning", "icon": "🟡", "title": "Fournisseurs - Créances pour emballages et matériel à rendre (4096)", "body": f"<b>Anomalie :</b> Solde créditeur (-{fmt_eur(emballages_crediteurs)}) non cohérent avec faibles variations antérieures{an_txt}.<br><br><b>Hypothèse :</b> Non restitution d'emballages ou matériel, ou omission de régularisation liée à contrats d'emballage.<br><b>Action recommandée :</b> Revoir tous les flux de retour d'emballages et vérifier l'existence d'accords fournisseur non apurés.<br><b>Impact :</b> Exposition potentielle à des litiges ou à une perte de {fmt_eur(emballages_crediteurs)} non apurée.", "badge": "Fournisseurs", "tag": "badge-warning"})

        # Anomalie 4 : Caisse 
        if caisse_max > 1000 or caisse_min < -0.01:
            alerts.append({"level": "critical", "icon": "🔴", "title": "Caisse (530) : Anomalie Majeure", "body": f"<b>Anomalie :</b> Solde inattendu détecté. La caisse est passée en négatif en cours d'année (pire solde : {fmt_eur(caisse_min)}) et a connu des pointes anormalement élevées ({fmt_eur(caisse_max)}).<br><br><b>Hypothèse :</b> Dépôts non enregistrés en banque, prélèvements personnels non comptabilisés, ou fausses écritures pour masquer un manque de trésorerie.<br><b>Action recommandée :</b> Contrôler d'urgence le journal de caisse et pointer les encaissements avec les tickets physiques.<br><b>Impact :</b> Forte suspicion de confusion de patrimoine et distorsion grave de la situation de trésorerie.", "badge": "Fraude / Caisse", "tag": "badge-critical"})

        # Anomalie 5 : Banque (Déjà capturée structurellement si bilan, mais on le laisse pour la vue FEC seule)
        if banque_fin < -0.01 and mode == "fec_only":
            an_txt = f" alors que le précédent était positif ({fmt_eur(banque_an)})" if banque_an > 0 else ""
            alerts.append({"level": "critical", "icon": "🔴", "title": "Banque (5121001)", "body": f"<b>Anomalie :</b> Solde négatif en banque (-{fmt_eur(abs(banque_fin))}){an_txt}.<br><br><b>Hypothèse :</b> Chèques non encore débités ou enregistrement de décaissements sans couverture réelle.<br><b>Action recommandée :</b> Faire un rapprochement bancaire complet et identifier les écritures non à jour.<br><b>Impact :</b> Risque de frais bancaires ou d’agios, impact direct sur la trésorerie disponible.", "badge": "Trésorerie", "tag": "badge-critical"})

        # Anomalie 6 : Recettes 10%
        if recettes_10 > 0.01:
            alerts.append({"level": "critical", "icon": "🔴", "title": "RECETTES 10% (7011)", "body": f"<b>Anomalie :</b> Solde crédit de recettes à 10% (-{fmt_eur(recettes_10)}).<br><br><b>Hypothèse :</b> Saisie ou allocation incorrecte des recettes ou possible confusion de taux de TVA sur les encaissements.<br><b>Action recommandée :</b> Analyser la ventilation des recettes, recouper avec les déclarations de TVA, vérifier les taux appliqués.<br><b>Impact :</b> Risque de déclaration incorrecte de TVA, impact direct sur le résultat et exposition à contrôles fiscaux.", "badge": "Fiscal / CA", "tag": "badge-critical"})

        # Anomalie 7 : TVA
        if tva_decaisser > 0.01:
            alerts.append({"level": "critical", "icon": "🔴", "title": "Taxes sur le chiffre d'affaires à décaisser (4455)", "body": f"<b>Anomalie :</b> Solde TVA à décaisser fortement négatif (-{fmt_eur(tva_decaisser)}).<br><br><b>Hypothèse :</b> Déséquilibre entre TVA collectée et déductible ou non-apurement d'exercices précédents.<br><b>Action recommandée :</b> Analyser le détail des flux TVA, recoupement entre TVA collectée (comptes 44571xxx) et déductible, vérifier la concordance avec les déclarations.<br><b>Impact :</b> Risque fiscal significatif ; montant à décaisser incorrect pouvant déboucher sur des pénalités.", "badge": "Risque Fiscal", "tag": "badge-critical"})

    return alerts

# ─────────────────────────────────────────────────────────────────
#  PLOTLY HELPERS
# ─────────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="DM Mono, monospace", color="#94A3B8"), margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(gridcolor="#2D3F5E", showline=False, zeroline=False), yaxis=dict(gridcolor="#2D3F5E", showline=False, zeroline=False))

def score_donut(value):
    color = "#10B981" if value >= 75 else ("#F59E0B" if value >= 50 else "#F43F5E")
    display_val = value if value > 0 else 0
    fig = go.Figure(go.Pie(values=[max(display_val, 0), max(100 - display_val, 100)], hole=0.78, marker=dict(colors=[color if display_val > 0 else "#2D3F5E", "#1A2744"]), showlegend=False, textinfo="none", hoverinfo="skip"))
    fig.add_annotation(text=f"<b>{value}</b>", x=0.5, y=0.55, font=dict(size=36, family="Syne", color="#F1F5F9"), showarrow=False)
    fig.add_annotation(text="/100", x=0.5, y=0.38, font=dict(size=13, family="DM Mono", color="#64748B"), showarrow=False)
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_layout(height=220, margin=dict(l=10, r=10, t=10, b=10))
    return fig

def ca_chart(cr: pd.DataFrame):
    fig = go.Figure()
    if cr["CA"].sum() > 0:
        fig.add_trace(go.Scatter(x=cr["Mois"], y=cr["CA"], mode="lines+markers", line=dict(color="#38BDF8", width=2.5), marker=dict(size=5, color="#38BDF8"), name="CA", fill="tozeroy", fillcolor="rgba(56,189,248,.07)"))
        fig.add_trace(go.Scatter(x=cr["Mois"], y=cr["EBIT"], mode="lines+markers", line=dict(color="#10B981", width=2, dash="dot"), marker=dict(size=5, color="#10B981"), name="EBIT"))
        fig.add_trace(go.Scatter(x=cr["Mois"], y=cr["Resultat_Net"], mode="lines", line=dict(color="#F59E0B", width=2), name="Résultat Net"))
    fig.update_layout(**PLOTLY_LAYOUT, height=280, legend=dict(orientation="h", y=1.1, font=dict(size=10)))
    return fig

def marges_chart(cr: pd.DataFrame):
    fig = go.Figure()
    if cr["CA"].sum() > 0:
        ca_safe    = cr["CA"].replace(0, float("nan"))
        marge_brute = (cr["CA"] - cr["Achats"]) / ca_safe * 100
        marge_nette = cr["Resultat_Net"] / ca_safe * 100
        fig.add_trace(go.Bar(x=cr["Mois"], y=marge_brute, name="Marge brute %",  marker_color="rgba(16,185,129,.7)"))
        fig.add_trace(go.Bar(x=cr["Mois"], y=marge_nette, name="Marge nette %",  marker_color="rgba(245,158,11,.7)"))
    fig.update_layout(**PLOTLY_LAYOUT, height=260, barmode="group", legend=dict(orientation="h", y=1.1, font=dict(size=10)))
    return fig

def bilan_chart(bilan: pd.DataFrame):
    fig = go.Figure()
    if not bilan.empty:
        items = bilan[bilan["Montant"] != 0].copy()
        if not items.empty:
            colors = ["#38BDF8", "#10B981", "#F59E0B", "#A78BFA", "#F43F5E", "#2DD4BF", "#FB923C", "#E879F9", "#6366F1", "#EC4899", "#8B5CF6"]
            marker_colors = [colors[i % len(colors)] for i in range(len(items))]
            
            fig.add_trace(go.Bar(
                x=items["Poste"], y=items["Montant"],
                marker_color=marker_colors,
                text=[fmt_eur(v, short=True) for v in items["Montant"]],
                textposition="outside", textfont=dict(size=10, family="DM Mono"),
            ))
    fig.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False, xaxis_tickfont=dict(size=9))
    return fig

# ─────────────────────────────────────────────────────────────────
#  ASSISTANT IA FORENSIC
# ─────────────────────────────────────────────────────────────────
AI_SYSTEM_CONTEXT = """You are ARIS — Audit Risk Intelligence System, an expert assistant in forensic accounting and financial auditing, specifically tailored to assist "Administrateurs Judiciaires" and "Mandataires Judiciaires" in charge of "procédures collectives" (insolvency, bankruptcy, restructuring proceedings).
You analyse structured accounting data provided in the context block below to detect financial anomalies, suspect asset movements, potential "abus de biens sociaux", and evaluate the true cash position (cessation des paiements, cash burn).

LANGUAGE RULE (ABSOLUTE — no exception):
Detect the language of the user's question and reply EXCLUSIVELY in that same language.
If the question is in French -> answer in French.
If the question is in English -> answer in English.

OUTPUT FORMAT RULES:
1. Plain text only. Zero HTML tags, zero CSS (no <div>, no </div>). You may use standard markdown (bold, bullets) for readability.
2. Be conversational, concise, and direct. Explain the "why" behind the numbers from the perspective of an insolvency practitioner.
3. DO NOT cut off mid-sentence. Finish your thoughts naturally.
4. If appropriate, and ONLY if it adds value, end your analysis with a single actionable advice focused on judicial administration (e.g., specific asset to recover, liability to challenge, specific audit to run) formatted as:
   -> Recommandation : [your advice]

FORENSIC INTELLIGENCE & TONE RULES:
- You are addressing the Auditor/Mandataire Judiciaire, NOT the business owner. NEVER use "your" (votre/vos) to refer to the company's financial data (e.g., say "les capitaux propres", not "vos capitaux propres").
- Maintain a strictly objective, legal, and professional tone. Avoid direct accusations (e.g., do not say "c'est la preuve d'un vol" or "le dirigeant a consommé l'actif"). Instead, use appropriate legal phrasing like "indice de confusion de patrimoine", "flux atypiques potentiels", or "anomalie comptable à investiguer".
- Exploit ALL figures present in the STRUCTURED FINANCIAL CONTEXT.
- Focus on signs of insolvency, hidden liabilities, and recoverable assets.
- Temperature is 0.4 — stay factual, avoid speculation beyond the data provided.
"""

def build_financial_context(cr: pd.DataFrame, bilan: pd.DataFrame, scores: dict, alerts: list, mode: str = "full") -> str:
    ca_total  = scores.get("ca_total", 0.0)
    rn_total  = scores.get("resultat_net", 0.0)

    _MODE_PREFIXES = {
        "fec_autogen": "CONTEXT: The P&L and Balance Sheet were auto-generated mathematically from the FEC.\n\n",
        "fec_only": "DATA WARNING: Only a transaction ledger (FEC) was imported.\n\n",
        "pdf": "CONTEXT: Financial data extracted from a PDF. No transaction ledger present.\n\n",
        "hybride": "CONTEXT: Hybrid Mode (PDF + FEC). Full analysis available.\n\n",
    }
    prefix = _MODE_PREFIXES.get(mode, "")
    annee = cr["Mois"].dt.year.max() if len(cr) > 0 else "N/A"
    
    ctx = [prefix, f"STRUCTURED FINANCIAL DATA (fiscal year {annee}):"]
    ctx.append(f"- Annual revenue (CA total) : {fmt_eur(ca_total)}")
    ctx.append(f"- Cumulative net result     : {fmt_eur(rn_total)}")
    ctx.append(f"- Global health score        : {scores.get('global', 0)}/100")
    ctx.append(f"- Break-even point (Seuil)  : {fmt_eur(scores.get('seuil_rentabilite', 0))}")
    ctx.append(f"- Global BFR                 : {fmt_eur(scores.get('bfr', 0))}")
    
    if alerts:
        ctx.append("\n--- DETECTED FORENSIC ALERTS ---")
        for a in alerts:
            lvl = "CRITICAL" if a['level'] == 'critical' else "WARNING" if a['level'] == 'warning' else "INFO"
            body_clean = re.sub(r"<[^>]+>", "", a['body']).replace('\n', ' ')
            ctx.append(f"[{lvl}] {a['title']}: {body_clean}")

    if not bilan.empty:
        ctx.append("\n--- BALANCE SHEET (BILAN) ---")
        for _, row in bilan[bilan["Montant"] != 0].iterrows():
            ctx.append(f"- {row['Poste']}: {fmt_eur(row['Montant'])}")

    if not cr.empty:
        ctx.append("\n--- MONTHLY DETAILS (P&L & BFR) ---")
        for _, row in cr.iterrows():
            m = row["Mois"].strftime("%b %Y")
            ca = row.get("CA", 0)
            ebit = row.get("EBIT", 0)
            rn = row.get("Resultat_Net", 0)
            bfr = row.get("BFR", 0)
            ctx.append(f"{m} -> CA: {fmt_eur(ca)} | EBIT: {fmt_eur(ebit)} | Net: {fmt_eur(rn)} | BFR: {fmt_eur(bfr)}")

    return "\n".join(ctx)

def _sanitise_ai_output(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw)
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()

def call_ai_forensic(user_question: str, cr: pd.DataFrame, bilan: pd.DataFrame, scores: dict, alerts: list, history: list, mode: str = "full", raw_pdf: bytes = None) -> str:
    if not _GEMINI_AVAILABLE or not _GEMINI_API_KEY:
        return "⚠️ Erreur: Module Google Generative AI non installé ou clé API manquante."

    financial_ctx = build_financial_context(cr, bilan, scores, alerts, mode=mode)
    prompt_parts = [AI_SYSTEM_CONTEXT, "\n\n--- STRUCTURED FINANCIAL CONTEXT ---\n", financial_ctx, "\n--- CONVERSATION HISTORY ---\n"]
    for msg in history[-4:]:
        role_label = "User" if msg["role"] == "user" else "ARIS"
        prompt_parts.append(f"{role_label}: {_sanitise_ai_output(msg.get('content', ''))}\n")

    prompt_parts.append(f"\n--- CURRENT QUESTION ---\nUser: {user_question}\nARIS:")
    
    contents = []
    # Si on a un PDF en mémoire, on l'injecte dans la requête à Gemini
    if raw_pdf:
        contents.append({"mime_type": "application/pdf", "data": base64.b64encode(raw_pdf).decode('utf-8')})
    
    contents.append("".join(prompt_parts))

    try:
        model    = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(contents, generation_config=genai.types.GenerationConfig(max_output_tokens=2048, temperature=0.4, stop_sequences=["\nUser:", "User:", "--- CURRENT QUESTION"]))
        return _sanitise_ai_output(response.text if response.text else "")
    except Exception as exc:
        return f"⚠️ Erreur Gemini : {exc}"

# ─────────────────────────────────────────────────────────────────
#  MAPPING PCG (Auto-Génération depuis le FEC avec BFR Mensuel)
# ─────────────────────────────────────────────────────────────────
def reconstruct_financials_from_fec(fec: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if fec is None or fec.empty or "Compte" not in fec.columns:
        return empty_cr(), empty_bilan()

    f_calc = fec.copy()
    f_calc["CompteStr"] = f_calc["Compte"].astype(str).str.replace(" ", "").str.lstrip("0")
    f_calc["Date"] = pd.to_datetime(f_calc["Date"], errors="coerce")
    f_calc = f_calc.dropna(subset=["Date"])
    
    if f_calc.empty: return empty_cr(), empty_bilan()
        
    f_calc["Mois"] = f_calc["Date"].dt.to_period("M").dt.to_timestamp()

    cr_records = []
    cumul_bfr = 0.0 # Accumulateur pour le BFR mensuel
    
    # On itère mois par mois dans l'ordre chronologique
    for mois, group in f_calc.sort_values(by="Date").groupby("Mois"):
        
        # Fonction pour le Résultat (Solde = Crédit - Débit)
        def solde(prefixes, is_credit_normal=True):
            mask = group["CompteStr"].apply(lambda x: any(x.startswith(p) for p in prefixes))
            subset = group[mask]
            if is_credit_normal:
                return subset["Credit"].sum() - subset["Debit"].sum()
            else:
                return subset["Debit"].sum() - subset["Credit"].sum()
            
        # Fonction pour le Bilan (Mouvement du mois = Débit - Crédit pour l'Actif)
        def solde_b_mvt(prefixes, is_credit_normal=False):
            mask = group["CompteStr"].apply(lambda x: any(x.startswith(p) for p in prefixes))
            subset = group[mask]
            if is_credit_normal:
                return subset["Credit"].sum() - subset["Debit"].sum()
            else:
                return subset["Debit"].sum() - subset["Credit"].sum()

        ca = max(0, solde(["70"]))
        achats = max(0, solde(["60"], False))
        charges_ext = max(0, solde(["61", "62"], False))
        salaires = max(0, solde(["64"], False))
        amortissements = max(0, solde(["68"], False))
        interets = max(0, solde(["66"], False))

        prod_expl = solde(["70", "71", "72", "73", "74", "75"])
        charg_expl = solde(["60", "61", "62", "63", "64", "65", "68"], False)
        ebit = prod_expl - charg_expl
        res_net = solde(["7"]) - solde(["6"], False)

        # Calcul de la variation mensuelle du BFR
        mvt_stocks = solde_b_mvt(["3"])
        mvt_creances = solde_b_mvt(["41"])
        mvt_dettes_fourn = solde_b_mvt(["40"], True)
        mvt_dettes_salaires = solde_b_mvt(["42"], True)
        mvt_dettes_fisc = solde_b_mvt(["43", "44"], True)
        
        # On ajoute le mouvement du mois à l'accumulateur total
        mvt_bfr = (mvt_stocks + mvt_creances) - (mvt_dettes_fourn + mvt_dettes_salaires + mvt_dettes_fisc)
        cumul_bfr += mvt_bfr

        cr_records.append({"Mois": mois, "CA": ca, "Achats": achats, "Charges_Ext": charges_ext, "Salaires": salaires, "Amortissements": amortissements, "EBIT": ebit, "Interets": interets, "Resultat_Net": res_net, "BFR": cumul_bfr})
    
    cr_df = pd.DataFrame(cr_records).sort_values("Mois").reset_index(drop=True) if cr_records else empty_cr()

    # Bilan Global de fin d'année
    def solde_b_total(prefixes, is_credit_normal=False):
        mask = f_calc["CompteStr"].apply(lambda x: any(x.startswith(p) for p in prefixes))
        subset = f_calc[mask]
        if is_credit_normal:
            return subset["Credit"].sum() - subset["Debit"].sum()
        else:
            return subset["Debit"].sum() - subset["Credit"].sum()

    bilan_records = [
        {"Poste": "Capitaux propres", "Montant": solde_b_total(["10", "11", "12", "13", "14", "15"], True)},
        {"Poste": "Dettes financières", "Montant": solde_b_total(["16", "17"], True)},
        {"Poste": "Immobilisations", "Montant": solde_b_total(["2"])},
        {"Poste": "Stocks", "Montant": solde_b_total(["3"])},
        {"Poste": "Créances clients", "Montant": solde_b_total(["41"])},
        {"Poste": "Dettes fournisseurs", "Montant": solde_b_total(["40"], True)},
        {"Poste": "Dettes salariales", "Montant": solde_b_total(["42"], True)},
        {"Poste": "Dettes fiscales/soc.", "Montant": solde_b_total(["43", "44"], True)},
        {"Poste": "Cptes courants (45)", "Montant": solde_b_total(["45"], True)},
        {"Poste": "Autres tiers (46-49)", "Montant": solde_b_total(["46", "47", "48", "49"], True)},
        {"Poste": "Trésorerie", "Montant": solde_b_total(["5"])}
    ]
    bilan_df = pd.DataFrame(bilan_records)

    return cr_df, bilan_df

# ─────────────────────────────────────────────────────────────────
#  MOTEUR OMNIVORE (TEXT, CSV & EXCEL ROBUSTE)
# ─────────────────────────────────────────────────────────────────
COLUMN_ALIASES = {"Montant": ["Montant", "Montant (€)", "Valeur"], "CA": ["CA", "Chiffre d'affaires", "Revenue"], "Resultat_Net": ["Resultat_Net", "Résultat Net"], "EBIT": ["EBIT", "Résultat Opérationnel"], "Achats": ["Achats", "Coût des ventes"], "Mois": ["Mois", "Période", "Date"], "Poste": ["Poste", "Libellé"], "Journal": ["Journal", "Code Journal"], "Compte": ["Compte", "N° Compte"], "Date": ["Date", "Date écriture"]}

def _normalise_columns(df: pd.DataFrame):
    alias_idx = {v.strip().lower(): k for k, variants in COLUMN_ALIASES.items() for v in variants}
    rmap = {c: alias_idx[c.strip().lower()] for c in df.columns if c.strip().lower() in alias_idx and alias_idx[c.strip().lower()] != c}
    return df.rename(columns=rmap), rmap

def _get_header_score(cols):
    score = 0
    for c in cols:
        c_clean = str(c).strip().lower().replace(" ", "").replace("_", "").replace(".", "").replace("°", "").replace("-", "").strip('"\'')
        if c_clean in ["journalcode", "codejournal", "jnl", "journal", "jo", "codejnl", "jrnl", "code"]: score += 1
        elif c_clean in ["ecrituredate", "dateecriture", "date", "dateecr", "datepiece", "periode"]: score += 1
        elif c_clean in ["comptenum", "numerocompte", "compte", "ncompte", "comptegeneral", "comptegénéral", "numcompte", "comptegen", "cpt"]: score += 1
        elif c_clean in ["ecriturelib", "libelleecriture", "libelle", "libellé", "lib", "libelleecr", "libelleoperation"]: score += 1
        elif c_clean in ["debit", "débit", "mntdebit", "montantdebit"]: score += 1
        elif c_clean in ["credit", "crédit", "mntcredit", "montantcredit"]: score += 1
        elif c_clean in ["montant", "montant(€)", "valeur", "solde"]: score += 1
    return score

def _clean_fec_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(lambda x: str(x).strip('"\' ') if pd.notna(x) else x)
    df.columns = [str(c).strip('"\' ') for c in df.columns]

    if _get_header_score(df.columns) < 3:
        best_row, max_score = -1, 0
        for idx, row in df.head(20).iterrows():
            score = _get_header_score(row.dropna().tolist())
            if score > max_score and score >= 3:
                max_score, best_row = score, idx
        
        if best_row != -1:
            new_header = df.iloc[best_row].fillna("Unnamed").astype(str).tolist()
            seen, dedup_header = {}, []
            for item in new_header:
                item_clean = item.strip('"\' ')
                if item_clean in seen:
                    seen[item_clean] += 1
                    dedup_header.append(f"{item_clean}_{seen[item_clean]}")
                else:
                    seen[item_clean] = 0
                    dedup_header.append(item_clean)
            df = df.iloc[best_row + 1:].copy()
            df.columns = dedup_header

    col_map = {}
    for c in df.columns:
        c_clean = str(c).strip().lower().replace(" ", "").replace("_", "").replace(".", "").replace("°", "").replace("-", "")
        if c_clean in ["journalcode", "codejournal", "jnl", "journal", "jo", "codejnl", "jrnl", "code"]: col_map[c] = "Journal"
        elif c_clean in ["ecrituredate", "dateecriture", "date", "dateecr", "datepiece", "periode"]: col_map[c] = "Date"
        elif c_clean in ["comptenum", "numerocompte", "compte", "ncompte", "comptegeneral", "comptegénéral", "numcompte", "comptegen", "cpt"]: col_map[c] = "Compte"
        elif c_clean in ["ecriturelib", "libelleecriture", "libelle", "libellé", "lib", "libelleecr", "libelleoperation"]: col_map[c] = "Libelle"
        elif c_clean in ["debit", "débit", "mntdebit", "montantdebit"]: col_map[c] = "Debit"
        elif c_clean in ["credit", "crédit", "mntcredit", "montantcredit"]: col_map[c] = "Credit"
        elif c_clean in ["montant", "montant(€)", "valeur", "solde"]: col_map[c] = "Montant"
            
    df = df.rename(columns=col_map)
    df, _ = _normalise_columns(df)

    for col in ("Debit", "Credit", "Montant"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(" ", "").str.replace(",", ".").str.replace("\xa0", "").str.replace("€", "").str.replace(r"[^\d\.-]", "", regex=True), errors="coerce").fillna(0.0)

    if "Montant" not in df.columns and "Debit" in df.columns and "Credit" in df.columns:
        df["Montant"] = df[["Debit", "Credit"]].max(axis=1)

    if "Date" in df.columns:
        dates_clean = df["Date"].astype(str).str.replace(r"\.0$", "", regex=True).str.replace(r"[^\d\/\-]", "", regex=True)
        df["Date"] = pd.to_datetime(dates_clean, format="%Y%m%d", errors="coerce").fillna(pd.to_datetime(dates_clean, dayfirst=True, errors="coerce"))
    
    return df

def _extract_from_excel(uploaded_file):
    uploaded_file.seek(0)
    file_buffer = io.BytesIO(uploaded_file.read())
    xl = pd.ExcelFile(file_buffer)
    
    cr_df, bilan_df, fec_df = None, None, None
    for sheet in xl.sheet_names:
        try:
            df_raw = xl.parse(sheet, dtype=str)
            if df_raw.empty: continue

            if len(df_raw.columns) == 1:
                col_str = str(df_raw.columns[0])
                sep_counts = {';': col_str.count(';'), '\t': col_str.count('\t'), ',': col_str.count(','), '|': col_str.count('|')}
                best_sep = max(sep_counts, key=sep_counts.get)
                if sep_counts[best_sep] >= 3:
                    df_split = df_raw.iloc[:, 0].astype(str).str.split(best_sep, expand=True)
                    new_cols = [c.strip('"\' ') for c in col_str.split(best_sep)]
                    if len(df_split.columns) == len(new_cols): df_split.columns = new_cols
                    df_raw = df_split
            
            if fec_df is None:
                df_fec_test = _clean_fec_dataframe(df_raw.copy())
                if "Compte" in df_fec_test.columns and ("Debit" in df_fec_test.columns or "Credit" in df_fec_test.columns or "Montant" in df_fec_test.columns):
                    fec_df = df_fec_test
                    continue
            if cr_df is None:
                df_norm, _ = _normalise_columns(df_raw.copy())
                if "Mois" in df_norm.columns and "CA" in df_norm.columns:
                    df_norm["Mois"] = pd.to_datetime(df_norm["Mois"], errors='coerce')
                    for c in ["CA", "Achats", "Charges_Ext", "Salaires", "Amortissements", "EBIT", "Resultat_Net", "BFR"]:
                        if c in df_norm.columns: df_norm[c] = pd.to_numeric(df_norm[c].astype(str).str.replace(r"[^\d\.-]", "", regex=True), errors="coerce").fillna(0.0)
                    cr_df = df_norm
                    continue
            if bilan_df is None:
                df_norm, _ = _normalise_columns(df_raw.copy())
                if "Poste" in df_norm.columns and "Montant" in df_norm.columns:
                    df_norm["Montant"] = pd.to_numeric(df_norm["Montant"].astype(str).str.replace(r"[^\d\.-]", "", regex=True), errors="coerce").fillna(0.0)
                    bilan_df = df_norm
                    continue
        except Exception: pass
            
    return cr_df, bilan_df, fec_df

def _read_fec_csv_txt(uploaded_file):
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    
    content = None
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252", "iso-8859-1"]:
        try:
            content = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError: pass
            
    if content is None: content = raw_bytes.decode('utf-8', errors='ignore')
    content = content.replace('"', '')
        
    lines = content.splitlines()
    if not lines: return None, "Fichier vide"
        
    first_line = lines[0]
    sep_counts = {';': first_line.count(';'), '\t': first_line.count('\t'), ',': first_line.count(','), '|': first_line.count('|')}
    sep = max(sep_counts, key=sep_counts.get)
    if sep_counts[sep] == 0: sep = ';' 
        
    try: df = pd.read_csv(io.StringIO(content), sep=sep, dtype=str, on_bad_lines="warn", quoting=csv.QUOTE_NONE)
    except Exception as e: return None, f"Erreur parsing : {e}"
        
    df = _clean_fec_dataframe(df)
    return df, None

@st.cache_data(show_spinner=False)
def extract_data_from_pdf(pdf_bytes: bytes):
    if not _GEMINI_AVAILABLE or not _GEMINI_API_KEY: return None, None, "Erreur API."
    prompt = '''Extrais les données financières de cette liasse fiscale en JSON strictement valide. 
    Aucun texte avant ou après. 
    Format exigé :
    {
      "bilan": [
        {"Poste": "Immobilisations", "Montant": 0},
        {"Poste": "Stocks", "Montant": 0},
        {"Poste": "Créances clients", "Montant": 0},
        {"Poste": "Trésorerie", "Montant": 0},
        {"Poste": "Capitaux propres", "Montant": 0},
        {"Poste": "Dettes financières", "Montant": 0},
        {"Poste": "Dettes fournisseurs", "Montant": 0},
        {"Poste": "Dettes salariales", "Montant": 0},
        {"Poste": "Dettes fiscales/soc.", "Montant": 0}
      ],
      "resultat": {
        "CA": 0, "Achats": 0, "Charges_Ext": 0, "Salaires": 0, "Amortissements": 0, "Interets": 0, "EBIT": 0, "Resultat_Net": 0, "Annee": 2024
      }
    }
    Remplace les 0 par les montants exacts trouvés dans le document. Si un montant est négatif, garde le signe moins. Si un poste n'existe pas, mets 0.'''
    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        res = model.generate_content([{"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode('utf-8')}, prompt]).text
        
        # Nettoyage robuste pour forcer la lecture du JSON
        json_str = res.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
            
        start = json_str.find('{')
        end = json_str.rfind('}') + 1
        if start != -1 and end != 0: 
            json_str = json_str[start:end]
            
        data = json.loads(json_str)
        
        b_df = pd.DataFrame(data.get("bilan", []))
        if not b_df.empty and "Montant" in b_df.columns: 
            b_df["Montant"] = pd.to_numeric(b_df["Montant"], errors="coerce").fillna(0)
            
        r = data.get("resultat", {})
        annee = int(r.get("Annee", 2024))
        
        cr_df = pd.DataFrame({
            "Mois": pd.date_range(f"{annee}-01-01", periods=12, freq="MS"),
            "CA": [float(r.get("CA", 0))/12]*12,
            "Achats": [float(r.get("Achats", 0))/12]*12,
            "Charges_Ext": [float(r.get("Charges_Ext", 0))/12]*12,
            "Salaires": [float(r.get("Salaires", 0))/12]*12,
            "Amortissements": [float(r.get("Amortissements", 0))/12]*12,
            "Interets": [float(r.get("Interets", 0))/12]*12,
            "EBIT": [float(r.get("EBIT", 0))/12]*12,
            "Resultat_Net": [float(r.get("Resultat_Net", 0))/12]*12,
            "BFR": [0]*12
        })
        return b_df, cr_df, None
    except Exception as e:
        return None, None, str(e)

def load_data(uploaded_files: list):
    if not uploaded_files: return empty_cr(), empty_bilan(), empty_fec(), empty_ndf(), "empty", None
    cr, bilan, fec, ndf = None, None, None, None
    source_cr = None
    raw_pdf = None

    for f in uploaded_files:
        ext = f.name.lower().rsplit(".", 1)[-1]
        if ext == "pdf":
            raw_pdf = f.getvalue()
            with st.spinner("Analyse de la liasse PDF par l'IA en cours..."):
                b_df, c_df, err = extract_data_from_pdf(raw_pdf)
            if not err: 
                cr, bilan = c_df, b_df
            else:
                st.sidebar.error(f"Erreur de lecture PDF : L'IA n'a pas pu extraire les données correctement ({err})")
        elif ext in ("txt", "csv"):
            f.seek(0)
            f_df, err = _read_fec_csv_txt(io.BytesIO(f.getvalue()))
            if not err and f_df is not None and "Compte" in f_df.columns:
                fec = f_df
            elif ext == "csv":
                c, b, f_test = _extract_from_excel(f)
                if c is not None: cr = c
                if b is not None: bilan = b
                if f_test is not None: fec = f_test
        elif ext in ("xlsx", "xls"):
            f.seek(0)
            c, b, f_df = _extract_from_excel(f)
            if c is not None: cr = c
            if b is not None: bilan = b
            if f_df is not None: fec = f_df

    fec_real = fec is not None
    cr_real = cr is not None
    bilan_real = bilan is not None

    if fec_real and (not cr_real or not bilan_real):
        cr_auto, bilan_auto = reconstruct_financials_from_fec(fec)
        if not cr_real:
            cr = cr_auto
            source_cr = "Auto-généré (Mapping PCG)"
            cr_real = True
        if not bilan_real:
            bilan = bilan_auto
            bilan_real = True

    if cr_real and bilan_real and fec_real: app_mode = "fec_autogen" if source_cr == "Auto-généré (Mapping PCG)" else "full"
    elif cr_real and bilan_real and not fec_real: app_mode = "pdf"
    elif fec_real and not cr_real and not bilan_real: app_mode = "fec_only"
    elif fec_real and (cr_real or bilan_real): app_mode = "hybride"
    else: app_mode = "empty"

    return cr if cr is not None else empty_cr(), bilan if bilan is not None else empty_bilan(), fec if fec is not None else empty_fec(), empty_ndf(), app_mode, raw_pdf

# ─────────────────────────────────────────────────────────────────
#  GENERATION RAPPORTS (MARKDOWN & PDF)
# ─────────────────────────────────────────────────────────────────
def generate_report(cr, bilan, fec, scores, alerts, app_mode):
    lines = [f"# RAPPORT D'AUDIT FORENSIC ({datetime.now().strftime('%d/%m/%Y')})\n"]
    
    # 1. Santé Financière
    lines.append("## 📊 Santé Financière")
    lines.append(f"- **Score Global** : {scores.get('global', 0)}/100")
    lines.append(f"- **CA Annuel** : {fmt_eur(scores.get('ca_total', 0))}")
    lines.append(f"- **Résultat Net** : {fmt_eur(scores.get('resultat_net', 0))}")
    lines.append(f"- **Marge Nette** : {round(scores.get('marge_nette', 0), 2)}%")
    lines.append(f"- **Seuil Rentabilité** : {fmt_eur(scores.get('seuil_rentabilite', 0))}")
    lines.append(f"- **BFR** : {fmt_eur(scores.get('bfr', 0))}\n")
    
    if not bilan.empty:
        lines.append("### Postes du Bilan")
        for _, row in bilan[bilan["Montant"] != 0].iterrows():
            lines.append(f"- {row['Poste']} : {fmt_eur(row['Montant'])}")
        lines.append("\n")

    # 2. Synthèse du FEC
    lines.append("## 📋 Synthèse du FEC")
    if not fec.empty:
        tot_d = fec["Debit"].sum() if "Debit" in fec.columns else 0.0
        tot_c = fec["Credit"].sum() if "Credit" in fec.columns else 0.0
        diff = abs(tot_d - tot_c)
        lines.append(f"- **Lignes FEC** : {len(fec):,}")
        lines.append(f"- **Total Débit** : {fmt_eur(tot_d)}")
        lines.append(f"- **Total Crédit** : {fmt_eur(tot_c)}")
        lines.append(f"- **Écart (Balance)** : {fmt_eur(diff)}\n")
    else:
        lines.append("FEC absent ou non reconnu.\n")

    # 3. Détail Mensuel
    lines.append("## 📑 Détail Mensuel")
    if not cr.empty:
        lines.append("| Période | CA | Marge Brute | Marge Nette | BFR | Résultat Net |")
        lines.append("|---|---|---|---|---|---|")
        for _, row in cr.iterrows():
            periode = row["Mois"].strftime("%b %Y").title()
            ca = row["CA"]
            mb = ca - row.get("Achats", 0)
            mn = (row["Resultat_Net"] / ca * 100) if ca != 0 else 0
            bfr = row.get("BFR", 0)
            rn = row["Resultat_Net"]
            lines.append(f"| {periode} | {fmt_eur(ca)} | {fmt_eur(mb)} | {mn:.2f}% | {fmt_eur(bfr)} | {fmt_eur(rn)} |")
        lines.append("\n")

    # 4. Alertes
    active_alerts = [a for a in alerts if a['level'] in ('critical','warning')]
    lines.append(f"## ⚠️ Alertes actives ({len(active_alerts)})")
    for a in active_alerts:
        body_clean = a['body'].replace('<b>', '**').replace('</b>', '**')
        body_clean = body_clean.replace('<br><br>', '\n\n').replace('<br>', '\n')
        lines.append(f"### {a['title']}\n{body_clean}\n")
            
    return "\n".join(lines)

def generate_pdf_report(cr, bilan, fec, scores, alerts, exercice):
    if not _FPDF_AVAILABLE: return b""
    pdf = FPDF()
    pdf.add_page()
    
    def ct(txt):
        txt = str(txt)
        txt = txt.replace("<br><br>", "\n").replace("<br>", "\n")
        txt = re.sub(r"<[^>]+>", "", txt)
        txt = txt.replace("€", "EUR").replace("\u202f", " ").replace("—", "-").replace("’", "'")
        return txt.encode('latin-1', 'replace').decode('latin-1')

    # Titre
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt=ct(f"RAPPORT D'AUDIT FORENSIC - {exercice}"), ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, txt=ct(f"Date d'export : {datetime.now().strftime('%d/%m/%Y')}"), ln=True, align='C')
    pdf.ln(5)
    
    # 1. Santé Financière
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 8, txt=ct("1. SANTE FINANCIERE"), ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(95, 6, txt=ct(f"Score Global : {scores.get('global', 0)}/100"))
    pdf.cell(95, 6, txt=ct(f"Seuil Rentabilite : {fmt_eur(scores.get('seuil_rentabilite', 0))}"), ln=True)
    pdf.cell(95, 6, txt=ct(f"CA Annuel : {fmt_eur(scores.get('ca_total', 0))}"))
    pdf.cell(95, 6, txt=ct(f"BFR : {fmt_eur(scores.get('bfr', 0))}"), ln=True)
    pdf.cell(95, 6, txt=ct(f"Resultat Net : {fmt_eur(scores.get('resultat_net', 0))}"))
    pdf.cell(95, 6, txt=ct(f"Marge Nette : {round(scores.get('marge_nette', 0), 2)}%"), ln=True)
    pdf.ln(5)
    
    # 2. Synthèse du FEC
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, txt=ct("2. SYNTHESE DU FEC"), ln=True, fill=True)
    pdf.set_font("Arial", size=10)
    if not fec.empty:
        tot_d = fec["Debit"].sum() if "Debit" in fec.columns else 0.0
        tot_c = fec["Credit"].sum() if "Credit" in fec.columns else 0.0
        pdf.cell(95, 6, txt=ct(f"Lignes FEC : {len(fec):,}"))
        pdf.cell(95, 6, txt=ct(f"Total Debit : {fmt_eur(tot_d)}"), ln=True)
        pdf.cell(95, 6, txt=ct(f"Ecart Balance : {fmt_eur(abs(tot_d - tot_c))}"))
        pdf.cell(95, 6, txt=ct(f"Total Credit : {fmt_eur(tot_c)}"), ln=True)
    else:
        pdf.cell(0, 6, txt=ct("FEC absent ou non reconnu."), ln=True)
    pdf.ln(5)

    # 3. Détail Mensuel
    pdf.set_font("Arial", 'B', 12)
    # L'erreur était ici : il manquait "ln=True" pour forcer le retour à la ligne !
    pdf.cell(0, 8, txt=ct("3. DETAIL MENSUEL"), ln=True, fill=True) 
    if not cr.empty:
        pdf.set_font("Arial", 'B', 9)
        col_w = [30, 30, 30, 25, 30, 30]
        headers = ["Periode", "CA", "Marge Brute", "Marge Nette", "BFR", "Res. Net"]
        for w, h in zip(col_w, headers):
            pdf.cell(w, 7, txt=ct(h), border=1, align='C')
        pdf.ln()
        pdf.set_font("Arial", size=9)
        for _, row in cr.iterrows():
            periode = row["Mois"].strftime("%b %Y").title()
            ca = row["CA"]
            mb = ca - row.get("Achats", 0)
            mn = f"{(row['Resultat_Net'] / ca * 100) if ca != 0 else 0:.2f}%"
            bfr = row.get("BFR", 0)
            rn = row["Resultat_Net"]
            
            pdf.cell(col_w[0], 6, txt=ct(periode), border=1)
            pdf.cell(col_w[1], 6, txt=ct(fmt_eur(ca)), border=1, align='R')
            pdf.cell(col_w[2], 6, txt=ct(fmt_eur(mb)), border=1, align='R')
            pdf.cell(col_w[3], 6, txt=ct(mn), border=1, align='R')
            pdf.cell(col_w[4], 6, txt=ct(fmt_eur(bfr)), border=1, align='R')
            pdf.cell(col_w[5], 6, txt=ct(fmt_eur(rn)), border=1, align='R')
            pdf.ln()
    else:
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 6, txt=ct("Details mensuels non disponibles."), ln=True)
    pdf.ln(5)

    # 4. Alertes Détectées
    active_alerts = [a for a in alerts if a['level'] in ('critical', 'warning')]
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, txt=ct(f"4. ALERTES FORENSIC ({len(active_alerts)})"), ln=True, fill=True)
    
    for a in active_alerts:
        pdf.set_font("Arial", 'B', 10)
        lvl = "CRITIQUE" if a['level'] == 'critical' else "AVERTISSEMENT"
        pdf.cell(0, 6, txt=ct(f"[{lvl}] {a['title']}"), ln=True)
        pdf.set_font("Arial", size=9)
        pdf.multi_cell(0, 5, txt=ct(a['body']))
        pdf.ln(3)
        
    return pdf.output(dest='S').encode('latin-1')

# ─────────────────────────────────────────────────────────────────
#  UI & AFFICHAGE
# ─────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("<div style='text-align:center;margin-bottom:24px;'><div style='font-family:Syne;font-size:1.4rem;font-weight:800;color:#F1F5F9;'>⬡ Bilansia</div><div style='font-family:DM Mono;font-size:9px;color:#64748B;letter-spacing:.15em;'>PORTAIL AUDIT v7.4</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:DM Mono;font-size:10px;color:#64748B;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;'>① Exercice analysé</div>", unsafe_allow_html=True)
        exercice = st.selectbox("Exercice", ["2027", "2026", "2025", "2024", "2023", "2022"], index=3, label_visibility="collapsed")
        st.divider()
        st.markdown("<div style='font-family:DM Mono;font-size:10px;color:#64748B;letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px;'>② Import des données</div>", unsafe_allow_html=True)
        
        uploader_key = f"upload_{exercice}"
        files = st.file_uploader("Fichiers", type=["xlsx", "csv", "txt", "pdf"], accept_multiple_files=True, label_visibility="collapsed", help="Formats acceptés :\n• Excel (.xlsx) : Bilan, Resultat, FEC\n• CSV / TXT : FEC (DGFiP ou export standard)\n• PDF : Liasse (IA Gemini)", key=uploader_key)
        
        if not files and exercice in st.session_state.data_store:
            stored_files = st.session_state.file_names_store.get(exercice, [])
            st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:11px;color:#10B981;margin-bottom:6px;text-align:center;'>✅ Récupéré depuis la mémoire :</div>", unsafe_allow_html=True)
            for fname in stored_files: st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#94A3B8;text-align:center;'>📄 {fname}</div>", unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Effacer le fichier" if len(stored_files) <= 1 else "🗑️ Effacer les fichiers", key=f"clear_{exercice}", use_container_width=True):
                del st.session_state.data_store[exercice]
                if exercice in st.session_state.file_signatures: del st.session_state.file_signatures[exercice]
                if exercice in st.session_state.file_names_store: del st.session_state.file_names_store[exercice]
                if f"chat_history_{exercice}" in st.session_state: del st.session_state[f"chat_history_{exercice}"]
                st.rerun()
        elif not files:
            st.markdown(f'<div class="upload-hint">📂 Glissez vos fichiers pour {exercice}</div>', unsafe_allow_html=True)
            
        mem_years = [y for y in ["2027", "2026", "2025", "2024", "2023", "2022"] if y in st.session_state.data_store and y != exercice]
        if mem_years: st.markdown(f"<div style='font-family:DM Mono,monospace;font-size:10px;color:#10B981;margin-top:12px;text-align:center;'>💾 Autres années en mémoire : {', '.join(mem_years)}</div>", unsafe_allow_html=True)
        st.divider()

    app_mode = "empty"
    cr, bilan, fec, ndf = empty_cr(), empty_bilan(), empty_fec(), empty_ndf()
    raw_pdf = None

    if files:
        current_sig = "-".join([f.name + str(f.size) for f in files])
        if current_sig != st.session_state.file_signatures.get(exercice):
            cr, bilan, fec, ndf, app_mode, raw_pdf = load_data(files)
            st.session_state.data_store[exercice] = (cr, bilan, fec, ndf, app_mode, raw_pdf)
            st.session_state.file_signatures[exercice] = current_sig
            st.session_state.file_names_store[exercice] = [f.name for f in files]
        else:
            cr, bilan, fec, ndf, app_mode, raw_pdf = st.session_state.data_store[exercice]
    elif exercice in st.session_state.data_store:
        cr, bilan, fec, ndf, app_mode, raw_pdf = st.session_state.data_store[exercice]

    alerts = detect_anomalies(cr, fec, ndf, bilan, mode=app_mode)
    scores = compute_scores(cr, bilan, alerts)

    with st.sidebar:
        st.markdown("##### 📥 Export du rapport")
        if app_mode != "empty":
            md_txt = generate_report(cr, bilan, fec, scores, alerts, app_mode)
            st.download_button("⬇️ Format Texte (.md)", md_txt, f"Rapport_{exercice}.md", "text/markdown", use_container_width=True)
            
            if _FPDF_AVAILABLE:
                pdf_data = generate_pdf_report(cr, bilan, fec, scores, alerts, exercice)
                st.download_button("⬇️ Format PDF (.pdf)", pdf_data, f"Rapport_{exercice}.pdf", "application/pdf", use_container_width=True)
            else:
                st.info("💡 Exécutez `pip install fpdf` pour activer l'export PDF.")
        else:
            st.markdown("<div style='font-family:DM Mono;font-size:10px;color:#64748B;'>Disponible après chargement.</div>", unsafe_allow_html=True)

    return exercice, files, cr, bilan, fec, ndf, app_mode, alerts, scores, raw_pdf

def render_empty_state():
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    kpi_data = [("CA Annuel", "0 €", "&nbsp;"), ("Résultat Net", "0 €", "&nbsp;"), ("Marge Nette", "0,00 %", "&nbsp;"), ("Seuil Rentab.", "0 €", "&nbsp;"), ("BFR", "0 €", "&nbsp;"), ("Alertes Actives", "0", "&nbsp;")]
    for col, (label, val, delta) in zip([k1, k2, k3, k4, k5, k6], kpi_data):
        with col: st.markdown(f'<div class="kpi-card"><div class="kpi-label">{label}</div><div class="kpi-value" style="color:#2D3F5E;">{val}</div><div class="kpi-delta" style="color:#2D3F5E;">{delta}</div></div>', unsafe_allow_html=True)
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    
    # Mise à jour de la liste des onglets pour l'état vide
    tab1, tab2, tab_detail, tab3, tab4 = st.tabs(["📊 Santé Financière", "📋 Synthèse du FEC", "📑 Détail Mensuel", "⚠️ Alertes", "🤖 Assistant IA"])
    
    _empty_html = '<div class="empty-state" style="padding: 60px 20px; text-align: center;"><div style="font-size: 48px; opacity: 0.3;">📂</div><div style="font-family: Syne, sans-serif; font-size: 1.2rem; font-weight: 700; color: #94A3B8;">Aucune donnée importée</div><div style="font-family: DM Mono, monospace; font-size: 11px; color: #64748B; margin-top: 8px;">Glissez vos fichiers dans la barre latérale pour démarrer.<br>Formats : Excel (.xlsx), CSV, FEC .txt, PDF liasse.</div></div>'
    
    with tab1: st.markdown(_empty_html, unsafe_allow_html=True)
    with tab2: st.markdown(_empty_html, unsafe_allow_html=True)
    with tab_detail: st.markdown(_empty_html, unsafe_allow_html=True)
    with tab3: st.markdown(_empty_html, unsafe_allow_html=True)
    with tab4: st.markdown(_empty_html, unsafe_allow_html=True)

def _render_chat_tab(cr, bilan, scores, alerts, mode, exercice, raw_pdf):
    history_key = f"chat_history_{exercice}"
    if history_key not in st.session_state: st.session_state[history_key] = [{"role": "assistant", "content": f"Bonjour. Je suis ARIS. Posez-moi une question sur vos données de {exercice}.", "time": datetime.now().strftime("%H:%M")}]
    chat_placeholder = st.empty()
    
    def refresh_chat_ui():
        html = '<div class="chat-container"><div class="chat-header">🤖 ARIS — Assistant Forensic</div><div class="chat-body">'
        for msg in st.session_state[history_key]:
            cls = "msg-user" if msg["role"] == "user" else "msg-ai"
            html += f'<div class="{cls}"><div class="msg-bubble">{msg["content"]}</div><div class="msg-meta">{msg.get("time", "")}</div></div>'
        html += '</div></div>'
        chat_placeholder.markdown(html, unsafe_allow_html=True)
        
    refresh_chat_ui()
    
    st.markdown("<div style='font-family:var(--font-mono); font-size:10px; color:var(--muted); margin-top: 12px; margin-bottom: 8px; text-transform: uppercase;'>⚡ Questions suggérées :</div>", unsafe_allow_html=True)
    
    q1 = "🔍 Indices de cessation des paiements ?"
    q2 = "💸 Analyse des flux suspects (Caisse, Banque)"
    q3 = "📋 Plan d'investigation recommandé"

    col1, col2, col3 = st.columns(3)
    shortcut_clicked = None
    if col1.button(q1, use_container_width=True): shortcut_clicked = q1
    if col2.button(q2, use_container_width=True): shortcut_clicked = q2
    if col3.button(q3, use_container_width=True): shortcut_clicked = q3

    with st.form(f"chat_form_{exercice}", clear_on_submit=True):
        col_inp, col_btn = st.columns([5, 1])
        with col_inp: user_input = st.text_input("Q", placeholder="Ex: Analyse la caisse...", label_visibility="collapsed")
        with col_btn: submitted = st.form_submit_button("→")
        
    final_question = shortcut_clicked if shortcut_clicked else (user_input if submitted and user_input.strip() else None)

    if final_question:
        st.session_state[history_key].append({"role": "user", "content": final_question, "time": datetime.now().strftime("%H:%M")})
        refresh_chat_ui()
        with st.spinner("ARIS analyse…"): answer = call_ai_forensic(final_question, cr, bilan, scores, alerts, st.session_state[history_key], mode, raw_pdf)
        st.session_state[history_key].append({"role": "assistant", "content": answer, "time": datetime.now().strftime("%H:%M")})
        st.rerun()

def main():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="secure-banner"><div class="dot"></div> Bilansia v7.5</div>', unsafe_allow_html=True)
    
    exercice, files, cr, bilan, fec, ndf, app_mode, alerts, scores, raw_pdf = render_sidebar()

    if app_mode == "empty":
        render_empty_state()
        return

    _nb_crit = sum(1 for a in alerts if a["level"] == "critical")
    _nb_warn = sum(1 for a in alerts if a["level"] == "warning")
    
    sr_val = fmt_eur(scores.get("seuil_rentabilite", 0), True)
    if scores.get("seuil_rentabilite", 0) == 0 and cr["CA"].sum() > 0: sr_val = "Inatteignable"
    marge_n_val = f"{round(scores.get('marge_nette', 0), 2)}%"
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.markdown(f'<div class="kpi-card"><div class="kpi-label">CA Annuel</div><div class="kpi-value">{fmt_eur(scores["ca_total"], True)}</div><div class="kpi-delta">&nbsp;</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi-card"><div class="kpi-label">Résultat Net</div><div class="kpi-value">{fmt_eur(scores["resultat_net"], True)}</div><div class="kpi-delta">&nbsp;</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi-card"><div class="kpi-label">Marge Nette</div><div class="kpi-value">{marge_n_val}</div><div class="kpi-delta">&nbsp;</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi-card"><div class="kpi-label">Seuil Rentab.</div><div class="kpi-value">{sr_val}</div><div class="kpi-delta">&nbsp;</div></div>', unsafe_allow_html=True)
    c5.markdown(f'<div class="kpi-card"><div class="kpi-label">BFR</div><div class="kpi-value">{fmt_eur(scores.get("bfr", 0), True)}</div><div class="kpi-delta">&nbsp;</div></div>', unsafe_allow_html=True)
    
    if _nb_crit + _nb_warn > 0:
        c6.markdown(f'<div class="kpi-card"><div class="kpi-label">Alertes Actives</div><div class="kpi-value" style="color:#F43F5E;">{_nb_crit + _nb_warn}</div><div class="kpi-delta">&nbsp;</div></div>', unsafe_allow_html=True)
    else:
        c6.markdown(f'<div class="kpi-card"><div class="kpi-label">Alertes Actives</div><div class="kpi-value">0</div><div class="kpi-delta">&nbsp;</div></div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div id='zone-onglets'></div>", unsafe_allow_html=True)
    
    # Changement dynamique du nom de l'onglet
    titre_onglet_detail = "📑 Synthèse Annuelle" if app_mode == "pdf" else "📑 Détail Mensuel"
    t1, t2, t_detail, t3, t4 = st.tabs(["📊 Santé Financière", "📋 Synthèse du FEC", titre_onglet_detail, "⚠️ Alertes", "🤖 Assistant IA"])
    
    with t1:
        st.markdown('<div class="section-header">🎯 Score Global & Évolution</div>', unsafe_allow_html=True)
        col1, col2 = st.columns([1,3])
        with col1: 
            st.plotly_chart(score_donut(scores["global"]), use_container_width=True)
        with col2: 
            if app_mode != "pdf":
                st.plotly_chart(ca_chart(cr), use_container_width=True)
            else:
                st.markdown("<br><br><br>", unsafe_allow_html=True)
                st.info("💡 L'évolution chronologique (CA, EBIT) nécessite un FEC. La liasse fiscale ne fournit que des totaux annuels.")
        
        if app_mode == "pdf":
            st.markdown('<div class="section-header">🏦 Postes du Bilan</div>', unsafe_allow_html=True)
            st.plotly_chart(bilan_chart(bilan), use_container_width=True)
        else:
            col_m, col_b = st.columns(2)
            with col_m:
                st.markdown('<div class="section-header">📊 Marges (%)</div>', unsafe_allow_html=True)
                st.plotly_chart(marges_chart(cr), use_container_width=True)
            with col_b:
                st.markdown('<div class="section-header">🏦 Postes du Bilan</div>', unsafe_allow_html=True)
                st.plotly_chart(bilan_chart(bilan), use_container_width=True)
            
    with t2:
        if not fec.empty:
            tot_d = fec["Debit"].sum() if "Debit" in fec.columns else 0.0
            tot_c = fec["Credit"].sum() if "Credit" in fec.columns else 0.0
            diff = abs(tot_d - tot_c)
            is_bal = diff < 0.01
            c_bal, i_bal = ("#10B981", "✅ Équilibré") if is_bal else ("#F43F5E", f"❌ Écart de {fmt_eur(diff)}")
            
            st.markdown('<div class="section-header">📋 Synthèse du Fichier des Écritures Comptables (FEC)</div>', unsafe_allow_html=True)
            st.markdown(f'''<div style="display:flex; gap:12px; margin-bottom:16px;"><div style="flex:1; background:rgba(0,0,0,0.2); border:1px solid var(--border); border-radius:8px; padding:12px; text-align:center;"><div style="font-family:var(--font-mono); font-size:10px; color:var(--muted); text-transform:uppercase;">Lignes FEC</div><div style="font-family:var(--font-display); font-size:1.4rem; font-weight:700; color:var(--white);">{len(fec):,}</div></div><div style="flex:1; background:rgba(0,0,0,0.2); border:1px solid var(--border); border-radius:8px; padding:12px; text-align:center;"><div style="font-family:var(--font-mono); font-size:10px; color:var(--muted); text-transform:uppercase;">Total Débit</div><div style="font-family:var(--font-display); font-size:1.4rem; font-weight:700; color:var(--white);">{fmt_eur(tot_d)}</div></div><div style="flex:1; background:rgba(0,0,0,0.2); border:1px solid var(--border); border-radius:8px; padding:12px; text-align:center;"><div style="font-family:var(--font-mono); font-size:10px; color:var(--muted); text-transform:uppercase;">Total Crédit</div><div style="font-family:var(--font-display); font-size:1.4rem; font-weight:700; color:var(--white);">{fmt_eur(tot_c)}</div></div><div style="flex:1; background:rgba(0,0,0,0.2); border:1px solid {c_bal}50; border-radius:8px; padding:12px; text-align:center;"><div style="font-family:var(--font-mono); font-size:10px; color:var(--muted); text-transform:uppercase;">Balance (Débit=Crédit)</div><div style="font-family:var(--font-display); font-size:1.1rem; font-weight:700; color:{c_bal}; margin-top:4px;">{i_bal}</div></div></div>'''.replace(",", " "), unsafe_allow_html=True)
            st.dataframe(fec.head(50), use_container_width=True)
        else: st.info("FEC absent.")
        
    with t_detail:
        if app_mode == "pdf":
            st.markdown('<div class="section-header">📑 Synthèse Annuelle (Liasse Fiscale)</div>', unsafe_allow_html=True)
            if not cr.empty:
                ca_annuel = cr["CA"].sum()
                achats_annuel = cr["Achats"].sum()
                rn_annuel = cr["Resultat_Net"].sum()
                mb_annuel = ca_annuel - achats_annuel
                mn_annuel = (rn_annuel / ca_annuel * 100) if ca_annuel != 0 else 0
                bfr_annuel = scores.get("bfr", 0)

                df_disp = pd.DataFrame({
                    "Période": [f"Exercice {exercice}"],
                    "CA": [f"{ca_annuel:,.0f} €".replace(",", "\u202f")],
                    "Marge Brute": [f"{mb_annuel:,.0f} €".replace(",", "\u202f")],
                    "Marge Nette": [f"{mn_annuel:.2f} %"],
                    "BFR": [f"{bfr_annuel:,.0f} €".replace(",", "\u202f")],
                    "Résultat Net": [f"{rn_annuel:,.0f} €".replace(",", "\u202f")]
                })
                
                st.dataframe(df_disp, use_container_width=True, hide_index=True)
            else:
                st.info("Données non disponibles.")
                
        else:
            st.markdown('<div class="section-header">📑 Détail Mensuel (Compte de Résultat & BFR)</div>', unsafe_allow_html=True)
            if not cr.empty:
                df_detail = cr.copy()
                df_detail["Période"] = df_detail["Mois"].dt.strftime("%b %Y").str.title()
                df_detail["Marge Brute"] = df_detail["CA"] - df_detail["Achats"]
                df_detail["Marge Nette"] = (df_detail["Resultat_Net"] / df_detail["CA"].replace(0, np.nan) * 100).fillna(0)
                
                df_disp = pd.DataFrame()
                df_disp["Période"] = df_detail["Période"]
                df_disp["CA"] = df_detail["CA"].apply(lambda x: f"{x:,.0f} €".replace(",", "\u202f"))
                df_disp["Marge Brute"] = df_detail["Marge Brute"].apply(lambda x: f"{x:,.0f} €".replace(",", "\u202f"))
                df_disp["Marge Nette"] = df_detail["Marge Nette"].apply(lambda x: f"{x:,.2f} %")
                
                bfr_col = df_detail["BFR"] if "BFR" in df_detail.columns else pd.Series([0]*len(df_detail))
                df_disp["BFR"] = bfr_col.apply(lambda x: f"{x:,.0f} €".replace(",", "\u202f"))
                
                df_disp["Résultat Net"] = df_detail["Resultat_Net"].apply(lambda x: f"{x:,.0f} €".replace(",", "\u202f"))
                
                st.dataframe(df_disp, use_container_width=True, hide_index=True)
            else:
                st.info("Les données mensuelles ne sont pas disponibles pour générer ce tableau.")
            
    with t3:
        for a in alerts:
            cls = "alert-critical" if a["level"]=="critical" else "alert-warning" if a["level"]=="warning" else "alert-info"
            st.markdown(f'<div class="alert-card {cls}"><div class="alert-icon">{a["icon"]}</div><div><div class="alert-title">{a["title"]}</div><div class="alert-body">{a["body"]}</div></div></div>', unsafe_allow_html=True)
            
    with t4:
        if _GEMINI_AVAILABLE and _GEMINI_API_KEY:
            _render_chat_tab(cr, bilan, scores, alerts, app_mode, exercice, raw_pdf)
        else:
            st.warning("⚠️ L'Assistant IA ARIS nécessite une clé API valide. Vous pouvez configurer votre clé dans les variables d'environnement.")

if __name__ == "__main__":
    main()