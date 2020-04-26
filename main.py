import os  # To check directory contents and make directories.
import sqlite3  # To access database.
from copy import copy  # To copy context in help command.

import discord  # To various Discord classes.
from aiohttp import ClientConnectorError as CCError  # To detect connection errors.
from discord.ext import commands  # For command functionality.

import travus_bot_base as tbb  # TBB functions and classes.


def setup_bot(bot_object: tbb.TravusBotBase):
    """Sets command prefix and returns Discord token from the database."""
    if "modules" not in os.listdir("."):  # Makes sure modules directory exists.
        os.mkdir("modules")
    db_con = sqlite3.connect("database.sqlite")  # Connect to database.
    db = db_con.cursor()
    db.execute("CREATE TABLE IF NOT EXISTS settings(flag TEXT PRIMARY KEY NOT NULL, value TEXT)")  # Create tables.
    db.execute("CREATE TABLE IF NOT EXISTS default_modules(module TEXT PRIMARY KEY NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS command_states(command TEXT PRIMARY KEY NOT NULL, state NUMERIC NOT NULL)")
    db_con.commit()
    db.execute("SELECT value FROM settings WHERE flag = ?", ("discord_token", ))  # Get bot token.
    discord_token = db.fetchone()
    db.execute("SELECT value FROM settings WHERE flag = ?", ("prefix", ))  # Get prefix.
    loaded_prefix = db.fetchone()
    if loaded_prefix is None:
        db.execute("INSERT INTO settings VALUES ('prefix', '!')")  # Commit default prefix if none is set.
        db_con.commit()
        loaded_prefix = ("!", )  # Use default prefix if none is set.
    db.close()
    db_con.close()
    if discord_token is None:  # Stop if no Discord token was found.
        print("Error: Discord bot token missing. Please run the setup file to set up the bot.")
        exit(1)
    if loaded_prefix[0] == "":  # If prefix was 'removed' set it to None type.
        loaded_prefix = (None, )
    bot_object.prefix = loaded_prefix[0]
    return discord_token[0].strip()  # Return Discord token.


async def get_prefix(bot_object, message):
    """This function is used by the bot to work with pings, and optionally a prefix."""
    if bot.prefix is not None:
        return commands.when_mentioned_or(bot_object.prefix)(bot_object, message)  # There is a prefix set.
    else:
        return commands.when_mentioned(bot_object, message)  # There is no prefix set.


