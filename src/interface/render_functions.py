from __future__ import annotations

from typing import TYPE_CHECKING

import configs.color as color

if TYPE_CHECKING:
    from tcod import Console


def render_bar(
        console: Console, current_value: int, maximum_value: int, total_width: int
) -> None:
    bar_width = int(float(current_value) / maximum_value * total_width)

    #red bar of empty health
    console.draw_rect(x=0, y=45, width=total_width, height=1, ch=1, bg=color.bar_empty)

    #on top of red bar, green bar of healthy health
    if bar_width > 0:
        console.draw_rect(
            x=0, y=45, width=bar_width, height=1, ch=1, bg=color.bar_filled
        )

    console.print(
        x=1, y=45, string=f"HP: {current_value}/{maximum_value}", fg=color.bar_text
    )

    