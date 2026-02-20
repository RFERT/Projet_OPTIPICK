import json
from pathlib import Path


def load_json(path: str):
    """
    Charge un fichier JSON et retourne son contenu (dict ou list).

    Args:
        path (str) : Chemin (relatif ou absolu) vers le fichier JSON.

    Returns:
        dict | list : Contenu du JSON converti en objet Python.

    Raises:
        FileNotFoundError : Si le fichier n'existe pas.
        json.JSONDecodeError : Si le fichier n'est pas un JSON valide.
    """
    file_path = Path(path)

    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data

if __name__ == "__main__":
    # Test de la fonction load_json
    try:
        data = load_json("data/warehouse.json")
        print("Contenu du JSON chargé avec succès :")
        print(data)
    except Exception as e:
        print(f"Erreur lors du chargement du JSON : {e}")