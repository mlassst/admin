# -*- coding: utf-8 -*-
"""Chargeurs cachés des bases et fonds de carte."""

from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"


@st.cache_data(show_spinner=False)
def load_bv() -> pd.DataFrame:
    df = pd.read_csv(DATA / "bv_enriched.csv", sep=";", dtype={"bv2022": str, "dep": str, "reg": str})
    df["bv2022"] = df["bv2022"].str.zfill(5)
    df["dep"] = df["dep"].astype(str).str.zfill(2)
    return df


@st.cache_data(show_spinner=False)
def load_aav() -> pd.DataFrame:
    df = pd.read_csv(DATA / "aav_enriched.csv", sep=";", dtype={"aav2020": str, "dep": str, "reg": str})
    df["aav2020"] = df["aav2020"].astype(str).str.zfill(3)
    df["dep"] = df["dep"].astype(str).str.zfill(2)
    return df


@st.cache_data(show_spinner=False)
def load_geojson_bv() -> dict:
    return json.loads((DATA / "bv2022.geojson").read_text())


@st.cache_data(show_spinner=False)
def load_geojson_aav() -> dict:
    return json.loads((DATA / "aav2020.geojson").read_text())
