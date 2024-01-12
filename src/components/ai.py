from __future__ import annotations

import random
from typing import List, Optional, Tuple, TYPE_CHECKING

import numpy as np
import tcod

from actions import Action, BumpAction, MeleeAction, MovementAction, WaitAction

if TYPE_CHECKING:
    from entity import Actor

class BaseAI (Action):

    #overrides BaseComponent, specifying actor
    entity: Actor

    def perform(self) -> None:
        raise NotImplementedError()
    
    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        '''Computes and returns a path to the target position
        
        If no valid path, returns empty list
        '''

        # Copy the walkable array
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        #want to fill in the cost array given the other entities
        for entity in self.entity.gamemap.entities:
            #check that entity blocks movement (enemy) and cost is not 0 (blocked)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                '''Add to the cost of a blocked position
                A lower number means more enemies will crowd behidn each other in the halls
                A higher number means enemies will take longer paths to surround the player
                '''
                cost[entity.x, entity.y] += 10

        #create a graph from the cost array and pass that to a pathfinder
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  #start position

        #compute the path to the destination and remove the starting poitn
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        #convert from List[List[int]] to List[Tuple[int, int]]
        return [(index[0], index[1]) for index in path]


class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor) -> None:
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []


    def perform(self) -> None:

        target = self.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  #Calculates Chebyshev distance

        #if in player's vision, right next to player, attack player
        if self.engine.game_map.visible[self.entity.x, self.entity.y]:
            if (distance <= 1):
                return MeleeAction(self.entity, dx, dy).perform()  #hits player if right next to

            self.path = self.get_path_to(target.x, target.y) #gets new path
            
        #in player's vision but not close enough to attack, move closer
        if len(self.path) > 0:
            dest_x, dest_y = self.path.pop(0)  #moves by 1 closer to player
            return MovementAction(
                self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
            ).perform()
        
        #not in player's vision, so wait
        return WaitAction(self.entity).perform()


class ConfusedEnemy(BaseAI):
    '''Confused entity will walk around aimlessly for a few rounds
    Will attack any actor that occupies a tile that it is moving into
    '''

    def __init__(self, entity: Actor, previous_ai: BaseAI, turns_remaining: int) -> None:
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

    def perform(self) -> None:

        #revert the AI back into its previous form after turns_remaining reaches 0
        if self.turns_remaining <= 0:
            self.engine.message_log.add_message(
                f"{self.entity.name} is no longer confused."
            )
            self.entity.ai = self.previous_ai

        else:  #is still confused
            #pick random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  #northwest
                    (0, -1), #north
                    (1, -1), #northeast
                    (-1, 0), #west
                    (1, 0),  #east
                    (-1, 1),  #southwest
                    (0, 1),  #south
                    (1, 1),  #southeast
                ]
            )

            self.turns_remaining -= 1
            
            #actor will try to move and attack in a random direction
            #can just bump into a wall, and waste a turn

            return BumpAction(self.entity, direction_x, direction_y,).perform()
