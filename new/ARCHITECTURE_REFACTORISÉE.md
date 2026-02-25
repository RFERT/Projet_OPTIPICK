# OPTIPICK - Architecture Refactorisée

## 📊 Vue d'ensemble

Le projet OPTIPICK est organisé selon une architecture en couches avec séparation des responsabilités :

```
src/
├── models.py              # 📦 Modèles de données (dataclasses)
├── loader.py              # 📂 Chargement JSON
├── utils.py               # 🛠 Utilitaires
├── constraints.py         # ✅ Vérifications des contraintes
│
├── allocation.py          # 🎯 JOUR 1-2 : Allocation des commandes
│
├── routing.py             # 🗺 JOUR 3a : Routage et optimisation TSP
│   ├── TSPOptimizer       # Classe pour résolution TSP
│   ├── nearest_neighbor_tsp()
│   ├── extract_unique_locations()
│   └── ...
│
├── optimization.py        # ⚙️ JOUR 4 : Allocation optimale (CSP)
│   └── AllocationOptimizer # Analyse de charge, regroupement
│
├── storage.py             # 📦 JOUR 5 : Optimisation du stockage
│   └── StorageOptimizer   # Analyse de fréquence, affinités
│
├── suite.py               # 🎭 ORCHESTRATEURS (Jours 3-5)
│   ├── run_day3()         # Appelle TSPOptimizer
│   ├── run_day4()         # Appelle AllocationOptimizer
│   ├── run_day5()         # Appelle StorageOptimizer
│   └── run_all_days_suite() # Exécute tous les jours
│
├── visualization.py       # 📈 Visualisation (bonus)
└── __init__.py
```

## 🎯 Responsabilités par fichier

### 1. **allocation.py** - Jours 1-2

- **`allocate_first_fit_day1()`** : Allocation naïve sans contraintes
- **`allocate_first_fit_day2()`** : Allocation avec contraintes activées
- **`AllocationResult`** : Dataclass pour les résultats

### 2. **routing.py** - Jour 3 (TSP)

- **`TSPOptimizer`** : Classe principale pour optimisation des tournées
  - `extract_locations()` : Extrait emplacements uniques par agent
  - `nearest_neighbor_tsp()` : Résolution TSP Nearest Neighbor
  - `optimize_agent_route()` : Optimise tournée d'un agent
  - `compute_distance_matrix()` : Matrice de distances Manhattan

- **Fonctions utilitaires** :
  - `nearest_neighbor_tsp()`
  - `extract_unique_locations()`
  - `build_nodes_with_entry()`
  - `compute_distance_matrix()`
  - `calculate_route_distance()`

### 3. **optimization.py** - Jour 4 (CSP)

- **`AllocationOptimizer`** : Optimisation de l'allocation
  - `find_compatible_orders()` : Identifie commandes regroupables
  - `compute_product_distance_sum()` : Calcule distances produits
  - `_can_combine_orders()` : Vérifie compatibilité 2 commandes

### 4. **storage.py** - Jour 5

- **`StorageOptimizer`** : Analyse et optimisation du stockage
  - `compute_product_frequency()` : Fréquence de commandage
  - `compute_product_affinity()` : Co-occurrence produits
  - `suggest_storage_reorganization()` : Propositions de zones

### 5. **suite.py** - ORCHESTRATEURS

- **`run_day3()`** : Exécute Jour 3 (crée TSPOptimizer, affiche résultats)
- **`run_day4()`** : Exécute Jour 4 (crée AllocationOptimizer, affiche résultats)
- **`run_day5()`** : Exécute Jour 5 (crée StorageOptimizer, affiche résultats)
- **`run_all_days_suite()`** : Exécute Jours 3-5 en séquence

## 🔄 Flux d'exécution

```
main.py
  │
  ├─ run_day1()        ← allocation.allocate_first_fit_day1()
  │
  ├─ run_day2()        ← allocation.allocate_first_fit_day2()
  │
  └─ run_all_days_suite()  [appelle suite.py]
      │
      ├─ run_day3()    ← routing.TSPOptimizer
      │   └─ Affiche résultats TSP
      │
      ├─ run_day4()    ← optimization.AllocationOptimizer
      │   └─ Affiche compatibilité & balance
      │
      └─ run_day5()    ← storage.StorageOptimizer
          └─ Affiche patterns & recommandations
```

## ✅ Avantages de cette architecture

| Aspect                             | Bénéfice                                                 |
| ---------------------------------- | -------------------------------------------------------- |
| **Séparation des responsabilités** | Chaque fichier = une tâche bien définie                  |
| **Réutilisabilité**                | Importer `TSPOptimizer` depuis n'importe où              |
| **Testabilité**                    | Tester `StorageOptimizer` indépendamment                 |
| **Maintenabilité**                 | Modifier `routing.py` sans toucher à `suite.py`          |
| **Extensibilité**                  | Ajouter `VisualizationOptimizer` dans `visualization.py` |
| **Clarté**                         | Structure correspond au workflow métier (Jour 1-5)       |

## 📚 Imports entre modules

```
suite.py
  ├─ from .routing import TSPOptimizer, nearest_neighbor_tsp, ...
  ├─ from .optimization import AllocationOptimizer
  └─ from .storage import StorageOptimizer

routing.py
  └─ from .models import Agent, Order, Product, Warehouse, Location

optimization.py
  └─ from .models import Agent, Order, Product, Location

storage.py
  └─ from .models import Order, Product
```

## 🚀 Utilisation

### Exécuter le projet complet

```bash
python main.py
```

### Importer un module spécifique

```python
from src.routing import TSPOptimizer
from src.optimization import AllocationOptimizer
from src.storage import StorageOptimizer

# Utiliser directement les classes
optimizer = TSPOptimizer(warehouse)
routes = optimizer.optimize_agent_route(agent, locations)
```

### Exécuter juste les Jours 3-5

```python
from src.suite import run_all_days_suite

results = run_all_days_suite(assignments, agents, orders, products, warehouse)
print(results['day3'])  # Résultats TSP
print(results['day4'])  # Résultats optimisation
print(results['day5'])  # Résultats stockage
```

## 📝 Notes de refactorisation

- ✅ Classes techniques **déplacées** de `suite.py` vers fichiers spécialisés
- ✅ Orchestrateurs **conservés** dans `suite.py` pour coordination
- ✅ Imports relatifs **utilisés** pour éviter dépendances circulaires
- ✅ Tests de compatibilité **réussis** avec tout le pipeline
