import os  # To clear terminal.
import sqlite3  # To access database.
from time import sleep  # To not quit immediately.

if __name__ == "__main__":

    def clr():
        """Clear the terminal."""
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear function that works across platforms.

    discord_token = ""
    clr()
    print("Setting up bot...")
    while len(discord_token) < 32:  # Ask for token repeatedly until received.
        print("Please enter your Discord bot token:")
        discord_token = input("> ").replace(" ", "").strip()
        clr()
        if len(discord_token) < 32:
            print("Invalid token length.")
    clr()
    print("Please enter a description of the bot for the about command. (Optional)")
    print("This needs to be under 2000 characters, does not support indent and newlines.\nType _prefix_ for the bot prefix:\n")
    bot_description = input()  # Ask for bot description.
    clr()
    print("Please enter additional credits for the about command. (Optional)")
    print("Credits for the base bot and the library are added automatically.")
    print("Should look something like this:\n\nPerson:\n\tMaintaining\n\tHosting\n\nPerson:\n\tProfile Image\n")
    print("Inline linking supported; [Text](URL)\n")
    print("This needs to be under 1000 characters, use \\n and \\t for newline and indent:")
    bot_additional_credits = input()  # Ask for additional credits.
    db_con = sqlite3.connect("database.sqlite")  # Connect to database.
    db = db_con.cursor()
    db.execute("CREATE TABLE IF NOT EXISTS settings(flag TEXT PRIMARY KEY NOT NULL, value TEXT)")  # Create tables.
    db.execute("CREATE TABLE IF NOT EXISTS default_modules(module TEXT PRIMARY KEY NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS command_states(command TEXT PRIMARY KEY NOT NULL, state NUMERIC NOT NULL)")
    db.execute("DELETE FROM settings WHERE flag = ?", ("discord_token", ))  # Remove old info and insert new info.
    db.execute("INSERT INTO settings VALUES (?, ?)", ("discord_token", discord_token))
    db.execute("DELETE FROM settings WHERE flag = ?", ("bot_description",))
    db.execute("INSERT INTO settings VALUES (?, ?)", ("bot_description", bot_description))
    db.execute("DELETE FROM settings WHERE flag = ?", ("bot_additional_credits",))
    db.execute("INSERT INTO settings VALUES (?, ?)", ("bot_additional_credits", bot_additional_credits))
    db_con.commit()  # Commit info and close database.
    db.close()
    db_con.close()
    clr()
    print("Necessary info has been set.")  # Report back to user, wait 5 seconds, and end.
    print("Proceed by running the main file.")
    sleep(5)
    exit(0)
