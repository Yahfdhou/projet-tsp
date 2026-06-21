# Social-Based Algorithm (SBA) pour le TSP

**Auteur :** LEHOUEIMEL Yahfdhou  
**Référence :** Ramezani F., Lotfi S. (2013). *Social-based algorithm (SBA)*. Applied Soft Computing, 13(5), 2837–2856.  
**Repository :** [https://github.com/Yahfdhou/projet-tsp](https://github.com/Yahfdhou/projet-tsp)

---

## Objectif

Ce projet adapte l'algorithme **SBA** (hybride EA + ICA) du papier original — conçu pour l'optimisation continue sur fonctions benchmark (Sphere, Rastrigin, etc.) — au **Travelling Salesman Problem (TSP)** en utilisant des représentations par **permutations**.

**Question de recherche :** SBA conserve-t-il sa supériorité après adaptation au TSP, comparé à **EA** et **ICA** ?

**Instances TSPLIB :** berlin52 (52 villes), eil51 (51 villes), kroA100 (100 villes).

---

## Structure du projet

```
projet-tsp/
├── data/tsplib/                 # Instances TSPLIB (.tsp)
├── experiments/
│   ├── run_comparison.py        # Expérience complète SBA vs EA vs ICA
│   └── run_single.py            # Test rapide d'un algorithme
├── scripts/
│   └── plot_results.py          # Graphique comparatif (barplot)
├── results/                     # Résultats CSV/JSON par expérience
├── src/tsp_sba/
│   ├── config.py                # Paramètres (papier + 2-opt)
│   ├── tsp/instance.py          # Chargement TSPLIB, matrice distances
│   ├── operators/
│   │   ├── genetic.py           # OX, inversion, assimilation
│   │   └── local_search.py      # 2-opt (recherche locale)
│   ├── algorithms/
│   │   ├── sba.py               # SBA — structure Monarchy
│   │   ├── ea.py                # EA baseline
│   │   └── ica.py               # ICA baseline
│   ├── statistics/wilcoxon.py   # Test de Wilcoxon
│   └── experiments/runner.py    # Moteur d'expérimentation
├── Dockerfile
├── docker-compose.yml
├── sheikh-deploy.sh             # Déploiement AWS
├── avant-opt.md                 # Rapport résultats sans 2-opt
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## Adaptation SBA → TSP

| Élément (papier original) | Adaptation TSP |
|---------------------------|----------------|
| Vecteurs réels | Permutations de villes |
| Uniform Crossover | **Order Crossover (OX)** |
| Gene Flip Mutation | **Inversion Mutation** |
| Assimilation numérique | **Copie de positions** |
| Structure sociale | **Monarchy** (meilleure dans le papier) |
| — | **2-opt** (extension TSP, recherche locale) |

---

## Algorithme SBA — Boucle Decade

À chaque **Decade** (itération), deux niveaux :

### Niveau 1 — EA (dans chaque pays)
1. **Sélection** par tournoi
2. **Croisement** Order Crossover (OX)
3. **Mutation** par inversion
4. **Remplacement** si l'enfant est meilleur
5. Mise à jour du **Leader** (meilleure personne du pays)

### Niveau 2 — ICA (entre pays et empires)
1. **Assimilation interne (Pi)** : personnes des colonies → leader impérialiste
2. **Assimilation externe (Pe)** : personnes → Empereur (Monarchy)
3. **Révolution** : mutation aléatoire (éviter optima locaux)
4. **Échange de position** : colonie meilleure remplace impérialiste
5. **Compétition impérialiste** : colonie faible rejoint empire puissant

### Condition d'arrêt
- Nombre fixe de décennies : `max_decades = n_cities × decades_multiplier`
- Exemple : berlin52 → 52 × 100 = **5200 decades**
- Retour du **meilleur tour** enregistré

### 2-opt (recherche locale)
Appliqué après init, crossover, mutation et assimilation pour éliminer les croisements d'arêtes dans les tours. Activé par défaut (`use_two_opt: true`).

---

## Paramètres (papier Ramezani & Lotfi)

| Paramètre | Symbole | Valeur |
|-----------|---------|--------|
| Crossover | Pc | 0.75 |
| Mutation | Pm | 0.050505 |
| Assimilation externe | Pe | 0.1 |
| Assimilation interne | Pi | 0.1 |
| Coefficient assimilation | β | 2.0 |
| Impérialistes | — | 8 |
| Pays | — | 22 |
| Personnes / pays | — | 4 |
| Structure sociale | — | Monarchy |
| Multiplicateur décennies | — | 100 |
| Runs par expérience | — | 30 |
| Test statistique | — | Wilcoxon (α = 0.05) |
| 2-opt | — | activé (désactiver : `--no-2-opt`) |

---

## Installation locale

```bash
git clone https://github.com/Yahfdhou/projet-tsp.git
cd projet-tsp
pip install -r requirements.txt
pip install -e .
```

---

## Utilisation locale

### Test rapide (1 instance, 1 algorithme)

```bash
python experiments/run_single.py --instance berlin52 --algorithm SBA --quick
```

### Expérience complète (30 runs, 3 algos, 3 instances, avec 2-opt)

```bash
python experiments/run_comparison.py --runs 30 --instances berlin52 eil51 kroA100 --decades-multiplier 100
```

### Mode rapide (3 runs)

```bash
python experiments/run_comparison.py --quick
```

### Sans 2-opt (baseline)

```bash
python experiments/run_comparison.py --runs 30 --no-2-opt
```

### Graphique comparatif

```bash
python scripts/plot_results.py results/experiment_YYYYMMDD_HHMMSS
```

---

## Docker

### Build

```bash
docker compose build
```

### Expérience complète (30 runs, avec 2-opt)

```bash
docker compose up --build comparison
```

En arrière-plan (AWS) :

```bash
docker compose up --build -d comparison
docker compose logs -f comparison
```

### Autres services

| Service | Commande | Description |
|---------|----------|-------------|
| `comparison-quick` | `docker compose run --rm comparison-quick` | 3 runs, test rapide |
| `comparison-no-2opt` | `docker compose run --rm comparison-no-2opt` | 30 runs sans 2-opt |
| `single` | `docker compose run --rm single` | 1 algo sur eil51 |
| `plot` | `docker compose run --rm plot results/experiment_...` | Barplot |

### Résultats Docker

Sauvegardés dans `./results/experiment_YYYYMMDD_HHMMSS/` (volume monté sur l'hôte).

---

## Déploiement AWS

```bash
cd ~/projet-tsp
git pull origin main
bash sheikh-deploy.sh
```

Le script `sheikh-deploy.sh` exécute :
1. `git pull origin main`
2. `sudo docker system prune -a -f`
3. Build de l'image Docker
4. `sudo docker run -d` avec volume `~/projet-tsp/results`

Suivre les logs :

```bash
sudo docker logs -f tsp-sba-run
# ou avec docker compose :
sudo docker compose logs -f comparison
```

---

## Résultats

Chaque expérience crée un dossier `results/experiment_YYYYMMDD_HHMMSS/` :

| Fichier | Contenu |
|---------|---------|
| `raw_results.csv` | Tous les runs (instance, algo, run_id, best_cost, seed) |
| `summary_statistics.csv` | Moyenne, écart-type, min, max, médiane, gap % |
| `wilcoxon_tests.csv` | Tests SBA vs EA et SBA vs ICA |
| `experiment_config.json` | Configuration utilisée |
| `comparison_barplot.png` | Graphique (via `plot_results.py`) |

### Consulter les résultats (Linux / AWS)

```bash
cd ~/projet-tsp/results/experiment_*/
cat summary_statistics.csv
cat wilcoxon_tests.csv
cat experiment_config.json
head -n 20 raw_results.csv
```

### Optima connus (TSPLIB)

| Instance | Villes | Optimum |
|----------|--------|---------|
| berlin52 | 52 | 7542 |
| eil51 | 51 | 426 |
| kroA100 | 100 | 21282 |

---

## Résultats obtenus

### Sans 2-opt (`avant-opt.md` — experiment_20260617_173656)

| Instance | SBA (moy) | Gap SBA | SBA vs EA (Wilcoxon) | SBA vs ICA |
|----------|-----------|---------|----------------------|------------|
| berlin52 | 7931 | 5.16% | p = 0.047 ✅ SBA | p = 0.008 ✅ SBA |
| eil51 | 435 | 2.18% | p < 0.00001 ✅ SBA | p < 0.00001 ✅ SBA |
| kroA100 | 22442 | 5.45% | p = 0.44 (non significatif) | p < 0.00001 ✅ SBA |

**Conclusion sans 2-opt :** SBA significativement meilleur que EA et ICA sur berlin52 et eil51. Solutions acceptables (gap 2–5%) mais pas optimales.

### Avec 2-opt (AWS — experiment_20260620_151524, quick 3 runs)

| Instance | SBA | EA | ICA | Gap |
|----------|-----|-----|-----|-----|
| berlin52 | 7542 | 7542 | 7542 | **0%** |
| eil51 | 426.33 | 426.33 | 426 | **~0%** |
| kroA100 | 21282 | 21282 | 21282 | **0%** |

**Conclusion avec 2-opt :** Gap quasi nul — optimum TSPLIB atteint ou très proche. Les trois algorithmes deviennent équivalents (Wilcoxon : tie).

> Rapport détaillé avant 2-opt : voir [`avant-opt.md`](avant-opt.md)

---

## Synchronisation GitHub

Les résultats ne sont **pas** uploadés automatiquement. Après une expérience :

```bash
cd ~/projet-tsp
git add results/
git commit -m "Add experiment results"
git push origin main
```

Sur votre machine locale :

```bash
git pull origin main
```

---

## Référence bibliographique

```bibtex
@article{ramezani2013sba,
  title={Social-based algorithm (SBA)},
  author={Ramezani, Fatemeh and Lotfi, Shahriar},
  journal={Applied Soft Computing},
  volume={13},
  number={5},
  pages={2837--2856},
  year={2013},
  publisher={Elsevier}
}
```

---

## Phrase pour le rapport

> J'ai lu l'article de Ramezani & Lotfi (2013), conservé la structure SBA originale (Monarchy, EA + ICA), adapté les opérateurs pour une représentation TSP par permutations, comparé SBA vs EA vs ICA sur trois instances TSPLIB avec 30 runs et le test de Wilcoxon, puis amélioré la qualité des solutions via la recherche locale 2-opt.

---

## Licence

Projet académique — LEHOUEIMEL Yahfdhou.
