import os
from time import sleep

import requests
from yaml import dump


def clr():
    """Clear the terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear function that works across platforms.


if __name__ == "__main__":

    token_ok = False  # Set to true when the token is valid.
    external = False  # Set to true if a external DB is used.
    settings = {"discord_token": "", "bot_description": "", "additional_credits": "", "pg_address": "postgres",
                "pg_user": "postgres", "pg_password": "postgres", "pg_port": "5432", "pg_database": "discord_bot"}
    clr()
    print("Setting up bot...")
    while not token_ok:  # Ask for token repeatedly until received.
        print("Please enter your Discord bot token:")
        token = input("> ").strip()
        clr()
        headers = {"Authorization": f"Bot {token}"}
        r = requests.get("https://discordapp.com/api/users/@me", headers=headers)
        if r.ok:
            token_ok = True
            settings["discord_token"] = token
        else:
            print("Invalid token.")
    clr()
    print("Please enter a description of the bot for the about command. (Optional)")
    print("This needs to be under 2000 characters, does not support indent and newlines.")
    print("Type _prefix_ for the bot prefix:\n")
    settings["bot_description"] = input()  # Ask for bot description.
    clr()
    print("Please enter additional credits for the about command. (Optional)")
    print("Credits for the base bot and the library are added automatically.")
    print("Should look something like this:\n\nPerson:\n\tMaintaining\n\tHosting\n\nPerson:\n\tProfile Image\n")
    print("Inline linking supported; [Text](URL)\n")
    print("This needs to be under 1000 characters, use \\n and \\t for newline and indent:")
    settings["additional_credits"] = input()  # Ask for additional credits.
    clr()
    print("Do you want to use an existing Postgres database? (N/y): ")
    if input().lower() in ["yes", "y", "true", "1"]:
        external = True
        clr()
        print("Please enter the host address for your Postgres database.")
        settings["pg_address"] = input("> ")
        clr()
        print("Please enter the user for your Postgres database.")
        settings["pg_user"] = input("> ")
        clr()
        print("Please enter the password for your Postgres database.")
        settings["pg_password"] = input("> ")
        clr()
        print("Please enter the database name for your Postgres database.")
        settings["pg_database"] = input("> ")
        clr()
        print("Please enter the port your Postgres database is listening on.")
        settings["pg_port"] = input("> ")
    with open("config.yml", "w") as config:
        dump(settings, config, default_flow_style=False)
    clr()
    print("Necessary info has been set.")  # Report back to user, wait 5 seconds, and end.
    print("Proceed by running the main file." if external else "Proceed by running 'docker-compose up'.")
    sleep(5)
    exit(0)
