# -*- coding: utf-8 -*-
"""Logique partagée pour les deux pages BV et AAV.

La structure est strictement identique : on factorise tout ici et chaque
page se contente de passer la maille (« BV » ou « AAV ») et ses spécificités.
"""

from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import streamlit as st

from .compute import kmeans_3, synthese_par_statut, fmt_int, fmt_float
from . import viz
from .ui import inject_css, footer

# Effectif d'ophtalmologistes uniques (clé nom + prénom + civilité), constant
# pour les deux mailles — c'est la statistique de référence pour communiquer.
NB_OPHTALMOS_UNIQUES = 4479


@dataclass
class MailleSpec:
    nom_long: str          # ex. "Bassin de Vie"
    nom_court: str         # ex. "BV"
    code_col: str          # ex. "bv2022"
    code_label: str        # ex. "Code BV"
    code_key_geojson: str  # ex. "bv2022"
    df_loader: callable
    geojson_loader: callable
    description: str       # bref pitch en haut de la page
    warning: str = ""      # bandeau d'alerte visible (optionnel)


def _ratio_1_pour_x(pop: float, nb: float) -> str:
    """Formate '1 ophtalmologiste pour X habitants'."""
    if nb <= 0:
        return "—"
    x = int(round(pop / nb))
    return f"1 pour {x:,}".replace(",", " ")


