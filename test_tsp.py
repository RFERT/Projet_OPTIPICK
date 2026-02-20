"""
Script de test pour l'algorithme TSP (Nearest Neighbor)

⚠️ NOTE: Ce test est maintenant intégré au projet principal dans main.py (Jour 3)
Exécutez simplement: python main.py

Ce script peut être utilisé pour tester de manière isolée le TSP.
"""

from src.models import Location
from src.routing import nearest_neighbor_tsp, calculate_route_distance
from src.utils import manhattan

def test_nearest_neighbor_simple():
    """Test simple du TSP avec l'heuristique du Plus Proche Voisin"""
    print("=== Test TSP - Plus Proche Voisin ===\n")
    
    # Points d'entrée (entrepôt)
    entry = Location(0, 0)
    
    # Emplacements à visiter (exemple)
    locations = [
        Location(2, 1),
        Location(1, 0),
        Location(4, 0),
        Location(3, 4),
        Location(2, 3),
    ]
    
    print("Entrée de l'entrepôt:", entry)
    print("Emplacements à visiter:")
    for i, loc in enumerate(locations):
        print(f"  {i+1}. {loc}")
    
    # Résoudre le TSP
    route = nearest_neighbor_tsp(locations, entry, manhattan)
    distance = calculate_route_distance(route, manhattan)
    
    print("\n=== Résultats ===")
    print("Route optimisée:")
    for i, loc in enumerate(route):
        if i == 0:
            print(f"  Départ: {loc}")
        elif i == len(route) - 1:
            print(f"  Retour: {loc}")
        else:
            print(f"  {i}. {loc}")
    
    print(f"\nDistance totale: {distance}")
    print(f"Nombre de visites: {len(route) - 2} (entrée, sortie non comptées)")
    return distance

if __name__ == "__main__":
    test_nearest_neighbor_simple()
    print("\n✅ Test réussi !")
