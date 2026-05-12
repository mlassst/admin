# -*- coding: utf-8 -*-
"""Page Méthodes & formules — pédagogique, avec un exemple chiffré pour chaque KPI."""

import streamlit as st

from lib.ui import inject_css, footer
from lib.loaders import load_bv, load_aav
from lib.compute import kmeans_3


st.set_page_config(
    page_title="Méthodes & formules — Dashboard L2",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()

st.markdown("# Méthodes & formules")
st.caption(
    "Chaque KPI du dashboard est dérivé d'une formule explicite. "
    "Cette page donne la définition, l'intuition, et un exemple chiffré sur les données réelles."
)

# Recalcul pour afficher les seuils K-means courants
bv  = load_bv()
aav = load_aav()
km_bv  = kmeans_3(bv)
km_aav = kmeans_3(aav)

st.divider()

# ──────────────────────────────────────────────────────────
st.markdown("### 1. La maille géographique")
st.write(
    "L'INSEE découpe le territoire en plusieurs niveaux emboîtés. Deux mailles "
    "sont retenues pour cette étude :"
)
st.markdown(
    "- **Bassin de Vie 2022 (BV)** — 1 708 zones, ~40 000 habitants en moyenne. "
    "C'est le territoire qui offre à ses habitants les services courants (commerces, "
    "médecin généraliste, école). Maille fine, adaptée au diagnostic local. "
    "Le découpage **couvre toute la France**.\n"
    "- **Aire d'Attraction des Villes 2020 (AAV)** — 699 zones, ~95 000 habitants "
    "en moyenne. Centrée sur un pôle d'emploi, elle reflète la zone de mobilité "
    "réelle d'un actif. Maille plus large, adaptée à la tarification par zone."
)
st.warning(
    "**Couverture territoriale partielle de la maille AAV** — les AAV ne "
    "couvrent pas l'ensemble de la France. Environ **8 900 communes** (~ 4,5 M "
    "habitants) sont situées « hors attraction des villes » (pseudo-AAV 000 dans "
    "le référentiel INSEE) : zones rurales isolées sans rattachement à un pôle "
    "d'emploi. Elles sont **exclues** de l'analyse AAV par cohérence territoriale "
    "et apparaissent en blanc sur la carte. Sur la maille BV, en revanche, "
    "toutes ces communes restent rattachées à un bassin et sont analysées."
)
st.caption(
    "Une commune appartient à un seul BV et à au plus une AAV. Les arrondissements "
    "de Paris, Lyon et Marseille sont recodés sur la commune mère (75056 / 69123 / 13055) "
    "pour aligner l'annuaire Ameli sur le référentiel INSEE."
)

st.divider()

# ──────────────────────────────────────────────────────────
st.markdown("### 2. Effectif d'ophtalmologistes — dédoublonnage 1/N")

c1, c2 = st.columns([1.2, 1])
with c1:
    st.write(
        "Un même ophtalmologiste apparaît plusieurs fois dans l'annuaire "
        "Ameli lorsqu'il exerce sur plusieurs sites (cabinet de groupe, "
        "vacations, clinique). Pour éviter le double comptage, on le compte "
        "une seule fois en répartissant son activité entre ses lieux d'exercice."
    )
    st.latex(r"\text{ETP}_z \;=\; \sum_{i \in z} \frac{1}{N_i}")
    st.markdown(
        "où $N_i$ est le **nombre de lieux d'exercice** du praticien $i$ "
        "et la somme porte sur tous les lieux situés dans la zone $z$. "
        "L'identifiant praticien est la clé `nom + prénom + civilité` "
        "(RPPS non disponible dans l'annuaire Ameli)."
    )

with c2:
    st.markdown("**Exemple chiffré**")
    st.markdown(
        "Le Dr Martin exerce dans **3** cabinets : "
        "Bourg-en-Bresse, Ambérieu, Nantua.\n"
        "On lui attribue $N = 3$ et donc une **pondération de 1/3** sur "
        "chacun des trois Bassins de Vie correspondants.\n"
        "Si dans le BV de Bourg-en-Bresse on ajoute deux autres praticiens "
        "monosite : ETP du BV = $1/3 + 1 + 1 = 2{,}33$."
    )

st.markdown("**Indicateur national**")
c1, c2 = st.columns(2)
c1.metric("Lignes annuaire Ameli filtrées sur la spécialité Ophtalmologie", "10 069")
c2.metric("Ophtalmologistes uniques (nom + prénom + civilité)", "4 479")

st.caption(
    "La somme des pondérations 1/N sur l'ensemble des lignes annuaire vaut exactement "
    "4 479 (par construction). Sur la maille BV elle vaut 4 465,2 — l'écart de 14 "
    "vient des 14 ophtalmologistes installés à l'étranger ou dans une commune "
    "non rattachée à un BV."
)

st.divider()

# ──────────────────────────────────────────────────────────
st.markdown("### 3. Densité d'accès")

c1, c2 = st.columns([1.2, 1])
with c1:
    st.write(
        "Indicateur de synthèse de l'étude. C'est le nombre "
        "d'ophtalmologistes (en ETP) rapporté à 100 000 habitants."
    )
    st.latex(r"\text{densit\'e}_z \;=\; \frac{\text{ETP}_z}{\text{pop}_z} \times 10^5")
    st.markdown(
        "Échelle de lecture indicative :"
    )
    st.markdown(
        "- $< 4$ → tension forte, peu ou pas d'ophtalmologue accessible.\n"
        "- $4 - 7$ → tension modérée, accès contraint.\n"
        "- $> 7$ → offre conforme à la moyenne nationale."
    )
    st.caption(
        "La densité est un indicateur **brut** : elle ne tient pas compte de "
        "la distance ou du temps de trajet. Un BV à densité moyenne peut "
        "concentrer toute son offre dans une seule commune et laisser les "
        "autres communes du BV en désert pratique."
    )

with c2:
    st.markdown("**Exemple chiffré — BV de Bordeaux (33063)**")
    st.markdown(
        "- ETP ophtalmologistes : **187,0**\n"
        "- Population 2023 : **991 755**\n"
        "- Densité : $\\frac{187,0}{991\\,755} \\times 10^5 = \\mathbf{18{,}85}$ oph/100k\n"
        "- Classement K-means : **OK** (densité > F₂₃ = 10,22)"
    )
    st.markdown("**Exemple chiffré — BV de Bressuire (79049)**")
    st.markdown(
        "- ETP : **0,67**\n"
        "- Population : **45 891**\n"
        "- Densité : $\\frac{0{,}67}{45\\,891} \\times 10^5 = \\mathbf{1{,}46}$ oph/100k\n"
        "- Classement : **Désert**"
    )

st.divider()

# ──────────────────────────────────────────────────────────
st.markdown("### 4. KPI « 1 ophtalmologiste pour X habitants »")

c1, c2 = st.columns([1.2, 1])
with c1:
    st.write(
        "C'est la lecture inverse de la densité, plus parlante en "
        "communication actuarielle. On rapporte la population de la zone à "
        "l'effectif d'ophtalmologistes qui y exerce."
    )
    st.latex(r"R_z \;=\; \frac{\text{pop}_z}{\text{ETP}_z}")
    st.markdown(
        "$R_z$ s'interprète comme le **nombre d'habitants couverts par un "
        "ophtalmologiste équivalent temps plein** dans la zone. Plus la "
        "valeur est grande, plus l'accès est contraint."
    )

with c2:
    st.markdown("**Exemple chiffré — France entière**")
    nat_pop = bv["population"].sum()
    nat_etp = bv["nb_docteurs_pondere"].sum()
    st.markdown(
        f"- Population : **{nat_pop/1e6:.1f} M** habitants\n"
        f"- ETP : **{nat_etp:.1f}**\n"
        f"- Ratio : $\\frac{{{nat_pop/1e6:.2f}\\text{{M}}}}{{{nat_etp:.0f}}} \\approx "
        f"\\mathbf{{{int(round(nat_pop/nat_etp)):,}}}$ habitants par ophtalmologiste."
        .replace(",", " ")
    )
    st.markdown("**À titre comparatif**")
    for r in ["Île-de-France", "Provence-Alpes-Côte d'Azur", "Bourgogne-Franche-Comté", "Hauts-de-France"]:
        sub = bv[bv["region"] == r]
        if len(sub) == 0:
            continue
        p, e = sub["population"].sum(), sub["nb_docteurs_pondere"].sum()
        if e > 0:
            st.markdown(f"- {r} : **1 pour {int(round(p/e)):,}**".replace(",", " "))

st.divider()

# ──────────────────────────────────────────────────────────
st.markdown("### 5. Classification K-means pondérée (k = 3)")

st.write(
    "Plutôt que de fixer arbitrairement les seuils Désert / Tension / OK "
    "(ex. < 4 oph/100k = désert), on laisse l'algorithme K-means les déterminer "
    "à partir de la distribution réelle de la densité. Chaque zone reçoit un "
    "poids proportionnel à sa population : la classification reflète "
    "l'expérience moyenne d'un habitant, pas l'effectif des territoires."
)

c1, c2 = st.columns([1.3, 1])
with c1:
    st.markdown("**Principe — minimisation de l'inertie intra-cluster pondérée**")
    st.latex(
        r"\min_{\mathcal{C}_1,\mathcal{C}_2,\mathcal{C}_3,\,\mu_1,\mu_2,\mu_3} "
        r"\; \sum_{k=1}^{3} \sum_{z \in \mathcal{C}_k} w_z \, (x_z - \mu_k)^2"
    )
    st.markdown(
        "- $x_z$ : densité de la zone $z$ (la variable à clusteriser).\n"
        "- $w_z$ : population de la zone $z$ (le poids).\n"
        "- $\\mu_k$ : centroïde du cluster $k$ — moyenne pondérée des "
        "densités des zones qui lui appartiennent.\n"
        "- L'algorithme itère deux étapes jusqu'à convergence :\n"
        "    1. **Affectation** : chaque zone est rattachée au cluster du "
        "centroïde le plus proche.\n"
        "    2. **Mise à jour** : chaque centroïde est recalculé comme la "
        "moyenne pondérée des zones qui lui sont affectées."
    )
    st.caption(
        "Implémentation : `sklearn.cluster.KMeans(n_clusters=3, n_init=20, "
        "random_state=42)`. Le paramètre `sample_weight` reçoit la population. "
        "20 initialisations différentes pour éviter les minima locaux."
    )

with c2:
    st.markdown("**Frontières & étiquetage**")
    st.markdown(
        "Une fois les trois centroïdes triés $\\mu_1 < \\mu_2 < \\mu_3$, "
        "on définit les frontières comme les milieux successifs :"
    )
    st.latex(r"F_{12} = \frac{\mu_1 + \mu_2}{2} \qquad F_{23} = \frac{\mu_2 + \mu_3}{2}")
    st.markdown(
        "- $\\text{densit\\'e}_z < F_{12}$ → **Désert**\n"
        "- $F_{12} \\le \\text{densit\\'e}_z < F_{23}$ → **Tension**\n"
        "- $\\text{densit\\'e}_z \\ge F_{23}$ → **OK**"
    )

st.markdown("**Exemple chiffré sur les données réelles**")
st.dataframe(
    {
        "Maille":   ["Bassin de Vie",  "Aire d'Attraction"],
        "μ₁ (Désert)":  [f"{km_bv.centres[0]:.2f}",  f"{km_aav.centres[0]:.2f}"],
        "μ₂ (Tension)": [f"{km_bv.centres[1]:.2f}",  f"{km_aav.centres[1]:.2f}"],
        "μ₃ (OK)":      [f"{km_bv.centres[2]:.2f}",  f"{km_aav.centres[2]:.2f}"],
        "F₁₂ (Désert→Tension)": [f"{km_bv.F12:.2f}", f"{km_aav.F12:.2f}"],
        "F₂₃ (Tension→OK)":     [f"{km_bv.F23:.2f}", f"{km_aav.F23:.2f}"],
    },
    use_container_width=True, hide_index=True,
)
st.caption(
    "Lecture : sur la maille BV, le centroïde Désert vaut 1,06 oph/100k — c'est la "
    "densité moyenne pondérée des BV en désert. La frontière F₁₂ = 4,43 sépare "
    "Désert et Tension : un BV à 5 oph/100k est classé Tension, un BV à 4 est "
    "classé Désert. Les frontières BV et AAV sont quasi identiques (4,4 et 10,2) — "
    "la grammaire « désert / tension / OK » est donc robuste au choix de maille."
)

st.divider()

# ──────────────────────────────────────────────────────────
st.markdown("### 6. Heatmap — densité lissée")

c1, c2 = st.columns([1.2, 1])
with c1:
    st.write(
        "La heatmap est une version lissée de la choroplèthe. Chaque zone "
        "contribue à un noyau gaussien centré sur son centroïde, pondéré par "
        "son **manque** d'ophtalmologistes : plus la densité locale est "
        "faible, plus le poids est élevé. Le lissage spatial fait alors "
        "ressortir les agrégats de zones sous-dotées comme de larges taches "
        "rouge écarlate."
    )
    st.latex(
        r"\text{intensit\'e}(x, y) "
        r"\;\propto\; \sum_{z}\; K\!\!\left(\frac{(x,y) - (lon_z, lat_z)}{h}\right) "
        r"\cdot \big[\max(D_{\text{ref}} - \text{densit\'e}_z,\; 0)\big]^{2}"
    )
    st.markdown(
        "- $K$ : noyau gaussien.\n"
        "- $h$ : largeur de bande (radius = 24, paramètre Plotly).\n"
        "- $D_{\\text{ref}}$ : seuil de référence, **piloté par le curseur "
        "latéral** sur les pages BV et AAV (valeur par défaut : 12 oph/100k).\n"
        "- Pondération **quadratique** : une zone à 0 ophtalmo apporte "
        "$D_{\\text{ref}}^{2}$, une zone à $D_{\\text{ref}}/2$ apporte "
        "$D_{\\text{ref}}^{2}/4$ — soit **4× moins** que la zone à zéro. "
        "Cette accélération fait clairement ressortir les déserts purs."
    )

with c2:
    st.markdown("**Lecture**")
    st.markdown(
        "- Les zones rouge écarlate signalent un **bloc de territoire où la "
        "densité est durablement faible** sur plusieurs zones contiguës.\n"
        "- Les taches isolées correspondent à un déficit local plus ponctuel.\n"
        "- L'absence de couleur indique que la zone et son voisinage sont "
        "correctement dotés."
    )

st.divider()

# ──────────────────────────────────────────────────────────
st.markdown("### 7. Contrôles qualité")
st.markdown(
    "- **Couverture annuaire jointe** : 99,8 % des lignes ophtalmologistes "
    "ont un code postal ou CEDEX joignable à un BV. Les deux non-jointes "
    "sont Monaco et Saint-Barthélemy.\n"
    "- **Effectif total** : 4 479 ophtalmologistes uniques sur l'ensemble de "
    "l'annuaire (clé nom + prénom + civilité).\n"
    "- **Somme des pondérations 1/N** : 4 479 (par construction, sur le fichier "
    "annuaire complet) → 4 465,2 sur la maille BV (perte des 14 lignes étrangères / "
    "non rattachées).\n"
    "- **Total ETP BV vs AAV** : 4 465,2 (BV) vs 4 422,3 (AAV) — l'écart vient "
    "des 42,9 ETP rattachés à la pseudo-AAV 000 « hors attraction des villes », "
    "exclue de l'analyse par cohérence territoriale."
)

footer()
