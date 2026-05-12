# -*- coding: utf-8 -*-
"""Fabriques de graphiques Plotly partagées par les pages BV / AAV."""

from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from .style import (NAVY, ACCENT, RED, ORANGE, GREEN, MUTED, GRID,
                    SCALE_DENSITE)

# Centre approximatif de la France métropolitaine
FRANCE_CENTER = {"lat": 46.6, "lon": 2.5}
FRANCE_ZOOM = 4.7


def _bbox_zoom(df: pd.DataFrame, lat_col: str = "lat", lon_col: str = "lon"):
    """Renvoie (center, zoom) adaptés à la bounding box des points fournis.

    On garde la vue France métropolitaine par défaut. Le zoom auto ne se
    déclenche que si la sélection est suffisamment petite (≤ 200 zones) et
    contenue dans la métropole — sinon les DOM tirent la box trop large.
    """
    d = df.dropna(subset=[lat_col, lon_col])
    if len(d) < 2 or len(d) > 200:
        return FRANCE_CENTER, FRANCE_ZOOM
    # Filtre métropole : lat dans [41, 52], lon dans [-5, 10]
    d = d[(d[lat_col].between(41, 52)) & (d[lon_col].between(-5, 10))]
    if len(d) < 2:
        return FRANCE_CENTER, FRANCE_ZOOM
    lat_span = d[lat_col].max() - d[lat_col].min()
    lon_span = d[lon_col].max() - d[lon_col].min()
    if lat_span > 8.0 or lon_span > 12.0:
        return FRANCE_CENTER, FRANCE_ZOOM
    span = max(lat_span, lon_span * 0.7)
    zoom = max(4.7, min(8.5, 4.7 + np.log2(11.0 / max(span, 0.5))))
    center = {"lat": float(d[lat_col].mean()), "lon": float(d[lon_col].mean())}
    return center, zoom

_STAT_COLOR = {"Désert": RED, "Tension": ORANGE, "OK": GREEN}


# ─────────────────────────── CARTES ───────────────────────────

def carte_choropleth(df: pd.DataFrame, geojson: dict, code_col: str,
                      lib_col: str, code_key: str,
                      densite_max: float = 15.0) -> go.Figure:
    """Carte choroplèthe densité ophtalmologistes / 100 000 hab.

    Deux traces superposées :
      1. Zones à 0 ophtalmologue → couleur uniforme noire (lisible distinctement).
      2. Zones à densité > 0 → dégradé rouge → vert plafonné à `densite_max`.
    """
    d = df.copy()
    d["densite_lbl"] = d["densite_100k"].round(2)
    d["pop_lbl"]     = (d["population"] / 1000).round(1)
    d["etp_lbl"]     = d["nb_docteurs_pondere"].round(2)

    # Split zones à 0 vs > 0
    zero = d[d["densite_100k"] <= 0.001].copy()
    pos  = d[d["densite_100k"]  > 0.001].copy()
    pos["densite_aff"] = np.clip(pos["densite_100k"], 0.001, densite_max)

    fig = go.Figure()

    # Trace 1 : zones à 0 ophtalmo — rouge écarlate vif, couleur unique
    if len(zero) > 0:
        cust0 = np.stack([zero[lib_col], zero["pop_lbl"], zero["statut"]], axis=1)
        fig.add_trace(go.Choroplethmap(
            geojson=geojson,
            locations=zero[code_col],
            z=[1]*len(zero),
            zmin=0, zmax=1,
            featureidkey=f"properties.{code_key}",
            colorscale=[[0, "#E11D2A"], [1, "#E11D2A"]],
            showscale=False,
            marker_line_color="rgba(255,255,255,0.7)",
            marker_line_width=0.4,
            name="Aucun ophtalmologue",
            customdata=cust0,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Aucun ophtalmologue recensé<br>"
                "Population : %{customdata[1]:.1f} k hab.<br>"
                "Statut : %{customdata[2]}<extra></extra>"
            ),
        ))

    # Trace 2 : zones avec praticien(s) — gradient densité
    if len(pos) > 0:
        cust = np.stack([pos[lib_col], pos["densite_lbl"], pos["pop_lbl"], pos["etp_lbl"], pos["statut"]], axis=1)
        fig.add_trace(go.Choroplethmap(
            geojson=geojson,
            locations=pos[code_col],
            z=pos["densite_aff"],
            featureidkey=f"properties.{code_key}",
            colorscale=SCALE_DENSITE,
            zmin=0.001, zmax=densite_max,
            marker_line_color="rgba(255,255,255,0.45)",
            marker_line_width=0.25,
            colorbar=dict(
                title=dict(text="oph / 100k hab.", font=dict(size=11)),
                tickfont=dict(size=10),
                len=0.65, thickness=14, x=0.99,
            ),
            name="Densité",
            customdata=cust,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Densité : <b>%{customdata[1]:.2f}</b> oph/100k<br>"
                "Population : %{customdata[2]:.1f} k hab.<br>"
                "ETP ophtalmos : %{customdata[3]:.2f}<br>"
                "Statut : %{customdata[4]}<extra></extra>"
            ),
        ))

    center, zoom = _bbox_zoom(d)
    fig.update_layout(
        map_style="carto-positron",
        map_center=center,
        map_zoom=zoom,
        margin=dict(t=10, b=10, l=10, r=10),
        height=620,
        font=dict(family="Inter, Helvetica, Arial", color=NAVY),
        paper_bgcolor="white",
        showlegend=False,
    )
    return fig