if __name__ == "__main__":
    bot = tbb.TravusBotBase(command_prefix=get_prefix)  # Define bot object.

    class CustomHelp(commands.HelpCommand):
        """Class for custom help command."""

        def __init__(self):
            """Initialization function that sets help and usage text for custom help command."""
            super(CustomHelp, self).__init__(command_attrs={"help": """This command shows a list of categorized
            commands you have access to. If the name of a command is sent along it will show detailed help
            information for that command, such as what the command does, aliases, what restrictions it has, and
            examples.""", "usage": "(COMMAND NAME)"})

        async def _send_help_entry(self, com_object):
            if com_object.qualified_name in bot.help.keys():
                if com_object.enabled:
                    embed = bot.help[com_object.qualified_name].make_help_embed(self.context)  # Send command help info.
                    await self.get_destination().send(embed=embed)
                else:
                    await self.get_destination().send(f"The `{com_object.qualified_name}` command has been disabled.")
            else:
                await self.get_destination().send("No help information is registered for this command.")

        async def _send_command_list(self, full_mapping):
            categories = {}  # List of categorized commands.
            filtered_mapping = {f"`{com.qualified_name}`": com for com in await self.filter_commands(full_mapping)}
            non_passing = list(set(full_mapping).difference(set(filtered_mapping.values())))
            new_ctx = copy(self.context)
            new_ctx.guild = None
            non_passing = {f'`{com.qualified_name}`¹': com for com in non_passing if await tbb.can_run(com, new_ctx)}
            filtered_mapping.update(non_passing)
            if len(filtered_mapping.items()) == 0:
                await self.get_destination().send("No help information was found.")
                return
            for com_text, com in filtered_mapping.items():
                if com.qualified_name in bot.help.keys():
                    command_help = bot.help[com.qualified_name]  # Get command help info.
                    category = command_help.category.lower() if command_help.category else "no category"
                    if category not in categories.keys():  # Add category if it wasn't encountered before.
                        categories[category] = []
                    categories[category].append(com_text)  # Add command to category.
            msg = f"__**Help Info {self.context.message.author.mention}:**__\n\n"
            for category in sorted(categories.keys()):
                category_text = f"**{category.title()}**\n{', '.join(sorted(categories[category]))}\n\n"
                if len(category_text) > 1950:
                    category_text = '\n'.join(tbb.split_long_messages(category_text))  # Break up too long categories.
                msg += self.remove_mentions(category_text)
            msg += '1 = In DMs only.\n' if len(non_passing) else ""
            msg += f"Use `{bot.get_bot_prefix()}help <COMMAND>` for more info on individual commands."
            msgs = tbb.split_long_messages(msg, 1950, "\n")  # Split the message along newlines if over 1950 long.
            for msg_to_send in msgs:
                await self.get_destination().send(msg_to_send)

        async def send_bot_help(self, mapping):
            """Function that triggers when help command is used without command."""
            full_mapping = []  # Command list.
            for com_mapping in mapping.values():
                full_mapping.extend(com_mapping)  # Add all cogs to list.
            full_mapping = set([com for com in full_mapping if com.enabled and not com.hidden])
            await self._send_command_list(full_mapping)

        async def send_command_help(self, command_object: commands.Command):
            """Function that triggers when help command is used with a command."""
            while command_object.qualified_name not in bot.help.keys() and hasattr(command_object, "parents") and len(command_object.parents):
                command_object = command_object.parents[0]  # Get parent in case it has help text.
            await self._send_help_entry(command_object)

        async def send_cog_help(self, cog: commands.Cog):
            """Function that triggers when help command is used with a cog."""
            full_mapping = set([com for com in cog.get_commands() if com.enabled and not com.hidden])
            await self._send_command_list(full_mapping)

        async def send_group_help(self, group):
            """Function that triggers when help command is used with a group."""
            while group.qualified_name not in bot.help.keys() and hasattr(group, "parents") and len(group.parents):
                print(group.parents)
                group = group.parents[0]  # Get parent in case it has help text.
            await self._send_help_entry(group)

        async def subcommand_not_found(self, command, string):
            """Function that returns content of error when subcommand invalid."""
            return f"The `{command.qualified_name}` command has no subcommand called `{string}`."

        async def command_not_found(self, string):
            """Function that returns content of error when command not found."""
            return f"No command called `{string}` found."


    @bot.event
    async def on_ready():
        """Loads additional flags and help info, loads default modules and sets bot presence."""
        if not bot.has_started:  # If first time setup has not been completed.
            delete_msgs = await tbb.db_get_one(bot.db_con, "SELECT value FROM settings WHERE flag = ?", ("delete_messages",))
            if delete_msgs is None:  # If no delete message flag is in database, set it to off in runtime and database.
                await tbb.db_set(bot.db_con, "INSERT INTO settings VALUES (?, ?)", ("delete_messages", "0"))
                delete_msgs = (0, )
            bot.delete_messages = int(delete_msgs[0])  # Set delete messages flag.
            bot_author = "[Travus](https://github.com/Travus):\n\tTravus Bot Base\n\tCore functions\n\n[Rapptz](https://github.com/Rapptz):\n\tDiscord.py\n\tasqlite"
            bot_description = await tbb.db_get_one(bot.db_con, "SELECT value FROM settings WHERE flag = ?", ("bot_description",))
            bot_description = (bot_description or ("No description for the bot was found. A description can be set using the setup file.", ))[0]
            bot_additional_credits = await tbb.db_get_one(bot.db_con, "SELECT value FROM settings WHERE flag = ?", ("bot_additional_credits",))
            if bot_additional_credits:
                bot_additional_credits = bot_additional_credits[0].replace("\\n", "\n").replace("\\r", "\n").replace("\\t", "\t")
            bot.add_module(bot.user.name, bot_author, None, bot_description, bot_additional_credits, bot.user.avatar_url)  # Add about command for bot.
            bot.add_command_help([com for com in bot.commands if com.name == "help"][0], "Core", None, ["", "info", "clear"])  # Add help info for help command.
            try:  # Try loading core_commands.py file containing basic non-unloadable commands.
                if "core_commands.py" in os.listdir("."):
                    bot.load_extension("core_commands")
                else:
                    raise FileNotFoundError("Core commands file not found.")
            except FileNotFoundError:  # If core_commands.py file is not found, error to console and shut down.
                await bot.db_con.close()
                print(f"[{tbb.cur_time()}] Core commands file not found.")
                exit(4)
            except Exception as e:  # If error is encountered in core_commands.py error to console and shut down.
                await bot.db_con.close()
                if isinstance(e, commands.ExtensionNotFound):  # If import error, clarify error further.
                    e = e.__cause__
                print(f"[{tbb.cur_time()}] Core functionality file failed to load.\n\nError:\n{e}")
                exit(3)
            default_modules = await tbb.db_get_all(bot.db_con, "SELECT module FROM default_modules", ())  # Get default modules.
            if default_modules:  # If default modules were found, get their names from the response.
                default_modules = [mod[0] for mod in default_modules]
            for mod in default_modules:  # Save module and help info before loading in case we need to roll back, then load default modules.
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
                except Exception as e:  # If en error was encountered while loading default module, reload old info ad error to console.
                    bot.help = old_help
                    bot.modules = old_modules
                    if isinstance(e, commands.ExtensionNotFound):  # If import error, clarify further.
                        e = e.__cause__
                    print(f"[{tbb.cur_time()}] Default module '{mod}' encountered and error.\n\n{str(e)}")
                    bot.last_module_error = f"The `{mod}` module failed while loading. The error was:\n\n{str(e)}"
                else:
                    print(f"Default module '{mod}' loaded.")
            await bot.update_command_states()  # Make sure any loaded commands are in the right state. (hidden, disabled)
            bot.has_started = True  # Flag that the first time setup has been completed.
        loaded_prefix = await tbb.db_get_one(bot.db_con, "SELECT value FROM settings WHERE flag = ?", ("prefix",))  # Get bot prefix for display in status message.
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"prefix: {loaded_prefix[0]}" if loaded_prefix[0] else "pings only"))  # Display status message.
        bot.is_connected = 1  # Flag that the bot is currently connected to Discord.
        print(f"{bot.user.name} is ready!\n------------------------------")


    @bot.event
    async def on_disconnect():
        """Writes to console if bot disconnects from Discord."""
        if bot.is_connected:  # If the bot was last connected, log disconnect to console.
            print(f"[{tbb.cur_time()}] Disconnected from Discord.")
            bot.is_connected = 0  # Flag that the bot is currently disconnected from Discord.


    @bot.event
    async def on_command(ctx: commands.Context):
        """Deletes command if command deletion is set."""
        if bot.delete_messages and ctx.guild:  # If the message is in a server and the delete messages flag is true.
            try:  # Try to delete message.
                await ctx.message.delete()
            except discord.Forbidden:  # Log to console if missing permission to delete message.
                print(f"[{tbb.cur_time()}] Error: Bot does not have required permissions to delete message.")


    @bot.event
    async def on_command_error(ctx: commands.Context, error=None):
        """Global error handler for miscellaneous errors."""
        if isinstance(error, (commands.NoPrivateMessage, commands.CommandOnCooldown, commands.DisabledCommand, commands.CheckFailure)):
            pass
        elif isinstance(error, commands.UserInputError):  # Send correct syntax based on command usage variable.
            if hasattr(ctx.command, "usage") and ctx.command.usage:
                await ctx.send(f"Correct syntax: `{bot.get_bot_prefix()}{ctx.command.full_parent_name + ' ' if ctx.command.full_parent_name else ''}{ctx.invoked_with} {ctx.command.usage or ''}`")
        elif isinstance(error, commands.NotOwner):  # Log to console.
            print(f'[{tbb.cur_time()}] {ctx.message.author.id}: Command "{ctx.command}" requires bot owner status')
        elif isinstance(error, commands.MissingPermissions):  # Log to console.
            print(f'[{tbb.cur_time()}] {ctx.message.author.id}: Command "{ctx.command}" requires additional permissions: {", ".join(error.missing_perms)}')
        elif isinstance(error, commands.MissingRole):  # Log to console.
            print(f'[{tbb.cur_time()}] {ctx.message.author.id}: Command "{ctx.command}" requires role: {error.missing_role}')
        elif isinstance(error, commands.MissingAnyRole):  # Log to console.
            print(f'[{tbb.cur_time()}] {ctx.message.author.id}: Command "{ctx.command}" requires role: {" or ".join(error.missing_roles)}')
        elif isinstance(error, commands.CommandNotFound):  # Log to console.
            print(f'[{tbb.cur_time()}] {ctx.message.author.id}: {error}')
        elif isinstance(error, CCError):  # Log to console if message wasn't properly sent to Discord.
            print(f'[{tbb.cur_time()}] {ctx.message.author.id}: Connection error to Discord. Message lost.')
        elif isinstance(error.__cause__, discord.Forbidden):  # Log to console if lacking permissions.
            print(f'[{tbb.cur_time()}] {ctx.message.author.id}: Missing permissions.')
        elif error is not None:  # Log error to console.
            print(f'[{tbb.cur_time()}] {ctx.message.author.id}: {error}')
        bot.last_error = f'[{tbb.cur_time()}] {ctx.message.author.id}: {error}'


    bot.help_command = CustomHelp()  # Set bot to use custom help command.
    try:  # Run the bot.
        bot.run(setup_bot(bot))
    except discord.LoginFailure:  # Exit if running the bot failed. Token probably wrong.
        print(f"[{tbb.cur_time()}] Error: Login failure, bot token is likely wrong or Discord is down!")
        exit(2)
