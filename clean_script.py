import os

# Clean game log


def clean_game_log():
    with open("game.log", "w"):
        pass

# Clean database


def clean_database():
    with open("database.txt", "w"):
        pass


# Execute
clean_game_log()
clean_database()
