from __future__ import annotations

from typing import Optional, TYPE_CHECKING
import tcod.event
import player_config as config
from tcod.event import KeyDown, Quit
from actions import Action, EscapeAction, BumpAction, WaitAction

if TYPE_CHECKING:
    from engine import Engine

class EventHandler(tcod.event.EventDispatch[Action]):

    #turns events into actions, each function returns none or action
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self) -> None:
        raise NotImplementedError()
    
    #Quit event, ie pressing the X button
    def ev_quit(self, event: Quit) -> Action | None:    #same thing as -> Optional[Action]
        raise SystemExit()
    

class MainGameEventHandler(EventHandler):

    #Main game, while player is alive 

    def handle_events(self) -> None:
        #gets list of user input events and iterates over them
        for event in tcod.event.wait():

            #action becomes whatever is returned by the user keypress's function, ie keydown if valid
            action = self.dispatch(event)

            if action is None:
                continue

            action.perform()
            self.engine.handle_enemy_turns()  #handles enemies after each *player event*, not tick/other time method

            self.engine.update_fov()  #updates the FOV before player's next action
    
    #receives key press events and returns either Action or None
    def ev_keydown(self, event: KeyDown) -> Action | None:
        action: Optional[Action] = None

        key = event.sym

        player = self.engine.player

        if key in config.MOVE_KEYS:
            dx, dy = config.MOVE_KEYS[key]
            action = BumpAction(player, dx, dy)

        elif key in config.WAIT_KEYS:
            action = WaitAction(player)

        elif key in config.ESCAPE_KEYS:
            action = EscapeAction(player)

        return action
    

class GameOverEventHandler(EventHandler):
    def handle_events(self) -> None:
        for event in tcod.event.wait():
            #action becomes whatever is returned by the user keypress's function, ie keydown if valid
            action = self.dispatch(event)

            if action is None:
                continue

            action.perform()

            #Just without handling enemies, or updating FOV

    def ev_keydown(self, event: KeyDown) -> Action | None:
        action: Optional[Action] = None
        
        key = event.sym
        player = self.engine.player

        #Can only escape
        if key in config.ESCAPE_KEYS:
            action = EscapeAction(player)
        
        return action