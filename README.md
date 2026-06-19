# Social-Based Algorithm (SBA) pour le TSP

**Auteurs du projet :** LEHOUEIMEL Yahfdhou  
**Référence :** Ramezani F., Lotfi S. (2013). *Social-based algorithm (SBA)*. Applied Soft Computing, 13(5), 2837-2856.

## Objectif

Ce projet adapte l'algorithme **SBA** (hybride EA + ICA) du papier original — conçu pour l'optimisation continue — à la **problème du voyageur de commerce (TSP)** en utilisant des représentations par permutations.

L'objectif est de vérifier si SBA conserve sa supériorité après adaptation, en comparant **SBA**, **EA** et **ICA** sur des instances TSPLIB.

## Structure du projet

```
projet-problem-TSP/
├── data/tsplib/              # Instances TSPLIB (berlin52, eil51, kroA100)
├── experiments/
│   ├── run_comparison.py     # Expérience complète (30 runs × 3 algos × 3 instances)
│   └── run_single.py         # Test rapide d'un algorithme
├── results/                  # Résultats générés (CSV, JSON)
├── src/tsp_sba/
│   ├── config.py             # Paramètres du papier (Pc, Pm, Pe, Pi, ...)
│   ├── tsp/                  # Chargement TSPLIB, calcul de distance
│   ├── operators/            # OX, inversion, assimilation par copie
│   ├── algorithms/
│   │   ├── sba.py            # SBA structure Monarchy
│   │   ├── ea.py             # EA autonome (baseline)
│   │   └── ica.py            # ICA autonome (baseline)
│   ├── statistics/           # Test de Wilcoxon
│   └── experiments/          # Moteur d'expérimentation
├── requirements.txt
└── README.md
```

## Adaptation TSP (contribution du projet)

| Élément (papier original) | Adaptation TSP |
|---------------------------|----------------|
| Vecteurs réels | Permutations de villes |
| Uniform Crossover | Order Crossover (OX) |
| Gene Flip Mutation | Inversion Mutation |
| Assimilation numérique | Copie de positions |
| Structure sociale | **Monarchy** (meilleure dans le papier) |

## Paramètres (papier Ramezani & Lotfi)

| Paramètre | Valeur |
|-----------|--------|
| Pc (crossover) | 0.75 |
| Pm (mutation) | 0.050505 |
| Pe (assimilation externe) | 0.1 |
| Pi (assimilation interne) | 0.1 |
| Coefficient (β) | 2.0 |
| Structure sociale | Monarchy |
| Runs par expérience | 30 |
| Test statistique | Wilcoxon |

## Installation

```bash
cd projet-problem-TSP
pip install -r requirements.txt
pip install -e .
```

## Utilisation

### Test rapide (une instance, un algorithme)

```bash
python experiments/run_single.py --instance berlin52 --algorithm SBA --quick
```

### Expérience complète

```bash
python experiments/run_comparison.py
```

### Mode rapide (3 runs, moins d'itérations)

```bash
python experiments/run_comparison.py --quick
```

### Options

```bash
python experiments/run_comparison.py --instances berlin52 eil51 --runs 30 --decades-multiplier 100
```

## Résultats

Les résultats sont sauvegardés dans `results/experiment_YYYYMMDD_HHMMSS/` :

- `raw_results.csv` — tous les runs
- `summary_statistics.csv` — moyenne, écart-type, min, max, gap vs optimum
- `wilcoxon_tests.csv` — tests SBA vs EA et SBA vs ICA
- `experiment_config.json` — configuration utilisée

## Optima connus (TSPLIB)

| Instance | Optimum |
|----------|---------|
| berlin52 | 7542 |
| eil51 | 426 |
| kroA100 | 21282 |

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

## Phrase pour le rapport

> J'ai lu l'article et compris son idée fondamentale, conservé sa structure originale, puis adapté ses opérateurs pour une représentation TSP par permutations, en gardant le même protocole expérimental afin que les résultats soient comparables à ceux de l'article original.
