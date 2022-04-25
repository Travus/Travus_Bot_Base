import logging
import os
from re import compile as re_cmp, findall  # Regex functions used in clean function for detecting mentions.
from typing import Callable, Dict, Iterable, List, Optional, Set, Type, TypeVar, Union

import asyncpg
import discord
from aiohttp import ClientConnectorError as CCError  # To detect connection errors.
from discord import (
    CategoryChannel,
    Embed,
    Forbidden,
    GroupChannel,
    Interaction,
    Member,
    Message,
    StageChannel,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
    utils,
)
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Command, Context

_ContextT = TypeVar("_ContextT", bound="Context[Any]")


def check_embed_length(ctx: Context, embed: Embed) -> Embed:
    """Checks the lengths of an embed, and returns an error embed instead if it's too long."""
    if len(embed) > 6000:
        embed = Embed(colour=discord.Color(0x990F02), timestamp=discord.utils.utcnow())
        embed.description = "The combined length of the embed was more than the 6000 character maximum!"
        embed.set_author(name="Oh no! Something went wrong!")
        embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)
    return embed


class DependencyError(commands.CommandError):
    """Custom exception raised when modules are missing dependencies."""

    def __init__(self, dependencies: List[str]):
        """Initialization of DependencyError exception."""
        self.message = f"Missing dependencies: {', '.join(dependencies)}"
        self.missing_dependencies = dependencies
        super().__init__(self.message)


class ConfigError(commands.CommandError):
    """Custom exception raised when missing config options."""

    def __init__(self, message: str = ""):
        """Initialization of ConfigError exception."""
        self.message = message
        super().__init__(self.message)


def required_config(requirements: Iterable[str]):
    """Function that makes sure config options are set."""

    async def predicate(predicate_ctx: Context) -> bool:
        missing = [f"`{requirement}`" for requirement in requirements if requirement not in predicate_ctx.bot.config]
        missing_str = ", ".join(missing)[:1850]
        if missing_str:
            await predicate_ctx.send(
                f"This command requires the following missing configuration options to be set: {missing_str}.\nPlease "
                f"contact an administrator for assistance."
            )
            raise ConfigError(f"Command {predicate_ctx.command.qualified_name} missing config options: {missing_str}")
        return not missing_str

    return commands.check(predicate)


class DatabaseCredentials:
    """Class that holds database credentials."""

    def __init__(self, user: str, password: str, host: str, port: str, database: str):
        """Initialization function for HelpInfo class."""
        self._user = user
        self._password = password
        self._host = host
        self._port = port
        self._database = database

    def get_credentials(self) -> Dict[str, str]:
        """Returns a dictionary mapping from user, password, host, port and database to the respective values."""
        return {
            "user": self._user,
            "password": self._password,
            "host": self._host,
            "port": self._port,
            "database": self._database,
        }


class GlobalChannel(commands.Converter):
    """Custom converter that returns user, or channel be it in the current server or another."""

    async def convert(
        self, ctx: Context, channel: str
    ) -> Union[TextChannel, VoiceChannel, StageChannel, CategoryChannel, GroupChannel, User, Thread]:
        """Converter method used by discord.py."""
        if isinstance(channel, str) and channel.lower() in ["here", "."]:
            return ctx.channel  # Get current channel if asked for.
        if isinstance(channel, str) and channel.lower() in ["dm", "dms", "pm", "pms"]:
            return ctx.author  # Get DM channel if asked for.
        try:
            return await commands.UserConverter().convert(ctx, channel)
        except commands.UserNotFound:
            pass
        try:
            return await commands.TextChannelConverter().convert(ctx, channel)
        except commands.ChannelNotFound:  # Channel not in server.
            pass
        try:
            return await commands.ThreadConverter().convert(ctx, channel)
        except commands.ThreadNotFound:
            pass
        try:
            converted = ctx.bot.get_channel(int(channel))
            if converted is None:
                raise commands.UserInputError("Could not identify channel.")
            return converted
        except ValueError:
            raise commands.UserInputError("Could not identify channel.")


