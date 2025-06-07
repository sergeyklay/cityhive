from cityhive.app.app import main


def run():
    """
    Run main() when current file is executed by an interpreter.

    This function ensures that main function is only executed when this
    file is run directly, not when imported as a module.
    """
    if __name__ == "__main__":
        main()


run()
