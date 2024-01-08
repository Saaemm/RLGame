from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import configs.color as color
from entity import Actor
import exceptions

#prevent circular imports with engine in main
if TYPE_CHECKING:
    from engine import Engine
    from entity import Actor, Entity, ConsumableItem, EquippableItem


class Action:
    def __init__(self, entity: Actor) -> None:
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
    
class PickupAction(Action):
    '''Pickup an item and add it to inventory, if there is room for it.'''

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        item = self.engine.game_map.get_item_at_location(actor_location_x, actor_location_y)

        if item is None:
            raise exceptions.Impossible("Nothing here to pick up...")
        
        if len(inventory.items) >= inventory.capacity:
            raise exceptions.Impossible("Your inventory is full.")
                
        self.engine.game_map.entities.remove(item)
        item.parent = self.entity.inventory
        inventory.items.append(item)

        self.engine.message_log.add_message(f"You picked up the {item.name}!")

class ConsumableItemAction(Action):
    def __init__(self, entity: Actor, item: ConsumableItem, target_xy: Optional[Tuple[int, int]] = None) -> None:
        super().__init__(entity)
        self.item = item
        if target_xy is None:
            target_xy = (entity.x, entity.y)
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        '''Return the actor at this action's destination'''
        return self.engine.game_map.get_actor_at_location(*self.target_xy)
    
    def perform(self) -> None:
        '''Invokes the item's ability; action will be given to provide context'''
        self.item.consumable.activate(self)

class DropItem(ConsumableItemAction):
    def perform(self) -> None:
        self.entity.inventory.drop(self.item)

class EquipAction(Action):
    def __init__(self, entity: Actor, item: EquippableItem) -> None:
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)

class EscapeAction(Action):
    def perform(self) -> None:
        raise SystemExit()
    
class WaitAction(Action):
    def perform(self) -> None:
        pass

class TakeStairsAction(Action):
    def perform(self) -> None:
        '''
        Take the stairs down if it exists
        '''
        if (self.entity.x, self.entity.y) == self.engine.game_map.downstairs_location:
            self.engine.game_world.generate_floor()
            self.engine.message_log.add_message("You have descended the staircase into the dark...", color.descend)

        else:
            raise exceptions.Impossible("There are no stairs here!")
        
class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int) -> None:
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
    
    @property
    def target_actor(self) -> Optional[Actor]:
        '''Return the actor at this action's destination'''
        return self.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()
    
class MeleeAction(ActionWithDirection):
    def perform(self) -> None:
        #gets target at destination location
        target = self.target_actor

        if not target:
            raise exceptions.Impossible("Nothing to attack.")  #No entity to attack, for safety
        
        damage = self.entity.fighter.power - target.fighter.defense

        #color of log output determined
        if self.entity is self.engine.player:
            attack_color = color.player_atk
        else:
            attack_color = color.enemy_atk

        attack_desc = f"{self.entity.name.capitalize()} attacks {target.name}"

        if damage > 0:
            self.engine.message_log.add_message(
                f"{attack_desc} for {damage} hit points.", attack_color
            )
            target.fighter.hp -= damage  #uses setter of fighter component

        else:
            self.engine.message_log.add_message(
                print(f"{attack_desc} but no damage is dealt"), attack_color
            )

class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not self.engine.game_map.in_bounds(dest_x, dest_y):
            #destination not in bounds
            raise exceptions.Impossible("The destination is blocked.")
        if not self.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            #note: currently requires that dx, dy at most 1
            #destination blocked by wall/other tile
            raise exceptions.Impossible("The destination is blocked.")
        if self.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            #destination is blocked by an entity
            raise exceptions.Impossible("The destination is blocked.")
        
        self.entity.move(self.dx, self.dy)

class BumpAction(ActionWithDirection):
    def perform(self) -> None:
        
        if self.target_actor is not None:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()