class GlobalTextChannel(commands.Converter):
    """Custom converter that returns user, or text channel be it in the current server or another."""

    async def convert(self, ctx: Context, text_channel: str) -> Union[TextChannel, GroupChannel, User, Thread]:
        """Converter method used by discord.py."""
        if isinstance(text_channel, str) and text_channel.lower() in ["here", "."]:
            return ctx.channel  # Get current channel if asked for.
        if isinstance(text_channel, str) and text_channel.lower() in ["dm", "dms", "pm", "pms"]:
            return ctx.author  # Get DM channel if asked for.
        try:
            return await commands.UserConverter().convert(ctx, text_channel)
        except commands.UserNotFound:
            pass
        try:
            return await commands.TextChannelConverter().convert(ctx, text_channel)
        except commands.ChannelNotFound:  # Channel not in server.
            pass
        try:
            return await commands.ThreadConverter().convert(ctx, text_channel)
        except commands.ThreadNotFound:
            pass
        try:
            converted = await ctx.bot.fetch_channel(int(text_channel))
            if not converted or not isinstance(converted, (TextChannel, GroupChannel, User, Thread)):
                raise commands.UserInputError("Could not identify text channel.")
            return converted
        except ValueError:
            raise commands.UserInputError("Could not identify text channel.")


class TBBContext(commands.Context):
    """Custom Context class that types bot correctly."""

    bot: "TravusBotBase"


