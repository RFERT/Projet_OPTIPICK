from .models import Location


def manhattan(a: Location, b: Location) -> int:
    """Distance Manhattan sur une grille : |x1-x2| + |y1-y2|."""
    return abs(a.x - b.x) + abs(a.y - b.y)

def JSON_to_py()
    pass