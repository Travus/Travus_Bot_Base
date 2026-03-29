import copy
import io
import logging
import os
from collections.abc import Callable, Coroutine, Iterable
from re import compile as re_cmp  # Regex functions used in clean function for detecting mentions.
from re import findall
from typing import Any, TypeVar

import asyncpg
import discord
from aiohttp import ClientConnectorError as CCError  # To detect connection errors.
from discord import (
    CategoryChannel,
    DMChannel,
    Embed,
    Forbidden,
    ForumChannel,
    GroupChannel,
    Interaction,
    Member,
    Message,
    PartialMessageable,
    StageChannel,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
    app_commands,
    utils,
)
from discord.ext import commands
from discord.ext.commands import Bot, Cog, Command, Context, Group

_ContextT = TypeVar("_ContextT", bound="Context[Any]")


def check_embed_length(author: User | Member, embed: Embed) -> Embed:
    """Checks the lengths of an embed, and returns an error embed instead if it's too long."""
    if len(embed) > 6000:
        embed = Embed(colour=discord.Color(0x990F02), timestamp=discord.utils.utcnow())
        embed.description = "The combined length of the embed was more than the 6000 character maximum!"
        embed.set_author(name="Oh no! Something went wrong!")
        embed.set_footer(text=author.display_name, icon_url=author.display_avatar)
    return embed


class DependencyError(commands.CommandError):
    """Custom exception raised when modules are missing dependencies."""

    def __init__(self, dependencies: list[str]):
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
        if predicate_ctx.command is None:
            BOT_LOG.error("Required config was used on non-command, this is not supported")
            return True
        missing = [f"`{requirement}`" for requirement in requirements if requirement not in predicate_ctx.bot.config]
        missing_str = ", ".join(missing)[:1850]
        if missing_str:
            await predicate_ctx.send(
                f"This command requires the following missing configuration options to be set: {missing_str}.\nPlease "
                "contact an administrator for assistance."
            )
            raise ConfigError(f"Command {predicate_ctx.command.qualified_name} missing config options: {missing_str}")
        return not missing_str

    return commands.check(predicate)


class DatabaseCredentials:
    """Class that holds database credentials."""

    def __init__(self, user: str, password: str, host: str, port: str | int, database: str):
        """Initialization function for DatabaseCredentials class."""
        self.user = user
        self.password = password
        self.host = host
        self.port = int(port)
        self.database = database


class GlobalChannel(commands.Converter):
    """Custom converter that returns user, or channel be it in the current server or another."""

    async def convert(
        self, ctx: Context, argument: str
    ) -> CategoryChannel | DMChannel | ForumChannel | GroupChannel | StageChannel | TextChannel | Thread | VoiceChannel:
        """Converter method used by discord.py."""
        if isinstance(argument, str) and argument.lower() in ["here", "."]:
            if isinstance(ctx.channel, PartialMessageable):
                raise commands.UserInputError(f"Unable to get channel details for channel ID: {ctx.channel.id}")
            return ctx.channel  # Get current channel if asked for.
        if isinstance(argument, str) and argument.lower() in ["dm", "dms", "pm", "pms"]:
            dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()  # Get DM channel if asked for.
            return dm_channel
        try:
            user = await commands.UserConverter().convert(ctx, argument)
            dm_channel = user.dm_channel or await user.create_dm()
            return dm_channel
        except commands.UserNotFound:
            pass
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.ChannelNotFound:  # Channel not in server.
            pass
        try:
            return await commands.ThreadConverter().convert(ctx, argument)
        except commands.ThreadNotFound:
            pass
        try:
            converted = await ctx.bot.fetch_channel(int(argument))
            if converted is None:
                raise commands.UserInputError("Could not identify channel.")
            return converted
        except ValueError:
            raise commands.UserInputError("Could not identify channel.") from None