def render(spec: MailleSpec):
    st.set_page_config(
        page_title=f"{spec.nom_long} — Dashboard L2",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()

    # ─── HEADER ───
    st.markdown(f"# {spec.nom_long}")
    st.caption(spec.description)
    if spec.warning:
        st.warning(spec.warning)

    # ─── CHARGEMENT ───
    df_full = spec.df_loader()
    geojson = spec.geojson_loader()

    # ─── SIDEBAR : filtres ───
    st.sidebar.header("Filtres")
    regions_dispo = sorted(df_full["region"].dropna().unique().tolist())
    regions_sel = st.sidebar.multiselect(
        "Région(s)", regions_dispo, default=[],
        help="Filtre toutes les visualisations. Vide = France entière.",
    )

    only_zero = st.sidebar.checkbox(
        f"Afficher uniquement les {spec.nom_court} à 0 ophtalmologue", value=False,
        help="Sous-ensemble des déserts purs (aucun praticien recensé).",
    )

    densite_max_carte = st.sidebar.number_input(
        "Seuil de référence (oph/100k)",
        min_value=2.0, max_value=40.0, value=12.0, step=0.1, format="%.1f",
        help="Pilote les deux cartes :\n"
              "• **Choroplèthe** : plafonne l'échelle de couleur (les valeurs "
              "au-delà sont colorées au max).\n"
              "• **Heatmap** : sert de seuil de référence pour le poids du "
              "manque. Plus la valeur est élevée, plus de zones contribuent "
              "à la chaleur ; plus elle est basse, seules les zones les plus "
              "sous-dotées ressortent.",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"**{len(df_full)} {spec.nom_court}** dans la base V4  ·  "
        f"**{df_full['population'].sum()/1e6:.1f} M** habitants couverts  ·  "
        f"**{NB_OPHTALMOS_UNIQUES:,}**".replace(",", " ") +
        " ophtalmologistes uniques."
    )

    # Filtre appliqué pour les visualisations
    df = df_full.copy()
    if regions_sel:
        df = df[df["region"].isin(regions_sel)]
    if only_zero:
        df = df[df["nb_docteurs_pondere"] == 0]

    if len(df) == 0:
        st.warning("Aucune zone ne correspond aux filtres sélectionnés.")
        footer()
        return

    # K-means : calcul sur la base **complète** (référentiel stable des seuils)
    # puis report du statut sur la sélection filtrée.
    km = kmeans_3(df_full)
    df = df.merge(km.df[[spec.code_col, "statut"]], on=spec.code_col, how="left")

    # ─── KPI STRIP ───
    n_zones = len(df)
    n_pop   = df["population"].sum()
    n_etp   = df["nb_docteurs_pondere"].sum()
    dens_moy = (n_etp / n_pop * 1e5) if n_pop else 0.0
    n_zero  = int((df["nb_docteurs_pondere"] == 0).sum())
    nb_desert = int((df["statut"] == "Désert").sum())
    pop_desert = df[df["statut"] == "Désert"]["population"].sum()

    # KPI nb ophtalmos = 4 479 si la sélection couvre toute la France ;
    # sinon, l'effectif unique sur la sélection est inconnu (les doctors
    # uniques sont multi-zones par construction), on affiche l'ETP arrondi.
    sel_globale = (not regions_sel and not only_zero)
    nb_ophtalmos_aff = (fmt_int(NB_OPHTALMOS_UNIQUES) if sel_globale
                         else f"{n_etp:.1f}".replace(".", ","))
    nb_ophtalmos_label = ("Ophtalmologistes uniques" if sel_globale
                          else f"Ophtalmologistes (ETP, somme 1/N)")
    nb_ophtalmos_help = (
        "Décompte sur la clé nom + prénom + civilité (annuaire santé Ameli "
        "filtré sur la spécialité ophtalmologie)."
        if sel_globale else
        "Sur la sélection : somme des pondérations 1/N par lieu d'exercice. "
        "Un praticien partagé entre la sélection et le reste de la France ne "
        "compte qu'une fraction de son activité ici."
    )

    st.markdown("### Chiffres-clés")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{spec.nom_court} dans la sélection", fmt_int(n_zones),
                help="Nombre de zones après application des filtres latéraux.")
    c2.metric("Population couverte", f"{n_pop/1e6:.2f} M".replace(".", ","),
                help="Somme des populations municipales INSEE 2023.")
    c3.metric(nb_ophtalmos_label, nb_ophtalmos_aff, help=nb_ophtalmos_help)
    c4.metric("1 ophtalmologiste pour…", _ratio_1_pour_x(n_pop, n_etp),
                help="Inverse de la densité : population / ETP. National = "
                      "1 ophtalmologiste pour ≈ 15 200 habitants.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Densité (oph / 100k)", fmt_float(dens_moy, 2),
                help="ETP × 100 000 / population. National = 6,56.")
    c2.metric(f"{spec.nom_court} en désert (K-means)", fmt_int(nb_desert),
                help=f"Densité inférieure à F₁₂ = {km.F12:.2f} oph/100k — "
                      "frontière issue du K-means pondéré (voir page Méthodes).")
    c3.metric("Population concernée",
                f"{pop_desert/1e6:.2f} M".replace(".", ","),
                f"{pop_desert/n_pop*100:.1f} %".replace(".", ","),
                delta_color="off",
                help="Habitants dans les zones classées Désert.")
    c4.metric(f"{spec.nom_court} à 0 ophtalmologue", fmt_int(n_zero),
                f"{n_zero/n_zones*100:.0f} %",
                delta_color="off",
                help="Aucun ETP recensé — désert pur, distinguées en noir sur la carte.")

    # ─── CARTE INTERACTIVE ───
    st.markdown(f"## Cartographie de la densité")

    c_opts, c_map = st.columns([1, 4])
    with c_opts:
        mode = st.radio(
            "Affichage",
            options=["Choroplèthe", "Heatmap tension"],
            index=0,
            help=(
                "**Choroplèthe** : densité par zone (noir = aucun ophtalmologue).\n"
                "**Heatmap tension** : noyaux gaussiens sur les centroïdes des "
                "zones Désert/Tension, pondérés par la population. Lecture "
                "côté assuré : où l'absence d'offre concerne le plus de monde."
            ),
        )
        st.markdown("---")
        st.caption(
            "Survol : libellé + densité + ETP. Zoom à la molette, panoramique "
            "au clic-glissé. Les données respectent les filtres latéraux."
        )
    with c_map:
        if mode == "Choroplèthe":
            fig = viz.carte_choropleth(
                df,
                geojson=geojson,
                code_col=spec.code_col, lib_col="libelle",
                code_key=spec.code_key_geojson,
                densite_max=densite_max_carte,
            )
        else:
            fig = viz.carte_heatmap(df, densite_ref=densite_max_carte)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    st.caption(
        "**Lecture.** La choroplèthe affiche la densité zone par zone. La "
        "heatmap est sa version lissée par noyau gaussien : chaque zone est "
        "pondérée par le carré de son manque d'offre par rapport au seuil "
        "de référence (curseur latéral). Les zones à 0 ophtalmologue "
        "contribuent ainsi 4× plus que les zones à mi-distance du seuil, "
        "ce qui les fait ressortir nettement en rouge écarlate."
    )

    # ─── HISTOGRAMME K-MEANS ───
    st.markdown("## Typologie K-means — Désert / Tension / OK")
    st.markdown(
        f"K-means pondéré (k=3) appliqué à la densité, poids = population. "
        f"Frontières issues des données : "
        f"**F₁₂ = {km.F12:.2f}**, **F₂₃ = {km.F23:.2f}**, "
        f"centroïdes μ₁ = {km.centres[0]:.2f}, μ₂ = {km.centres[1]:.2f}, "
        f"μ₃ = {km.centres[2]:.2f}."
    )

    c1, c2 = st.columns([1.55, 1])
    with c1:
        st.plotly_chart(
            viz.histogramme_kmeans(km.df, km.F12, km.F23, km.centres,
                                     label_zones=spec.nom_court),
            use_container_width=True, config={"displaylogo": False},
        )
    with c2:
        syn = synthese_par_statut(km.df, spec.code_col)
        st.plotly_chart(viz.barre_zones_vs_pop(syn, label_zone=spec.nom_court.lower() + "s"),
                         use_container_width=True, config={"displaylogo": False})

        st.markdown("**Synthèse par statut**")
        tbl = syn.assign(**{
            "Zones": syn["nb_zones"].astype(int),
            "% zones": syn["% zones"].round(1).astype(str) + " %",
            "Pop (M)": (syn["pop"] / 1e6).round(2),
            "% pop":   syn["% pop"].round(1).astype(str) + " %",
            "ETP":     syn["ETP"].round(1),
            "Densité": syn["densité moy. (oph/100k)"].round(2),
        })[["Statut", "Zones", "% zones", "Pop (M)", "% pop", "ETP", "Densité"]]
        st.dataframe(tbl, hide_index=True, use_container_width=True,
                      column_config={
                          "Densité": st.column_config.NumberColumn(
                              "Densité", help="ETP × 100 000 / population — densité moyenne pondérée par statut",
                              format="%.2f"),
                      })

    # ─── COMPARATIF RÉGIONS ───
    st.markdown("## Densité moyenne par région")
    st.plotly_chart(viz.barres_regions(df_full), use_container_width=True,
                     config={"displaylogo": False})
    st.caption(
        "Densité pondérée par la population de chaque région. Ligne pointillée "
        "verticale = densité nationale. Code couleur : vert ≥ 7 · orange 4–7 · "
        "rouge < 4 oph / 100 000 hab."
    )

    # ─── CLASSEMENT ───
    st.markdown(f"## Classement des {spec.nom_court} — accès le plus contraint")

    df_class = (df[df["population"] >= 5000]
                   .sort_values("densite_100k")
                   .head(30))

    tab1, tab2 = st.tabs([f"Top 30 — les plus en tension", "Tableau complet (filtrable)"])

    with tab1:
        st.caption("Zones de plus de 5 000 habitants, classées par densité croissante.")
        cols_show = [spec.code_col, "libelle", "region", "population",
                     "nb_docteurs_pondere", "densite_100k", "statut"]
        st.dataframe(
            df_class[cols_show].assign(
                population=df_class["population"].astype(int),
                nb_docteurs_pondere=df_class["nb_docteurs_pondere"].round(2),
                densite_100k=df_class["densite_100k"].round(2),
            ).rename(columns={
                spec.code_col: spec.code_label,
                "libelle": f"Libellé {spec.nom_court}",
                "region": "Région",
                "population": "Population",
                "nb_docteurs_pondere": "ETP",
                "densite_100k": "Densité /100k",
                "statut": "Statut",
            }),
            hide_index=True, use_container_width=True, height=500,
        )

    with tab2:
        cols_show = [spec.code_col, "libelle", "region", "dep", "population",
                     "nb_docteurs_pondere", "densite_100k", "statut"]
        st.dataframe(
            df[cols_show].sort_values("densite_100k").assign(
                population=df["population"].astype(int),
                nb_docteurs_pondere=df["nb_docteurs_pondere"].round(2),
                densite_100k=df["densite_100k"].round(2),
            ).rename(columns={
                spec.code_col: spec.code_label,
                "libelle": f"Libellé {spec.nom_court}",
                "region": "Région",
                "dep": "Dép.",
                "population": "Population",
                "nb_docteurs_pondere": "ETP",
                "densite_100k": "Densité /100k",
                "statut": "Statut",
            }),
            hide_index=True, use_container_width=True, height=520,
        )
        csv = df[cols_show].to_csv(index=False, sep=";").encode("utf-8")
        st.download_button(
            f"Télécharger le tableau ({len(df)} {spec.nom_court}, CSV)",
            data=csv,
            file_name=f"dashboard_L2_{spec.nom_court.lower()}.csv",
            mime="text/csv",
        )

    st.caption(
        f"Base utilisée : `docteurs_ophtalmo_v4"
        f"{'_aav' if spec.nom_court=='AAV' else ''}.csv` "
        f"({len(df_full)} {spec.nom_court}). "
        f"Le détail des formules et un exemple chiffré pour chaque KPI sont "
        f"sur la page **Méthodes & formules**."
    )

    footer()
