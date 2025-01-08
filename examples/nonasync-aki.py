import akipy

aki = akipy.Akinator()
aki.start_game()

while not aki.finished:
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