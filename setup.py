import os
from time import sleep

import requests
from yaml import dump


def clr():
    """Clear the terminal."""
    os.system("cls" if os.name == "nt" else "clear")  # Clear function that works across platforms.


def main():
    """Contains the setup.py business logic."""
    token_ok = False  # Set to true when the token is valid.
    external = False  # Set to true if a external DB is used.
    settings = {
        "discord_token": "",
        "pg_address": "postgres",
        "pg_user": "postgres",
        "pg_password": "postgres",
        "pg_port": "5432",
        "pg_database": "discord_bot",
    }
    clr()
    print("Setting up bot...")
    while not token_ok:  # Ask for token repeatedly until received.
        print("Please enter your Discord bot token:")
        token = input("> ").strip()
        clr()
        headers = {"Authorization": f"Bot {token}"}
        response = requests.get("https://discordapp.com/api/users/@me", headers=headers)
        if response.ok:
            token_ok = True
            settings["discord_token"] = token
        else:
            print("Invalid token.")
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
    with open("config.yml", "w", encoding="utf8") as config:
        dump(settings, config, default_flow_style=False)
    clr()
    print("Necessary info has been set.")  # Report back to user, wait 5 seconds, and end.
    print("Proceed by running the main file." if external else "Proceed by running 'docker-compose up -d'.")
    print("Once the bot has started, use the 'botconfig' command to change it's settings.")
    sleep(5)
    exit(0)


if __name__ == "__main__":
    main()
