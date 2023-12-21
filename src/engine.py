from typing import Set, Iterable, Any

from tcod.context import Context
from tcod.console import Console

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

    def handle_events(self, events: Iterable[Any]) -> None:

        #gets list of user input events and iterates over them
        for event in events:

            #action becomes whatever is returned by the user keypress's function, ie keydown if valid
            action = self.event_handler.dispatch(event)

            if action is None:
                continue

            action.perform(engine=self, entity=self.player)
            
    def render(self, console: Console, context: Context) -> None:

        #updates map
        self.game_map.render(console)

        #renders all entities on screen
        for entity in self.entities:
            console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)

        #update and clear/get rid of leftovers step
        context.present(console)
        console.clear()