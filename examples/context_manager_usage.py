"""
Example demonstrating context manager usage for automatic resource cleanup.

Using context managers ensures HTTP clients are properly closed, preventing
resource leaks and improving performance through connection pooling.
"""

import akipy

# Using context manager - automatically cleans up resources
with akipy.Akinator() as aki:
    aki.start_game()

    while not aki.finished:
        ans = input(str(aki) + "\n\t")
        if ans == "b":
            try:
                aki.back()
            except akipy.CantGoBackAnyFurther:
                print("Already at the first question!")
        else:
            try:
                aki.answer(ans)
            except akipy.InvalidChoiceError:
                print(
                    "Invalid choice! Use: yes/no/idk/probably/probably not, or 'b' to go back"
                )

    # Display results
    print("\n" + "=" * 50)
    print(aki)
    if aki.name_proposition:
        print(f"Character: {aki.name_proposition}")
        print(f"Description: {aki.description_proposition}")
        print(f"Times played: {aki.pseudo}")
        print(f"Photo: {aki.photo}")
    print("=" * 50)

# HTTP client is automatically closed when exiting the 'with' block
print("\nResources cleaned up automatically!")
