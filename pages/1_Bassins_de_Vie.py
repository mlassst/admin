# -*- coding: utf-8 -*-
"""Page Bassin de Vie."""

from lib.loaders import load_bv, load_geojson_bv
from lib.page_maille import MailleSpec, render

render(MailleSpec(
    nom_long="Bassin de Vie",
    nom_court="BV",
    code_col="bv2022",
    code_label="Code BV",
    code_key_geojson="bv2022",
    df_loader=load_bv,
    geojson_loader=load_geojson_bv,
    description=(
        "1 708 Bassins de Vie 2022 · maille fine du vécu quotidien "
        "(~40 000 habitants en moyenne par zone)."
    ),
))
