# Rapport des résultats — Avant l'ajout du 2-opt

**Auteur :** LEHOUEIMEL Yahfdhou  
**Référence :** Ramezani F., Lotfi S. (2013). *Social-based algorithm (SBA)*. Applied Soft Computing, 13(5), 2837–2856.  
**Problème :** Travelling Salesman Problem (TSP)  
**Date de l'expérience :** 2026-06-17 (`experiment_20260617_173656`)  
**État :** Résultats obtenus **sans** recherche locale (2-opt)

---

## 1. Contexte du projet

L'article original de Ramezani & Lotfi (2013) propose le **Social-Based Algorithm (SBA)** — un hybride entre **Evolutionary Algorithm (EA)** et **Imperialist Competitive Algorithm (ICA)** — et l'évalue sur des **fonctions d'optimisation continue** (Sphere, Rastrigin, Rosenbrock, etc.).

Ce projet adapte SBA au **Travelling Salesman Problem (TSP)** :

- **TSP :** trouver le plus court tour hamiltonien passant par N villes une fois chacune et revenant au point de départ.
- **Représentation :** permutations de villes (au lieu de vecteurs réels).
- **Opérateurs adaptés :** Order Crossover (OX), mutation par inversion, assimilation par copie de positions.
- **Structure sociale :** Monarchy (la meilleure structure dans l'article original).

L'objectif n'est pas de battre les solveurs TSP de référence (Concorde, LKH), mais de **vérifier si SBA conserve son avantage** face à EA et ICA après adaptation au TSP.

---

## 2. Protocole expérimental

### 2.1 Instances TSPLIB

| Instance | Nombre de villes | Optimum connu | Type |
|----------|------------------|---------------|------|
| **berlin52** | 52 | 7 542 | EUC_2D |
| **eil51** | 51 | 426 | EUC_2D |
| **kroA100** | 100 | 21 282 | EUC_2D |

### 2.2 Algorithmes comparés

| Algorithme | Description |
|------------|-------------|
| **SBA** | Hybride EA + ICA, structure Monarchy (algorithme principal) |
| **EA** | Algorithme évolutionnaire autonome (baseline du papier) |
| **ICA** | Algorithme impérialiste compétitif autonome (baseline du papier) |

### 2.3 Paramètres (papier Ramezani & Lotfi)

| Paramètre | Symbole | Valeur |
|-----------|---------|--------|
| Probabilité de crossover | Pc | 0.75 |
| Probabilité de mutation | Pm | 0.050505 |
| Assimilation externe | Pe | 0.1 |
| Assimilation interne | Pi | 0.1 |
| Coefficient d'assimilation | β | 2.0 |
| Nombre d'impérialistes | — | 8 |
| Nombre de pays | — | 22 |
| Personnes par pays | — | 4 |
| Structure sociale | — | Monarchy |
| Multiplicateur de décennies | — | 100 |

### 2.4 Protocole statistique

| Élément | Valeur |
|---------|--------|
| Nombre de runs par (instance, algorithme) | **30** |
| Total d'exécutions | **270** (3 × 3 × 30) |
| Test statistique | **Wilcoxon signed-rank** (apparié, α = 0.05) |
| Métrique principale | Longueur du meilleur tour trouvé (`best_cost`) |
| Recherche locale (2-opt) | **Non utilisée** |

---

## 3. Tableau récapitulatif des statistiques

### 3.1 Résultats complets (30 runs par configuration)

| Instance | Algorithme | Moyenne | Écart-type | Min | Max | Médiane | Optimum | Gap moyen (%) |
|----------|------------|---------|------------|-----|-----|---------|---------|---------------|
| berlin52 | **SBA** | 7 931.10 | 115.25 | 7 732 | 8 108 | 7 976.5 | 7 542 | **5.16** |
| berlin52 | EA | 8 017.17 | 201.09 | **7 542** | 8 660 | 8 004.5 | 7 542 | 6.30 |
| berlin52 | ICA | 8 047.07 | 193.90 | 7 547 | 8 437 | 8 051.0 | 7 542 | 6.70 |
| eil51 | **SBA** | **435.30** | **4.41** | **430** | 447 | 433.5 | 426 | **2.18** |
| eil51 | EA | 449.07 | 7.77 | 431 | 466 | 448.5 | 426 | 5.41 |
| eil51 | ICA | 447.80 | 8.98 | 432 | 467 | 448.0 | 426 | 5.12 |
| kroA100 | SBA | 22 441.93 | 366.41 | 21 916 | 23 343 | 22 364.0 | 21 282 | 5.45 |
| kroA100 | **EA** | **22 388.93** | 469.83 | **21 611** | 23 318 | 22 387.0 | 21 282 | **5.20** |
| kroA100 | ICA | 24 160.80 | 421.43 | 23 126 | 24 853 | 24 142.5 | 21 282 | 13.53 |

*Gap moyen (%) = 100 × (moyenne − optimum) / optimum*

### 3.2 Meilleur cas par algorithme (gap minimum)

| Instance | Algorithme | Meilleur tour | Gap min (%) | Atteint l'optimum ? |
|----------|------------|---------------|-------------|---------------------|
| berlin52 | SBA | 7 732 | 2.52 | Non (0/30 runs) |
| berlin52 | EA | **7 542** | **0.00** | **Oui (1/30 runs)** |
| berlin52 | ICA | 7 547 | 0.07 | Non (proche, 1 run ≤ 1%) |
| eil51 | SBA | 430 | 0.94 | Non (1 run ≤ 1%) |
| eil51 | EA | 431 | 1.17 | Non |
| eil51 | ICA | 432 | 1.41 | Non |
| kroA100 | SBA | 21 916 | 2.98 | Non |
| kroA100 | EA | 21 611 | 1.55 | Non |
| kroA100 | ICA | 23 126 | 8.66 | Non |

### 3.3 Classement par instance (selon la moyenne)

| Rang | berlin52 | eil51 | kroA100 |
|------|----------|-------|---------|
| 1ᵉʳ | **SBA** (7 931) | **SBA** (435) | **EA** (22 389) |
| 2ᵉ | EA (8 017) | ICA (448) | SBA (22 442) |
| 3ᵉ | ICA (8 047) | EA (449) | ICA (24 161) |

---

## 4. Tests statistiques de Wilcoxon (SBA vs autres)

Le test de Wilcoxon compare les 30 résultats appariés de SBA contre EA ou ICA sur chaque instance.

| Instance | Comparaison | Moyenne SBA | Moyenne autre | p-value | Significatif (α=0.05) | Meilleur | Amélioration SBA (%) |
|----------|-------------|-------------|---------------|---------|------------------------|----------|----------------------|
| berlin52 | SBA vs EA | 7 931.10 | 8 017.17 | 0.0473 | **Oui** | **SBA** | +1.07 % |
| berlin52 | SBA vs ICA | 7 931.10 | 8 047.07 | 0.0082 | **Oui** | **SBA** | +1.44 % |
| eil51 | SBA vs EA | 435.30 | 449.07 | 4.31×10⁻⁶ | **Oui** | **SBA** | +3.07 % |
| eil51 | SBA vs ICA | 435.30 | 447.80 | 1.07×10⁻⁵ | **Oui** | **SBA** | +2.79 % |
| kroA100 | SBA vs EA | 22 441.93 | 22 388.93 | 0.4400 | Non | EA (−0.24 %) | — |
| kroA100 | SBA vs ICA | 22 441.93 | 24 160.80 | 1.73×10⁻⁶ | **Oui** | **SBA** | +7.11 % |

*Amélioration SBA (%) = 100 × (1 − moyenne_SBA / moyenne_autre), formule Eq. (14) du papier.*

---

## 5. Analyse détaillée

### 5.1 berlin52 (52 villes)

**Observations :**

- SBA obtient la **meilleure moyenne** (7 931) avec l'**écart-type le plus faible** (115), ce qui indique une meilleure **stabilité** que EA (σ = 201) et ICA (σ = 194).
- SBA bat EA et ICA de manière **statistiquement significative** (p = 0.047 et p = 0.008).
- EA a trouvé l'**optimum exact une fois** (7 542) sur 30 runs, mais sa moyenne reste inférieure à SBA à cause de runs très mauvais (max = 8 660).
- Gap moyen SBA : **5.16 %** — acceptable pour une métaheuristique sans recherche locale, mais loin d'un résultat « excellent ».

**Interprétation :** SBA tire profit de la structure Monarchy (EA intra-pays + assimilation inter-pays) pour explorer plus efficacement l'espace des permutations sur cette instance de taille moyenne.

### 5.2 eil51 (51 villes)

**Observations :**

- **Meilleure performance globale du projet** : gap moyen SBA de seulement **2.18 %**.
- SBA domine clairement EA et ICA avec des p-values extrêmement faibles (< 10⁻⁵).
- Meilleur tour SBA : 430 (gap 0.94 % de l'optimum 426) — très proche mais jamais optimal sur 30 runs.
- SBA est aussi le plus **stable** (σ = 4.41 vs 7.77 pour EA).

**Interprétation :** Sur les petites instances, l'adaptation SBA au TSP est la plus convaincante. La combinaison OX + inversion + assimilation suffit à bien performer sans 2-opt.

### 5.3 kroA100 (100 villes)

**Observations :**

- Instance la plus difficile : gap moyen ~5 % pour SBA et EA, **13.5 %** pour ICA.
- **SBA n'est pas significativement meilleur que EA** (p = 0.44) ; EA est légèrement devant en moyenne (−0.24 %).
- **SBA bat ICA de façon très significative** (p < 10⁻⁶, +7.11 % d'amélioration).
- ICA semble mal adapté aux instances de 100 villes (assimilation par copie de positions moins efficace sur de grands permutations).

**Interprétation :** L'avantage de SBA diminue quand la taille de l'instance augmente. La structure hybride ne compense pas entièrement la difficulté combinatoire du TSP à 100 villes.

### 5.4 ICA — point faible récurrent

| Instance | Gap moyen ICA | Gap moyen SBA | Écart |
|----------|---------------|---------------|-------|
| berlin52 | 6.70 % | 5.16 % | ICA +1.54 pp |
| eil51 | 5.12 % | 2.18 % | ICA +2.94 pp |
| kroA100 | **13.53 %** | 5.45 % | ICA +8.08 pp |

ICA est systématiquement le moins performant, avec une dégradation marquée sur kroA100. Cela confirme l'intérêt de l'hybridation SBA (EA + ICA) plutôt que ICA seul.

### 5.5 Stabilité (écart-type)

| Instance | σ SBA | σ EA | σ ICA | Plus stable |
|----------|-------|------|-------|-------------|
| berlin52 | **115.25** | 201.09 | 193.90 | SBA |
| eil51 | **4.41** | 7.77 | 8.98 | SBA |
| kroA100 | **366.41** | 469.83 | 421.43 | SBA |

SBA présente l'écart-type le plus faible sur **les trois instances**, signe d'une convergence plus régulière.

---

## 6. Évaluation globale de la qualité des solutions

### 6.1 Les solutions sont-elles « excellentes » ?

| Critère | Seuil « excellent » | Résultat actuel | Verdict |
|---------|---------------------|-----------------|---------|
| Gap moyen | < 1 % | 2.18 % – 5.45 % (SBA) | Non atteint |
| Atteinte de l'optimum | Régulière (≥ 50 % des runs) | 1/270 runs (EA, berlin52) | Non atteint |
| Supériorité statistique SBA | Significatif sur toutes instances | 2/3 instances vs EA, 3/3 vs ICA | Partiellement atteint |
| Comparaison algorithmique | SBA ≥ EA, ICA | Oui sauf kroA100 vs EA | Globalement atteint |

**Conclusion :** Les solutions sont de **qualité acceptable à bonne** pour une adaptation directe de SBA au TSP, mais **pas excellentes** au sens de la littérature TSP (où l'on vise gap < 1 % ou optimum systématique).

### 6.2 Pourquoi les gaps persistent-ils ?

1. **Absence de recherche locale** — pas de 2-opt ni 3-opt pour éliminer les croisements d'arêtes dans les tours.
2. **Adaptation depuis l'optimisation continue** — les opérateurs (OX, inversion) sont des approximations des opérateurs du papier.
3. **Nature NP-difficile du TSP** — l'espace de recherche croît en factorielle (51! ≈ 10⁶⁶ pour eil51).
4. **Pas de heuristiques constructives avancées** — seul un nearest-neighbor est utilisé pour l'initialisation du premier pays.

### 6.3 Ce qui fonctionne bien

| Aspect | Évaluation |
|--------|------------|
| Adaptation SBA → TSP (permutations) | Réussie |
| Structure Monarchy | Efficace sur berlin52 et eil51 |
| Protocole expérimental (30 runs, Wilcoxon) | Conforme au papier |
| SBA vs ICA | SBA significativement meilleur (3/3) |
| SBA vs EA | SBA significativement meilleur (2/3) |
| Stabilité de SBA | Meilleure sur les 3 instances |

---

## 7. Synthèse par objectif du projet

| Objectif du professeur | Statut | Commentaire |
|------------------------|--------|-------------|
| Appliquer SBA au TSP (pas seulement fonctions mathématiques) | Atteint | Représentation par permutations, opérateurs adaptés |
| Comparer SBA, EA, ICA | Atteint | 270 exécutions, tableaux et tests complets |
| Vérifier la supériorité de SBA | Partiellement atteint | Significatif sur 2/3 instances vs EA, 3/3 vs ICA |
| Obtenir des solutions proches de l'optimum | Non atteint | Gaps 2–5 % en moyenne |

---

## 8. Motivation pour la phase suivante (2-opt)

Ce document constitue la **ligne de base (baseline)** avant l'ajout du **2-opt** — une recherche locale qui :

- supprime les croisements d'arêtes dans un tour ;
- améliore un tour existant sans changer l'algorithme global ;
- est standard dans la littérature TSP pour réduire les gaps de plusieurs points de pourcentage.

**Hypothèse :** l'ajout de 2-opt après crossover/mutation devrait :

- réduire les gaps moyens vers **< 1–2 %** ;
- permettre d'atteindre l'optimum plus fréquemment sur eil51 et berlin52 ;
- conserver l'ordre relatif SBA > EA > ICA (à vérifier par une nouvelle expérience).

Une comparaison **avant/après 2-opt** permettra de quantifier l'apport de la recherche locale indépendamment de l'adaptation SBA.

---

## 9. Fichiers de résultats

| Fichier | Contenu |
|---------|---------|
| `results/experiment_20260617_173656/raw_results.csv` | 270 lignes (tous les runs) |
| `results/experiment_20260617_173656/summary_statistics.csv` | Statistiques agrégées |
| `results/experiment_20260617_173656/wilcoxon_tests.csv` | Tests SBA vs EA / ICA |
| `results/experiment_20260617_173656/experiment_config.json` | Configuration utilisée |
| `results/experiment_20260617_173656/comparison_barplot.png` | Graphique comparatif |

---

## 10. Conclusion

L'expérience **sans 2-opt** démontre que l'adaptation de SBA au TSP est **fonctionnelle et partiellement concluante** :

- **SBA est significativement meilleur que EA et ICA** sur berlin52 et eil51.
- **SBA reste comparable à EA** sur kroA100, mais **nettement supérieur à ICA**.
- Les solutions obtenues ont un **gap moyen de 2–5 %**, ce qui est **honorable pour un projet académique** mais **insuffisant pour une résolution « excellente »** du TSP.

Ce rapport sert de référence pour mesurer l'impact de la phase suivante : **intégration du 2-opt** et nouvelle campagne expérimentale.

---

*Document généré avant l'implémentation du 2-opt — projet TSP-SBA, LEHOUEIMEL Yahfdhou.*
