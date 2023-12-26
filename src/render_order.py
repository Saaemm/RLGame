from enum import auto, Enum

class RenderOrder(Enum):
    '''Lower values will be rendered first, thus seen last'''
    CORPSE = auto()
    ITEM = auto()
    ACTOR = auto()