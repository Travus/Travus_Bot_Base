# pylint: disable=too-many-lines
import logging
from asyncio import sleep as asleep  # For waiting asynchronously.
from os import listdir  # To check files on disk.

import discord
from asyncpg import IntegrityConstraintViolationError  # To check for database conflicts.
from discord import Embed, Interaction, app_commands
from discord.ext import commands  # For implementation of bot commands.

import travus_bot_base as tbb  # TBB functions and classes.
from travus_bot_base import clean  # Shorthand for cleaning output.


async def setup(bot: tbb.TravusBotBase):
    """Setup function ran when module is loaded."""
    cog = CoreFunctionalityCog(bot)
    await bot.add_cog(cog)  # Add cog and command help info.
    # Core commands with slash versions managed by _apply_core_commands_mode.
    # pylint: disable-next=protected-access
    bot._core_slash_commands.extend(
        [cog.slash_about, cog.slash_usage, cog.slash_module, cog.slash_default, cog.slash_config, cog.slash_command]
    )
    # pylint: disable-next=protected-access
    bot._core_prefix_commands.extend([cog.about, cog.usage, cog.module, cog.default, cog.config, cog.command])
    bot.add_command_help(CoreFunctionalityCog.module_list, "Core", {"perms": ["Administrator"]}, [""])
    bot.add_command_help(CoreFunctionalityCog.module_load, "Core", {"perms": ["Administrator"]}, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.module_unload, "Core", {"perms": ["Administrator"]}, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.module_reload, "Core", {"perms": ["Administrator"]}, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.module_lasterror, "Core", {"perms": ["Administrator"]}, [""])
    bot.add_command_help(CoreFunctionalityCog.slash_module_list, "Core", {"perms": ["Administrator"]}, [""])
    bot.add_command_help(
        CoreFunctionalityCog.slash_module_load, "Core", {"perms": ["Administrator"]}, ["fun", "economy"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.slash_module_unload, "Core", {"perms": ["Administrator"]}, ["fun", "economy"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.slash_module_reload, "Core", {"perms": ["Administrator"]}, ["fun", "economy"]
    )
    bot.add_command_help(CoreFunctionalityCog.slash_module_lasterror, "Core", {"perms": ["Administrator"]}, [""])
    bot.add_command_help(CoreFunctionalityCog.default, "Core", None, ["list", "add", "remove"])
    bot.add_command_help(CoreFunctionalityCog.default_list, "Core", None, [""])
    bot.add_command_help(CoreFunctionalityCog.default_add, "Core", None, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.default_remove, "Core", None, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.slash_default_list, "Core", {"perms": ["Administrator"]}, [""])
    bot.add_command_help(
        CoreFunctionalityCog.slash_default_add, "Core", {"perms": ["Administrator"]}, ["fun", "economy"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.slash_default_remove, "Core", {"perms": ["Administrator"]}, ["fun", "economy"]
    )
    bot.add_command_help(CoreFunctionalityCog.command_enable, "Core", {"perms": ["Administrator"]}, ["balance", "pay"])
    bot.add_command_help(CoreFunctionalityCog.command_disable, "Core", {"perms": ["Administrator"]}, ["balance", "pay"])
    bot.add_command_help(CoreFunctionalityCog.command_show, "Core", {"perms": ["Administrator"]}, ["module", "balance"])
    bot.add_command_help(CoreFunctionalityCog.command_hide, "Core", {"perms": ["Administrator"]}, ["module", "balance"])
    bot.add_command_help(
        CoreFunctionalityCog.slash_command_enable, "Core", {"perms": ["Administrator"]}, ["balance", "pay"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.slash_command_disable, "Core", {"perms": ["Administrator"]}, ["balance", "pay"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.slash_command_show, "Core", {"perms": ["Administrator"]}, ["module", "balance"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.slash_command_hide, "Core", {"perms": ["Administrator"]}, ["module", "balance"]
    )
    bot.add_command_help(CoreFunctionalityCog.about, "Core", None, ["", "fun"])
    bot.add_command_help(CoreFunctionalityCog.slash_about, "Core", None, ["", "dev"])
    bot.add_command_help(CoreFunctionalityCog.usage, "Core", None, ["", "dev"])
    bot.add_command_help(CoreFunctionalityCog.slash_usage, "Core", None, ["", "dev"])
    bot.add_command_help(CoreFunctionalityCog.config, "Core", {"perms": ["Administrator"]}, ["get", "set", "unset"])
    bot.add_command_help(CoreFunctionalityCog.config_get, "Core", {"perms": ["Administrator"]}, ["", "alert_channel"])
    bot.add_command_help(CoreFunctionalityCog.config_unset, "Core", {"perms": ["Administrator"]}, ["alert_channel"])
    bot.add_command_help(
        CoreFunctionalityCog.slash_config_get, "Core", {"perms": ["Administrator"]}, ["", "alert_channel"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.slash_config_set,
        "Core",
        {"perms": ["Administrator"]},
        ["alert_channel 353246496952418305"],
    )
    bot.add_command_help(
        CoreFunctionalityCog.slash_config_unset, "Core", {"perms": ["Administrator"]}, ["alert_channel"]
    )
    bot.add_command_help(CoreFunctionalityCog.shutdown, "Core", None, ["", "1h", "1h30m", "10m-30s", "2m30s"])
    bot.add_command_help(CoreFunctionalityCog.botconfig_prefix, "Core", None, ["$", "bot!", "bot ?", "remove"])
    bot.add_command_help(CoreFunctionalityCog.botconfig_deletemessages, "Core", None, ["enable", "y", "disable", "n"])
    bot.add_command_help(CoreFunctionalityCog.botconfig_ephemeral, "Core", None, ["enable", "y", "disable", "n"])
    bot.add_command_help(CoreFunctionalityCog.botconfig_core_commands, "Core", None, ["slash", "prefix", "both"])
    bot.add_command_help(
        CoreFunctionalityCog.botconfig,
        "Core",
        None,
        ["prefix", "deletemessages", "description", "credits", "ephemeral", "core-commands"],
    )
    bot.add_command_help(
        CoreFunctionalityCog.botconfig_description, "Core", None, ["remove", "This is a sample description."]
    )
    bot.add_command_help(
        CoreFunctionalityCog.module, "Core", {"perms": ["Administrator"]}, ["list", "load", "unload", "reload"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.command, "Core", {"perms": ["Administrator"]}, ["enable", "disable", "show", "hide"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.config_set, "Core", {"perms": ["Administrator"]}, ["alert_channel 353246496952418305"]
    )
    bot.add_command_help(
        CoreFunctionalityCog.botconfig_credits,
        "Core",
        None,
        ["remove", "`\n```\n[Person](URL):\n\tBot Profile Image\n``"],
    )


async def teardown(bot: tbb.TravusBotBase):
    """Teardown function ran when module is unloaded."""
    core_cmd_names = ["about", "usage", "module", "default", "config", "command"]
    # pylint: disable-next=protected-access
    bot._core_slash_commands = [com for com in bot._core_slash_commands if com.name not in core_cmd_names]
    # pylint: disable-next=protected-access
    bot._core_prefix_commands = [com for com in bot._core_prefix_commands if com.name not in core_cmd_names]
    await bot.remove_cog("CoreFunctionalityCog")  # Remove cog and command help info.
    bot.remove_command_help(CoreFunctionalityCog)


class CoreFunctionalityCog(commands.Cog):
    """Cog that holds default functionality."""

    def __init__(self, bot: tbb.TravusBotBase):
        """Initialization function loading bot object for cog."""
        self.bot = bot
        self.log = logging.getLogger("core_commands")
        self.log.setLevel(logging.INFO)

    async def _module_operation(  # pylint: disable=too-many-statements,too-many-branches
        self, invoker: commands.Context | Interaction, operation: str, mod: str
    ):
        """To avoid code duplication in the except blocks all module command functionality is grouped together."""

        # Abstract over prefix Context vs slash Interaction.
        if isinstance(invoker, commands.Context):

            async def send(content="", **kwargs):
                await invoker.send(content, **kwargs)

            user_id = invoker.author.id
        else:

            async def send(content="", **kwargs):
                await self.bot.send_response(invoker, content, **kwargs)

            user_id = invoker.user.id

        def clean_text(text: str, escape_md: bool = True, replace_bt: bool = False) -> str:
            return tbb.clean_no_ctx(self.bot, invoker.guild, text, escape_md, replace_bt)

        async def load() -> str:
            """Contains the logic for loading a module."""
            if f"{mod}.py" in listdir("modules"):
                await self.bot.load_extension(f"modules.{mod}")
                await self.bot.update_command_states()
                self.log.info(f"{user_id}: loaded '{mod}' module.")
                return f"Module `{mod_name}` successfully loaded."
            return f"No `{mod_name}` module was found."

        async def unload() -> str:
            """Contains the logic for unloading a module."""
            await self.bot.unload_extension(f"modules.{mod}")
            self.log.info(f"{user_id}: unloaded '{mod}' module.")
            return f"Module `{mod_name}` successfully unloaded."

        async def reload() -> str:
            """Contains the logic for reloading a module."""
            if f"{mod}.py" in listdir("modules"):
                await self.bot.reload_extension(f"modules.{mod}")
                await self.bot.update_command_states()
                self.log.info(f"{user_id}: reloaded '{mod}' module.")
                return f"Module `{mod_name}` successfully reloaded."
            if mod in self.bot.modules:
                return f"The `{mod_name}` module file is no longer found on disk. Reload canceled."
            return f"No `{mod_name}` module was found."

        old_help = dict(self.bot.help)  # Save old help and module info in case we need to roll back.
        old_modules = dict(self.bot.modules)
        old_tree_commands = self.bot.tree.get_commands()  # Save tree state for sync rollback.
        self.bot.extension_ctx = invoker  # Save context/interaction in case loaded module has use for it.
        mod_name = clean_text(mod, False, True)
        result = ""
        try:
            if operation == "load":
                result = await load()
            elif operation == "unload":
                result = await unload()
            elif operation == "reload":
                result = await reload()
        except commands.ExtensionAlreadyLoaded:  # If module was already loaded.
            await send(f"The `{mod_name}` module was already loaded.")
        except commands.ExtensionNotLoaded:  # If module wasn't loaded to begin with.
            await send(f"No `{mod_name}` module is loaded.")
        except commands.ExtensionFailed as e:
            self.bot.help = old_help
            self.bot.modules = old_modules
            if isinstance(e.original, tbb.DependencyError):
                missing_deps = [f"`{clean_text(elem, False, True)}`" for elem in e.original.missing_dependencies]
                await send(f"Module `{mod_name}` requires these missing dependencies: {', '.join(missing_deps)}")
            else:
                await send(
                    "**Error! Something went really wrong! Contact module maintainer.**\nError logged to console and "
                    "stored in module error command."
                )
            self.log.error(f"{user_id}: tried loading '{mod}' module, and it failed:\n\n{e}")
            self.bot.last_module_error = (
                f"The `{clean_text(mod, False)}` module failed while loading. The error was:\n\n{clean_text(str(e))}"
            )
        except Exception as e:
            self.bot.help = old_help
            self.bot.modules = old_modules
            await send(
                "**Error! Something went really wrong! Contact module maintainer.**\nError logged to console and "
                "stored in module error command."
            )
            if isinstance(e, commands.ExtensionNotFound):  # Clarify error further in case it was an import error.
                e = e.__cause__
            self.log.error(f"{user_id}: tried loading '{mod}' module, and it failed:\n\n{e!s}")
            self.bot.last_module_error = (
                f"The `{clean_text(mod, False)}` module failed while loading. The error was:\n\n{clean_text(str(e))}"
            )
        else:
            try:
                await self.bot._apply_core_commands_mode(sync=False)  # pylint: disable=protected-access
                if {id(com) for com in self.bot.tree.get_commands()} != {id(com) for com in old_tree_commands}:
                    await send(f"{result}\nSyncing slash command tree, this may take a moment...")
                    await self.bot.tree.sync()
                    await send("Slash command tree synced.")
                else:
                    await send(result)
            except Exception as sync_error:  # Sync failed — rollback local state.
                self.bot.help = old_help
                self.bot.modules = old_modules
                self.bot.tree.clear_commands(guild=None)
                for cmd in old_tree_commands:
                    self.bot.tree.add_command(cmd)
                error_msg = f"Tree sync failed after {operation} of '{mod}': {sync_error}"
                self.log.error(error_msg)
                self.bot.last_module_error = error_msg
                await send(
                    "Module operation succeeded but slash command sync failed. Changes have been rolled back.\n"
                    "Error stored in module lasterror command."
                )
        finally:  # Reset context as loading has concluded.
            self.bot.extension_ctx = None

    @commands.is_owner()
    @commands.group(
        invoke_without_command=True,
        name="botconfig",
        usage="<prefix/deletemessages/description/credits/ephemeral/core-commands>",
    )
    async def botconfig(self, ctx: commands.Context):
        """This command sets the bot's prefix, command trigger deletion behaviour, description, additional credits
        section, ephemeral response behaviour, and core command mode. For more information, check the help entry of one
        of these subcommands; `prefix`, `deletemessages`, `description`, `credits`, `ephemeral`, `core-commands`."""
        assert ctx.command is not None
        raise commands.BadArgument(f"No subcommand given for {ctx.command.name}.")

    @commands.is_owner()
    @botconfig.command(name="prefix", usage="<NEW PREFIX/remove>")
    async def botconfig_prefix(self, ctx: commands.Context, *, new_prefix: str):
        """This command changes the bot prefix. The default prefix is `!`. Prefixes can be everything from symbols to
        words or a combination of the two, and can even include spaces, though they cannot start or end with spaces
        since Discord removes empty space at the start and end of messages. The prefix is saved across reboots. Setting
        the prefix to `remove` will remove the prefix. The bot will always listen to pings as if they were a prefix,
        regardless of if there is another prefix set or not. Maximum prefix length is 20."""
        if len(new_prefix) > 20:
            await ctx.send("The maximum prefix length is 20.")
            return
        self.bot.prefix = new_prefix if new_prefix.lower() != "remove" else None  # If 'remove', prefix is set to None.
        await self.bot.update_status()
        async with self.bot.db.acquire() as conn:
            await conn.execute(
                "UPDATE settings SET value = $1 WHERE key = 'prefix'",
                new_prefix if new_prefix.lower() != "remove" else "",
            )  # Empty string is no prefix.
        if new_prefix.lower() != "remove":  # Give feedback to user.
            await ctx.send(f"The bot prefix has successfully been changed to `{new_prefix}`.")
        else:
            await ctx.send("The bot is now only listens to pings.")

    @commands.is_owner()
    @botconfig.command(
        name="deletemessages",
        aliases=["deletemsgs", "deletecommands", "deletecmds", "delmessages", "delmsgs", "delcommands", "delcmds"],
        usage="<enable/disable>",
    )
    async def botconfig_deletemessages(self, ctx: commands.Context, operation: str):
        """This command sets the behaviour for deletion of command triggers. If this is enabled then messages that
        trigger commands will be deleted. Is this is disabled then the bot will not delete messages that trigger
        commands. Per default this is enabled. This setting is saved across restarts."""
        op = operation.lower()
        async with self.bot.db.acquire() as conn:
            if op in ["enable", "true", "on", "yes", "y", "+", "1"]:  # Values interpreted as true.
                if self.bot.delete_messages:
                    await ctx.send("The bot is already deleting command triggers.")
                    return
                await conn.execute("UPDATE settings SET value = '1' WHERE key = 'delete_messages'")
                self.bot.delete_messages = 1
                await ctx.send("Now deleting command triggers.")
            elif op in ["disable", "false", "off", "no", "n", "-", "0"]:  # Values interpreted as false.
                if not self.bot.delete_messages:
                    await ctx.send("The bot is already not deleting command triggers.")
                    return
                await conn.execute("UPDATE settings SET value = '0' WHERE key = 'delete_messages'")
                self.bot.delete_messages = 0
                await ctx.send("No longer deleting command triggers.")
            else:
                raise commands.BadArgument("Operation not supported.")

    @commands.is_owner()
    @botconfig.command(
        name="ephemeral",
        usage="<enable/disable>",
    )
    async def botconfig_ephemeral(self, ctx: commands.Context, operation: str):
        """This command sets whether core slash command responses are ephemeral (only visible to the user who ran the
        command). If enabled, slash command responses will be ephemeral by default. If disabled, responses will be
        visible to everyone. Per default this is enabled. This setting is saved across restarts. Module authors can
        choose to respect this setting for their own slash commands."""
        async with self.bot.db.acquire() as conn:
            if operation.lower() in ["enable", "true", "on", "yes", "y", "+", "1"]:
                if self.bot.ephemeral:
                    await ctx.send("Ephemeral responses are already enabled.")
                    return
                await conn.execute("UPDATE settings SET value = '1' WHERE key = 'ephemeral'")
                self.bot.ephemeral = True
                await ctx.send("Slash command responses are now ephemeral.")
            elif operation.lower() in ["disable", "false", "off", "no", "n", "-", "0"]:
                if not self.bot.ephemeral:
                    await ctx.send("Ephemeral responses are already disabled.")
                    return
                await conn.execute("UPDATE settings SET value = '0' WHERE key = 'ephemeral'")
                self.bot.ephemeral = False
                await ctx.send("Slash command responses are now visible to everyone.")
            else:
                raise commands.BadArgument("Operation not supported.")

    @commands.is_owner()
    @botconfig.command(name="core-commands", aliases=["corecommands", "corecmds"], usage="<slash/prefix/both>")
    async def botconfig_core_commands(self, ctx: commands.Context, mode: str):
        """This command sets whether core commands are registered as slash commands, prefix commands, or both. The
        default is `slash`. The `help` command always exists as both slash and prefix regardless of this setting.
        The `botconfig` command is always prefix-only. This setting is saved across restarts."""
        mode = mode.lower()
        if mode not in ("slash", "prefix", "both"):
            raise commands.BadArgument("Mode must be `slash`, `prefix`, or `both`.")
        if mode == self.bot.core_commands_mode:
            await ctx.send(f"Core commands mode is already set to `{mode}`.")
            return
        self.bot.core_commands_mode = mode
        async with self.bot.db.acquire() as conn:
            await conn.execute("UPDATE settings SET value = $1 WHERE key = 'core_commands_mode'", mode)
        await ctx.send(f"Core commands mode set to `{mode}`.\nSyncing slash command tree, this may take a moment...")
        await self.bot._apply_core_commands_mode()  # pylint: disable=protected-access
        await self.bot.update_status()
        await ctx.send("Slash command tree synced.")

    @commands.is_owner()
    @botconfig.command(name="description", aliases=["desc"], usage="<DESCRIPTION/remove>")
    async def botconfig_description(self, ctx: commands.Context, *, description: str):
        """This command sets the bot description that is used by the about command. The description can technically be
        up to 4096 characters long, keep however in mind that Discord messages have a maximum length of 4000 characters
        (2000 without Nitro). If `remove` is sent along then the description will be removed. The special keyword
        `_prefix_` wil be replaced by the current bot prefix."""
        assert self.bot.user is not None
        async with self.bot.db.acquire() as conn:
            if description.lower() == "remove":
                await conn.execute("UPDATE settings SET value = '' WHERE key = 'bot_description'")
                self.bot.modules[self.bot.user.name.lower()].description = (
                    "No description for the bot found. Set description with `botconfig` command."
                )
                await ctx.send("The description has been removed.")
            else:
                await conn.execute("UPDATE settings SET value = $1 WHERE key = 'bot_description'", description)
                self.bot.modules[self.bot.user.name.lower()].description = description
                await ctx.send("The description has been set.")

    @commands.is_owner()
    @botconfig.command(name="credits", usage="<CREDITS/remove>   *OBS: See help command entry!*")
    async def botconfig_credits(self, ctx: commands.Context, *, description: str):
        """This command sets the additional credits section of the about command. The additional credits section can be
        at most 1024 characters long, and supports both new lines, indents and embedded links. Indents of 5 spaces are
        recommended. Embedded links should look like so; `[displayed text](URL)`. The credits should be passed inside a
        multi-line code block in order for new lines and tabs to work correctly. If `remove` is passed instead then the
        additional credits section is removed."""
        assert self.bot.user is not None
        description = description.strip()
        async with self.bot.db.acquire() as conn:
            if description.lower() == "remove":
                await conn.execute("UPDATE settings SET value = '' WHERE key = 'additional_credits'")
                self.bot.modules[self.bot.user.name.lower()].credits = None
                await ctx.send("The additional credits section has been removed.")
                return
            if description.count("```") != 2 or description[:3] != "```" or description[-3:] != "```":
                await ctx.send("Credits must be fully encased in a multi-line code block.")
                return
            description = description.removeprefix("```").removesuffix("```").strip()  # Remove code block.
            description = description.replace(" ", "\u202f")  # Prevent whitespace from disappearing.
            if len(description) > 1024:
                await ctx.send("Credits too long. Credits can be at most 1024 characters long.")
                return
            await conn.execute("UPDATE settings SET value = $1 WHERE key = 'additional_credits'", description)
            self.bot.modules[self.bot.user.name.lower()].credits = description
            await ctx.send("The additional credits section has been set.")

    @commands.has_permissions(administrator=True)
    @commands.group(
        invoke_without_command=True, name="module", aliases=["modules"], usage="<list/load/unload/reload/lasterror>"
    )
    async def module(self, ctx: commands.Context):
        """This command can load, unload, reload and list available modules. It can also show any errors that occur
        during the loading process. Modules contain added functionality, such as commands. The intended purpose for
        modules is to extend the bot's functionality in semi-independent packages so that parts of the bot's
        functionality can be removed or restarted without affecting the rest of the bot's functionality. See the help
        text for the subcommands for more info."""
        assert ctx.command is not None
        raise commands.BadArgument(f"No subcommand given for {ctx.command.name}.")

    @commands.has_permissions(administrator=True)
    @module.command(name="list")
    async def module_list(self, ctx: commands.Context):
        """This command lists all currently loaded and available modules. For the bot to find new modules they need to
        be placed inside the modules folder inside the bot directory. Modules listed by this command can be loaded,
        unloaded and reloaded by the respective commands for this. See help text for `module load`, `module unload`
        and `module reload` for more info on this."""
        loaded_modules = [
            f"`{clean(ctx, mod.replace('modules.', ''), False, True)}`, "
            for mod in self.bot.extensions
            if mod != "core_commands"
        ] or ["None, "]
        available_modules = [
            f"`{clean(ctx, mod, False, True).replace('.py', '')}`, "
            for mod in listdir("modules")
            if mod.endswith(".py")
        ]
        available_modules = [mod for mod in available_modules if mod not in loaded_modules] or ["None, "]
        loaded_modules[-1] = loaded_modules[-1][:-2]
        available_modules[-1] = available_modules[-1][:-2]
        paginator = commands.Paginator(prefix="", suffix="", linesep="")
        paginator.add_line("Loaded modules: ")
        for mod in loaded_modules:
            paginator.add_line(mod)
        paginator.add_line("\nAvailable Modules: ")
        for mod in available_modules:
            paginator.add_line(mod)
        for page in paginator.pages:
            await ctx.send(page)

    @commands.has_permissions(administrator=True)
    @module.command(name="load", aliases=["l"], usage="<MODULE NAME>")
    async def module_load(self, ctx: commands.Context, *, mod: str):
        """This command loads modules. Modules should be located inside the module folder in the bot directory. The
        `module list` command can be used to show all modules available for loading. Once a module is loaded the
        functionality defined in the module file will be added to the bot. If an error is encountered during the
        loading process the user will be informed and the `module error` command can then be used to see the error
        details. The module will then not be loaded. If you want modules to stay loaded after restarts, see the
        `default` command."""
        await self._module_operation(ctx, "load", mod)

    @commands.has_permissions(administrator=True)
    @module.command(name="unload", aliases=["ul"], usage="<MODULE NAME>")
    async def module_unload(self, ctx: commands.Context, *, mod: str):
        """This command unloads modules. When a loaded module is unloaded its functionality will be removed. You can
        use the `module list` command to see all currently loaded modules. This will not prevent default modules from
        being loaded when the bot starts. See the `default` command for removing modules starting with the bot."""
        await self._module_operation(ctx, "unload", mod)

    @commands.has_permissions(administrator=True)
    @module.command(name="reload", aliases=["rl"], usage="<MODULE NAME>")
    async def module_reload(self, ctx: commands.Context, *, mod: str):
        """This command reloads a module that is currently loaded. This will unload and load the module in one command.
        If the module is no longer present or the loading process encounters an error the module will not be reloaded
        and the functionality from before the reload will be retained and the user informed, the `module error` command
        can then be used to see the error details. You can use the module list command to see all currently loaded
        modules."""
        await self._module_operation(ctx, "reload", mod)

    @commands.has_permissions(administrator=True)
    @module.command(name="lasterror", aliases=["error", "le"])
    async def module_lasterror(self, ctx: commands.Context):
        """This command will show the last error that was encountered during the module load or reloading process. This
        information will also be logged to the console when the error first is encountered. This command retains this
        information until another error replaces it, or the bot shuts down."""
        if self.bot.last_module_error:
            await ctx.send(self.bot.last_module_error[:1999])
        else:
            await ctx.send("There have not been any errors loading modules since the last restart.")

    @commands.is_owner()
    @commands.group(invoke_without_command=True, name="default", aliases=["defaults"], usage="<add/remove/list>")
    async def default(self, ctx: commands.Context):
        """This command is used to add, remove or list default modules. Modules contain added functionality, such as
        commands. Default modules are loaded automatically when the bot starts and as such any functionality in them
        will be available as soon as the bot is online. For more info see the help text of the subcommands."""
        assert ctx.command is not None
        raise commands.BadArgument(f"No subcommand given for {ctx.command.name}.")

    @commands.is_owner()
    @default.command(name="list")
    async def default_list(self, ctx: commands.Context):
        """This command lists all current default modules. For more information on modules see the help text for the
        `module` command. All modules in this list start as soon as the bot is launched. For a list of all available or
        loaded modules see the `module list` command."""
        async with self.bot.db.acquire() as conn:
            result = await conn.fetch("SELECT module FROM default_modules")
        result = [f"`{clean(ctx, val['module'], False, True)}`, " for val in result] or ["None, "]
        result[-1] = result[-1][:-2]
        paginator = commands.Paginator(prefix="", suffix="", linesep="")
        paginator.add_line("Default modules: ")
        for mod in result:
            paginator.add_line(mod)
        for page in paginator.pages:
            await ctx.send(page)

    @commands.is_owner()
    @default.command(name="add", usage="<MODULE NAME>")
    async def default_add(self, ctx: commands.Context, *, mod: str):
        """This command adds a module to the list of default modules. Modules in this list are loaded automatically
        once the bot starts. This command does not load modules if they are not already loaded until the bot is started
        the next time. For that, see the `module load` command. For a list of existing default modules, see the
        `default list` command. For more info on modules see the help text for the `module` command."""
        if f"{mod}.py" in listdir("modules"):  # Check if such a module even exists.
            try:
                async with self.bot.db.acquire() as conn:
                    await conn.execute("INSERT INTO default_modules VALUES ($1)", mod)
                    await ctx.send(f"The `{clean(ctx, mod, False, True)}` module is now a default module.")
            except IntegrityConstraintViolationError:
                await ctx.send(f"The `{clean(ctx, mod, False, True)}` module is already a default module.")
        else:
            await ctx.send(f"No `{clean(ctx, mod, False, True)}` module was found.")

    @commands.is_owner()
    @default.command(name="remove", usage="<MODULE NAME>")
    async def default_remove(self, ctx: commands.Context, *, mod: str):
        """This command removes a module from the list of default modules. Once removed from this list the module will
        no longer automatically be loaded when the bot starts. This command will not unload commands that are already
        loaded. For that, see the `module unload` command. For a list of existing default modules, see the
        `default list` command. For more info on modules see the help text for the `module` command."""
        async with self.bot.db.acquire() as conn:
            result = await conn.fetchval("SELECT module FROM default_modules WHERE module = $1", mod)
            if result:
                await conn.execute("DELETE FROM default_modules WHERE module = $1", mod)
                await ctx.send(f"Removed `{clean(ctx, mod, False, True)}` module from default modules.")
            else:
                await ctx.send(f"No `{clean(ctx, mod, False, True)}` module in default modules.")

    @commands.has_permissions(administrator=True)
    @commands.group(
        invoke_without_command=True, name="command", aliases=["commands"], usage="<enable/disable/show/hide>"
    )
    async def command(self, ctx: commands.Context):
        """This command disables, enables, hides and shows prefix commands. Hiding commands means they don't show up
        in the overall help command list. Disabling a command means it can't be used. Disabled commands also do not
        show up in the overall help command list and the specific help text for the command will not be viewable.
        Core commands cannot be disabled. These settings are saved across restarts. Slash command visibility is
        managed through Discord's integrations panel in server settings."""
        assert ctx.command is not None
        raise commands.BadArgument(f"No subcommand given for {ctx.command.name}.")

    async def _command_get_state(self, command: commands.Command) -> int:
        """Helper function for the 'command' command that gets the state of the command."""
        async with self.bot.db.acquire() as conn:
            cog_com_name = f"{command.cog.__class__.__name__ + '.' if command.cog else ''}{command.name}"
            response = await conn.fetchval("SELECT state FROM command_states WHERE command = $1", cog_com_name)
            if response is None:
                await conn.execute("INSERT INTO command_states VALUES ($1, $2)", cog_com_name, 0)
                response = 0
            return response

    async def _command_set_state(self, command: commands.Command, state: int):
        """Helper function for the 'command' command that sets the state of the command."""
        async with self.bot.db.acquire() as conn:
            await conn.execute(
                "UPDATE command_states SET state = $1 WHERE command = $2",
                state,
                f"{command.cog.__class__.__name__ + '.' if command.cog else ''}{command.name}",
            )

    @commands.has_permissions(administrator=True)
    @command.command(name="enable", usage="<COMMAND NAME>")
    async def command_enable(self, ctx: commands.Context, *, command_name: str):
        """This command enables prefix commands which have previously been disabled. This will allow them to be used
        again. It will also add the command back into the list of commands shown by the help command and re-enable
        the viewing of its help text given the command has help text, and it has not otherwise been hidden."""
        if command_name in self.bot.all_commands:  # Check if command exists and get it's state.
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if self.bot.all_commands[command_name].enabled:  # If command is already enabled, report back.
                await ctx.send(f"The `{clean(ctx, command_name)}` command is already enabled.")
            else:
                self.bot.all_commands[command_name].enabled = True
                await self._command_set_state(self.bot.all_commands[command_name], 0 if state == 2 else 1)
                await ctx.send(f"The `{clean(ctx, command_name)}` command is now enabled.")
        else:
            await ctx.send(f"No `{clean(ctx, command_name)}` command found.")

    @commands.has_permissions(administrator=True)
    @command.command(name="disable", usage="<COMMAND NAME>")
    async def command_disable(self, ctx: commands.Context, *, command_name: str):
        """This command can disable prefix commands. Disabled commands cannot be used and are removed from the
        list of commands shown by the help command. The command's help text will also not be viewable. Core
        commands cannot be disabled. Disabled commands can be re-enabled with the `command enable` command."""
        if command_name in self.bot.all_commands:  # Check if command exists and get it's state.
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if command_name in self.bot.help and self.bot.help[command_name].category.lower() == "core":
                await ctx.send("Core commands cannot be disabled.")
            else:
                if not self.bot.all_commands[command_name].enabled:  # Check if the command is already disabled.
                    await ctx.send(f"The `{clean(ctx, command_name)}` command is already disabled.")
                else:
                    self.bot.all_commands[command_name].enabled = False
                    await self._command_set_state(self.bot.all_commands[command_name], 2 if state == 0 else 3)
                    await ctx.send(f"The `{clean(ctx, command_name)}` command is now disabled.")
        else:
            await ctx.send(f"No `{clean(ctx, command_name)}` command found.")

    @commands.has_permissions(administrator=True)
    @command.command(name="show", usage="<COMMAND NAME>")
    async def command_show(self, ctx: commands.Context, *, command_name: str):
        """This command will show prefix commands which have previously been hidden, reversing the hiding of the
        command. This will add the command back into the list of commands shown by the help command. This
        will not re-enable the command if it has been disabled. Showing disabled commands alone will not
        be enough to re-add them to the help list since disabling them also hides them from the help list.
        See the `command enable` command to re-enable disabled commands."""
        if command_name in self.bot.all_commands:  # Check if command exists and get it's state.
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if not self.bot.all_commands[command_name].hidden:  # Check if command i already visible.
                await ctx.send(f"The `{clean(ctx, command_name)}` command is already shown.")
            else:
                self.bot.all_commands[command_name].hidden = False
                await self._command_set_state(self.bot.all_commands[command_name], 0 if state == 1 else 2)
                await ctx.send(f"The `{clean(ctx, command_name)}` command is now shown.")
        else:
            await ctx.send(f"No `{clean(ctx, command_name)}` command found.")

    @commands.has_permissions(administrator=True)
    @command.command(name="hide", usage="<COMMAND NAME>")
    async def command_hide(self, ctx: commands.Context, *, command_name: str):
        """This command will hide prefix commands from the list of commands shown by the help command. It will
        not disable the viewing of the help text for the command if someone already knows its name.
        Commands which have been hidden can be un-hidden with the `command show` command."""
        if command_name in self.bot.all_commands:  # Check if command exists and get it's state.
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if self.bot.all_commands[command_name].hidden:  # Check if command is already hidden.
                await ctx.send(f"The `{clean(ctx, command_name)}` command is already hidden.")
            else:
                self.bot.all_commands[command_name].hidden = True
                await self._command_set_state(self.bot.all_commands[command_name], 1 if state == 0 else 3)
                await ctx.send(f"The `{clean(ctx, command_name)}` command is now hidden.")
        else:
            await ctx.send(f"No `{clean(ctx, command_name)}` command found.")

    @commands.command(name="about", aliases=["info"], usage="(MODULE NAME)")
    async def about(self, ctx: commands.Context, *, module_name: str | None = None):
        """This command gives information about modules, such as a description, authors, and other credits. Module
        authors can even add a small image to be displayed alongside this info. If no module name is given or the
        bot's name is used then information about the bot itself is shown."""
        assert self.bot.user is not None
        if module_name is None:  # If no value is passed along we display the about page for the bot itself.
            if self.bot.user.name.lower() in self.bot.modules:  # Check if the bot has an entry.
                embed = self.bot.modules[self.bot.user.name.lower()].make_about_embed(
                    ctx.author
                )  # Make and send response.
                await ctx.send(embed=embed)
            else:
                raise RuntimeError("Bot info module not found.")
        elif module_name.lower() in self.bot.modules:  # Check if the passed along value has an entry.
            embed = self.bot.modules[module_name.lower()].make_about_embed(ctx.author)  # Make and send response.
            await ctx.send(embed=embed)
        else:
            response = f"No information for `{clean(ctx, module_name)}` module was found."
            if module_name not in [mod.replace("modules.", "") for mod in self.bot.extensions]:
                response += "\nAdditionally no module with this name is loaded."
            await ctx.send(response)

    @commands.command(name="usage", usage="(MODULE NAME)")
    async def usage(self, ctx: commands.Context, *, module_name: str | None = None):
        """This command explains how a module is intended to be used. If no module name is given it will
        show some basic information about usage of the bot itself."""
        assert self.bot.user is not None
        if module_name is None or module_name.lower() in [self.bot.user.name.lower(), "core_commands", "core commands"]:
            pref = self.bot.get_bot_prefix()
            response = (
                "**How To Use:**\nThis bot features a variety of commands. You can get a list of all commands "
                f"you have access to with the `{pref}help` command. In order to use a command your message has "
                f"to start with the *bot prefix*, the bot prefix is currently set to `{pref}`. Simply type "
                "this prefix, followed by a command name, and you will run the command. For more information "
                f"on individual commands, run `{pref}help` followed by the command name. This will give you "
                "info on the command, along with some examples of it and any aliases the command might have. "
                "You might not have access to all commands everywhere, the help command will only tell you "
                "about commands you have access to in that channel, and commands you can run only in the DMs "
                "with the bot. DM only commands will be labeled as such by the help command.\n\nSome commands "
                "accept extra input, an example would be how the help command accepts a command name. You can "
                "usually see an example of how the command is used on the command's help page. If you use a "
                "command incorrectly by missing some input or sending invalid input, it will send you the "
                "expected input. This is how to read the expected input:\n\nArguments encased in `<>` are "
                "obligatory.\nArguments encased in `()` are optional and can be skipped.\nArguments written "
                "in all uppercase are placeholders like names.\nArguments not written in uppercase are exact "
                "values.\nIf an argument lists multiple things separated by `/` then any one of them is valid."
                f"\nThe `<>` and `()` symbols are not part of the command.\n\nSample expected input: `{pref}"
                f"about (MODULE NAME)`\nHere `{pref}about` is the command, and it takes an optional argument. "
                "The argument is written in all uppercase, so it is a placeholder. In other words you are "
                "expected to replace 'MODULE NAME' with the actual name of a module. Since the module name is "
                f"optional, sending just `{pref}about` is also a valid command."
            )
            await ctx.send(response)
        elif module_name.lower() in self.bot.modules:
            usage = self.bot.modules[module_name.lower()].usage
            if usage is None:
                await ctx.send(f"The `{clean(ctx, module_name)}` module does not have its usage defined.")
            else:
                usage_content = usage()
                if isinstance(usage_content, str):
                    await ctx.send(usage_content if len(usage_content) < 1950 else f"{usage_content[:1949]}...")
                elif isinstance(usage_content, Embed):
                    await ctx.send(embed=usage_content)
        else:
            response = f"No information for `{clean(ctx, module_name)}` module was found."
            if module_name not in [mod.replace("modules.", "") for mod in self.bot.extensions]:
                response += "\nAdditionally no module with this name is loaded."
            await ctx.send(response)

    @commands.has_permissions(administrator=True)
    @commands.group(invoke_without_command=True, name="config", usage="<get/set/unset>")
    async def config(self, ctx: commands.Context):
        """This command is used to get, set and unset configuration options used by other modules or commands. All
        config options are saves as strings. Converting them to the proper type is up to the module or command that
        uses them. See the help text for the subcommands for more info."""
        assert ctx.command is not None
        raise commands.BadArgument(f"No subcommand given for {ctx.command.name}.")

    @commands.has_permissions(administrator=True)
    @config.command(name="get", usage="(CONFIG_OPTION)")
    async def config_get(self, ctx: commands.Context, option: str | None = None):
        """This command is used to get the value of config options. Using this, one can check what configuration
        options are set to. If no option is given, all options and their values are shown."""
        if option is None or option.lower() == "all":
            if not self.bot.config:
                await ctx.send("No configuration options are set.")
                return
            paginator = commands.Paginator()
            for line in [f"{key}: {value}" for key, value in self.bot.config.items()]:
                line = tbb.clean(ctx, line, False, True)
                paginator.add_line(line if len(line) < 1992 else f"{line[:1989]}...")
            for page in paginator.pages:
                await ctx.send(page)
        elif option.lower() in self.bot.config:
            value = tbb.clean(ctx, self.bot.config[option], False, True)
            option = tbb.clean(ctx, option, False, True)
            line = f"Option: `{option}`, value: `{value}`"
            await ctx.send(line if len(line) < 1994 else f"{line[:1991]}...")
        else:
            option = tbb.clean(ctx, option, False, True)
            await ctx.send(f"No configuration option `{option if len(option) < 1960 else option[:1959]}...` is set.")

    @commands.has_permissions(administrator=True)
    @config.command(name="set", usage="CONFIG_OPTION> <VALUE>")
    async def config_set(self, ctx: commands.Context, option: str, *, value: str):
        """This command sets a configuration option. Configuration options are used by other modules or commands.
        Setting an option which already exists will overwrite the option. Setting an option which does not exist will
        create it. The keyword all cannot be used as a configuration option as it is used by the get command to get all
        options."""
        option = option.lower()
        if option == "all":
            await ctx.send("The keyword `all` cannot be used as a configuration option.")
        else:
            self.bot.config[option] = value
            async with self.bot.db.acquire() as conn:
                await conn.execute(
                    "INSERT INTO config VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = $2", option, value
                )
            option = tbb.clean(ctx, option, False, True)
            value = tbb.clean(ctx, value, False, True)
            line = f"Configuration option `{option}` has been set to `{value}`."
            await ctx.send(line if len(line) < 2000 else f"{line[:1996]}...")

    @commands.has_permissions(administrator=True)
    @config.command(name="unset", usage="<CONFIG_OPTION> <VALUE>")
    async def config_unset(self, ctx: commands.Context, option: str):
        """This command allows for the removal of configuration options. Removing configuration options which are
        required by commands or modules will stop these from working."""
        option = option.lower()
        if option in self.bot.config:
            del self.bot.config[option]
            async with self.bot.db.acquire() as conn:
                await conn.execute("DELETE FROM config WHERE key = $1", option)
                option = tbb.clean(ctx, option, False, True)
            line = f"Configuration option `{option}` has been unset."
            await ctx.send(line if len(line) < 2000 else f"{line[:1996]}...")
        else:
            option = tbb.clean(ctx, option, False, True)
            line = f"No configuration option `{option}` exists."
            await ctx.send(line if len(line) < 2000 else f"{line[:1996]}...")

    @commands.is_owner()
    @commands.command(name="shutdown", aliases=["goodbye", "goodnight"], usage="(TIME BEFORE SHUTDOWN)")
    async def shutdown(self, ctx: commands.Context, countdown: str | None = None):
        """This command turns the bot off. A delay can be set causing the bot to wait before shutting down. The time
        uses a format of numbers followed by units, see examples for details. Times supported are weeks (w), days (d),
        hours (h), minutes (m) and seconds (s), and even negative numbers. For this command the delay must be between
        0 seconds and 24 hours. Supplying no time will cause the bot to shut down immediately. Once started, a shutdown
        cannot be stopped."""
        if countdown is None:  # If no time is passed along, shut down the bot immediately.
            await ctx.send("Goodbye!")
            await self.bot.close()
        else:
            try:
                time = tbb.parse_time(countdown, 0, 86400, True)  # Parse time to get time in seconds.
                await ctx.send(f"Shutdown will commence in {time} seconds.")
                await asleep(time)
                await ctx.send("Shutting down!")
                await self.bot.close()
            except ValueError as e:  # If time parser encounters error, and error is exceeding of limit, report back.
                if str(e) in ["Time too short.", "Time too long."]:
                    await ctx.send("The time for this command must be between 0 seconds to 24 hours.")
                else:  # If another error is encountered, log to console.
                    await ctx.send("The time could not be parsed correctly.")
                    self.log.error(f"{ctx.author.id}: {e!s}")
                    self.bot.last_error = f"{ctx.author.id}: {e!s}"

    @app_commands.command(name="about", description="Shows information about the bot or a module.")
    @app_commands.describe(module_name="Module to show info for, or omit for bot info.")
    async def slash_about(self, interaction: Interaction, module_name: str | None = None):
        """This command gives information about modules, such as a description, authors, and other credits. Module
        authors can even add a small image to be displayed alongside this info. If no module name is given or the
        bot's name is used then information about the bot itself is shown."""
        assert self.bot.user is not None
        if module_name is None:
            if self.bot.user.name.lower() in self.bot.modules:
                embed = self.bot.modules[self.bot.user.name.lower()].make_about_embed(interaction.user)
                await self.bot.send_response(interaction, embed=embed)
            else:
                raise RuntimeError("Bot info module not found.")
        elif module_name.lower() in self.bot.modules:
            embed = self.bot.modules[module_name.lower()].make_about_embed(interaction.user)
            await self.bot.send_response(interaction, embed=embed)
        else:
            mod = tbb.clean_no_ctx(self.bot, interaction.guild, module_name, False, True)
            response = f"No information for `{mod}` module was found."
            if module_name not in [ext.replace("modules.", "") for ext in self.bot.extensions]:
                response += "\nAdditionally no module with this name is loaded."
            await self.bot.send_response(interaction, response)

    @slash_about.autocomplete("module_name")
    async def slash_about_autocomplete(self, _interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for module_name parameter of /about."""
        return [
            app_commands.Choice(name=name, value=name) for name in self.bot.modules if current.lower() in name.lower()
        ][:25]

    @app_commands.command(name="usage", description="Explains how to use the bot or a module.")
    @app_commands.describe(module_name="Module to show usage info for, or omit for general bot usage.")
    async def slash_usage(self, interaction: Interaction, module_name: str | None = None):
        """This command explains how a module is intended to be used. If no module name is given it will
        show some basic information about usage of the bot itself."""
        assert self.bot.user is not None
        if module_name is None or module_name.lower() in [self.bot.user.name.lower(), "core_commands", "core commands"]:
            response = (
                "**How To Use:**\nThis bot features a variety of commands available as slash commands. "
                "Type `/` in the chat bar to see all available slash commands. For a list of all commands "
                "you have access to, use the `/help` command. For more information on individual commands, "
                "run `/help` followed by the command name. This will give you info on the command and any "
                "examples of it. You might not have access to all commands everywhere, the help command will "
                "only tell you about commands you have access to in that channel, and commands you can run "
                "only in the DMs with the bot. DM only commands will be labeled as such by the help command."
                "\n\nSome commands accept extra input, an example would be how the help command accepts a "
                "command name. The slash command interface will show you what each argument expects. This is "
                "how to read the argument descriptions shown by this bot:\n\nArguments encased in `<>` are "
                "obligatory.\nArguments encased in `()` are optional and can be skipped.\nArguments written "
                "in all uppercase are placeholders like names.\nArguments not written in uppercase are exact "
                "values.\nIf an argument lists multiple things separated by `/` then any one of them is valid."
                "\nThe `<>` and `()` symbols are not part of the command.\n\nSample expected input: "
                "`/about (MODULE NAME)`\nHere `/about` is the command, and it takes an optional argument. "
                "The argument is written in all uppercase, so it is a placeholder. In other words you are "
                "expected to replace 'MODULE NAME' with the actual name of a module. Since the module name "
                "is optional, sending just `/about` is also a valid command."
            )
            await self.bot.send_response(interaction, response)
        elif module_name.lower() in self.bot.modules:
            mod_usage = self.bot.modules[module_name.lower()].usage
            if mod_usage is None:
                mod = tbb.clean_no_ctx(self.bot, interaction.guild, module_name, False, True)
                await self.bot.send_response(interaction, f"The `{mod}` module does not have its usage defined.")
            else:
                usage_content = mod_usage()
                if isinstance(usage_content, str):
                    await self.bot.send_response(
                        interaction, usage_content if len(usage_content) < 1950 else f"{usage_content[:1949]}..."
                    )
                elif isinstance(usage_content, Embed):
                    await self.bot.send_response(interaction, embed=usage_content)
        else:
            mod = tbb.clean_no_ctx(self.bot, interaction.guild, module_name, False, True)
            response = f"No information for `{mod}` module was found."
            if module_name not in [ext.replace("modules.", "") for ext in self.bot.extensions]:
                response += "\nAdditionally no module with this name is loaded."
            await self.bot.send_response(interaction, response)

    @slash_usage.autocomplete("module_name")
    async def slash_usage_autocomplete(self, _interaction: Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocomplete for module_name parameter of /usage."""
        return [
            app_commands.Choice(name=name, value=name) for name in self.bot.modules if current.lower() in name.lower()
        ][:25]

    slash_module = app_commands.Group(
        name="module",
        description="Load, unload, reload, and list bot modules.",
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True),
    )

    @slash_module.command(name="list", description="Lists loaded and available modules.")
    async def slash_module_list(self, interaction: Interaction):
        """This command lists all currently loaded and available modules. For the bot to find new modules they need to
        be placed inside the modules folder inside the bot directory. Modules listed by this command can be loaded,
        unloaded and reloaded by the respective commands for this."""
        assert interaction.guild is not None
        loaded_modules = [
            f"`{tbb.clean_no_ctx(self.bot, interaction.guild, mod.replace('modules.', ''), False, True)}`, "
            for mod in self.bot.extensions
            if mod != "core_commands"
        ] or ["None, "]
        available_modules = [
            f"`{tbb.clean_no_ctx(self.bot, interaction.guild, mod, False, True).replace('.py', '')}`, "
            for mod in listdir("modules")
            if mod.endswith(".py")
        ]
        available_modules = [mod for mod in available_modules if mod not in loaded_modules] or ["None, "]
        loaded_modules[-1] = loaded_modules[-1][:-2]
        available_modules[-1] = available_modules[-1][:-2]
        paginator = commands.Paginator(prefix="", suffix="", linesep="")
        paginator.add_line("Loaded modules: ")
        for mod in loaded_modules:
            paginator.add_line(mod)
        paginator.add_line("\nAvailable Modules: ")
        for mod in available_modules:
            paginator.add_line(mod)
        for page in paginator.pages:
            await self.bot.send_response(interaction, page)

    @slash_module.command(name="load", description="Loads a module.")
    @app_commands.describe(module="Name of the module to load.")
    async def slash_module_load(self, interaction: Interaction, module: str):
        """This command loads modules. Modules should be located inside the module folder in the bot directory. The
        `/module list` command can be used to show all modules available for loading. Once a module is loaded the
        functionality defined in the module file will be added to the bot."""
        await interaction.response.defer(ephemeral=self.bot.ephemeral)
        await self._module_operation(interaction, "load", module)

    @slash_module.command(name="unload", description="Unloads a module.")
    @app_commands.describe(module="Name of the module to unload.")
    async def slash_module_unload(self, interaction: Interaction, module: str):
        """This command unloads modules. When a loaded module is unloaded its functionality will be removed. You can
        use the `/module list` command to see all currently loaded modules."""
        await interaction.response.defer(ephemeral=self.bot.ephemeral)
        await self._module_operation(interaction, "unload", module)

    @slash_module.command(name="reload", description="Reloads a module.")
    @app_commands.describe(module="Name of the module to reload.")
    async def slash_module_reload(self, interaction: Interaction, module: str):
        """This command reloads a module that is currently loaded. This will unload and load the module in one command.
        If the loading process encounters an error the module will not be reloaded and the functionality from before
        the reload will be retained."""
        await interaction.response.defer(ephemeral=self.bot.ephemeral)
        await self._module_operation(interaction, "reload", module)

    @slash_module.command(name="lasterror", description="Shows the last module loading error.")
    async def slash_module_lasterror(self, interaction: Interaction):
        """This command will show the last error that was encountered during the module load or reloading process. This
        information will also be logged to the console when the error first is encountered. This command retains this
        information until another error replaces it, or the bot shuts down."""
        if self.bot.last_module_error:
            await self.bot.send_response(interaction, self.bot.last_module_error[:1999])
        else:
            await self.bot.send_response(
                interaction, "There have not been any errors loading modules since the last restart."
            )

    @slash_module_load.autocomplete("module")
    async def slash_module_load_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /module load — shows available (not yet loaded) modules."""
        loaded = {mod.replace("modules.", "") for mod in self.bot.extensions if mod != "core_commands"}
        available = [
            mod.replace(".py", "")
            for mod in listdir("modules")
            if mod.endswith(".py") and mod.replace(".py", "") not in loaded
        ]
        return [app_commands.Choice(name=name, value=name) for name in available if current.lower() in name.lower()][
            :25
        ]

    @slash_module_unload.autocomplete("module")
    async def slash_module_unload_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /module unload — shows loaded modules."""
        loaded = [mod.replace("modules.", "") for mod in self.bot.extensions if mod != "core_commands"]
        return [app_commands.Choice(name=name, value=name) for name in loaded if current.lower() in name.lower()][:25]

    @slash_module_reload.autocomplete("module")
    async def slash_module_reload_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /module reload — shows loaded modules."""
        loaded = [mod.replace("modules.", "") for mod in self.bot.extensions if mod != "core_commands"]
        return [app_commands.Choice(name=name, value=name) for name in loaded if current.lower() in name.lower()][:25]

    slash_default = app_commands.Group(
        name="default",
        description="Manage default modules that load on startup.",
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True),
    )

    @slash_default.command(name="list", description="Lists all default modules.")
    async def slash_default_list(self, interaction: Interaction):
        """This command lists all current default modules. All modules in this list start as soon as the bot is
        launched. For a list of all available or loaded modules see the `/module list` command."""
        async with self.bot.db.acquire() as conn:
            result = await conn.fetch("SELECT module FROM default_modules")
        entries = [
            f"`{tbb.clean_no_ctx(self.bot, interaction.guild, val['module'], False, True)}`, " for val in result
        ] or ["None, "]
        entries[-1] = entries[-1][:-2]
        paginator = commands.Paginator(prefix="", suffix="", linesep="")
        paginator.add_line("Default modules: ")
        for mod in entries:
            paginator.add_line(mod)
        for page in paginator.pages:
            await self.bot.send_response(interaction, page)

    @slash_default.command(name="add", description="Adds a module to the default list.")
    @app_commands.describe(module="Name of the module to add as default.")
    async def slash_default_add(self, interaction: Interaction, module: str):
        """This command adds a module to the list of default modules. Modules in this list are loaded automatically
        once the bot starts. This command does not load modules if they are not already loaded."""
        if f"{module}.py" in listdir("modules"):
            try:
                async with self.bot.db.acquire() as conn:
                    await conn.execute("INSERT INTO default_modules VALUES ($1)", module)
                    mod = tbb.clean_no_ctx(self.bot, interaction.guild, module, False, True)
                    await self.bot.send_response(interaction, f"The `{mod}` module is now a default module.")
            except IntegrityConstraintViolationError:
                mod = tbb.clean_no_ctx(self.bot, interaction.guild, module, False, True)
                await self.bot.send_response(interaction, f"The `{mod}` module is already a default module.")
        else:
            mod = tbb.clean_no_ctx(self.bot, interaction.guild, module, False, True)
            await self.bot.send_response(interaction, f"No `{mod}` module was found.")

    @slash_default.command(name="remove", description="Removes a module from the default list.")
    @app_commands.describe(module="Name of the module to remove from defaults.")
    async def slash_default_remove(self, interaction: Interaction, module: str):
        """This command removes a module from the list of default modules. Once removed the module will no longer
        automatically be loaded when the bot starts. This will not unload modules that are already loaded."""
        async with self.bot.db.acquire() as conn:
            result = await conn.fetchval("SELECT module FROM default_modules WHERE module = $1", module)
            mod = tbb.clean_no_ctx(self.bot, interaction.guild, module, False, True)
            if result:
                await conn.execute("DELETE FROM default_modules WHERE module = $1", module)
                await self.bot.send_response(interaction, f"Removed `{mod}` module from default modules.")
            else:
                await self.bot.send_response(interaction, f"No `{mod}` module in default modules.")

    @slash_default_add.autocomplete("module")
    async def slash_default_add_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /default add — shows available modules on disk."""
        available = [mod.replace(".py", "") for mod in listdir("modules") if mod.endswith(".py")]
        return [app_commands.Choice(name=name, value=name) for name in available if current.lower() in name.lower()][
            :25
        ]

    @slash_default_remove.autocomplete("module")
    async def slash_default_remove_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /default remove — shows current default modules."""
        async with self.bot.db.acquire() as conn:
            result = await conn.fetch("SELECT module FROM default_modules")
        defaults = [val["module"] for val in result]
        return [app_commands.Choice(name=name, value=name) for name in defaults if current.lower() in name.lower()][:25]

    slash_config = app_commands.Group(
        name="config",
        description="Get, set, or unset bot configuration options.",
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True),
    )

    @slash_config.command(name="get", description="Shows the value of a config option, or all options.")
    @app_commands.describe(option="Config option to look up, or omit to show all.")
    async def slash_config_get(self, interaction: Interaction, option: str | None = None):
        """This command shows the value of a configuration option. If no option is given, all configuration
        options and their values are shown."""
        if option is None or option.lower() == "all":
            if not self.bot.config:
                await self.bot.send_response(interaction, "No configuration options are set.")
                return
            paginator = commands.Paginator()
            for line in [f"{key}: {value}" for key, value in self.bot.config.items()]:
                line = tbb.clean_no_ctx(self.bot, interaction.guild, line, False, True)
                paginator.add_line(line if len(line) < 1992 else f"{line[:1989]}...")
            for page in paginator.pages:
                await self.bot.send_response(interaction, page)
        elif option.lower() in self.bot.config:
            value = tbb.clean_no_ctx(self.bot, interaction.guild, self.bot.config[option.lower()], False, True)
            opt = tbb.clean_no_ctx(self.bot, interaction.guild, option.lower(), False, True)
            line = f"Option: `{opt}`, value: `{value}`"
            await self.bot.send_response(interaction, line if len(line) < 1994 else f"{line[:1991]}...")
        else:
            opt = tbb.clean_no_ctx(self.bot, interaction.guild, option, False, True)
            await self.bot.send_response(
                interaction, f"No configuration option `{opt if len(opt) < 1960 else opt[:1959]}...` is set."
            )

    @slash_config.command(name="set", description="Sets a configuration option.")
    @app_commands.describe(option="Configuration option name.", value="Value to set.")
    async def slash_config_set(self, interaction: Interaction, option: str, value: str):
        """This command sets a configuration option used by other modules or commands. Setting an existing option
        overwrites it. The keyword 'all' cannot be used as an option name."""
        option = option.lower()
        if option == "all":
            await self.bot.send_response(interaction, "The keyword `all` cannot be used as a configuration option.")
        else:
            self.bot.config[option] = value
            async with self.bot.db.acquire() as conn:
                await conn.execute(
                    "INSERT INTO config VALUES ($1, $2) ON CONFLICT (key) DO UPDATE SET value = $2", option, value
                )
            opt = tbb.clean_no_ctx(self.bot, interaction.guild, option, False, True)
            val = tbb.clean_no_ctx(self.bot, interaction.guild, value, False, True)
            line = f"Configuration option `{opt}` has been set to `{val}`."
            await self.bot.send_response(interaction, line if len(line) < 2000 else f"{line[:1996]}...")

    @slash_config.command(name="unset", description="Removes a configuration option.")
    @app_commands.describe(option="Configuration option to remove.")
    async def slash_config_unset(self, interaction: Interaction, option: str):
        """This command removes a configuration option. Removing options required by commands or modules will stop
        those from working."""
        option = option.lower()
        if option in self.bot.config:
            del self.bot.config[option]
            async with self.bot.db.acquire() as conn:
                await conn.execute("DELETE FROM config WHERE key = $1", option)
            opt = tbb.clean_no_ctx(self.bot, interaction.guild, option, False, True)
            line = f"Configuration option `{opt}` has been unset."
            await self.bot.send_response(interaction, line if len(line) < 2000 else f"{line[:1996]}...")
        else:
            opt = tbb.clean_no_ctx(self.bot, interaction.guild, option, False, True)
            line = f"No configuration option `{opt}` exists."
            await self.bot.send_response(interaction, line if len(line) < 2000 else f"{line[:1996]}...")

    @slash_config_get.autocomplete("option")
    async def slash_config_get_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /config get — shows existing config keys and 'all'."""
        keys = ["all", *self.bot.config]
        return [app_commands.Choice(name=key, value=key) for key in keys if current.lower() in key.lower()][:25]

    @slash_config_set.autocomplete("option")
    async def slash_config_set_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /config set — shows existing config keys."""
        return [app_commands.Choice(name=key, value=key) for key in self.bot.config if current.lower() in key.lower()][
            :25
        ]

    @slash_config_unset.autocomplete("option")
    async def slash_config_unset_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /config unset — shows existing config keys."""
        return [app_commands.Choice(name=key, value=key) for key in self.bot.config if current.lower() in key.lower()][
            :25
        ]

    slash_command = app_commands.Group(
        name="command",
        description="Enable, disable, show, or hide prefix commands.",
        guild_only=True,
        default_permissions=discord.Permissions(administrator=True),
    )

    @slash_command.command(name="enable", description="Enables a previously disabled prefix command.")
    @app_commands.describe(command_name="Name of the prefix command to enable.")
    async def slash_command_enable(self, interaction: Interaction, command_name: str):
        """This command enables prefix commands which have previously been disabled. This will allow them to be used
        again. It will also add the command back into the list of commands shown by the help command and re-enable
        the viewing of its help text given the command has help text, and it has not otherwise been hidden."""
        if command_name in self.bot.all_commands:
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if self.bot.all_commands[command_name].enabled:
                name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
                await self.bot.send_response(interaction, f"The `{name}` command is already enabled.")
            else:
                self.bot.all_commands[command_name].enabled = True
                await self._command_set_state(self.bot.all_commands[command_name], 0 if state == 2 else 1)
                name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
                await self.bot.send_response(interaction, f"The `{name}` command is now enabled.")
        else:
            name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
            await self.bot.send_response(interaction, f"No `{name}` command found.")

    @slash_command.command(name="disable", description="Disables a prefix command.")
    @app_commands.describe(command_name="Name of the prefix command to disable.")
    async def slash_command_disable(self, interaction: Interaction, command_name: str):
        """This command can disable prefix commands. Disabled commands cannot be used and are removed from the
        list of commands shown by the help command. The command's help text will also not be viewable. Core
        commands cannot be disabled. Disabled commands can be re-enabled with the `/command enable` command."""
        if command_name in self.bot.all_commands:
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if command_name in self.bot.help and self.bot.help[command_name].category.lower() == "core":
                await self.bot.send_response(interaction, "Core commands cannot be disabled.")
            else:
                if not self.bot.all_commands[command_name].enabled:
                    name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
                    await self.bot.send_response(interaction, f"The `{name}` command is already disabled.")
                else:
                    self.bot.all_commands[command_name].enabled = False
                    await self._command_set_state(self.bot.all_commands[command_name], 2 if state == 0 else 3)
                    name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
                    await self.bot.send_response(interaction, f"The `{name}` command is now disabled.")
        else:
            name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
            await self.bot.send_response(interaction, f"No `{name}` command found.")

    @slash_command.command(name="show", description="Shows a previously hidden prefix command.")
    @app_commands.describe(command_name="Name of the prefix command to show.")
    async def slash_command_show(self, interaction: Interaction, command_name: str):
        """This command will show prefix commands which have previously been hidden, reversing the hiding of the
        command. This will add the command back into the list of commands shown by the help command. This
        will not re-enable the command if it has been disabled."""
        if command_name in self.bot.all_commands:
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if not self.bot.all_commands[command_name].hidden:
                name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
                await self.bot.send_response(interaction, f"The `{name}` command is already shown.")
            else:
                self.bot.all_commands[command_name].hidden = False
                await self._command_set_state(self.bot.all_commands[command_name], 0 if state == 1 else 2)
                name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
                await self.bot.send_response(interaction, f"The `{name}` command is now shown.")
        else:
            name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
            await self.bot.send_response(interaction, f"No `{name}` command found.")

    @slash_command.command(name="hide", description="Hides a prefix command from the help list.")
    @app_commands.describe(command_name="Name of the prefix command to hide.")
    async def slash_command_hide(self, interaction: Interaction, command_name: str):
        """This command will hide prefix commands from the list of commands shown by the help command. It will
        not disable the viewing of the help text for the command if someone already knows its name.
        Commands which have been hidden can be un-hidden with the `/command show` command."""
        if command_name in self.bot.all_commands:
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if self.bot.all_commands[command_name].hidden:
                name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
                await self.bot.send_response(interaction, f"The `{name}` command is already hidden.")
            else:
                self.bot.all_commands[command_name].hidden = True
                await self._command_set_state(self.bot.all_commands[command_name], 1 if state == 0 else 3)
                name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
                await self.bot.send_response(interaction, f"The `{name}` command is now hidden.")
        else:
            name = tbb.clean_no_ctx(self.bot, interaction.guild, command_name, False, True)
            await self.bot.send_response(interaction, f"No `{name}` command found.")

    @slash_command_enable.autocomplete("command_name")
    async def slash_command_enable_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /command enable — shows disabled commands."""
        names = sorted({cmd.name for cmd in self.bot.all_commands.values() if not cmd.enabled})
        return [app_commands.Choice(name=name, value=name) for name in names if current.lower() in name.lower()][:25]

    @slash_command_disable.autocomplete("command_name")
    async def slash_command_disable_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /command disable — shows enabled non-core commands."""
        core = {n for n, h in self.bot.help.items() if h.category.lower() == "core"}
        names = sorted({cmd.name for cmd in self.bot.all_commands.values() if cmd.enabled and cmd.name not in core})
        return [app_commands.Choice(name=name, value=name) for name in names if current.lower() in name.lower()][:25]

    @slash_command_show.autocomplete("command_name")
    async def slash_command_show_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /command show — shows hidden commands."""
        names = sorted({cmd.name for cmd in self.bot.all_commands.values() if cmd.hidden})
        return [app_commands.Choice(name=name, value=name) for name in names if current.lower() in name.lower()][:25]

    @slash_command_hide.autocomplete("command_name")
    async def slash_command_hide_autocomplete(
        self, _interaction: Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete for /command hide — shows non-hidden commands."""
        names = sorted({cmd.name for cmd in self.bot.all_commands.values() if not cmd.hidden})
        return [app_commands.Choice(name=name, value=name) for name in names if current.lower() in name.lower()][:25]
