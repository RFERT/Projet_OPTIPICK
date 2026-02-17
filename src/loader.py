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
