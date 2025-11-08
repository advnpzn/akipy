"""
Example demonstrating async context manager usage for automatic resource cleanup.

Using async context managers ensures HTTP clients are properly closed in async code,
preventing resource leaks and improving performance through connection pooling.
"""

import asyncio
from akipy.async_akinator import Akinator


async def play_akinator():
    # Using async context manager - automatically cleans up resources
    async with Akinator() as aki:
        await aki.start_game()

        print("Think of a character, and I'll try to guess it!")
        print("Answer with: yes/no/idk/probably/probably not, or 'b' to go back\n")

        while not aki.finished:
            ans = input(str(aki) + "\n\t")
            if ans == "b":
                try:
                    await aki.back()
                except Exception as e:
                    print(f"Can't go back: {e}")
            else:
                try:
                    await aki.answer(ans)
                except Exception as e:
                    print(f"Error: {e}")

        # Display results
        print("\n" + "=" * 50)
        print(aki)
        if aki.name_proposition:
            print(f"Character: {aki.name_proposition}")
            print(f"Description: {aki.description_proposition}")
            print(f"Times played: {aki.pseudo}")
            print(f"Photo: {aki.photo}")
        print("=" * 50)

    # HTTP client is automatically closed when exiting the 'async with' block
    print("\nResources cleaned up automatically!")


if __name__ == "__main__":
    asyncio.run(play_akinator())
