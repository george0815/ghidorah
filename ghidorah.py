

def main(): 
    while True:
        PrintMenu()
        choice = input("Select an option: ")
        if choice == '1':
            print("Starting new game...")
            # Add logic to start a new game
        elif choice == '2':
            print("Loading game...")
            # Add logic to load a game
        elif choice == '3':
            print("Opening options...")
            # Add logic for options
        elif choice == '4':
            print("Exiting game. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


def PrintMenu():
    print("1. Start Game")
    print("2. Load Game")
    print("3. Options")
    print("4. Exit")    


if __name__ == '__main__':
    main()