class GlobalTextChannel(commands.Converter):
    """Custom converter that returns user, or text channel be it in the current server or another."""

    async def convert(
        self, ctx: Context, argument: str
    ) -> DMChannel | ForumChannel | GroupChannel | StageChannel | TextChannel | Thread:
        """Converter method used by discord.py."""
        if isinstance(argument, str) and argument.lower() in ["here", "."]:
            if isinstance(ctx.channel, PartialMessageable):
                raise commands.UserInputError(f"Unable to get channel details for channel ID: {ctx.channel.id}")
            if isinstance(ctx.channel, VoiceChannel):
                raise commands.UserInputError("Channel is voice and not text channel.")
            return ctx.channel  # Get current channel if asked for.
        if isinstance(argument, str) and argument.lower() in ["dm", "dms", "pm", "pms"]:
            dm_channel = ctx.author.dm_channel or await ctx.author.create_dm()  # Get DM channel if asked for.
            return dm_channel
        try:
            user = await commands.UserConverter().convert(ctx, argument)
            dm_channel = user.dm_channel or await user.create_dm()
            return dm_channel
        except commands.UserNotFound:
            pass
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.ChannelNotFound:  # Channel not in server.
            pass
        try:
            return await commands.ThreadConverter().convert(ctx, argument)
        except commands.ThreadNotFound:
            pass
        try:
            converted = await ctx.bot.fetch_channel(int(argument))
            if not converted or not isinstance(converted, (GroupChannel, ForumChannel, TextChannel, Thread)):
                raise commands.UserInputError("Could not identify text channel.")
            return converted
        except ValueError:
            raise commands.UserInputError("Could not identify text channel.") from None


class TBBContext(commands.Context):
    """Custom Context class that types bot correctly."""

    bot: "TravusBotBase"


