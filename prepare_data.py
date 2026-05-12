# -*- coding: utf-8 -*-
"""
Enrichit les bases V4 (BV et AAV) avec les libellés, lat/lon et codes
département/région pour servir directement le dashboard sans dépendre des
fichiers Excel INSEE.

Sortie :
    data/bv_enriched.csv
    data/aav_enriched.csv
"""

from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).parent
DATA = ROOT / "data"

V4_BV  = DATA / "docteurs_ophtalmo_v4.csv"
V4_AAV = DATA / "docteurs_ophtalmo_v4_aav.csv"
GJ_BV  = DATA / "bv2022.geojson"
GJ_AAV = DATA / "aav2020.geojson"

# Lookup département/région : on s'appuie sur la sortie 02_sorties si présente
# (couvre 1683/1708 BV). Pour les ~25 BV manquants : déduction via préfixe du code.
SORTIE_BV  = Path("/Users/martin/Documents/Data challenge/Datachallenge claude/02_sorties/ophtalmologues_par_bv.csv")
SORTIE_AAV = Path("/Users/martin/Documents/Data challenge/Datachallenge claude/02_sorties/ophtalmologues_par_aav.csv")


def num(s):
    return pd.to_numeric(s.astype(str).str.replace(",", ".", regex=False), errors="coerce")


def centroids(geojson_path: Path, code_key: str, lib_key: str) -> pd.DataFrame:
    gj = json.loads(geojson_path.read_text())
    rows = [{
        code_key: f["properties"][code_key],
        "libelle": f["properties"][lib_key],
        "lat": f["properties"]["lat"],
        "lon": f["properties"]["lon"],
    } for f in gj["features"]]
    return pd.DataFrame(rows)


def enrich(v4_path: Path, gj_path: Path, sortie_path: Path, code_key: str, lib_key: str, pop_key: str) -> pd.DataFrame:
    v4 = pd.read_csv(v4_path, sep=";", dtype={code_key: str})
    v4["nb_docteurs_pondere"] = num(v4["nb_docteurs_pondere"])
    v4[pop_key] = num(v4[pop_key])
    v4 = v4.rename(columns={pop_key: "population"})

    # Nettoyage : retire les lignes parasites et la pseudo-AAV "000" (hors
    # attraction des villes) qui n'est pas un territoire cohérent et n'a pas
    # de polygone dans le geojson.
    if code_key == "aav2020":
        v4 = v4[~v4[code_key].isin(["AAV2020", "000"])].copy()

    cent = centroids(gj_path, code_key, lib_key)

    sortie = pd.read_csv(sortie_path, sep=";", dtype={code_key: str, "dep": str, "reg": str})
    sortie = sortie[[code_key, "dep", "reg", "region"]].drop_duplicates(code_key)

    df = v4.merge(cent, on=code_key, how="left").merge(sortie, on=code_key, how="left")

    # Fallback dep/reg : pour les codes BV/AAV non présents dans 02_sorties
    # On extrait le département du préfixe du code (BV2022 = 5 chars, AAV = 3 chars
    # où les 2 premiers chiffres du code BV codent le dept de la commune centre).
    if code_key == "bv2022":
        df["dep"] = df["dep"].fillna(df[code_key].str[:2])
    df["dep"] = df["dep"].fillna("00")
    df["region"] = df["region"].fillna("Non renseigné")

    # Densité ophtalmologistes pour 100 000 habitants
    df["densite_100k"] = (df["nb_docteurs_pondere"] / df["population"]) * 1e5
    df["densite_100k"] = df["densite_100k"].fillna(0.0)

    cols = [code_key, "libelle", "dep", "region", "lat", "lon",
            "population", "nb_docteurs_pondere", "densite_100k"]
    return df[cols]


def main():
    bv = enrich(V4_BV, GJ_BV, SORTIE_BV, "bv2022", "libbv2022", "population_2023_bv")
    aav = enrich(V4_AAV, GJ_AAV, SORTIE_AAV, "aav2020", "libaav2020", "population_2023_aav")

    bv.to_csv(DATA / "bv_enriched.csv", sep=";", index=False)
    aav.to_csv(DATA / "aav_enriched.csv", sep=";", index=False)

    print("BV  :", len(bv), "lignes  ·  pop", f"{bv['population'].sum()/1e6:.1f} M",
          " ·  ETP", f"{bv['nb_docteurs_pondere'].sum():.1f}")
    print("AAV :", len(aav), "lignes  ·  pop", f"{aav['population'].sum()/1e6:.1f} M",
          " ·  ETP", f"{aav['nb_docteurs_pondere'].sum():.1f}")
    print("BV manquants lat :", bv["lat"].isna().sum())
    print("AAV manquants lat:", aav["lat"].isna().sum())
    print("BV par region :")
    print(bv["region"].value_counts().head(20))


if __name__ == "__main__":
    main()
