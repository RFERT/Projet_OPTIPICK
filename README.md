# 📦 OPTIPICK - Système d'Optimisation d'Entrepôt

Système complet d'optimisation d'allocation et de routage pour la gestion d'un entrepôt, avec allocation intelligente des commandes aux agents et simulation des trajets de picking.

## 🎯 Objectifs du Projet

Ce projet implémente une solution multi-jour pour optimiser :
- **Jour 1** : Allocation naïve (sans contraintes)
- **Jour 2** : Allocation avec contraintes
- **Jour 3** : Optimisation du routage et des trajets
- **Jour 4** : Réaffectation dynamique des commandes
- **Jour 5** : Optimisation avancée avec contraintes de stockage

## 📁 Structure du Projet

```
OPTIPICK/
├── app_streamlit.py           # Interface Web interactive
├── main.py                     # Script principal d'exécution
├── data/                       # Données de simulation
│   ├── agents.json            # Profils des agents
│   ├── orders.json            # Commandes à traiter
│   ├── products.json          # Catalogue produits
│   └── warehouse.json         # Configuration entrepôt
├── src/                        # Code source principal
│   ├── models.py              # Modèles de données (Warehouse, Product, Agent, Order)
│   ├── loader.py              # Chargement et conversion JSON ↔ Python
│   ├── allocation.py          # Algorithmes d'allocation
│   ├── routing.py             # Calculs de trajectoires et TSP
│   ├── constraints.py         # Vérification des contraintes
│   ├── optimization.py        # Optimisation des allocations
│   ├── storage.py             # Optimisation du stockage
│   ├── visualization.py       # Visualisation des données
│   └── utils.py               # Fonctions utilitaires
├── tests/                      # Suite de tests
│   ├── test_allocation.py
│   ├── test_constraints.py
│   ├── test_routing.py
│   ├── test_tsp.py
│   ├── test_integration_streamlit.py
│   └── verify_environment.py
├── results/                    # Résultats d'exécution
│   ├── allocation_results.json
│   ├── metrics.json
│   └── routes.json
└── requirements.txt            # Dépendances Python
```

## 🚀 Démarrage Rapide

### Installation

1. **Cloner le repository**
   ```bash
   git clone <url-du-repo>
   cd Projet_OPTIPICK
   ```

2. **Créer un environnement virtuel**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # ou
   .venv\Scripts\activate     # Windows
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

### Exécution

#### Mode Console (Script Principal)
```bash
python main.py
```
Exécute la simulation complète sur les 5 jours et affiche les résultats en console.

#### Mode Interface Web (Streamlit)
```bash
streamlit run app_streamlit.py
```
Lance l'interface interactive dans votre navigateur (http://localhost:8501)

## 📊 Modules Principaux

### `models.py` - Modèles de Données
- `Warehouse` : Configuration de l'entrepôt (dimensions, zones)
- `Product` : Produits avec poids, dimensions, catégorie
- `Agent` : Agents de picking (type, capacité, vitesse)
- `Order` : Commandes avec articles et priorité
- `Location` : Positions 3D dans l'entrepôt

### `allocation.py` - Allocation des Commandes
- `allocate_first_fit_day1()` : Allocation simple (Jour 1)
- `allocate_with_constraints_day2()` : Allocation avec contraintes (Jour 2)
- Algorithmes optimisés : First-Fit, Best-Fit, Round-Robin

### `routing.py` - Calcul des Trajets
- `calculate_distance()` : Distance euclidienne
- `traveling_salesman_problem()` : Résolution du TSP
- `generate_route()` : Génération de trajectoires optimisées

### `constraints.py` - Vérification des Contraintes
- Capacité des agents
- Limites de poids
- Compatibilité des produits
- Contraintes temporelles

### `optimization.py` - Optimisation
- `AllocationOptimizer` : Classe d'optimisation multi-objectif
- Minimisation du coût de trajet
- Équilibrage de charge

### `storage.py` - Optimisation du Stockage
- `StorageOptimizer` : Optimisation de la disposition des produits
- Rapprochement des articles similaires
- Minimisation des distances de picking

## 📈 Fonctionnalités de l'Interface Streamlit

### 📋 Onglets Disponibles

1. **Tableau de Bord** 
   - Statistiques globales
   - Métriques de performance
   - Résumé des allocations

