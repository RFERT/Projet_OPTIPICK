class Location():
    def __init__(self, x, y):
        self.x = x
        self.y = y 

    @classmethod
    def from_list(cls,coords: list[int]) -> "Location":
        return cls(coords[0], coords[1])
    
