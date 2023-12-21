from typing import Tuple

class Entity:
    '''
    Generic object to represetn players, enemies, items
    '''
    def __init__(self, x: int, y: int, char: str, color: Tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.char = char
        self.color = color

    def move(self, dx: int, dy: int) -> None:
        #moves the entity
        self.x += dx
        self.y += dy