from akipy.async_akinator import Akinator

import akipy
import asyncio

aki = Akinator()


async def main():
    # swap to object mode
    await aki.start_game(game_mode="o")

    while not aki.finished:
        ans = input(str(aki) + "\n\t")
        if ans == "b":
            try:
                await aki.back()
            except akipy.CantGoBackAnyFurther:
                pass
        else:
            try:
                await aki.answer(ans)
            except akipy.InvalidChoiceError:
                pass


asyncio.run(main())

print(aki)
print(aki.name_proposition)
print(aki.description_proposition)
print(aki.pseudo)
print(aki.photo)
