# akipy
Python library wrapper for [akinator.com](https://akinator.com)
You can use this in your python projects to integrate Akinator functionalities.

Wrapper is still in development.
Some things may or may not work. If you experience issues, feel free to raise an issue here.

Some things that could be improved:
* Exception Handling
* Docs
* Better error Handling
* Custom Exceptions

If you want to help, the above is the main priority for now.

# Why ?
I already used to use a wrapper library for Akinator ([akinator.py](https://github.com/Ombucha/akinator.py)) before.
But suddenly it seems to be not working. I debugged and made 
sure the problem is because of API changes from Akinator themselves. 
There were so many changes making me think I would have to change a lot of things. 
So instead of doing that, I just made it from scratch. Obviously I took a lot 
of inspiration from the old Python wrapper I was using thus the code structure 
would look very similar. In fact, I'm trying to replicate the same interface that 
was present in the old wrapper. Because I don't want to make changes to any piece 
of software that may depend on this library (which isn't working now).

I hope there isn't any interface breaking changes here. If there are any, please 
contact me either through Telegram or raise an issue here on GitHub or if you want 
to help, raise a Pull Request.

# Installation

`pip install akipy`

# Usage

There is both synchronous and asynchronous variants of `akipy` available.

Synchronous: `from akipy import Akinator`

Asynchronous: `from akipy.async_akipy import Akinator`

I'll provide a sample usage for synchronous usage of `Akinator`.
All the examples are also in the project's examples folder. So please check them out as well.

```python
import akipy

aki = akipy.Akinator()
aki.start_game()

while not aki.win:
    ans = input(str(aki) + "\n\t")
    if ans == "b":
        try:
            aki.back()
        except akipy.CantGoBackAnyFurther:
            pass
    else:
        try:
            aki.answer(ans)
        except akipy.InvalidChoiceError:
            pass

print(aki)
print(aki.name_proposition)
print(aki.description_proposition)
print(aki.pseudo)
print(aki.photo)
```