def carte_heatmap(df: pd.DataFrame, lat_col: str = "lat", lon_col: str = "lon",
                   pop_col: str = "population", densite_col: str = "densite_100k",
                   densite_ref: float = 12.0,
                   mode: str = "manque") -> go.Figure:
    """Heatmap = densité lissée par noyau gaussien.

    Chaque zone est plottée à son centroïde et pondérée par son **manque**
    d'ophtalmologistes, avec une intensité quadratique :

        poids = max(densite_ref − densité, 0) ** 2

    L'exposant 2 fait sortir nettement les zones à 0 ophtalmologue :
        - densité 0 et densite_ref=12  → poids 144
        - densité 6                     → poids  36
        - densité 9                     → poids   9
        - densité ≥ densite_ref         → poids   0

    Le paramètre `densite_ref` est piloté par le curseur de la sidebar :
    plus il est élevé, plus de zones contribuent au rendu (heatmap moins
    sélective). Plus il est bas, seules les zones les plus sous-dotées
    ressortent.
    """
    d = df.dropna(subset=[lat_col, lon_col]).copy()
    d = d[d[pop_col] > 0]

    manque = np.clip(densite_ref - d[densite_col].values, 0.0, densite_ref)
    poids = manque ** 2

    titre = (f"Tension lissée<br>"
             f"(seuil de référence : <b>{densite_ref:.1f}</b> oph/100k)")
    # Échelle blanc transparent → écarlate vif → bordeaux.
    # Saturation accélérée : dès 25 % du max, on est déjà en rouge vif —
    # cela fait ressortir les zones à 0 ophtalmologue plutôt que de noyer
    # tout le territoire dans un dégradé pâle.
    scale = [
        [0.00, "rgba(255,255,255,0)"],
        [0.04, "#FEE7E3"],
        [0.12, "#F4A89F"],
        [0.25, "#EE7466"],
        [0.45, "#E94B3C"],
        [0.70, "#E11D2A"],
        [1.00, "#9C0E18"],
    ]
    # Rayon ajusté en fonction du seuil : plus le seuil est bas, moins de
    # zones contribuent → on resserre le noyau pour conserver de la
    # localisation sur les points actifs.
    radius = int(np.clip(12 + densite_ref, 16, 30))

    # zmax explicite : la pondération étant quadratique, le poids max
    # théorique vaut densite_ref². On fixe zmax au poids cumulé attendu
    # autour d'un point à 0 ophtalmo, ce qui rend la saturation du
    # rendu indépendante du seuil choisi par l'utilisateur.
    zmax = float(densite_ref ** 2) * 1.2

    fig = go.Figure(go.Densitymap(
        lat=d[lat_col].astype(float).tolist(),
        lon=d[lon_col].astype(float).tolist(),
        z=poids.tolist() if hasattr(poids, "tolist") else list(poids),
        radius=radius,
        zmin=0, zmax=zmax,
        colorscale=scale,
        opacity=0.82,
        colorbar=dict(title=dict(text=titre, font=dict(size=11)),
                       tickfont=dict(size=10), len=0.55, thickness=14, x=0.99),
        hovertemplate=("lat %{lat:.2f} · lon %{lon:.2f}<br>poids : %{z:,.0f}<extra></extra>"),
    ))
    center, zoom = _bbox_zoom(d)
    fig.update_layout(
        map_style="carto-positron",
        map_center=center,
        map_zoom=zoom,
        margin=dict(t=10, b=10, l=10, r=10),
        height=620,
        font=dict(family="Inter, Helvetica, Arial", color=NAVY),
        paper_bgcolor="white",
    )
    return fig


