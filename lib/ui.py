# -*- coding: utf-8 -*-
"""Composants UI réutilisables : hero, KPI cards, pull-quote."""

from __future__ import annotations
import streamlit as st


def inject_css():
    from .style import CSS
    st.markdown(CSS, unsafe_allow_html=True)


def hero(titre: str, sous_titre: str, meta: str = "Data Challenge 2026 · Master 1 Actuariat (SARADS)"):
    st.markdown(f"""
    <div class="hero">
      <h1>{titre}</h1>
      <div class="subtitle">{sous_titre}</div>
      <div class="meta">{meta}</div>
    </div>
    """, unsafe_allow_html=True)


def kpi(label: str, value: str, help_text: str = "", tone: str = "accent"):
    """Carte KPI. tone ∈ {accent, red, orange, green}."""
    st.markdown(f"""
    <div class="kpi {tone}">
      <div class="label">{label}</div>
      <div class="value">{value}</div>
      <div class="help">{help_text}</div>
    </div>
    """, unsafe_allow_html=True)


def pull(text: str):
    st.markdown(f'<div class="pull">{text}</div>', unsafe_allow_html=True)


def footer():
    st.markdown("""
    <div class="footer">
      Source offre : Annuaire santé Ameli (data.gouv.fr, mars 2026) ·
      Source demande : Recensement INSEE 2023 ·
      Mailles : Bassin de Vie 2022, Aire d'Attraction des Villes 2020 ·
      Spécialité : Ophtalmologie uniquement ·
      Dédoublonnage : pondération 1/N par lieu d'exercice.
    </div>
    """, unsafe_allow_html=True)