class TravusBotBase(Bot):
    """Custom bot class with database connection."""

    class _HelpInfo:
        """Class that holds help info for commands."""

        def __init__(
            self,
            get_prefix: Callable,
            command: Command,
            category: str = "no category",
            restrictions: Dict[str, Union[List[str], str]] = None,
            examples: List[str] = None,
        ):
            """Initialization function loading all necessary information for HelpInfo class."""
            res = restrictions  # Shortening often used variable name.
            self.get_prefix = get_prefix
            self.name = command.qualified_name
            self.description = command.help.replace("\n", " ") if command.help else "No description found."
            self.aliases = list(command.aliases) or []
            self.aliases.append(command.name)
            self.category = category
            self.examples = examples or []
            self.permissions = res["perms"] if isinstance(res, dict) and "perms" in res.keys() else []
            self.roles = res["roles"] if isinstance(res, dict) and "roles" in res.keys() else []
            self.other_restrictions = res["other"] if isinstance(res, dict) and "other" in res.keys() else ""
            self.owner_only, self.guild_only, self.dm_only = False, False, False
            for check in command.checks:
                if "is_owner" in str(check):
                    self.owner_only = True
                if "guild_only" in str(check):
                    self.guild_only = True
                if "dm_only" in str(check):
                    self.dm_only = True

        def make_help_embed(self, ctx: Context) -> Embed:
            """Creates embeds for command based on info stored in class."""
            embed = Embed(colour=discord.Color(0x4A4A4A), timestamp=discord.utils.utcnow())
            description = f"Category: {self.category.title()}\n\n{self.description}"
            embed.description = description if len(description) < 4097 else f"{description[:4092]}..."
            embed.set_author(name=f"{self.name.title()} Command"[:255])
            aliases = "\n".join(sorted(self.aliases))  # Make and add aliases blurb.
            embed.add_field(name="Aliases", value=f"```\n{aliases[:1017]}```", inline=True)
            restrictions = "Bot Owner Only: Yes\n" if self.owner_only else ""  # Make and add restrictions blurb.
            restrictions += "DM Only: Yes\n" if self.dm_only else ""
            restrictions += "" if self.dm_only else "Server Only: Yes" if self.guild_only else "Server Only: No"
            restrictions += (
                ("\nPermissions:\n" + "\n".join(f"   {perm}" for perm in self.permissions)) if self.permissions else ""
            )
            restrictions += (
                ("\nAny role of:\n" + "\n".join([f"   {role}" for role in self.roles])) if self.roles else ""
            )
            restrictions += f"\n{self.other_restrictions}" if self.other_restrictions else ""
            embed.add_field(name="Restrictions", value=f"```{restrictions[:1017]}```", inline=True)
            examples = "\n".join(
                [
                    f"`{self.get_prefix()}{self.name} {example}`" if example else f"`{self.get_prefix()}{self.name}`"
                    for example in self.examples
                ]
            )
            embed.add_field(name="Examples", value=examples[:1017] or "No examples found.", inline=False)
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return check_embed_length(ctx, embed)

    class _ModuleInfo:
        """Class that holds info for modules."""

        def __init__(
            self,
            get_prefix: Callable,
            name: str,
            author: str,
            usage: Callable[[], Union[str, Embed]] = None,
            description: str = None,
            extra_credits: str = None,
            image_link: Union[str, discord.Asset] = None,
        ):
            """Initialization function loading all necessary information for ModuleInfo class."""
            self.get_prefix = get_prefix
            self.name = name
            # Convert tabs to non-skipped spaces.
            self.author = author.replace("\t", "\u202F\u202F\u202F\u202F\u202F")
            self.description = description.replace("\n", " ") if description else "No module description found."
            self.credits = extra_credits.replace("\t", "\u202F\u202F\u202F\u202F\u202F") if extra_credits else None
            self.image = image_link
            self.usage = usage

        def make_about_embed(self, ctx: Context) -> Embed:
            """Creates embeds for module based on info stored in class."""
            embed = Embed(colour=discord.Color(0x4A4A4A), timestamp=discord.utils.utcnow())
            description = self.description.replace("_prefix_", self.get_prefix())
            embed.description = description if len(description) < 4097 else f"{description[:4092]}..."
            embed.set_author(name=self.name)
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            if self.image:
                embed.set_thumbnail(url=self.image)
            author = self.author if len(self.author) < 1024 else f"{self.author[:1020]}..."
            if not self.credits:
                embed.add_field(name="Authored By", value=author)
            else:  # If there are additional credits make both sections inline.
                extra_credits = self.credits if len(self.credits) < 1024 else f"{self.credits[:1020]}..."
                embed.add_field(name="Authored By", value=author, inline=True)
                embed.add_field(name="Additional Credits", value=extra_credits, inline=True)
            return check_embed_length(ctx, embed)

    class _CustomHelp(commands.HelpCommand):
        """Class for custom help command."""

        context: TBBContext

        def __init__(self):
            """Initialization function that sets help and usage text for custom help command."""
            super(TravusBotBase._CustomHelp, self).__init__(
                command_attrs={
                    "help": """This command shows a list of categorized commands you have access to. If the name of
                    a command is sent along it will show detailed help information for that command, such as what the
                    command does, aliases, what restrictions it has, and examples.""",
                    "usage": "(COMMAND NAME)",
                }
            )

        async def _send_help_entry(self, com_object):
            """Help function which sends help entry og single command. Factored out for DRYer code."""
            if com_object.qualified_name in self.context.bot.help.keys():
                if com_object.enabled:
                    embed = self.context.bot.help[com_object.qualified_name].make_help_embed(self.context)
                    await self.get_destination().send(embed=embed)  # Send command help info.
                else:
                    await self.get_destination().send(f"The `{com_object.qualified_name}` command has been disabled.")
            else:
                await self.get_destination().send("No help information is registered for this command.")

        async def _send_command_list(self, full_mapping: Set[Command]):
            """Help function which sends the command list. Factored out for DRYer code."""
            categories: Dict[str, List[str]] = {}  # List of categorized commands.
            filtered_mapping = {f"`{com.qualified_name}`": com for com in await self.filter_commands(full_mapping)}
            non_passing = list(set(full_mapping).difference(set(filtered_mapping.values())))
            new_message = self.context.message
            new_message.guild = None
            new_ctx = await self.context.bot.get_context(new_message)
            non_passing = {f"`{com.qualified_name}`¹": com for com in non_passing if await can_run(com, new_ctx)}
            filtered_mapping.update(non_passing)
            if not filtered_mapping:
                await self.get_destination().send("No help information was found.")
                return
            for com_text, com in filtered_mapping.items():
                if com.qualified_name in self.context.bot.help.keys():
                    command_help = self.context.bot.help[com.qualified_name]  # Get command help info.
                    category = command_help.category.lower() if command_help.category else "no category"
                    if category not in categories:  # Add category if it wasn't encountered before.
                        categories[category] = []
                    categories[category].append(com_text)  # Add command to category.

            paginator = commands.Paginator(prefix="", suffix="", linesep="")
            paginator.add_line(f"__**Help Info {self.context.message.author.mention}:**__\n\n")
            for category in sorted(categories.keys()):
                paginator.add_line(f"**{category.title()}**\n")
                category_commands = [f"{com}, " for com in sorted(categories[category])]
                category_commands[-1] = f"{category_commands[-1][:-2]}\n\n"  # Replace ', ' with '\n\n' on last command
                for com in category_commands:
                    paginator.add_line(self.remove_mentions(com))
            end = "1 = In DMs only.\n" if any(["¹" in elem for cat in categories.values() for elem in cat]) else ""
            end += f"Use `{self.context.bot.get_bot_prefix()}help <COMMAND>` for more info on individual commands."
            paginator.add_line(end)
            for page in paginator.pages:
                await self.get_destination().send(page)

        async def send_bot_help(self, mapping):
            """Function that triggers when help command is used without command."""
            full_mapping = []  # Command list.
            for com_mapping in mapping.values():
                full_mapping.extend(com_mapping)  # Add all cogs to list.
            full_mapping = {com for com in full_mapping if com.enabled and not com.hidden}
            await self._send_command_list(full_mapping)

        async def send_command_help(self, command_object: Command):
            """Function that triggers when help command is used with a command."""
            while command_object.qualified_name not in self.context.bot.help.keys() and len(command_object.parents):
                command_object = command_object.parents[0]  # Get parent in case it has help text.
            await self._send_help_entry(command_object)

        async def send_cog_help(self, cog: Cog):
            """Function that triggers when help command is used with a cog."""
            full_mapping = {com for com in cog.get_commands() if com.enabled and not com.hidden}
            await self._send_command_list(full_mapping)

        async def send_group_help(self, group):
            """Function that triggers when help command is used with a group."""
            while group.qualified_name not in self.context.bot.help.keys() and len(group.parents):
                group = group.parents[0]  # Get parent in case it has help text.
            await self._send_help_entry(group)

        def subcommand_not_found(self, command, string):
            """Function that returns content of error when subcommand invalid."""
            return f"The `{command.qualified_name}` command has no subcommand called `{string}`."

        def command_not_found(self, string):
            """Function that returns content of error when command not found."""
            return f"No command called `{string}` found."

    def __init__(self, database_credentials: DatabaseCredentials, *args, **kwargs):
        """Initialization function loading all necessary information for TravusBotBase class."""
        super().__init__(*args, **kwargs)
        self.db: Optional[asyncpg.Pool] = None
        self.log = BOT_LOG
        self.last_module_error: Optional[str] = None
        self.last_error: Optional[str] = None
        self.extension_ctx: Optional[Context] = None
        self.help: Dict[str, TravusBotBase._HelpInfo] = {}
        self.modules: Dict[str, TravusBotBase._ModuleInfo] = {}
        self.is_connected: int = 0
        self.help_command = self._CustomHelp()
        self.config: Dict[str, str] = {}
        self._db_creds = database_credentials

    async def get_context(
        self, origin: Union[Message, Interaction], *, cls: Optional[Type[_ContextT]] = None
    ) -> Union[TBBContext, _ContextT]:
        """Create TBBContexts with correct bot typing."""
        return await super().get_context(origin, cls=cls or TBBContext)

    async def _load_db_options(self):
        """Create, set up and query database for info. Create default values if database is empty."""
        async with self.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "CREATE TABLE IF NOT EXISTS settings(key VARCHAR PRIMARY KEY NOT NULL, value VARCHAR)"
                )
                await conn.execute("CREATE TABLE IF NOT EXISTS default_modules(module VARCHAR PRIMARY KEY NOT NULL)")
                await conn.execute(
                    "CREATE TABLE IF NOT EXISTS command_states(command VARCHAR PRIMARY KEY NOT NULL, "
                    "state INTEGER NOT NULL)"
                )
                await conn.execute("CREATE TABLE IF NOT EXISTS config(key VARCHAR PRIMARY KEY NOT NULL, value VARCHAR)")
                await conn.execute(
                    "INSERT INTO settings VALUES ('additional_credits', '') ON CONFLICT (key) DO NOTHING"
                )
                await conn.execute("INSERT INTO settings VALUES ('bot_description', '') ON CONFLICT (key) DO NOTHING")
                await conn.execute("INSERT INTO settings VALUES ('delete_messages', '0') ON CONFLICT (key) DO NOTHING")
                await conn.execute("INSERT INTO settings VALUES ('prefix', '!') ON CONFLICT (key) DO NOTHING")
            loaded_prefix = await self.db.fetchval("SELECT value FROM settings WHERE key = 'prefix'")
            delete_msgs = await conn.fetchval("SELECT value FROM settings WHERE key = 'delete_messages'")
            config = await conn.fetch("SELECT key, value FROM config")

        self.prefix: Optional[str] = loaded_prefix or None
        self.delete_messages: int = int(delete_msgs) if delete_msgs is not None else 1
        self.add_command_help(
            [com for com in self.commands if com.name == "help"][0], "Core", None, ["", "about", "help"]
        )  # Add help info for help command.
        for key, value in [(pair["key"], pair["value"]) for pair in config]:
            self.config[key] = value

    async def _load_default_commands(self):
        """Load the default commands from core_commands.py"""
        try:
            if "core_commands.py" in os.listdir("."):
                await self.load_extension("core_commands")
                await self.update_command_states()
            else:
                raise FileNotFoundError("Core commands file not found.")
        except FileNotFoundError:
            self.log.critical("Error: Core commands file not found.")
            await self.db.close()
            exit(4)
        except Exception as e:
            if isinstance(e, commands.ExtensionNotFound):
                e = e.__cause__
            self.log.critical(f"Error: Core functionality file failed to load.\n\nError:\n{e}")
            await self.db.close()
            exit(3)

    async def _load_default_modules(self):
        """Load default modules once bot has cached."""

        async def load_module(default_list: List[str], module: str, propagate=False) -> bool:
            """Attempt to load a module, and recursively attempts to loads dependencies."""
            if module not in default_list:
                return False
            default_list.remove(module)

            old_help = dict(self.help)  # Save module and help info before loading in case we need to roll back.
            old_modules = dict(self.modules)
            self.extension_ctx = None
            try:  # Try loading default module.
                if f"{module}.py" in os.listdir("modules"):
                    await self.load_extension(f"modules.{module}")
                else:
                    raise FileNotFoundError("Core commands file not found.")
            except FileNotFoundError:  # If module wasn't found.
                if propagate:
                    raise
                self.last_error = f"Default module '{module}' not found."
                self.log.warning(f"Default module '{module}' not found.")
                return False
            except commands.ExtensionFailed as e:
                self.help = old_help
                self.modules = old_modules
                if propagate:
                    raise
                if isinstance(e.original, DependencyError):
                    if all(load_module(default_list, dependency) for dependency in e.original.missing_dependencies):
                        try:
                            default_list.append(module)
                            if load_module(default_list, module, True):
                                return True
                        except Exception as ee:
                            e = ee
                self.log.error(f"Default module '{module}' encountered and error.\n\n{str(e)}")
                self.last_module_error = f"The `{module}` module failed while loading. The error was:\n\n{str(e)}"
                return False
            except Exception as e:  # If en error was encountered while loading default module, roll back.
                self.help = old_help
                self.modules = old_modules
                if propagate:
                    raise
                if isinstance(e, commands.ExtensionNotFound):  # If import error, clarify further.
                    e = e.__cause__
                self.log.error(f"Default module '{module}' encountered and error.\n\n{str(e)}")
                self.last_module_error = f"The `{module}` module failed while loading. The error was:\n\n{str(e)}"
                return False
            else:
                self.log.info(f"Default module '{module}' loaded.")
                return True

        async with self.db.acquire() as conn:
            default_modules = await conn.fetch("SELECT module FROM default_modules")
        default_modules = [mod["module"] for mod in default_modules]
        await self.wait_until_ready()  # Wait until object cashing is done.

        for mod in list(default_modules):
            await load_module(default_modules, mod)
        await self.update_command_states()  # Make sure commands are in the right state. (hidden, disabled)

    async def start(self, token: str, *, reconnect: bool = True):
        """Connect to the database and load default data, commands, and modules, then start the bot."""
        try:
            async with asyncpg.create_pool(**self._db_creds.get_credentials()) as pool:
                self.db: asyncpg.pool.Pool = pool
                await self._load_db_options()
                await self._load_default_commands()
                await self._load_default_modules()  # Waits for bot to be ready
                await super(TravusBotBase, self).start(token, reconnect=reconnect)
        except asyncpg.exceptions.InvalidCatalogNameError:
            self.log.critical("Error: Failed to connect to database. Database name not found.")
        except asyncpg.exceptions.InvalidPasswordError:
            self.log.critical("Error: Failed to connect to database. Username or password incorrect.")
        except OSError:
            self.log.critical("Error: Failed to connect to database. Connection error.")
        except Exception as e:
            self.log.critical(f"Error: {e}")

    async def close(self):
        """Coses the bot and the database connections."""
        if self.db is not None:
            await self.db.close()
        await super().close()

    def get_bot_prefix(self) -> str:
        """Returns the current bot prefix, or a mention of the bot in text form followed by a space."""
        if self.prefix is not None:
            return self.prefix
        return f"@{self.user.display_name}#{self.user.discriminator} "

    def check_dependencies(self, dependencies: List[str]):
        """Checks if all dependencies are met. Raises DependencyError with the missing dependencies if not."""
        dependencies = dependencies.copy()
        if "core_commands" in dependencies and "core_commands" in self.extensions:  # core_commands is not in modules
            dependencies.remove("core_commands")
        for dependency in dependencies:
            if f"modules.{dependency}" in self.extensions:
                dependencies.remove(dependency)
        if dependencies:
            raise DependencyError(dependencies)

    def add_module(
        self,
        name: str,
        author: str,
        usage: Callable[[], Union[str, Embed]] = None,
        description: str = None,
        additional_credits: str = None,
        image_link: Union[str, discord.Asset] = None,
    ):
        """Function that is used to add module info to the bot correctly. Used to minimize developmental errors."""
        info = self._ModuleInfo(self.get_bot_prefix, name, author, usage, description, additional_credits, image_link)
        if name.lower() not in self.modules.keys():
            self.modules[name.lower()] = info
        else:
            raise RuntimeError(f"A module with the name '{name}' already exists.")

    def remove_module(self, name: str):
        """Function that is used to remove module info to the bot correctly. Used to minimize developmental errors."""
        if name.lower() in self.modules.keys():
            del self.modules[name.lower()]

    def add_commands(self, command_list: List[Command]):
        """Adds multiple commands at once using bot.add_command."""
        for com in command_list:
            self.add_command(com)

    def remove_commands(self, command_list: List[Union[Command, str]]):
        """Removed multiple commands at once using bot.remove_command. Accepts command names or commands."""
        for com in command_list:
            self.remove_command(com.name if isinstance(com, Command) else com)

    async def update_command_states(self):
        """Function that get command state (hidden, disabled) for every command currently loaded."""
        async with self.db.acquire() as conn:
            async with conn.transaction():
                for command in self.commands:
                    cog_com_name = f"{f'{command.cog_name}.' if command.cog_name else ''}{command.name}"
                    command_state = await conn.fetchval(
                        "SELECT state FROM command_states WHERE command = $1;", cog_com_name
                    )
                    if command_state is None:  # If a command has no state registered, set it to visible and enables.
                        command_state = (0,)
                        await conn.execute("INSERT INTO command_states VALUES ($1, $2)", cog_com_name, 0)
                    if command_state == 1:  # Set command to be hidden.
                        command.enabled = True
                        command.hidden = True
                    elif command_state == 2:  # Set command to be disabled.
                        command.enabled = False
                        command.hidden = False
                    elif command_state == 3:  # Set command to be hidden and disabled.
                        command.enabled = False
                        command.hidden = True

    def add_command_help(
        self,
        command,
        category: str = "no category",
        restrictions: Dict[str, Union[List[str], str]] = None,
        examples: List[str] = None,
    ):
        """Function that is used to add help info to the bot correctly. Used to minimize developmental errors. Command
        should be either a command or a command group."""
        # The Command argument is currently not typed due to type checking issues in PyCharm, should be type 'Command'.
        self.help[command.qualified_name] = self._HelpInfo(
            self.get_bot_prefix, command, category, restrictions, examples
        )

    def remove_command_help(self, command: Union[Command, Type[Cog], str, List[Union[Command, str]]]):
        """Function that is used to remove command help info from the bot correctly. Used to minimize developmental
        errors."""
        if isinstance(command, list):  # Remove all in list, if list is passed.
            for com in command:
                name = com.qualified_name if isinstance(com, Command) else com
                if name in self.help:
                    del self.help[name]
        elif isinstance(command, Command):  # Remove single if only one is passed.
            if command.qualified_name in self.help:
                del self.help[command.qualified_name if isinstance(command, Command) else command]
        elif issubclass(command, Cog):
            for com in command(self).walk_commands():
                if com.qualified_name in self.help:
                    del self.help[com.qualified_name]
        elif isinstance(command, str):
            if command in self.help:
                del self.help[command]

    async def on_ready(self):
        """This function runs every time the bot connects to Discord. This happens multiple times.
        Sets about command and bot status. These require the bot to be online and hence are in here."""
        if self.user.name.lower() not in self.modules.keys():
            async with self.db.acquire() as conn:
                bot_credits = await conn.fetchval("SELECT value FROM settings WHERE key = 'additional_credits'")
                bot_desc = await conn.fetchval("SELECT value FROM settings WHERE key = 'bot_description'")
            bot_author = (
                "[Travus](https://github.com/Travus):\n\tTravus Bot Base\n\tCore functions\n\n"
                "[Rapptz](https://github.com/Rapptz):\n\tDiscord.py"
            )
            bot_credits = (
                bot_credits.replace("\\n", "\n").replace("\\r", "\n").replace("\\t", "\t") if bot_credits else None
            )
            bot_desc = bot_desc or "No description for the bot found. Set description with `botconfig` command."
            self.add_module(self.user.name, bot_author, None, bot_desc, bot_credits, self.user.display_avatar)
        activity = discord.Activity(
            type=discord.ActivityType.listening, name=f"prefix: {self.prefix}" if self.prefix else "pings only"
        )
        await self.change_presence(activity=activity)  # Display status message.
        self.is_connected = 1  # Flag that the bot is currently connected to Discord.
        self.log.info(f"{self.user.name} is ready!\n------------------------------")

    async def on_disconnect(self):
        """Writes to console if bot disconnects from Discord."""
        if self.is_connected:  # If the bot was last connected, log disconnect to console.
            self.log.info("Disconnected from Discord.")
            self.is_connected = 0  # Flag that the bot is currently disconnected from Discord.

    async def on_resumed(self):
        """Writes to console if bot reconnects to Discord."""
        if not self.is_connected:  # If the bot was last disconnected, log reconnect to console.
            self.log.info("Reconnected to Discord.")
            self.is_connected = 1  # Flag that the bot is currently connected to Discord.

    async def on_command(self, ctx: Context):
        """Deletes command if command deletion is set."""
        if self.delete_messages and ctx.guild:  # If the message is in a server and the delete messages flag is true.
            try:  # Try to delete message.
                await ctx.message.delete()
            except Forbidden:  # Log to console if missing permission to delete message.
                self.log.warning("Bot does not have required permissions to delete message.")

    async def on_command_error(self, ctx: Context, error=None):
        """Global error handler for miscellaneous errors."""
        if isinstance(
            error,
            (commands.NoPrivateMessage, commands.CommandOnCooldown, commands.DisabledCommand, commands.CheckFailure),
        ):
            pass
        elif isinstance(error, commands.UserInputError):  # Send correct syntax based on command usage variable.
            if hasattr(ctx.command, "usage") and ctx.command.usage:
                await ctx.send(
                    f"Correct syntax: `{self.get_bot_prefix()}"
                    f"{ctx.command.full_parent_name + ' ' if ctx.command.full_parent_name else ''}"
                    f"{ctx.invoked_with} {ctx.command.usage or ''}`"
                )
        elif isinstance(error, commands.NotOwner):  # Log to console.
            self.log.warning(f"{ctx.author.id}: Command '{ctx.command}' requires bot owner status")
        elif isinstance(error, commands.MissingPermissions):  # Log to console.
            self.log.warning(
                f"{ctx.author.id}: Command '{ctx.command}' requires additional permissions: "
                f"{', '.join(error.missing_permissions)}"
            )
        elif isinstance(error, commands.MissingRole):  # Log to console.
            self.log.warning(f"{ctx.author.id}: Command '{ctx.command}' requires role: {error.missing_role}")
        elif isinstance(error, commands.MissingAnyRole):  # Log to console.
            self.log.warning(
                f"{ctx.author.id}: Command '{ctx.command}' requires role: " f"{' or '.join(error.missing_roles)}"
            )
        elif isinstance(error, commands.CommandNotFound):  # Log to console.
            self.log.warning(f"{ctx.author.id}: {error}")
        elif isinstance(error, CCError):  # Log to console if message wasn't properly sent to Discord.
            self.log.warning(f"{ctx.author.id}: Connection error to Discord. Message lost.")
        elif isinstance(error.__cause__, Forbidden):  # Log to console if lacking permissions.
            self.log.warning(f"{ctx.author.id}: Missing permissions.")
        elif error is not None:  # Log error to console.
            self.log.warning(f"{ctx.author.id}: {error}")
        self.last_error = f"[{cur_time()}] {ctx.author.id}: {error}"


