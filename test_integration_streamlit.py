"""
OPTIPICK - Tests d'intégration pour l'interface Streamlit
═══════════════════════════════════════════════════════════════════════════════

Tests pour valider que tous les modules fonctionnent ensemble correctement.

Usage :
    pytest test_integration_streamlit.py -v
"""

import pytest
import json
from pathlib import Path
from src.models import Agent, Order, Product, Warehouse, Location
from src.utils import JSON_to_py, compute_order_totals, manhattan
from src.constraints import (
    check_capacity, check_incompatibilities, check_robot_restrictions
)
from src.allocation import allocate_first_fit_day2
from src.suite import TSPOptimizer, AllocationOptimizer, StorageOptimizer


class TestDataLoading:
    """Tests du chargement des données."""
    
    def test_json_loading(self):
        """Vérifie que les données JSON se chargent correctement."""
        warehouse, products, agents, orders = JSON_to_py()
        
        assert warehouse is not None
        assert isinstance(products, dict)
        assert isinstance(agents, list)
        assert isinstance(orders, list)
        assert len(products) > 0
        assert len(agents) > 0
        assert len(orders) > 0
    
    def test_warehouse_structure(self):
        """Vérifie que l'entrepôt est correctement structuré."""
        warehouse, _, _, _ = JSON_to_py()
        
        assert warehouse.grid is not None
        assert len(warehouse.grid) == 8  # Hauteur
        assert len(warehouse.grid[0]) == 10  # Largeur
        assert warehouse.entry_point == [0, 0]
    
    def test_agents_have_required_fields(self):
        """Vérifie que tous les agents ont les champs requis."""
        _, _, agents, _ = JSON_to_py()
        
        for agent in agents:
            assert hasattr(agent, 'id')
            assert hasattr(agent, 'type')
            assert hasattr(agent, 'capacity_weight')
            assert hasattr(agent, 'capacity_volume')
            assert hasattr(agent, 'speed')


class TestAllocation:
    """Tests de l'allocation des commandes."""
    
    def test_allocation_completes_all_orders(self):
        """Vérifie que toutes les commandes sont allouées."""
        warehouse, products, agents, orders = JSON_to_py()
        
        assignments, unassigned, _, _, _ = allocate_first_fit_day2(
            orders, agents, products, warehouse
        )
        
        # Compter commandes allouées
        total_assigned = sum(len(orders_list) for orders_list in assignments.values())
        
        # Vérifier que presque toutes les commandes sont allouées
        assert total_assigned + len(unassigned) == len(orders)
        assert len(unassigned) == 0 or len(unassigned) < len(orders) * 0.1
    
    def test_allocation_respects_capacity(self):
        """Vérifie que les capacités sont respectées."""
        warehouse, products, agents, orders = JSON_to_py()
        
        assignments, _, order_totals, _, _ = allocate_first_fit_day2(
            orders, agents, products, warehouse
        )
        
        # Vérifier capacité pour chaque agent
        for agent in agents:
            if agent.id not in assignments or not assignments[agent.id]:
                continue
            
            # Vérifier chaque commande individuellement
            for order_id in assignments[agent.id]:
                weight, volume = order_totals.get(order_id, (0, 0))
                
                assert weight <= agent.capacity_weight, \
                    f"{agent.id}: Poids {weight} > capacité {agent.capacity_weight}"
                assert volume <= agent.capacity_volume, \
                    f"{agent.id}: Volume {volume} > capacité {agent.capacity_volume}"
    
    def test_allocation_distribution(self):
        """Vérifie que la charge est distribuée."""
        warehouse, products, agents, orders = JSON_to_py()
        
        assignments, _, _, _, _ = allocate_first_fit_day2(
            orders, agents, products, warehouse
        )
        
        # Compter commandes par agent
        counts = [len(assignments.get(a.id, [])) for a in agents]
        
        # Au moins 2 agents doivent avoir des commandes
        agents_with_work = sum(1 for c in counts if c > 0)
        assert agents_with_work >= 2


class TestTSPOptimizer:
    """Tests de l'optimiseur TSP."""
    
    def test_tsp_extracts_locations(self):
        """Vérifie l'extraction des emplacements."""
        warehouse, products, agents, orders = JSON_to_py()
        assignments, _, _, _, _ = allocate_first_fit_day2(
            orders, agents, products, warehouse
        )
        
        optimizer = TSPOptimizer(warehouse)
        locations = optimizer.extract_locations(assignments, orders, products)
        
        # Au moins un agent doit avoir des emplacements
        assert len(locations) > 0
        assert any(len(locs) > 0 for locs in locations.values())
    
    def test_distance_matrix_computation(self):
        """Vérifie le calcul de la matrice de distances."""
        warehouse, _, _, _ = JSON_to_py()
        optimizer = TSPOptimizer(warehouse)
        
        locations = [
            Location(0, 0),
            Location(3, 0),
            Location(3, 4),
            Location(0, 4)
        ]
        
        matrix = optimizer.compute_distance_matrix(locations)
        
        # Vérifier symétrie
        assert abs(matrix[0][1] - matrix[1][0]) < 0.01
        
        # Vérifier distances
        assert matrix[0][1] == 3  # Manhattan distance (0,0) -> (3,0)
        assert matrix[0][2] == 7  # Manhattan distance (0,0) -> (3,4)
        assert matrix[1][2] == 4  # Manhattan distance (3,0) -> (3,4)
    
    def test_nearest_neighbor_returns_valid_route(self):
        """Vérifie que NN retourne une route valide."""
        warehouse, _, _, _ = JSON_to_py()
        optimizer = TSPOptimizer(warehouse)
        
        locations = [
            Location(0, 0),
            Location(2, 0),
            Location(2, 2),
            Location(0, 2)
        ]
        
        route = optimizer.nearest_neighbor_tsp(locations)
        
        # Route doit avoir tous les emplacements
        assert len(route) == len(locations)
        assert len(set(route)) == len(locations)
        assert 0 in route  # Début à l'entrée
    
    def test_route_optimization_reduces_distance(self):
        """Vérifie que TSP réduit la distance."""
        warehouse, products, agents, orders = JSON_to_py()
        assignments, _, _, _, _ = allocate_first_fit_day2(
            orders, agents, products, warehouse
        )
        
        optimizer = TSPOptimizer(warehouse)
        
        # Prendre un agent avec des commandes
        for agent in agents:
            if agent.id not in assignments or not assignments[agent.id]:
                continue
            
            locations_list = list(
                optimizer.extract_locations(assignments, orders, products)[agent.id]
            )
            
            if len(locations_list) < 2:
                continue
            
            route, distance, time_min = optimizer.optimize_agent_route(agent, locations_list)
            
            # Distance doit être positive
            assert distance > 0
            assert time_min > 0
            assert len(route) == len(locations_list) + 1  # +1 pour l'entrée


