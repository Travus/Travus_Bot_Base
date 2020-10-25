import os  # To check directory contents and make directories.
from asyncio import sleep as asleep, get_event_loop

import asyncpg
import requests
import yaml
from discord import Intents
from discord.ext import commands  # For command functionality.

import travus_bot_base as tbb  # TBB functions and classes.


async def run():
    """Connect, set up and fetch from database, load default modules and core_commands file and start bot."""
    if "modules" not in os.listdir("."):  # Makes sure modules directory exists.
        os.mkdir("modules")

    # Attempt to connect to database.
    retries = 5
    db = None
    if "config.yml" not in os.listdir("."):
        print("Please run setup.py first!")
        exit(5)
    with open("config.yml", "r") as config:
        conf = yaml.safe_load(config)
    while retries:
        try:
            db = await asyncpg.create_pool(user=conf["pg_user"], password=conf["pg_password"],
                                           host=conf["pg_address"], port=conf["pg_port"], database=conf["pg_database"])
            break
        except asyncpg.exceptions.InvalidCatalogNameError:
            print("Error: Failed to connect to database. Database name not found.")
            retries -= 1
            await asleep(5)
        except asyncpg.exceptions.InvalidPasswordError:
            print("Error: Failed to connect to database. Username or password incorrect.")
            retries -= 1
            await asleep(5)
        except OSError:
            print("Error: Failed to connect to database. Connection error.")
            retries -= 1
            await asleep(5)
        except Exception as e:
            print(f"Error: {e}")
            retries -= 1
            await asleep(5)
    if not retries:
        print("Failed to connect to database.")
        exit(1)

    # Validate Discord token.
    discord_token = conf["discord_token"] if "discord_token" in conf.keys() else None  # Get bot token.
    if discord_token is None:  # Stop if no Discord token was found.
        print("Error: Discord bot token missing. Please run the setup file to set up the bot.")
        await db.close()
        exit(2)
    else:
        headers = {"Authorization": f"Bot {discord_token}"}
        r = requests.get("https://discordapp.com/api/users/@me", headers=headers)
        if not r.ok:
            print("Error: Login failure, bot token is likely wrong or Discord is down!")
            await db.close()
            exit(2)

    # Create, set up and query database for info. Create default values if database is empty.
    async with db.acquire() as conn:
        async with conn.transaction():
            await conn.execute("CREATE TABLE IF NOT EXISTS settings(key VARCHAR PRIMARY KEY NOT NULL, value VARCHAR)")
            await conn.execute("CREATE TABLE IF NOT EXISTS default_modules(module VARCHAR PRIMARY KEY NOT NULL)")
            await conn.execute("CREATE TABLE IF NOT EXISTS command_states(command VARCHAR PRIMARY KEY NOT NULL, "
                               "state INTEGER NOT NULL)")
            await conn.execute("INSERT INTO settings VALUES ('additional_credits', '') ON CONFLICT (key) DO NOTHING")
            await conn.execute("INSERT INTO settings VALUES ('bot_description', '') ON CONFLICT (key) DO NOTHING")
            await conn.execute("INSERT INTO settings VALUES ('delete_messages', '0') ON CONFLICT (key) DO NOTHING")
            await conn.execute("INSERT INTO settings VALUES ('prefix', '!') ON CONFLICT (key) DO NOTHING")
        loaded_prefix = await db.fetchval("SELECT value FROM settings WHERE key = 'prefix'")
        delete_msgs = await conn.fetchval("SELECT value FROM settings WHERE key = 'delete_messages'")
        default_modules = await conn.fetch("SELECT module FROM default_modules")

    # Assign database pool, prefix, and message deletion flag as bot variables. Add help entry for help command.
    bot.db = db
    bot.prefix = loaded_prefix or None
    bot.delete_messages = int(delete_msgs) if delete_msgs is not None else 0  # Set delete messages flag.
    bot.add_command_help([com for com in bot.commands if com.name == "help"][0], "Core", None,
                         ["", "about", "help"])  # Add help info for help command.

    # Load default modules.
    default_modules = [mod["module"] for mod in default_modules]
    for mod in default_modules:  # Save module and help info before loading in case we need to roll back.
        old_help = dict(bot.help)
        old_modules = dict(bot.modules)
        bot.extension_ctx = None
        try:  # Try loading default modules.
            if f"{mod}.py" in os.listdir("modules"):
                bot.load_extension(f"modules.{mod}")
            else:
                raise FileNotFoundError("Core commands file not found.")
        except FileNotFoundError:  # If module wasn't found.
            print(f"[{tbb.cur_time()}] Default module '{mod}' not found.")
        except Exception as e:  # If en error was encountered while loading default module, roll back.
            bot.help = old_help
            bot.modules = old_modules
            if isinstance(e, commands.ExtensionNotFound):  # If import error, clarify further.
                e = e.__cause__
            print(f"[{tbb.cur_time()}] Default module '{mod}' encountered and error.\n\n{str(e)}")
            bot.last_module_error = f"The `{mod}` module failed while loading. The error was:\n\n{str(e)}"
        else:
            print(f"Default module '{mod}' loaded.")
    await bot.update_command_states()  # Make sure commands are in the right state. (hidden, disabled)

    try:  # Try loading core_commands.py file containing basic non-unloadable commands.
        if "core_commands.py" in os.listdir("."):
            bot.load_extension("core_commands")
        else:
            raise FileNotFoundError("Core commands file not found.")
    except FileNotFoundError:  # If core_commands.py file is not found, error to console and shut down.
        print("Error: Core commands file not found.")
        await db.close()
        exit(4)
    except Exception as e:  # If error is encountered in core_commands.py error to console and shut down.
        if isinstance(e, commands.ExtensionNotFound):  # If import error, clarify error further.
            e = e.__cause__
        print(f"Error: Core functionality file failed to load.\n\nError:\n{e}")
        await db.close()
        exit(3)

    await bot.start(discord_token)


async def close():
    """Coses the bot and the database connections."""
    await bot.close()
    await bot.db.close()
    print("Bot closed due to KeyboardInterrupt.")


async def get_prefix(bot_object, message):
    """This function is used by the bot to work with pings, and optionally a prefix."""
    if bot_object.prefix is not None:
        return commands.when_mentioned_or(bot_object.prefix)(bot_object, message)  # There is a prefix set.
    else:
        return commands.when_mentioned(bot_object, message)  # There is no prefix set.

if __name__ == '__main__':
    intent = Intents.all()
    bot = tbb.TravusBotBase(command_prefix=get_prefix, intents=intent)
    try:
        get_event_loop().run_until_complete(run())
    except KeyboardInterrupt:
        get_event_loop().run_until_complete(close())
