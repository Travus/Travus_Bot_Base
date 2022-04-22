import asyncio
import logging
import os  # To check directory contents and make directories.

import requests
import yaml
from discord import Intents
from discord.ext import commands  # For command functionality.

import travus_bot_base as tbb  # TBB functions and classes.


async def get_prefix(bot_object, message):
    """This function is used by the bot to work with pings, and optionally a prefix."""
    if bot_object.prefix is not None:
        return commands.when_mentioned_or(bot_object.prefix)(bot_object, message)  # There is a prefix set.
    return commands.when_mentioned(bot_object, message)  # There is no prefix set.


async def main(logger: logging.Logger):
    """Check required files and directories are in place, and set up bot. Returns bot and token."""
    config_options = ["discord_token", "pg_address", "pg_database", "pg_password", "pg_port", "pg_user"]

    if "modules" not in os.listdir("."):
        os.mkdir("modules")
        logger.info("Created modules directory.")

    if "config.yml" not in os.listdir("."):
        logger.critical("Please run setup.py first!")
        exit(5)
    with open("config.yml", "r", encoding="utf8") as config_object:
        config = yaml.safe_load(config_object)
        if not all(element in config and config[element] is not None for element in config_options):
            logger.critical("Config was found, but lacked required options. Please run setup.py first.")
            exit(5)

    # Validate Discord token.
    headers = {"Authorization": f"Bot {config['discord_token']}"}
    response = requests.get("https://discordapp.com/api/users/@me", headers=headers)
    if not response.ok:
        logger.critical("Error: Login failure, bot token is likely wrong or Discord is down.")
        exit(2)

    intent = Intents.all()
    db_credentials = tbb.DatabaseCredentials(
        user=config["pg_user"],
        password=config["pg_password"],
        host=config["pg_address"],
        port=config["pg_port"],
        database=config["pg_database"],
    )
    discord_token = config["discord_token"]
    bot = tbb.TravusBotBase(db_credentials, command_prefix=get_prefix, intents=intent)
    await bot.start(discord_token)


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    log = logging.getLogger("main")
    log.setLevel(logging.INFO)
    log.info("Starting bot...")
    asyncio.run(main(log))
