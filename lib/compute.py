# -*- coding: utf-8 -*-
"""K-means pondéré, Gini, KPIs."""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans


@dataclass
class KmeansResult:
    """Résultat d'un K-means pondéré k=3 sur la densité."""

    F12: float       # frontière Désert / Tension
    F23: float       # frontière Tension / OK
    centres: list    # centroides triés croissants : mu1, mu2, mu3
    df: pd.DataFrame  # df + colonne 'statut' (Désert / Tension / OK)


@st.cache_data(show_spinner=False)
def kmeans_3(df: pd.DataFrame, densite_col: str = "densite_100k", pop_col: str = "population", seed: int = 42) -> KmeansResult:
    """K-means pondéré k=3 sur la densité, poids = population.

    Renvoie les centroïdes triés, les deux frontières F12 et F23, et le df enrichi
    d'une colonne 'statut' ∈ {Désert, Tension, OK}.
    """
    work = df[[densite_col, pop_col]].dropna().copy()
    work = work[work[pop_col] > 0]
    if len(work) < 3:
        # Cas pathologique : pas assez de zones pour 3 clusters
        out = df.copy()
        out["statut"] = "OK"
        return KmeansResult(F12=0.0, F23=0.0, centres=[0.0, 0.0, 0.0], df=out)

    X = work[[densite_col]].values
    w = work[pop_col].values
    km = KMeans(n_clusters=3, n_init=20, random_state=seed)
    labels = km.fit_predict(X, sample_weight=w)

    centres_bruts = km.cluster_centers_.ravel()
    ordre = np.argsort(centres_bruts)
    rename = {old: new for new, old in enumerate(ordre)}
    centres = sorted(centres_bruts.tolist())
    F12 = (centres[0] + centres[1]) / 2
    F23 = (centres[1] + centres[2]) / 2

    # Étiquetage du df complet (les zones avec pop=0 -> Désert par défaut)
    out = df.copy()
    out["statut"] = np.where(
        out[densite_col] < F12, "Désert",
        np.where(out[densite_col] < F23, "Tension", "OK"),
    )
    return KmeansResult(F12=F12, F23=F23, centres=centres, df=out)


@st.cache_data(show_spinner=False)
def synthese_par_statut(df: pd.DataFrame, code_col: str, pop_col: str = "population") -> pd.DataFrame:
    ordre = ["Désert", "Tension", "OK"]
    rec = (df.groupby("statut")
             .agg(nb_zones=(code_col, "count"),
                  pop=(pop_col, "sum"),
                  ETP=("nb_docteurs_pondere", "sum"))
             .reindex(ordre))
    rec["% zones"] = rec["nb_zones"] / rec["nb_zones"].sum() * 100
    rec["% pop"]   = rec["pop"] / rec["pop"].sum() * 100
    rec["densité moy. (oph/100k)"] = (rec["ETP"] / rec["pop"]) * 1e5
    rec = rec.reset_index().rename(columns={"statut": "Statut"})
    return rec


def fmt_int(x: float) -> str:
    return f"{int(round(x)):,}".replace(",", " ")


def fmt_pct(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f} %".replace(".", ",")


def fmt_float(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")
