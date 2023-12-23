from typing import Set, Iterable, Any

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler

#drawing map, entities, handles player input
class Engine:
    def __init__(self, entities: Set[Entity], event_handler: EventHandler, game_map: GameMap, player: Entity) -> None:
        self.entities = entities
        self.event_handler = event_handler
        self.game_map = game_map
        self.player = player

        self.update_fov()

    def handle_events(self, events: Iterable[Any]) -> None:

        #gets list of user input events and iterates over them
        for event in events:

            #action becomes whatever is returned by the user keypress's function, ie keydown if valid
            action = self.event_handler.dispatch(event)

            if action is None:
                continue

            action.perform(engine=self, entity=self.player)

            self.update_fov()  #updates the FOV before player's next action

    def update_fov(self) -> None:
        '''Recompute the visible area based on the player's POV'''
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8
        )
        #update "explored" to include "visible"
        self.game_map.explored |= self.game_map.visible
            
    def render(self, console: Console, context: Context) -> None:

        #updates map
        self.game_map.render(console)

        #renders all entities on screen
        for entity in self.entities:
            #only print entities in FOV
            if self.game_map.visible[entity.x, entity.y]:
                console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)

        #update and clear/get rid of leftovers step
        context.present(console)
        console.clear()