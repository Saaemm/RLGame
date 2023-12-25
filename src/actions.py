from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

#prevent circular imports with engine in main
if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class Action:
    def __init__(self, entity: Entity) -> None:
        super().__init__()

        #Entity is the entity doing the action
        self.entity = entity

    @property
    def engine(self) -> Engine:
        '''Returns the engine that this action belongs to'''
        return self.entity.gamemap.engine

    def perform(self) -> None:
        '''Perform the action by 'self.entity' in 'self.engine' scope

        must be overridden/overloaded by action subclasses
        '''

        raise NotImplementedError()


class EscapeAction(Action):
    def perform(self) -> None:
        raise SystemExit()
    
class WaitAction(Action):
    def perform(self) -> None:
        pass

class ActionWithDirection(Action):
    def __init__(self, entity: Entity, dx: int, dy: int) -> None:
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        '''Returns this action's destination'''
        return (self.entity.x + self.dx, self.entity.y + self.dy)
    
    @property
    def blocking_entity(self) -> Optional[Entity]:
        '''Returns the blocking entity at the action's destination'''
        return self.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()
    
class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        #gets target at destination location
        target = self.blocking_entity

        if not target:
            return  #No entity to attack, for safety
        
        print(f"{self.entity.name} kicked {target.name}, much to its chagrin!")

class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            return #destination not in bounds
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            #note: currently requires that dx, dy at most 1
            return #destination blocked by wall/other tile
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            return  #destination is blocked by an entity
        
        self.entity.move(self.dx, self.dy)

class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        
        if self.blocking_entity is not None:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()