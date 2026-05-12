# -*- coding: utf-8 -*-
"""Palette et CSS partagés du dashboard."""

# Palette « Midnight Executive » revisitée pour l'angle assureur
NAVY    = "#1F2A44"   # texte titres, axes
ACCENT  = "#3B5998"   # accent principal (CTA, sliders)
DEEP    = "#0E1A33"   # bandeau header
SAND    = "#F4F6FB"   # background secondaire
WHITE   = "#FFFFFF"
GRID    = "#E5E7EB"
MUTED   = "#6B7280"

# Statut désert / tension / OK
RED     = "#C0392B"
ORANGE  = "#F59E0B"
GREEN   = "#1F8F5E"

# Échelles de densité (continues)
SCALE_DENSITE = [
    [0.00, "#7B1A12"],   # rouge foncé — désert profond
    [0.15, "#C0392B"],
    [0.30, "#E8743C"],
    [0.45, "#F4B266"],
    [0.60, "#FFE08A"],
    [0.75, "#A8D5A2"],
    [0.90, "#3FA66A"],
    [1.00, "#0F5C2E"],   # vert foncé — bien doté
]

# CSS injecté pour soigner l'apparence
CSS = """
<style>
  :root {
    --navy: #1F2A44;
    --accent: #3B5998;
    --deep: #0E1A33;
    --sand: #F4F6FB;
    --muted: #6B7280;
    --grid: #E5E7EB;
  }
  /* en-tête streamlit pleine largeur */
  .block-container { padding-top: 1.5rem !important; padding-bottom: 3rem; max-width: 1400px; }
  h1, h2, h3 { color: var(--navy); font-weight: 700; letter-spacing: -0.01em; }
  h1 { font-size: 2.0rem !important; }
  h2 { font-size: 1.45rem !important; margin-top: 1.8rem !important; border-bottom: 1px solid var(--grid); padding-bottom: 0.35rem; }
  h3 { font-size: 1.10rem !important; color: var(--accent); }

  /* Header bandeau */
  .hero {
    background: linear-gradient(120deg, var(--deep) 0%, var(--navy) 50%, var(--accent) 100%);
    color: white; padding: 1.6rem 1.8rem; border-radius: 12px; margin-bottom: 1.6rem;
    box-shadow: 0 4px 18px rgba(15, 26, 51, 0.18);
  }
  .hero h1 { color: white !important; margin: 0 0 0.5rem 0; font-size: 1.85rem !important; }
  .hero .subtitle { color: #C9D3E8; font-size: 1.0rem; max-width: 850px; }
  .hero .meta { color: #94A3C2; font-size: 0.82rem; margin-top: 0.7rem; letter-spacing: 0.04em; text-transform: uppercase;}

  /* Cartes KPI */
  .kpi {
    background: white; border: 1px solid var(--grid); border-radius: 10px;
    padding: 1rem 1.1rem 0.9rem 1.1rem; height: 100%;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  }
  .kpi .label { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; }
  .kpi .value { color: var(--navy); font-size: 1.9rem; font-weight: 800; margin: 0.18rem 0 0.25rem 0; line-height: 1.05; }
  .kpi .help  { color: var(--muted); font-size: 0.78rem; line-height: 1.35; }
  .kpi.accent  { border-top: 4px solid var(--accent); }
  .kpi.red     { border-top: 4px solid #C0392B; }
  .kpi.orange  { border-top: 4px solid #F59E0B; }
  .kpi.green   { border-top: 4px solid #1F8F5E; }

  /* Tableaux */
  .stDataFrame { border-radius: 8px; border: 1px solid var(--grid); }

  /* Citations encadrées */
  .pull {
    background: var(--sand); border-left: 3px solid var(--accent); padding: 0.9rem 1.1rem;
    border-radius: 6px; margin: 0.6rem 0 1.2rem 0; color: var(--navy); font-style: italic;
  }

  /* Footer */
  .footer { color: var(--muted); font-size: 0.75rem; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid var(--grid); }

  /* Cache les éléments par défaut */
  #MainMenu, footer, header { visibility: hidden; }
  [data-testid="stToolbar"] { display: none; }

  /* Pills */
  .pill { display: inline-block; padding: 0.18rem 0.55rem; border-radius: 999px; font-size: 0.72rem;
          font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; }
  .pill.red    { background: #FBE3DF; color: #7B1A12; }
  .pill.orange { background: #FEF1D6; color: #8C6315; }
  .pill.green  { background: #DBF0E1; color: #15532E; }
</style>
"""