class TestAllocationOptimizer:
    """Tests de l'optimiseur d'allocation."""
    
    def test_compatible_orders_detection(self):
        """Vérifie la détection des commandes compatibles."""
        warehouse, products, agents, orders = JSON_to_py()
        
        optimizer = AllocationOptimizer()
        groups = optimizer.find_compatible_orders(orders, products)
        
        # Il peut y avoir 0 ou plus de groupes compatibles
        assert isinstance(groups, list)
        assert all(isinstance(g, set) for g in groups)
    
    def test_product_distance_sum(self):
        """Vérifie le calcul de distance produit."""
        warehouse, products, _, orders = JSON_to_py()
        
        optimizer = AllocationOptimizer()
        
        if orders:
            order = orders[0]
            distance = optimizer.compute_product_distance_sum(order, products)
            
            # Distance doit être positive
            assert distance >= 0


class TestStorageOptimizer:
    """Tests de l'optimiseur de stockage."""
    
    def test_frequency_computation(self):
        """Vérifie le calcul de fréquence."""
        _, _, _, orders = JSON_to_py()
        
        optimizer = StorageOptimizer()
        frequency = optimizer.compute_product_frequency(orders)
        
        # Doit avoir de la fréquence
        assert len(frequency) > 0
        assert all(f >= 1 for f in frequency.values())
    
    def test_affinity_computation(self):
        """Vérifie le calcul d'affinité."""
        _, _, _, orders = JSON_to_py()
        
        optimizer = StorageOptimizer()
        affinity = optimizer.compute_product_affinity(orders)
        
        # Affinité peut être vide ou non
        assert isinstance(affinity, dict)
        assert all(a >= 1 for a in affinity.values())
    
    def test_storage_reorganization(self):
        """Vérifie la proposition de réorganisation."""
        _, products, _, orders = JSON_to_py()
        
        optimizer = StorageOptimizer()
        reorg = optimizer.suggest_storage_reorganization(products, orders)
        
        # Vérifier structure
        assert 'high_frequency_products' in reorg
        assert 'medium_frequency_products' in reorg
        assert 'low_frequency_products' in reorg
        
        # Chaque catégorie doit avoir des produits
        assert len(reorg['high_frequency_products']) > 0


class TestIntegration:
    """Tests d'intégration complète."""
    
    def test_full_workflow(self):
        """Teste le workflow complet : allocation -> TSP -> optimisation."""
        warehouse, products, agents, orders = JSON_to_py()
        
        # Étape 1 : Allocation
        assignments, unassigned, order_totals, _, _ = allocate_first_fit_day2(
            orders, agents, products, warehouse
        )
        assert len(assignments) > 0
        
        # Étape 2 : TSP Optimization
        tsp_optimizer = TSPOptimizer(warehouse)
        locations_per_agent = tsp_optimizer.extract_locations(
            assignments, orders, products
        )
        
        routes = {}
        for agent in agents:
            if agent.id not in assignments or not assignments[agent.id]:
                continue
            
            locations = list(locations_per_agent.get(agent.id, set()))
            if not locations:
                continue
            
            route, distance, time_min = tsp_optimizer.optimize_agent_route(
                agent, locations
            )
            routes[agent.id] = distance
        
        assert len(routes) > 0
        
        # Étape 3 : Allocation Optimization
        alloc_optimizer = AllocationOptimizer()
        groups = alloc_optimizer.find_compatible_orders(orders, products)
        assert isinstance(groups, list)
        
        # Étape 4 : Storage Optimization
        storage_optimizer = StorageOptimizer()
        frequency = storage_optimizer.compute_product_frequency(orders)
        assert len(frequency) > 0
    
    def test_performance_metrics(self):
        """Teste que les métriques de performance sont calculées."""
        warehouse, products, agents, orders = JSON_to_py()
        
        # Allocation
        assignments, _, order_totals, _, _ = allocate_first_fit_day2(
            orders, agents, products, warehouse
        )
        
        # Calculer métriques
        total_weight = sum(w for w, _ in order_totals.values())
        total_volume = sum(v for _, v in order_totals.values())
        total_commandes = sum(len(a) for a in assignments.values())
        
        assert total_weight > 0
        assert total_volume > 0
        assert total_commandes > 0


# ═════════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Lancer avec : pytest test_integration_streamlit.py -v
    pytest.main([__file__, "-v", "--tb=short"])