# ─────────────────────────── HISTOGRAMME K-MEANS ───────────────────────────

def histogramme_kmeans(df: pd.DataFrame, F12: float, F23: float, centres: list,
                       label_zones: str = "zones",
                       densite_max: float = 30.0) -> go.Figure:
    """Distribution coloriée par statut, avec frontières K-means.

    Les zones à densité = 0 sont affichées dans une barre hachée à part
    (l'axe Y est tronqué à la hauteur maximale des bins > 0 afin de
    préserver la lisibilité de la distribution).
    """
    n_zero = int((df["densite_100k"] <= 0.001).sum())
    df_pos = df[df["densite_100k"] > 0.001].copy()

    # Calcul manuel des hauteurs de bins > 0 pour déterminer le plafond Y
    bin_size = densite_max / 60.0
    bins = np.arange(0, densite_max + bin_size, bin_size)
    y_pos_counts = np.histogram(
        df_pos["densite_100k"].clip(0, densite_max).values, bins=bins
    )[0]
    y_max_pos = int(y_pos_counts.max()) if len(y_pos_counts) else 1
    y_cap = int(y_max_pos * 1.25)  # marge pour annotation

    fig = go.Figure()

    # Barre Désert pour les zones à densité = 0 — hauteur tronquée + annotation
    if n_zero > 0:
        bar_h = min(n_zero, int(y_max_pos * 1.15))   # cap visuel
        fig.add_trace(go.Bar(
            x=[0.0],
            y=[bar_h],
            width=[bin_size * 0.95],
            marker=dict(color=RED),
            opacity=0.92,
            name=f"0 ophtalmologue (n = {n_zero})",
            hovertemplate=(
                f"<b>{n_zero} {label_zones} à 0 ophtalmologue</b><br>"
                "(barre tronquée à l'échelle)<extra></extra>"
            ),
        ))
        # Étiquette de l'effectif réel au-dessus de la barre
        fig.add_annotation(
            x=0, y=bar_h, text=f"<b>{n_zero}</b>",
            showarrow=False, yshift=10,
            font=dict(size=12, color=RED),
        )

    for stat in ["Désert", "Tension", "OK"]:
        sub = df_pos[df_pos["statut"] == stat]
        fig.add_trace(go.Histogram(
            x=sub["densite_100k"].clip(0, densite_max),
            xbins=dict(start=bin_size, end=densite_max, size=bin_size),
            marker=dict(color=_STAT_COLOR[stat]),
            opacity=0.92,
            name=stat,
            hovertemplate=(stat + "<br>densité : %{x:.1f}<br>nb " + label_zones + " : %{y}<extra></extra>"),
        ))

    # Frontières + centroïdes
    for x, lab in [(F12, f"F₁₂ = {F12:.2f}"), (F23, f"F₂₃ = {F23:.2f}")]:
        fig.add_vline(x=x, line=dict(color=NAVY, width=1.4, dash="dot"))
        fig.add_annotation(x=x, y=1.02, yref="paper",
                            text=lab, showarrow=False,
                            font=dict(size=11, color=NAVY))
    for c, lab in zip(centres, ["μ₁", "μ₂", "μ₃"]):
        fig.add_annotation(x=c, y=-0.02, yref="paper",
                            text=lab, showarrow=False,
                            font=dict(size=12, color=NAVY, family="serif"))

    fig.update_layout(
        barmode="stack", bargap=0.0,
        height=380, margin=dict(t=30, l=10, r=10, b=30),
        xaxis=dict(title="Densité (ophtalmologistes / 100 000 hab.)",
                   gridcolor=GRID, zeroline=False,
                   range=[-bin_size, densite_max + 0.5]),
        yaxis=dict(title="Nombre de " + label_zones, gridcolor=GRID, zeroline=False,
                   range=[0, y_cap]),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, Helvetica, Arial", color=NAVY, size=12),
        legend=dict(orientation="h", y=1.14, x=0.0, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


# ─────────────────────────── RÉPARTITION (zones vs pop) ───────────────────────────

def barre_zones_vs_pop(synthese: pd.DataFrame, label_zone: str = "zones") -> go.Figure:
    """Deux barres empilées 100% : % zones vs % population, par statut."""
    fig = go.Figure()
    for stat in ["Désert", "Tension", "OK"]:
        row = synthese[synthese["Statut"] == stat].iloc[0]
        fig.add_trace(go.Bar(
            x=[row["% zones"], row["% pop"]],
            y=[f"% {label_zone}", "% population"],
            orientation="h",
            marker=dict(color=_STAT_COLOR[stat]),
            name=stat,
            text=[f"{row['% zones']:.1f} %", f"{row['% pop']:.1f} %"],
            textposition="inside",
            textfont=dict(color="white", size=12),
            hovertemplate=(stat + "<br>%{y} : %{x:.1f} %<extra></extra>"),
        ))
    fig.update_layout(
        barmode="stack",
        height=180, margin=dict(t=10, b=10, l=10, r=10),
        xaxis=dict(showticklabels=False, range=[0, 100]),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, Helvetica, Arial", color=NAVY, size=12),
        legend=dict(orientation="h", y=1.35, x=0.0, bgcolor="rgba(0,0,0,0)"),
        showlegend=True,
    )
    return fig


# ─────────────────────────── COMPARATIF RÉGIONS ───────────────────────────

def barres_regions(df: pd.DataFrame, n: int = 18) -> go.Figure:
    """Barres horizontales : densité régionale (pondérée par pop), triées."""
    reg = (df.groupby("region")
              .agg(ETP=("nb_docteurs_pondere", "sum"),
                   pop=("population", "sum"))
              .assign(densite=lambda x: x["ETP"] / x["pop"] * 1e5)
              .sort_values("densite"))
    reg = reg[reg["pop"] > 0].head(n)
    colors = [RED if v < 4 else ORANGE if v < 7 else GREEN for v in reg["densite"]]

    fig = go.Figure(go.Bar(
        x=reg["densite"], y=reg.index, orientation="h",
        marker=dict(color=colors),
        text=[f"{v:.2f}" for v in reg["densite"]],
        textposition="outside",
        hovertemplate=("<b>%{y}</b><br>Densité : %{x:.2f} oph/100k<extra></extra>"),
    ))
    fig.add_vline(x=df["nb_docteurs_pondere"].sum() / df["population"].sum() * 1e5,
                  line=dict(color=NAVY, width=1.4, dash="dot"))
    fig.update_layout(
        height=max(280, 28 * len(reg)),
        margin=dict(t=20, l=10, r=30, b=10),
        xaxis=dict(title="Densité (oph / 100 000 hab.)", gridcolor=GRID, zeroline=False),
        yaxis=dict(title="", gridcolor=GRID),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter, Helvetica, Arial", color=NAVY, size=12),
        showlegend=False,
    )
    return fig
