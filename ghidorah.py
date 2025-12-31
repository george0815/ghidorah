
#1. create a source class
#2. create classes for each source that inherit from source class
#3. each class has a search function and a status check function
#4. for search, just execute each source's search function, same with status check
#5. return all results in a list





class source:

    def __init__(self):
        print("Initializing...")

    def check_status(url):
        #ping url for health check
        #do test queries for information
        pass


class ThePirateBay(source):

    def __init__(self):
        SELF.url = "Thepiratebay.com"

    def search(self, query):
        #Check status
        #parse using beautiful soup
        #return info back to list
        pass



    def check_status(self):
        Super().check_status(SELF.url)






def search(query):
    pass

def statusCheck():
    pass








def main(): 
    while True:
        PrintMenu()
        choice = input("Select an option: ")
        if choice == '1':
            choice = input("Enter query:")
            search(choice)
        elif choice == '2':
            print("Performing status check...")

        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


def PrintMenu():
    print("1. Search")
    print("2. Check Status")
    print("3. Exit")


if __name__ == '__main__':
    main()