def parse_time(duration: str, minimum: int = None, maximum: int = None, error_on_exceeded: bool = True) -> int:
    """Function that parses time in a NhNmNs format. Supports weeks, days, hours, minutes and seconds, positive and
    negative amounts and max values. Minimum and maximum values can be set (in seconds), and whether a error should
    occur or the max / min value should be used when these are exceeded."""
    last, t_total = 0, 0
    t_frames = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}
    for index, char in enumerate(duration):  # For every character in time string.
        if char.lower() in t_frames.keys():
            if duration[last:index] != "":
                t_total += int(duration[last:index]) * t_frames[char.lower()]
            last = index + 1
        elif char not in ["+", "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:  # Valid characters.
            raise ValueError("Invalid character encountered during time parsing.")
    if minimum and t_total < minimum:  # If total time is less than minimum.
        if error_on_exceeded:
            raise ValueError("Time too short.")
        t_total = minimum
    if maximum and t_total > maximum:  # If total time is more than maximum.
        if error_on_exceeded:
            raise ValueError("Time too long.")
        t_total = maximum
    return t_total


async def send_in_global_channel(ctx: Context, channel: Optional[GlobalTextChannel], msg: str, other_dms: bool = False):
    """Sends a message in any text channel across servers and DMs. Has flag to allow sending to foreign DMs."""
    user = ctx.author
    try:
        if isinstance(channel, (User, Member)) and channel.id != user.id and not other_dms:
            await ctx.send("Sending messages to another user's DMs is forbidden.")
        elif isinstance(channel, (User, Member)) and (channel.id == user.id or other_dms):
            await channel.send(msg)
        elif isinstance(channel, TextChannel) and channel.permissions_for(user).send_messages or channel is None:
            await (channel or ctx.channel).send(msg)
        elif isinstance(channel, Thread):
            if not channel.permissions_for(user).send_messages_in_threads or channel.locked or channel.archived:
                await ctx.send("You do not have permission to send messages in this thread.")
            else:
                if channel.is_private():
                    if user not in await channel.fetch_members() and not channel.permissions_for(user).manage_threads:
                        await ctx.send("You do not have permission to send messages in this private thread.")
                else:
                    await channel.send(msg)
        else:
            await ctx.send("You do not have permission to send messages in this channel.")
    except Forbidden:
        await ctx.send("Cannot send messages in given channel.")


async def can_run(command: Command, ctx: Context) -> bool:
    """This function uses command.can_run to see if a command can be run by a user, but does not raise exceptions."""
    try:
        await command.can_run(ctx)
    except commands.CommandError:
        return False
    else:
        return True


def cur_time() -> str:
    """Get current UTC time in YYYY-MM-DD HH:MM format."""
    return str(discord.utils.utcnow())[0:16]


async def del_message(msg: Message):
    """Tries to delete a passed message, handling permission errors."""
    if msg.guild:
        try:  # Try to delete message.
            await msg.delete()
        except Forbidden:  # Log to console if missing permission to delete message.
            BOT_LOG.warning("Bot does not have required permissions to delete message.")


def _clean(
    bot: TravusBotBase,
    guild: Optional[discord.Guild],
    text: str,
    escape_markdown: bool = True,
    replace_backticks: bool = False,
) -> str:
    """Underlying function used by clean and clean_no_ctx functions."""
    transformations: Dict[str, str] = {}

    def resolve_member(_id):
        """Resolves user mentions."""
        member = bot.get_user(_id)
        return "@" + member.name if member else "@deleted-user"

    transformations.update(
        ("<@%s>" % member_id, resolve_member(member_id)) for member_id in [int(x) for x in findall(r"<@!?(\d+)>", text)]
    )
    transformations.update(
        ("<@!%s>" % member_id, resolve_member(member_id))
        for member_id in [int(x) for x in findall(r"<@!?(\d+)>", text)]
    )

    if guild:

        def resolve_channel(_id):
            """Resolves channel mentions."""
            ch = guild.get_channel(_id)
            return ("<#%s>" % _id), ("#" + ch.name if ch else "#deleted-channel")

        def resolve_role(_id):
            """Resolves role mentions."""
            role = guild.get_role(_id)
            return "@" + role.name if role else "@deleted-role"

        transformations.update(resolve_channel(channel) for channel in [int(x) for x in findall(r"<#(\d+)>", text)])
        transformations.update(
            ("<@&%s>" % role_id, resolve_role(role_id)) for role_id in [int(x) for x in findall(r"<@&(\d+)>", text)]
        )

    def repl(obj):
        """Function used in regex substitution."""
        return transformations.get(obj.group(0), "")

    pattern = re_cmp("|".join(transformations.keys()))
    result = pattern.sub(repl, text)
    if escape_markdown:
        result = utils.escape_markdown(result)
    if replace_backticks:
        result = result.replace("`", "ˋ")
    return utils.escape_mentions(result)


def clean(ctx: Context, text: str, escape_markdown: bool = True, replace_backticks: bool = False) -> str:
    """Cleans text, escaping mentions and markdown. Tries to change mentions to text."""
    return _clean(ctx.bot, ctx.guild, text, escape_markdown, replace_backticks)


def clean_no_ctx(
    bot: TravusBotBase,
    guild: Optional[discord.Guild],
    text: str,
    escape_markdown: bool = True,
    replace_backticks: bool = False,
) -> str:
    """Cleans text, escaping mentions and markdown. Tries to change mentions to text. Works without context."""
    return _clean(bot, guild, text, escape_markdown, replace_backticks)


def unembed_urls(text: str) -> str:
    """Finds all URLs in a text and encases them in <> to escape prevent embedding."""

    def repl(obj):
        """Function used in regex substitution."""
        return f"<{obj.group(0).strip('<').strip('>')}>"

    ptrn = re_cmp(r"(\b|<)https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_+.~#?&\\/=]*)>?")
    text = ptrn.sub(repl, text)
    return text


BOT_LOG = logging.getLogger("bot")
BOT_LOG.setLevel(logging.INFO)