class TravusBotBase(Bot):  # pylint: disable=too-many-ancestors, too-many-instance-attributes
    """Custom bot class with database connection."""

    db: asyncpg.Pool

    class _HelpInfo:
        """Class that holds help info for commands."""

        def __init__(
            self,
            get_prefix: Callable,
            command: Command | Group | app_commands.Command | app_commands.Group,
            category: str = "no category",
            restrictions: dict[str, list[str] | str] | None = None,
            examples: list[str] | None = None,
        ):
            """Initialization function loading all necessary information for HelpInfo class."""
            res = restrictions  # Shortening often used variable name.
            self.get_prefix = get_prefix
            self.name = command.qualified_name
            self.is_slash = isinstance(command, (app_commands.Command, app_commands.Group))
            self.category = category
            self.examples = examples or []
            self.permissions = res["perms"] if isinstance(res, dict) and "perms" in res else []
            self.roles = res["roles"] if isinstance(res, dict) and "roles" in res else []
            self.other_restrictions = res["other"] if isinstance(res, dict) and "other" in res else ""
            self.owner_only, self.guild_only, self.dm_only = False, False, False

            if isinstance(command, (app_commands.Command, app_commands.Group)):
                doc = command.callback.__doc__ if isinstance(command, app_commands.Command) else None
                self.description = doc.replace("\n", " ") if doc else command.description or "No description found."
                self.aliases = [command.name]
                self.guild_only = command.guild_only
            else:
                self.description = command.help.replace("\n", " ") if command.help else "No description found."
                self.aliases = list(command.aliases) or []
                self.aliases.append(command.name)
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
            prefix = "/" if self.is_slash else self.get_prefix()
            examples = "\n".join(
                [
                    f"`{prefix}{self.name} {example}`" if example else f"`{prefix}{self.name}`"
                    for example in self.examples
                ]
            )
            embed.add_field(name="Examples", value=examples[:1017] or "No examples found.", inline=False)
            embed.set_footer(text=ctx.author.display_name, icon_url=ctx.author.display_avatar)
            return check_embed_length(ctx.author, embed)

    class _ModuleInfo:
        """Class that holds info for modules."""

        def __init__(
            self,
            get_prefix: Callable,
            name: str,
            author: str,
            usage: Callable[[], str | Embed] | None = None,
            description: str | None = None,
            extra_credits: str | None = None,
            image_link: str | discord.Asset | None = None,
        ):
            """Initialization function loading all necessary information for ModuleInfo class."""
            self.get_prefix = get_prefix
            self.name = name
            # Convert tabs to non-skipped spaces.
            self.author = author.replace("\t", "\u202f\u202f\u202f\u202f\u202f")
            self.description = description.replace("\n", " ") if description else "No module description found."
            self.credits = extra_credits.replace("\t", "\u202f\u202f\u202f\u202f\u202f") if extra_credits else None
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
            return check_embed_length(ctx.author, embed)

    class _CustomHelp(commands.HelpCommand):
        """Class for custom help command."""

        context: TBBContext  # pyright: ignore[reportIncompatibleVariableOverride]

        def __init__(self):
            """Initialization function that sets help and usage text for custom help command."""
            super().__init__(
                command_attrs={
                    "help": """This command shows a list of categorized commands you have access to. If the name of
                    a command is sent along it will show detailed help information for that command, such as what the
                    command does, aliases, what restrictions it has, and examples.""",
                    "usage": "(COMMAND NAME)",
                }
            )

        async def _send_help_entry(self, com_object):
            """Help function which sends help entry og single command. Factored out for DRYer code."""
            if com_object.qualified_name in self.context.bot.help:
                if com_object.enabled:
                    embed = self.context.bot.help[com_object.qualified_name].make_help_embed(self.context)
                    await self.get_destination().send(embed=embed)  # Send command help info.
                else:
                    await self.get_destination().send(f"The `{com_object.qualified_name}` command has been disabled.")
            else:
                await self.get_destination().send("No help information is registered for this command.")

        async def _send_command_list(self, full_mapping: set[Command]):
            """Help function which sends the command list. Factored out for DRYer code."""
            categories: dict[str, list[str]] = {}  # List of categorized commands.
            filtered_mapping = {f"`{com.qualified_name}`": com for com in await self.filter_commands(full_mapping)}
            non_passing = list(set(full_mapping).difference(set(filtered_mapping.values())))
            new_message = copy.copy(self.context.message)
            new_message.guild = None
            new_ctx = await self.context.bot.get_context(new_message)
            dm_only = {f"`{com.qualified_name}`¹": com for com in non_passing if await can_run(com, new_ctx)}
            filtered_mapping.update(dm_only)
            if not filtered_mapping:
                await self.get_destination().send("No help information was found.")
                return
            for com_text, com in filtered_mapping.items():
                if com.qualified_name in self.context.bot.help:
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
            end = "1 = In DMs only.\n" if any("¹" in elem for cat in categories.values() for elem in cat) else ""
            end += f"Use `{self.context.bot.get_bot_prefix()}help <COMMAND>` for more info on individual commands."
            paginator.add_line(end)
            for page in paginator.pages:
                await self.get_destination().send(page)

        async def send_bot_help(self, mapping, /):
            """Function that triggers when help command is used without command."""
            full_mapping = []  # Command list.
            for com_mapping in mapping.values():
                full_mapping.extend(com_mapping)  # Add all cogs to list.
            full_mapping = {com for com in full_mapping if com.enabled and not com.hidden}
            await self._send_command_list(full_mapping)

        async def send_command_help(self, command_object: Command[Any, ..., Any], /):
            """Function that triggers when help command is used with a command."""
            while command_object.qualified_name not in self.context.bot.help and len(command_object.parents):
                command_object = command_object.parents[0]  # Get parent in case it has help text.
            await self._send_help_entry(command_object)

        async def send_cog_help(self, cog: Cog, /):
            """Function that triggers when help command is used with a cog."""
            full_mapping = {com for com in cog.get_commands() if com.enabled and not com.hidden}
            await self._send_command_list(full_mapping)

        async def send_group_help(self, group: Group[Any, ..., Any], /):
            """Function that triggers when help command is used with a group."""
            while group.qualified_name not in self.context.bot.help and len(group.parents):
                group = group.parents[0]  # Get parent in case it has help text.
            await self._send_help_entry(group)

        def subcommand_not_found(self, command: Command[Any, ..., Any], string: str, /):
            """Function that returns content of error when subcommand invalid."""
            return f"The `{command.qualified_name}` command has no subcommand called `{string}`."

        def command_not_found(self, string: str, /):
            """Function that returns content of error when command not found."""
            return f"No command called `{string}` found."

    def __init__(self, database_credentials: DatabaseCredentials, *args, **kwargs):
        """Initialization function loading all necessary information for TravusBotBase class."""
        super().__init__(*args, **kwargs)
        self.log: logging.Logger = BOT_LOG
        self.last_module_error: str | None = None
        self.last_error: str | None = None
        self.extension_ctx: Context | None = None
        self.help: dict[str, TravusBotBase._HelpInfo] = {}
        self.modules: dict[str, TravusBotBase._ModuleInfo] = {}
        self.is_connected: int = 0
        self.help_command = self._CustomHelp()
        self.config: dict[str, str] = {}
        self._db_creds = database_credentials
        self.prefix: str | None = None
        self.delete_messages: int = 1
        self.ephemeral: bool = True
        self.core_commands_mode: str = "slash"
        self._core_slash_commands: list[app_commands.Command | app_commands.Group] = []
        self._core_prefix_commands: list[Command | commands.Group] = []
        self.send_long_text: Callable[[Context, str], Coroutine[Any, Any, None]] = send_long_text

    async def get_context(
        self, origin: Message | Interaction, /, *, cls: type[_ContextT] | None = None
    ) -> TBBContext | _ContextT:
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
                await conn.execute("INSERT INTO settings VALUES ('ephemeral', '1') ON CONFLICT (key) DO NOTHING")
                await conn.execute(
                    "INSERT INTO settings VALUES ('core_commands_mode', 'slash') ON CONFLICT (key) DO NOTHING"
                )
            loaded_prefix = await self.db.fetchval("SELECT value FROM settings WHERE key = 'prefix'")
            delete_msgs = await conn.fetchval("SELECT value FROM settings WHERE key = 'delete_messages'")
            ephemeral = await conn.fetchval("SELECT value FROM settings WHERE key = 'ephemeral'")
            core_mode = await conn.fetchval("SELECT value FROM settings WHERE key = 'core_commands_mode'")
            config = await conn.fetch("SELECT key, value FROM config")

        self.prefix = loaded_prefix or None
        self.delete_messages = int(delete_msgs) if delete_msgs is not None else 1
        self.ephemeral = bool(int(ephemeral)) if ephemeral is not None else True
        self.core_commands_mode = core_mode if core_mode in ("slash", "prefix", "both") else "slash"
        self.add_command_help(
            next(com for com in self.commands if com.name == "help"), "Core", None, ["", "about", "help"]
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

        async def load_module(default_list: list[str], module: str, propagate=False) -> bool:
            """Attempt to load a module, and recursively attempts to load dependencies."""
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
                if isinstance(e.original, DependencyError) and all(
                    load_module(default_list, dependency) for dependency in e.original.missing_dependencies
                ):
                    try:
                        default_list.append(module)
                        if load_module(default_list, module, True):
                            return True
                    except Exception as ee:
                        e = ee
                self.log.error(f"Default module '{module}' encountered and error.\n\n{e!s}")
                self.last_module_error = f"The `{module}` module failed while loading. The error was:\n\n{e!s}"
                return False
            except Exception as e:  # If en error was encountered while loading default module, roll back.
                self.help = old_help
                self.modules = old_modules
                if propagate:
                    raise
                if isinstance(e, commands.ExtensionNotFound):  # If import error, clarify further.
                    e = e.__cause__
                self.log.error(f"Default module '{module}' encountered and error.\n\n{e!s}")
                self.last_module_error = f"The `{module}` module failed while loading. The error was:\n\n{e!s}"
                return False
            self.log.info(f"Default module '{module}' loaded.")
            return True

        async with self.db.acquire() as conn:
            default_modules = await conn.fetch("SELECT module FROM default_modules")
        default_modules = [mod["module"] for mod in default_modules]
        await self.wait_until_ready()  # Wait until object cashing is done.

        for mod in list(default_modules):
            await load_module(default_modules, mod)
        await self.update_command_states()  # Make sure commands are in the right state. (hidden, disabled)
        await self._apply_core_commands_mode(sync=False)  # Enforce mode before syncing.
        await self.tree.sync()  # Sync tree after loading default modules (picks up module slash commands).

    async def setup_hook(self):
        """Called after the bot is logged in but before connecting to the gateway. Loads DB options and commands."""
        self.tree.on_error = self._on_app_command_error
        await self._load_db_options()
        await self._load_default_commands()
        self.loop.create_task(self._load_default_modules())  # Runs after bot is ready (waits internally).

    async def start(self, token: str, *, reconnect: bool = True):
        """Connect to the database and start the bot."""
        try:
            async with asyncpg.create_pool(
                user=self._db_creds.user,
                password=self._db_creds.password,
                host=self._db_creds.host,
                port=self._db_creds.port,
                database=self._db_creds.database,
            ) as pool:
                self.db = pool
                await super().start(token, reconnect=reconnect)
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
        assert self.user is not None
        return f"{self.user.mention} "

    async def send_response(self, interaction: Interaction, content: str = "", **kwargs) -> None:
        """Send a response to an interaction, respecting the ephemeral setting. Uses followup if already responded."""
        if "ephemeral" not in kwargs:
            kwargs["ephemeral"] = self.ephemeral
        if interaction.response.is_done():
            await interaction.followup.send(content, **kwargs)
        else:
            await interaction.response.send_message(content, **kwargs)

    async def _apply_core_commands_mode(self, sync: bool = True):
        """Register/unregister core slash and prefix commands based on core_commands_mode setting."""
        # Slash commands: add or remove from tree
        for cmd in self._core_slash_commands:
            if self.core_commands_mode in ("slash", "both"):
                if self.tree.get_command(cmd.name) is None:
                    self.tree.add_command(cmd)
            else:
                if self.tree.get_command(cmd.name) is not None:
                    self.tree.remove_command(cmd.name)
        # Prefix commands: enable or disable (help is excluded — always both)
        for cmd in self._core_prefix_commands:
            if cmd.name == "help":
                continue
            cmd.enabled = self.core_commands_mode in ("prefix", "both")
        if sync:
            await self.tree.sync()

    def check_dependencies(self, dependencies: list[str]):
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
        usage: Callable[[], str | Embed] | None = None,
        description: str | None = None,
        additional_credits: str | None = None,
        image_link: str | discord.Asset | None = None,
    ):
        """Function that is used to add module info to the bot correctly. Used to minimize developmental errors."""
        info = self._ModuleInfo(self.get_bot_prefix, name, author, usage, description, additional_credits, image_link)
        if name.lower() not in self.modules:
            self.modules[name.lower()] = info
        else:
            raise RuntimeError(f"A module with the name '{name}' already exists.")

    def remove_module(self, name: str):
        """Function that is used to remove module info to the bot correctly. Used to minimize developmental errors."""
        if name.lower() in self.modules:
            del self.modules[name.lower()]

    def add_commands(self, command_list: list[Command]):
        """Adds multiple commands at once using bot.add_command."""
        for com in command_list:
            self.add_command(com)

    def remove_commands(self, command_list: list[Command | str]):
        """Removed multiple commands at once using bot.remove_command. Accepts command names or commands."""
        for com in command_list:
            self.remove_command(com.name if isinstance(com, Command) else com)

    async def update_command_states(self):
        """Function that get command state (hidden, disabled) for every command currently loaded."""
        async with self.db.acquire() as conn, conn.transaction():
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
        command: Command | Group | app_commands.Command | app_commands.Group,
        category: str = "no category",
        restrictions: dict[str, list[str] | str] | None = None,
        examples: list[str] | None = None,
    ):
        """Function that is used to add help info to the bot correctly. Used to minimize developmental errors. Command
        should be either a prefix command, prefix command group, app command, or app command group."""
        self.help[command.qualified_name] = self._HelpInfo(
            self.get_bot_prefix, command, category, restrictions, examples
        )

    def remove_command_help(self, command: Command | type[Cog] | str | list[Command | str]):
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
        elif issubclass(command.__class__, Cog) and not isinstance(command, str):
            for com in command(self).walk_commands():
                if com.qualified_name in self.help:
                    del self.help[com.qualified_name]
        elif isinstance(command, str) and command in self.help:
            del self.help[command]

    async def update_status(
        self,
        text: str | None = None,
        activity_type: discord.ActivityType = discord.ActivityType.listening,
    ):
        """Update bot presence/status. If no text is given, defaults to showing the current prefix/help info
        based on core commands mode. If text is given, it is used as-is with the given activity type."""
        if text is None:
            if self.core_commands_mode == "slash":
                text = "/help"
            elif self.core_commands_mode == "both":
                text = f"prefix: {self.prefix} | /help" if self.prefix else "/help"
            else:
                text = f"prefix: {self.prefix}" if self.prefix else "pings only"
        activity = discord.Activity(type=activity_type, name=text)
        await self.change_presence(activity=activity)

    async def on_ready(self):
        """This function runs every time the bot connects to Discord. This happens multiple times.
        Sets about command and bot status. These require the bot to be online and hence are in here."""
        assert self.user is not None
        if self.user.name.lower() not in self.modules:
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
        await self.update_status()
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
        if ctx.interaction is not None:  # Don't delete interaction-triggered messages.
            return
        if self.delete_messages and ctx.guild:  # If the message is in a server and the delete messages flag is true.
            try:  # Try to delete message.
                await ctx.message.delete()
            except Forbidden:  # Log to console if missing permission to delete message.
                self.log.warning("Bot does not have required permissions to delete message.")

    async def on_command_error(self, ctx: Context, error: commands.CommandError, /):
        """Global error handler for miscellaneous errors."""
        if isinstance(
            error,
            (commands.NoPrivateMessage, commands.CommandOnCooldown, commands.DisabledCommand, commands.CheckFailure),
        ):
            pass
        elif isinstance(error, commands.UserInputError):  # Send correct syntax based on command usage variable.
            if ctx.command is not None and ctx.command.usage:
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
                f"{ctx.author.id}: Command '{ctx.command}' requires role: "
                f"{' or '.join(str(r) for r in error.missing_roles)}"
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

    async def _on_app_command_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        """Global error handler for app command errors. Assigned to tree.on_error in setup_hook."""
        command_name = interaction.command.qualified_name if interaction.command else "unknown"
        if isinstance(error, (app_commands.CommandOnCooldown, app_commands.NoPrivateMessage)):
            pass
        elif isinstance(error, app_commands.MissingPermissions):
            self.log.warning(
                f"{interaction.user.id}: Command '/{command_name}' requires additional permissions: "
                f"{', '.join(error.missing_permissions)}"
            )
        elif isinstance(error, app_commands.CheckFailure):
            pass
        elif isinstance(error.__cause__, Forbidden):
            self.log.warning(f"{interaction.user.id}: Missing permissions.")
        elif error is not None:
            self.log.warning(f"{interaction.user.id}: /{command_name}: {error}")
        self.last_error = f"[{cur_time()}] {interaction.user.id}: /{command_name}: {error}"


