from akipy.async_akipy import Akinator

import akipy
import asyncio

aki = Akinator()


async def main():
    await aki.start_game()

    while not aki.finished:
        ans = input(str(aki) + "\n\t")
        if ans == "b":
            try:
                await aki.back()
            except akipy.CantGoBackAnyFurther:
                pass
        else:
            await aki.answer(ans)

asyncio.run(main())

print(aki)
print(aki.name_proposition)
print(aki.description_proposition)
print(aki.pseudo)
print(aki.photo)