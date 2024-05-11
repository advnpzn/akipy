from akipy.async_akipy import Akinator

import akipy
import asyncio

aki = Akinator()


async def main():
    q = await aki.start_game()

    while not aki.win:
        ans = input(aki.question + "\n\t")
        if ans == "b":
            try:
                await aki.back()
            except akipy.CantGoBackAnyFurther:
                pass
        else:
            await aki.answer(ans)

asyncio.run(main())