def parse_time(
    duration: str, minimum: int | None = None, maximum: int | None = None, error_on_exceeded: bool = True
) -> int:
    """Function that parses time in a NhNmNs format. Supports weeks, days, hours, minutes and seconds, positive and
    negative amounts and max values. Minimum and maximum values can be set (in seconds), and whether an error should
    occur or the max / min value should be used when these are exceeded."""
    last, t_total = 0, 0
    t_frames = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}
    for index, char in enumerate(duration):  # For every character in time string.
        if char.lower() in t_frames:
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


async def send_in_global_channel(ctx: Context, channel: GlobalTextChannel | None, msg: str, other_dms: bool = False):
    """Sends a message in any text channel across servers and DMs. Has flag to allow sending to foreign DMs."""
    user = ctx.author
    try:
        if isinstance(channel, DMChannel):
            if channel.recipient and channel.recipient.id != user.id and not other_dms:
                await ctx.send("Sending messages to another user's DMs is forbidden.")
            else:
                await channel.send(msg)
        elif channel is None:
            await ctx.channel.send(msg)
        elif isinstance(channel, TextChannel) and isinstance(user, Member):
            if channel.permissions_for(user).send_messages:
                await channel.send(msg)
            else:
                await ctx.send("You do not have permission to send messages in this channel.")
        elif isinstance(channel, Thread) and isinstance(user, Member):
            if not channel.permissions_for(user).send_messages_in_threads or channel.locked or channel.archived:
                await ctx.send("You do not have permission to send messages in this thread.")
            elif channel.is_private():
                if user not in await channel.fetch_members() and not channel.permissions_for(user).manage_threads:
                    await ctx.send("You do not have permission to send messages in this private thread.")
            else:
                await channel.send(msg)
        else:
            await ctx.send("You do not have permission to send messages in this channel.")
    except Forbidden:
        await ctx.send("Cannot send messages in given channel.")


