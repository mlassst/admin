# Dashboard L2 — Déserts ophtalmologiques en France

Restitution interactive du livrable 2 du Data Challenge 2026 — KPI, cartes
choroplèthes et heatmaps, sur les deux mailles **Bassin de Vie 2022** et
**Aire d'Attraction des Villes 2020**.

Stack : **Streamlit** + **Plotly** + **scikit-learn** (K-means pondéré).

---

## 1. Aperçu

Trois pages :

| Page | Contenu |
|---|---|
| **Accueil** (`app.py`) | Contexte assureur · 12 KPI nationaux · comparaison BV ↔ AAV · méthodologie |
| **Bassin de Vie** | 1 708 BV · choroplèthe + heatmap offre/tension · K-means · Lorenz/Gini · ranking · export CSV |
| **Aire d'Attraction** | 701 AAV · mêmes visuels recalibrés sur la distribution AAV |

Données :

- `data/docteurs_ophtalmo_v4.csv` (BV) et `data/docteurs_ophtalmo_v4_aav.csv` (AAV) — base canonique
- `data/bv2022.geojson` / `data/aav2020.geojson` — polygones INSEE simplifiés (1707 / 699 features)
- `data/bv_enriched.csv` / `data/aav_enriched.csv` — bases pré-jointes générées par `prepare_data.py`

---

## 2. Lancer en local

```bash
cd "L2/dashboard"
pip install -r requirements.txt
python3 prepare_data.py        # une seule fois — produit bv_enriched.csv / aav_enriched.csv
python3 -m streamlit run app.py
```

→ http://localhost:8501

---

## 3. Déploiement (hors local, lien partageable)

Trois options testées. La **Streamlit Community Cloud** est la plus simple
pour partager un lien public sans serveur à gérer.

### Option A — Streamlit Community Cloud (recommandé, gratuit)

**Lien public type :** `https://<votre-app>.streamlit.app`

1. Pousser ce dossier `L2/dashboard/` sur un dépôt GitHub **public**
   (par exemple `data-challenge-2026-dashboard`).
2. Aller sur https://share.streamlit.io → *Create app* → connecter GitHub.
3. Renseigner :
   - **Repository** : votre dépôt
   - **Branch** : `main`
   - **Main file path** : `app.py` (si le dashboard est à la racine)
     ou `L2/dashboard/app.py` (si imbriqué)
4. Cliquer **Deploy**. La build dure ~2 min ; le lien est disponible
   ensuite et se met à jour automatiquement à chaque `git push`.

**Notes** :

- Le tier gratuit accepte des dépôts publics, 1 GB de RAM, suspend l'app
  après ~7 jours d'inactivité (redémarrage automatique au premier visiteur).
- Le fichier `.streamlit/config.toml` est respecté (thème, port, etc.).

### Option B — Hugging Face Spaces (gratuit, SDK Streamlit natif)

**Lien public type :** `https://huggingface.co/spaces/<user>/<space>`

1. Créer un Space sur https://huggingface.co/new-space avec :
   - **SDK** : Streamlit
   - **Hardware** : CPU basic (gratuit)
2. Cloner le repo Space localement :
   ```bash
   git clone https://huggingface.co/spaces/<user>/<space> hf_space
   cp -R L2/dashboard/* hf_space/
   cd hf_space && git add . && git commit -m "deploy" && git push
   ```
3. HF build l'image et publie automatiquement.

### Option C — Render.com (gratuit avec sleep, plus de contrôle)

1. Sur Render → *New Web Service* → connecter GitHub.
2. **Build command** : `pip install -r requirements.txt && python3 prepare_data.py`
3. **Start command** :
   `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
4. Plan **Free** suffit (sleep après 15 min d'inactivité, redémarrage ~30 s).

---

## 4. Structure du code

```
L2/dashboard/
├── app.py                       Accueil — contexte + KPI master
├── pages/
│   ├── 1_Bassins_de_Vie.py      Page BV (3 lignes — délègue à page_maille)
│   └── 2_Aires_d_Attraction.py  Page AAV (idem)
├── lib/
│   ├── loaders.py               Chargeurs cachés (CSV + geojson)
│   ├── compute.py               K-means pondéré · Gini · synthèse statut
│   ├── viz.py                   Choroplèthe · heatmaps · histogramme · Lorenz · barres régions
│   ├── ui.py                    Hero · cartes KPI · pull-quotes · footer
│   ├── style.py                 Palette + CSS injecté
│   └── page_maille.py           Mise en page partagée BV/AAV (factorise tout)
├── data/                        CSV + geojson (~5 Mo total)
├── prepare_data.py              Enrichissement V4 → bv_enriched / aav_enriched
├── .streamlit/config.toml       Thème
└── requirements.txt
```

---

## 5. Indicateurs et méthodologie

### Densité

$$
\text{densité}_z = \frac{\sum_{i \in z} \frac{1}{N_i}}{\text{pop}_z} \times 10^5
$$

où $N_i$ est le nombre de lieux d'exercice du praticien $i$ (dédoublonnage 1/N).

### K-means pondéré (k = 3)

Sur la variable « densité (oph/100k) », pondéré par la population de la zone.
Trois centroïdes triés $\mu_1 < \mu_2 < \mu_3$ et deux frontières
$F_{12} = (\mu_1 + \mu_2)/2$, $F_{23} = (\mu_2 + \mu_3)/2$. Étiquetage
**Désert / Tension / OK**. `random_state = 42`, 20 initialisations.

### Coefficient de Gini

Aire entre la courbe de Lorenz pondérée (cumul population vs cumul d'offre)
et la diagonale d'égalité, × 2. Plage [0 ; 1].

### Cartes

- **Choroplèthe** : couleur par zone, plafonnée visuellement par l'utilisateur
  (slider 10–40 oph/100k) pour préserver le contraste.
- **Heatmap offre** : kernel density sur les centroïdes, poids = ETP cap à 30
  (sinon Paris écrase tout).
- **Heatmap tension** : kernel density sur les centroïdes des seules zones
  Désert/Tension, poids = population (kép 200 k).

---

## 6. Données et sources

| Source | Volume | Rôle |
|---|---|---|
| Annuaire santé Ameli (data.gouv.fr) | 547 615 lignes → 10 069 ophtalmos | Offre |
| Recensement INSEE 2023 | 34 877 communes | Demande |
| Bassin de Vie 2022 (INSEE) | 1 708 BV | Maille principale |
| Aire d'Attraction 2020 (INSEE) | 701 AAV | Maille secondaire |
| CP → INSEE (data.gouv.fr) | 36 370 couples | Référentiel postal |
| CEDEX → INSEE (GitHub geocodage-spd) | 10 789 couples | Complément CEDEX |

Périmètre : **ophtalmologie uniquement**. Effectif retenu : 4 479
ophtalmologistes uniques (clé nom + prénom + civilité).
