import basic

while True:  # Infinite loop to read the raw input from the terminal window
    text = input("basic > ")
    result, error = basic.run("<stdin>", text)  # Uses the run function in the basic file to return the token objects and any errors

    if error: print(error.message())
    else: print(result)
    