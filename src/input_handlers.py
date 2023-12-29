from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from tcod.console import Console
import tcod.event
import tcod.constants
import configs.interface_config as config
from tcod.event import KeyDown, MouseButtonDown, MouseMotion, Quit

import actions
from actions import (Action, EscapeAction, BumpAction, WaitAction, PickupAction)
import configs.color as color
from entity import Item
import exceptions

if TYPE_CHECKING:
    from engine import Engine
    from entity import Item

class EventHandler(tcod.event.EventDispatch[Action]):

    #turns events into actions, each function returns none or action
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> None:
        self.handle_action(self.dispatch(event))

    def handle_action(self, action: Optional[Action]) -> bool:
        '''Handle actions returned from event methods
        
        Returns True if the action will advance a turn
        '''
        if action is None:  #player has not taken turn yet
            return False
        
        try:
            action.perform()

        except exceptions.Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], color.impossible)
            return False  #skips enemy turns on exceptions
        
        self.engine.handle_enemy_turns()  #handles enemies after each *player turn*, not tick/other time method

        self.engine.update_fov()  #updates the FOV before player's next action
        return True

    def ev_mousemotion(self, event: MouseMotion) -> Action | None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y
    
    #Quit event, ie pressing the X button
    def ev_quit(self, event: Quit) -> Action | None:    #same thing as -> Optional[Action]
        raise SystemExit()
    
    def on_render(self, console: tcod.console.Console) -> None:
        self.engine.render(console)
    

class MainGameEventHandler(EventHandler):

    #Main game, while player is alive 
    
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

        elif key == tcod.event.KeySym.v:
            #go to history viewer render/input state
            self.engine.event_handler = HistoryViewer(self.engine)

        elif key == tcod.event.KeySym.g:
            #pickup
            action = PickupAction(player)

        elif key == tcod.event.KeySym.i:
            #inventory use
            self.engine.event_handler = InventoryActivateHandler(self.engine)
        elif key == tcod.event.KeySym.d:
            #inventory drop
            self.engine.event_handler = InventoryDropHandler(self.engine)

        #no valid key was pressed
        return action
    

class GameOverEventHandler(EventHandler):

    def on_render(self, console: Console) -> None:
        super().on_render(console)
    
        player = self.engine.player

        #prints game over if needed, can be folded into another function
        if not player.is_alive:
            console.print(
                x=30,
                y=25,
                string="GAME OVER"
            )

    def ev_keydown(self, event: KeyDown) -> Action | None:

        #Can only escape
        if event.sym in config.ESCAPE_KEYS:
            raise SystemExit()
        
        return None
    

class HistoryViewer(EventHandler):
    '''Prints the message log history on a larger window that can be navigated'''

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: Console) -> None:
        super().on_render(console)  #Draws the main game as the background

        log_console = tcod.console.Console(console.width-6, console.height-6)  #new console

        #Draw a frame with a custom banner title
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(
            0, 0, log_console.width, 1, "-|Message History|-", alignment=tcod.constants.CENTER
        )

        #Render the message log using the cursor parameter
        self.engine.message_log.render_messages(
            console=log_console,
            x=1, 
            y=1, 
            width=log_console.width - 2, 
            height=log_console.height - 2,
            messages=self.engine.message_log.messages[: self.cursor + 1]
        )
        log_console.blit(console, 3, 3) #superimposes log_console onto console for rendering

    def ev_keydown(self, event: KeyDown) -> Action | None:
        if event.sym in config.CURSOR_Y_KEYS:
            adjust = config.CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                #go from the top to the bottom when on the edge
                self.cursor = self.log_length-1
            elif adjust > 0 and self.cursor == self.log_length-1:
                #go from bottom to top when on edge
                self.cursor = 0
            else:
                #otherwise move while being bounded by the history log [0, log_length)
                self.cursor = max(0, min(self.cursor+adjust, self.log_length - 1))
        
        elif event.sym == tcod.event.KeySym.HOME or event.sym == tcod.event.KeySym.h:
            self.cursor = 0 #go to the top
        
        elif event.sym == tcod.event.KeySym.END or event.sym == tcod.event.KeySym.g:
            self.cursor = self.log_length-1 #go to the last message
        
        else: 
            #any other key goes back to main game state inputs/render
            self.engine.event_handler = MainGameEventHandler(self.engine)


class AskUserEventHandler(EventHandler):
    '''Handles user input for actions which require special input.'''

    def handle_action(self, action: Optional[Action]) -> bool:
        '''Return to the main event handler when a valid action is performed.'''
        if super().handle_action(action):
            self.engine.event_handler = MainGameEventHandler(self.engine)
            return True
        
        return False
    
    def ev_keydown(self, event: KeyDown) -> Action | None:
        '''By default, any key exits this input handler'''
        if event.sym in {  #Ignore modifier keys
            tcod.event.KeySym.LSHIFT,  
            tcod.event.KeySym.RSHIFT,  
            tcod.event.KeySym.LCTRL,  
            tcod.event.KeySym.RCTRL,  
            tcod.event.KeySym.LALT,  
            tcod.event.KeySym.RALT,  
        }:
            return None
        return self.on_exit()
    
    def ev_mousebuttondown(self, event: MouseButtonDown) -> Action | None:
        '''by default, any mouse click exits the input handler'''
        return self.on_exit()
    
    def on_exit(self) -> Optional[Action]:
        '''Called when user tries to exit or cancel an action. 

        By default, returns to the main event handler
        '''
        self.engine.event_handler = MainGameEventHandler(self.engine)
        return None
    
class InventoryEventHandler(AskUserEventHandler):
    '''This handler lets the user select an item.
    
    What happens depends on the subclass
    '''

    TITLE = "<missing title>"

    def on_render(self, console: tcod.console.Console) -> None:
        '''Renders an inventory menu, displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, 
        so the player can always see where they are'''
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2
        
        if height <= 3:
            height = 3

        if self.engine.player.x <= 30:
            x = 40
        else: 
            x = 0

        y = 0

        width = len(self.TITLE) + 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                console.print(x + 1, y + i + 1, f"({item_key}) {item.name}")
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: KeyDown) -> Action | None:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.KeySym.a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", color.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[Action]:
        '''Called when user selects a valid item'''
        raise NotImplementedError()
    
class InventoryActivateHandler(InventoryEventHandler):
    '''Handles using an inventory item'''

    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> Action | None:
        '''Return the action for the selected item'''
        return item.consumable.get_action(self.engine.player)
    
class InventoryDropHandler(InventoryEventHandler):
    '''Handles dropping an item from inventory'''

    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> Action | None:
        '''Drops the item'''
        return actions.DropItem(self.engine.player, item)