# -*- coding: utf-8 -*-
"""Page d'accueil — minimaliste : pitch + 4 KPI + 3 entrées vers les pages."""

import streamlit as st

from lib.loaders import load_bv
from lib.compute import kmeans_3
from lib.ui import inject_css, footer

NB_OPHTALMOS_UNIQUES = 4479


st.set_page_config(
    page_title="Déserts ophtalmologiques — Dashboard L2",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()


# ───── Titre ─────

st.markdown("# Déserts ophtalmologiques en France")
st.caption(
    "Livrable 2 du Data Challenge 2026 · Master 1 Actuariat (SARADS) · 12 mai 2026"
)

st.markdown(
    "Cartographie interactive de l'accès à l'ophtalmologie en France, "
    "vue d'un assureur santé : où l'offre est-elle insuffisante, "
    "combien d'assurés sont concernés, et avec quelle intensité."
)


# ───── Chiffres-clés ─────

bv  = load_bv()
km_bv = kmeans_3(bv)
nb_desert = int((km_bv.df["statut"] == "Désert").sum())
pop_desert = km_bv.df[km_bv.df["statut"] == "Désert"]["population"].sum()
n_pop = bv["population"].sum()
n_etp = bv["nb_docteurs_pondere"].sum()
ratio_1_pour = int(round(n_pop / NB_OPHTALMOS_UNIQUES))

st.markdown("### Chiffres-clés (France entière)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ophtalmologistes uniques",
           f"{NB_OPHTALMOS_UNIQUES:,}".replace(",", " "),
           help="Décompte sur l'annuaire santé Ameli filtré sur la spécialité, "
                 "clé nom + prénom + civilité.")
c2.metric("Densité nationale",
           f"{n_etp / n_pop * 1e5:.2f}".replace(".", ","),
           help="Ophtalmologistes pour 100 000 habitants.")
c3.metric("1 ophtalmologiste pour…",
           f"{ratio_1_pour:,}".replace(",", " ") + " hab.",
           help="Inverse de la densité. Plus la valeur est élevée, plus l'accès est contraint.")
c4.metric("Population en désert",
           f"{pop_desert / 1e6:.1f} M".replace(".", ","),
           f"{pop_desert / n_pop * 100:.1f} %".replace(".", ","),
           delta_color="off",
           help=f"Habitants vivant dans un Bassin de Vie dont la densité est "
                 f"inférieure à F₁₂ = {km_bv.F12:.2f} oph/100k (classification K-means).")


# ───── Trois entrées vers les pages ─────

st.write("")
st.markdown("---")
st.write("")

c1, c2, c3 = st.columns(3, gap="large")
with c1:
    st.markdown("### Maille Bassin de Vie")
    st.markdown(
        "1 708 zones, ~40 000 habitants en moyenne.  \n"
        "Maille fine pour le diagnostic territorial."
    )
    st.page_link("pages/1_Bassins_de_Vie.py", label="Ouvrir l'analyse BV")

with c2:
    st.markdown("### Maille Aire d'Attraction")
    st.markdown(
        "699 zones, ~95 000 habitants en moyenne.  \n"
        "Maille large pour la lecture stratégique."
    )
    st.page_link("pages/2_Aires_d_Attraction.py", label="Ouvrir l'analyse AAV")

with c3:
    st.markdown("### Méthodes & formules")
    st.markdown(
        "Détail des KPI, exemples chiffrés,  \n"
        "justification du K-means pondéré."
    )
    st.page_link("pages/3_Methodes_et_formules.py", label="Ouvrir les méthodes")


# ───── Sources, en bas de page ─────

st.write("")
st.markdown("---")
st.markdown(
    "**Sources**  ·  Annuaire santé Ameli (data.gouv.fr) — offre ; "
    "Recensement INSEE 2023 — demande ; Bassin de Vie 2022 et Aire d'Attraction 2020 "
    "(INSEE) — maille ; data.gouv.fr et geocodage-spd — référentiels CP / CEDEX. "
    "**Périmètre** : ophtalmologie uniquement."
)

footer()
