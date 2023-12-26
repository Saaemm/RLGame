from typing import List, Reversible, Tuple
import textwrap

import tcod

import configs.color as color


class Message:
    def __init__(self, text: str, fg: Tuple[int, int, int]) -> None:
        self.plain_text = text
        self.fg = fg
        self.count = 1

    @property
    def full_text(self) -> str:
        '''The full text of this message, including the count if necessary'''
        if self.count > 1:
            return f"{self.plain_text} (x{self.count})"
        return self.plain_text
    
class MessageLog:
    def __init__(self) -> None:
        self.messages: List[Message] = []

    def add_message(
            self, text: str, fg: Tuple[int, int, int] = color.white, *, stack: bool = True,
    ) -> None:
        '''Add message to the log
        'text' is message text, 'fg' is text color
        If 'stack' is True, then the message can stack with the previous message of the same text
        '''
        if stack and len(self.messages) > 0 and text == self.messages[-1].plain_text:
            self.messages[-1].count += 1
        else: 
            self.messages.append(Message(text, fg))

    def render(
        self, console: tcod.console.Console, x: int, y: int, width: int, height: int,
    ) -> None:
        '''Render this log over the given area.
        'x', 'y', 'width', 'height' is the rect region to render onto the 'console'
        '''
        self.render_messages(console, x, y, width, height, self.messages)

    @staticmethod
    def render_messages(
        console: tcod.console.Console,
        x: int, 
        y: int,
        width: int, 
        height: int, 
        messages: Reversible[Message],
    ) -> None:
        '''Render the messages provided. 
        The 'messages' are rendered starting at the last message and going backward'''
        y_offset = height-1

        for message in reversed(messages):
            for line in reversed(textwrap.wrap(message.full_text, width)):
                console.print(x=x, y=y + y_offset, string=line, fg=message.fg)
                y_offset -= 1
                if y_offset < 0: 
                    return  # No more space to print messages