async def send_long_text(ctx: Context, text: str) -> None:
    """Send text as a code block if short enough, otherwise upload as a .txt file."""
    if len(text) <= 1950:
        await ctx.send(f"```py\n{text}\n```")
    else:
        file = discord.File(io.BytesIO(text.encode()), filename="output.txt")
        await ctx.send("Output too long, uploaded as file.", file=file)


async def can_run(command: Command, ctx: Context) -> bool:
    """This function uses command.can_run to see if a command can be run by a user, but does not raise exceptions."""
    try:
        await command.can_run(ctx)
    except commands.CommandError:
        return False
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
    guild: discord.Guild | None,
    text: str,
    escape_markdown: bool = True,
    replace_backticks: bool = False,
) -> str:
    """Underlying function used by clean and clean_no_ctx functions."""
    transformations: dict[str, str] = {}

    def resolve_member(_id):
        """Resolves user mentions."""
        member = bot.get_user(_id)
        return "@" + member.name if member else "@deleted-user"

    transformations.update(
        (f"<@{member_id}>", resolve_member(member_id)) for member_id in [int(x) for x in findall(r"<@!?(\d+)>", text)]
    )
    transformations.update(
        (f"<@!{member_id}>", resolve_member(member_id)) for member_id in [int(x) for x in findall(r"<@!?(\d+)>", text)]
    )

    if guild:

        def resolve_channel(_id):
            """Resolves channel mentions."""
            ch = guild.get_channel(_id)
            return f"<#{_id}>", ("#" + ch.name if ch else "#deleted-channel")

        def resolve_role(_id):
            """Resolves role mentions."""
            role = guild.get_role(_id)
            return "@" + role.name if role else "@deleted-role"

        transformations.update(resolve_channel(channel) for channel in [int(x) for x in findall(r"<#(\d+)>", text)])
        transformations.update(
            (f"<@&{role_id}>", resolve_role(role_id)) for role_id in [int(x) for x in findall(r"<@&(\d+)>", text)]
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
    guild: discord.Guild | None,
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

    regex = re_cmp(r"(\b|<)https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_+.~#?&\\/=]*)>?")
    text = regex.sub(repl, text)
    return text


BOT_LOG = logging.getLogger("bot")
BOT_LOG.setLevel(logging.INFO)
