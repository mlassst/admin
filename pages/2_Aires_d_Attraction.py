# -*- coding: utf-8 -*-
"""Page Aire d'Attraction des Villes."""

from lib.loaders import load_aav, load_geojson_aav
from lib.page_maille import MailleSpec, render

render(MailleSpec(
    nom_long="Aire d'Attraction des Villes",
    nom_court="AAV",
    code_col="aav2020",
    code_label="Code AAV",
    code_key_geojson="aav2020",
    df_loader=load_aav,
    geojson_loader=load_geojson_aav,
    description=(
        "699 Aires d'Attraction 2020 · maille plus large centrée sur les "
        "pôles d'emploi (~95 000 habitants en moyenne par zone)."
    ),
    warning=(
        "**Couverture territoriale partielle.** La maille AAV ne recouvre "
        "pas l'ensemble du territoire : environ **8 900 communes** (~ 4,5 M "
        "habitants) sont classées « hors attraction des villes » par l'INSEE "
        "et n'entrent pas dans l'analyse. Elles apparaissent **en blanc** sur "
        "la carte. Pour une vue exhaustive du territoire, utiliser la maille "
        "Bassin de Vie."
    ),
))