2. **Jour 1-2 : Allocation**
   - Visualisation des allocations naïves et optimisées
   - Tableau des agents et leurs commandes
   - Distribution de charge

3. **Jour 3 : Routage**
   - Animation des trajets dans l'entrepôt
   - Visualisation 2D/3D des routes
   - Statistiques de distance

4. **Jour 4 : Réaffectation**
   - Comparaison des allocations
   - Histogrammes de distribution
   - Amélioration des métriques

5. **Jour 5 : Optimisation Avancée**
   - Graphiques de performance
   - Heatmaps de l'entrepôt
   - Analyse comparative

## 🔧 Configuration des Données

### Format des Données JSON

**warehouse.json** : Configuration de l'entrepôt
```json
{
  "name": "Warehouse A",
  "width": 100,
  "height": 50,
  "depth": 20,
  "zones": [...]
}
```

**products.json** : Catalogue produits
```json
{
  "P001": {
    "name": "Produit 1",
    "weight": 5.0,
    "width": 10,
    "height": 10,
    "depth": 10,
    "category": "Electronics"
  }
}
```

**agents.json** : Profils des agents
```json
{
  "A001": {
    "name": "Agent 1",
    "type": "Picker",
    "max_weight": 50,
    "speed": 2.0
  }
}
```

**orders.json** : Commandes
```json
{
  "O001": {
    "customer": "Customer 1",
    "items": ["P001", "P002"],
    "priority": "HIGH",
    "deadline": "2024-03-01"
  }
}
```

## 🧪 Tests

Exécuter la suite de tests :
```bash
python -m pytest tests/
```

Tests disponibles :
- `test_allocation.py` : Tests des algorithmes d'allocation
- `test_constraints.py` : Vérification des contraintes
- `test_routing.py` : Validation du routage
- `test_tsp.py` : Résolution du TSP
- `test_integration_streamlit.py` : Tests d'intégration

## 📊 Résultats et Métriques

Les résultats d'exécution sont sauvegardés dans le dossier `results/` :
- `allocation_results.json` : Détail des allocations par jour
- `metrics.json` : Métriques de performance
- `routes.json` : Trajectoires et distances

### Métriques Principales
- **Taux d'allocation** : % de commandes assignées
- **Distance moyenne** : Distance totale de picking par agent
- **Utilisation de capacité** : % de capacité utilisée
- **Temps estimé** : Durée de picking estimée
- **Coût** : Coût total de logistique

## 🔄 Flux de Travail par Jour

### Jour 1 : Allocation Naïve
Allocation simple des commandes aux agents sans considération de contraintes.

### Jour 2 : Allocation Optimisée
Allocation prenant en compte les contraintes (capacité, poids, compatibilité).

### Jour 3 : Routage Optimisé
Calcul des trajets optimaux dans l'entrepôt (TSP).

### Jour 4 : Réaffectation Dynamique
Analyse et réaffectation des commandes pour améliorer les métriques.

### Jour 5 : Optimisation Avancée
Optimisation complète du système avec contraintes de stockage et multi-objectifs.

## 📝 Variables d'Environnement

Vous pouvez configurer le comportement via des variables d'environnement :
```bash
export DATA_DIR="./data"
export RESULTS_DIR="./results"
export LOG_LEVEL="INFO"
```

## 🐛 Dépannage

### ModuleNotFoundError sur `models`
**Solution** : Assurez-vous que les imports utilisent les chemins relatifs (`.models` au lieu de `models`).

### Port 8501 déjà utilisé
```bash
streamlit run app_streamlit.py --server.port 8502
```

### Données manquantes
Vérifiez que les fichiers JSON existent dans le dossier `data/` :
```bash
ls -la data/
```

## 📚 Documentation Supplémentaire

- [Guide Streamlit](new/GUIDE_STREAMLIT.py)
- [Architecture du Projet](new/ARCHITECTURE_REFACTORISÉE.md)
- [Résumé de Refactorisation](new/REFACTORISATION_RÉSUMÉ.md)

## 📄 Licence

Ce projet est licencié sous la licence [LICENSE](LICENSE).

## 👥 Auteur

Projet OPTIPICK - 2025

---

**Questions ?** Consultez les documents dans le dossier `new/` ou exécutez les tests pour valider votre installation.
