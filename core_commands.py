from asyncio import sleep as asleep  # For waiting asynchronously.
from os import listdir  # To check files on disk.

from discord import Embed, Activity, ActivityType  # For bot status
from discord.ext import commands  # For implementation of bot commands.

import travus_bot_base as tbb  # TBB functions and classes.
from travus_bot_base import clean  # Shorthand for cleaning output.


def setup(bot: tbb.TravusBotBase):
    """Setup function ran when module is loaded."""
    bot.add_cog(CoreFunctionalityCog(bot))  # Add cog and command help info.
    bot.add_command_help(CoreFunctionalityCog.botconfig, "Core", None,
                         ["prefix", "deletemessages", "description", "credits"])
    bot.add_command_help(CoreFunctionalityCog.botconfig_prefix, "Core", None, ["$", "bot!", "bot ?", "remove"])
    bot.add_command_help(CoreFunctionalityCog.botconfig_deletemessages, "Core", None, ["enable", "y", "disable", "n"])
    bot.add_command_help(CoreFunctionalityCog.botconfig_description, "Core", None,
                         ["remove", "This is a sample description."])
    bot.add_command_help(CoreFunctionalityCog.botconfig_credits, "Core", None,
                         ["remove", "`\n```\n[Person](URL):\n\tBot Profile Image\n``"])
    bot.add_command_help(CoreFunctionalityCog.module, "Core", {"perms": ["Administrator"]},
                         ["list", "load", "unload", "reload"])
    bot.add_command_help(CoreFunctionalityCog.module_list, "Core", {"perms": ["Administrator"]}, [""])
    bot.add_command_help(CoreFunctionalityCog.module_load, "Core", {"perms": ["Administrator"]}, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.module_unload, "Core", {"perms": ["Administrator"]}, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.module_reload, "Core", {"perms": ["Administrator"]}, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.default, "Core", None, ["list", "add", "remove"])
    bot.add_command_help(CoreFunctionalityCog.default_list, "Core", None, [""])
    bot.add_command_help(CoreFunctionalityCog.default_add, "Core", None, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.default_remove, "Core", None, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.command, "Core", {"perms": ["Administrator"]},
                         ["enable", "disable", "show", "hide"])
    bot.add_command_help(CoreFunctionalityCog.command_enable, "Core", {"perms": ["Administrator"]}, ["balance", "pay"])
    bot.add_command_help(CoreFunctionalityCog.command_disable, "Core", {"perms": ["Administrator"]}, ["balance", "pay"])
    bot.add_command_help(CoreFunctionalityCog.command_show, "Core", {"perms": ["Administrator"]}, ["module", "balance"])
    bot.add_command_help(CoreFunctionalityCog.command_hide, "Core", {"perms": ["Administrator"]}, ["module", "balance"])
    bot.add_command_help(CoreFunctionalityCog.about, "Core", None, ["", "fun"])
    bot.add_command_help(CoreFunctionalityCog.usage, "Core", None, ["", "dev"])
    bot.add_command_help(CoreFunctionalityCog.shutdown, "Core", None, ["", "1h", "1h30m", "10m-30s", "2m30s"])


def teardown(bot: tbb.TravusBotBase):
    """Teardown function ran when module is unloaded."""
    bot.remove_cog("CoreFunctionalityCog")  # Remove cog and command help info.
    bot.remove_command_help(CoreFunctionalityCog)


class CoreFunctionalityCog(commands.Cog):
    """Cog that holds default functionality."""

    def __init__(self, bot: tbb.TravusBotBase):
        """Initialization function loading bot object for cog."""
        self.bot = bot

    async def _module_operation(self, ctx: commands.Context, operation: str, mod: str):
        """To avoid code duplication in the except blocks all module command functionality is grouped together."""
        old_help = dict(self.bot.help)  # Save old help and module info in we need to roll back.
        old_modules = dict(self.bot.modules)
        self.bot.extension_ctx = ctx  # Save context in case loaded module has use for it.
        try:
            if operation == "load":  # Try loading the module.
                if f"{mod}.py" in listdir("modules"):  # Check if module is there to differentiate errors more easily.
                    self.bot.load_extension(f"modules.{mod}")
                    await self.bot.update_command_states()
                    await ctx.send(f"Module `{clean(ctx, mod)}` successfully loaded.")
                    print(f"[{tbb.cur_time()}] {ctx.message.author.id} loaded '{mod}' module.")
                else:
                    await ctx.send(f"No `{clean(ctx, mod)}` module was found.")
            elif operation == "unload":
                self.bot.unload_extension(f"modules.{mod}")
                await ctx.send(f"Module `{clean(ctx, mod)}` successfully unloaded.")
                print(f"[{tbb.cur_time()}] {ctx.message.author.id} unloaded '{mod}' module.")
            elif operation == "reload":  # Try reloading the module.
                if f"{mod}.py" in listdir("modules"):  # Check if module is even still there before we reload.
                    self.bot.reload_extension(f"modules.{mod}")
                    await self.bot.update_command_states()
                    await ctx.send(f"Module `{clean(ctx, mod)}` successfully reloaded.")
                    print(f"[{tbb.cur_time()}] {ctx.message.author.id} reloaded '{mod}' module.")
                else:
                    if mod in self.bot.modules:
                        await ctx.send(f"The `{clean(ctx, mod)}` module file is no longer found on disk. "
                                       f"Reload canceled.")
                    else:
                        await ctx.send(f"No `{clean(ctx, mod)}` module was found.")
        except commands.ExtensionAlreadyLoaded:  # If module was already loaded.
            await ctx.send(f"The `{clean(ctx, mod)}` module was already loaded.")
        except commands.ExtensionNotLoaded:  # If module wasn't loaded to begin with.
            await ctx.send(f"No `{clean(ctx, mod)}` module is loaded.")
        except Exception as e:  # If module crashed while loading, restore old help and module info.
            self.bot.help = old_help
            self.bot.modules = old_modules
            await ctx.send("**Error! Something went really wrong! Contact module maintainer.**\n"
                           "Error printed to console and stored in module error command.")
            if isinstance(e, commands.ExtensionNotFound):  # Clarify error further in case it was an import error.
                e = e.__cause__
            print(f"[{tbb.cur_time()}] {ctx.message.author.id} tried loading '{mod}' module, and it failed:"
                  f"\n\n{str(e)}")
            self.bot.last_module_error = f"The `{clean(ctx, mod)}` module failed while loading. The error was:" \
                                         f"\n\n{clean(ctx, str(e))}"
        finally:  # Reset context as loading has concluded.
            self.bot.extension_ctx = None

    @commands.is_owner()
    @commands.group(invoke_without_command=True, name="botconfig", usage="<prefix/deletemessages/description/credits>")
    async def botconfig(self, ctx: commands.Context):
        """This command sets the bot's prefix, command trigger deletion behaviour, description and additional credits
        section. Fore more information check the help entry of one of these subcommands; `prefix`, `deletemessages`,
        `description`, `credits`."""
        raise commands.BadArgument(f"No subcommand given for {ctx.command.name}.")

    @commands.is_owner()
    @botconfig.command(name="prefix", usage="<NEW PREFIX/remove>")
    async def botconfig_prefix(self, ctx: commands.Context, *, new_prefix: str):
        """This command changes the bot prefix. The default prefix is `!`. Prefixes can be everything from symbols to
        words or a combination of the two, and can even include spaces, though they cannot start or end with spaces
        since Discord removes empty space at the start and end of messages. The prefix is saved across reboots. Setting
        the prefix to `remove` will remove the prefix. The bot will always listen to pings as if they were a prefix,
        regardless of if there is another prefix set or not."""
        self.bot.prefix = new_prefix if new_prefix.lower() != "remove" else None  # If 'remove', prefix is set to None.
        activity = Activity(type=ActivityType.listening,
                            name=f"prefix: {new_prefix}" if new_prefix.lower() != "remove" else "pings only")
        await self.bot.change_presence(activity=activity)  # Set status.
        async with self.bot.db.acquire() as conn:
            await conn.execute("UPDATE settings SET value = $1 WHERE key = 'prefix'",
                               new_prefix if new_prefix.lower() != "remove" else "")  # Empty string is no prefix.
        if new_prefix.lower() != "remove":  # Give feedback to user.
            await ctx.send(f"The bot prefix has successfully been changed to `{new_prefix}`.")
        else:
            await ctx.send("The bot is now only listens to pings.")

    @commands.is_owner()
    @botconfig.command(name="deletemessages", aliases=["deletemsgs", "deletecommands", "deletecmds", "delmessages",
                                                       "delmsgs", "delcommands", "delcmds"], usage="<enable/disable>")
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
    @botconfig.command(name="description", aliases=["desc"], usage="<DESCRIPTION/remove>")
    async def botconfig_description(self, ctx: commands.Context, *, description: str):
        """This command sets the bot description that is used by the about command. The description can technically be
        up to 2048 characters long, keep however in mind that Discord messages have a maximum length of 2000 characters
        characters, that normal messages have, in order to send the command that sets the description. If `remove` is
        sent along then the description will be removed. The special keyword `_prefix_` wil be replaced by the current
        bot prefix."""
        async with self.bot.db.acquire() as conn:
            if description.lower() == "remove":
                await conn.execute("UPDATE settings SET value = '' WHERE key = 'bot_description'")
                self.bot.modules[self.bot.user.name.lower()].description = ("No description for the bot found. "
                                                                            "Set description with `botconfig` command.")
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
            description = description.strip("```").strip()  # Remove code block.
            description = description.replace(" ", "\u202F")  # Prevent whitespace from disappearing.
            if len(description) > 1024:
                await ctx.send("Credits too long. Credits can be at most 1024 characters long.")
                return
            await conn.execute("UPDATE settings SET value = $1 WHERE key = 'additional_credits'", description)
            self.bot.modules[self.bot.user.name.lower()].credits = description
            await ctx.send("The additional credits section has been set.")

    @commands.has_permissions(administrator=True)
    @commands.group(invoke_without_command=True, name="module", aliases=["modules"],
                    usage="<list/load/unload/reload/error>")
    async def module(self, ctx: commands.Context):
        """This command can load, unload, reload and list available modules. It can also show any errors that occur
        during the loading process. Modules contain added functionality, such as commands. The intended purpose for
        modules is to extend the bot's functionality in semi-independent packages so that parts of the bot's
        functionality can be removed or restarted without affecting the rest of the bot's functionality. See the help
        text for the subcommands for more info."""
        raise commands.BadArgument(f"No subcommand given for {ctx.command.name}.")

    @commands.has_permissions(administrator=True)
    @module.command(name="list")
    async def module_list(self, ctx: commands.Context):
        """This command lists all currently loaded and available modules. For the bot to find new modules they need to
        be placed inside the modules folder inside the bot directory. Modules listed by this command can be loaded,
        unloaded and reloaded by the respective commands for this. See help text for `module load`, `module unload`
        and `module reload` for more info on this."""
        loaded_modules = [f"`{clean(ctx, mod.replace('modules.', ''))}`" for mod in self.bot.extensions.keys()
                          if mod != "core_commands"]  # Get all loaded modules bar core_functions.
        available_modules = [f'`{clean(ctx, mod.replace(".py", ""))}`' for mod in listdir("modules")
                             if mod.endswith(".py") and f"`{mod.replace('.py', '')}`" not in loaded_modules]
        await ctx.send(f"Loaded modules: {'None' if not loaded_modules else ', '.join(loaded_modules)}\n"
                       f"Available Modules: {'None' if not available_modules else ', '.join(available_modules)}")

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
        """This command unloads modules. When a loaded module is unloaded it's functionality will be removed. You can
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
    @module.command(name="error")
    async def module_error(self, ctx: commands.Context):
        """This command will show the last error that was encountered during the module load or reloading process. This
        information will also be printed to the console when the error first is encountered. This command retains this
        information until another error replaces it, or the bot shuts down."""
        if self.bot.last_module_error:
            await ctx.send(self.bot.last_module_error)
        else:
            await ctx.send("There have not been any errors loading modules since the last restart.")

    @commands.is_owner()
    @commands.group(invoke_without_command=True, name="default", aliases=["defaults"], usage="<add/remove/list>")
    async def default(self, ctx: commands.Context):
        """This command is used to add, remove or list default modules. Modules contain added functionality, such as
        commands. Default modules are loaded automatically when the bot starts and as such any functionality in them
        will be available as soon as the bot is online. For more info see the help text of the subcommands."""
        raise commands.BadArgument(f"No subcommand given for {ctx.command.name}.")

    @commands.is_owner()
    @default.command(name="list")
    async def default_list(self, ctx: commands.Context):
        """This command lists all current default modules. For more information on modules see the help text for the
        `module` command. All modules in this list start as soon as the bot is launched. For a list of all available or
        loaded modules see the `module list` command."""
        async with self.bot.db.acquire() as conn:
            result = await conn.fetch("SELECT module FROM default_modules")
        result = [f"`{clean(ctx, val['module'])}`" for val in result] if len(result) > 0 else None
        await ctx.send(f"Default modules: {'None' if result is None else ', '.join(result)}")

    @commands.is_owner()
    @default.command(name="add", usage="<MODULE NAME>")
    async def default_add(self, ctx: commands.Context, *, mod: str):
        """This command adds a module to the list of default modules. Modules in this list are loaded automatically
        once the bot starts. This command does not load modules if they are not already loaded until the bot is started
        the next time. For that, see the `module load` command. For a list of existing default modules, see the
        `default list` command. For more info on modules see the help text for the `module` command."""
        if f"{mod}.py" in listdir("modules"):  # Check if such a module even exists.
            async with self.bot.db.acquire() as conn:
                response = await conn.execute("INSERT INTO default_modules VALUES ($1)", mod)
            if not response:  # If no error occurred while adding the module to the database report back.
                await ctx.send(f"The `{clean(ctx, mod)}` module is now a default module.")
            else:
                await ctx.send(f"The `{clean(ctx, mod)}` module is already a default module.")
        else:
            await ctx.send(f"No `{clean(ctx, mod)}` module was found.")

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
                await ctx.send(f"Removed `{clean(ctx, mod)}` module from default modules.")
            else:
                await ctx.send(f"No `{clean(ctx, mod)}` module in default modules.")

    @commands.has_permissions(administrator=True)
    @commands.group(invoke_without_command=True, name="command", aliases=["commands"],
                    usage="<enable/disable/show/hide>")
    async def command(self, ctx: commands.Context):
        """This command disables, enables, hides and shows other commands. Hiding commands means they don't show up in
        the overall help command list. Disabling a command means it can't be used. Disabled commands also do not show
        up in the overall help command list and the specific help text for the command will not be viewable. Core
        commands cannot be disabled. These settings are saved across restarts."""
        raise commands.BadArgument(f"No subcommand given for {ctx.command.name}.")

    async def _command_get_state(self, command: commands.Command) -> int:
        """Helper function for command command that gets the state of the command."""
        async with self.bot.db.acquire() as conn:
            cog_com_name = f"{command.cog.__class__.__name__ + '.' if command.cog else ''}{command.name}"
            response = await conn.fetchval("SELECT state FROM command_states WHERE command = $1", cog_com_name)
            if response is None:
                await conn.execute("INSERT INTO command_states VALUES ($1, $2)", cog_com_name, 0)
                response = 0
            return response

    async def _command_set_state(self, command: commands.Command, state: int):
        """Helper function for command command that sets the state of the command."""
        async with self.bot.db.acquire() as conn:
            await conn.execute("UPDATE command_states SET state = $1 WHERE command = $2",
                               state, f"{command.cog.__class__.__name__ + '.' if command.cog else ''}{command.name}")

    @commands.has_permissions(administrator=True)
    @command.command(name="enable", usage="<COMMAND NAME>")
    async def command_enable(self, ctx: commands.Context, *, command_name: str):
        """This command enables commands which have previously been disabled. This will allow them to be used again.
        It will also add the command back into the list of commands shown by the help command and re-enable the
        viewing of it's help text given the command has help text and it has not otherwise been hidden."""
        if command_name in self.bot.all_commands.keys():  # Check if command exists and get it's state.
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
        """This command can disable other commands. Disabled commands cannot be used and are removed from the
        list of commands shown by the help command. The command's help text will also not be viewable. Core
        commands cannot be disabled. Disabled commands can be re-enabled with the `command enable` command."""
        if command_name in self.bot.all_commands.keys():  # Check if command exists and get it's state.
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if command_name in self.bot.help.keys() and self.bot.help[command_name].category.lower() == "core":
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
        """This command will show commands which have previously been hidden, reversing the hiding of the
        command. This will add the command back into the list of commands shown by the help command. This
        will not re-enable the command if it has been disabled. Showing disabled commands alone will not
        be enough to re-add them to the help list since disabling them also hides them from the help list.
        See the `command enable` command to re-enable disabled commands."""
        if command_name in self.bot.all_commands.keys():  # Check if command exists and get it's state.
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
        """This command will hide commands from the list of commands shown by the help command. It will
        not disable the viewing of the help text for the command if someone already knows it's name.
        Commands who have been hidden can be un-hidden with the `command show` command."""
        if command_name in self.bot.all_commands.keys():  # Check if command exists and get it's state.
            state = await self._command_get_state(self.bot.all_commands[command_name])
            if self.bot.all_commands[command_name].hidden:  # Check if command is already hidden.
                await ctx.send(f"The `{clean(ctx, command_name)}` command is already hidden.")
            else:
                self.bot.all_commands[command_name].hidden = True
                await self._command_set_state(self.bot.all_commands[command_name], 1 if state == 0 else 3)
                await ctx.send(f"The `{clean(ctx, command_name)}` command is now hidden.")
        else:
            await ctx.send(f"No `{clean(ctx, command_name)}` command found.")

    @commands.command(name="about", alias=["info"], usage="(MODULE NAME)")
    async def about(self, ctx: commands.Context, *, module_name: str = None):
        """This command gives information about modules, such as a description, authors, and other credits. Module
        authors can even add a small image to be displayed alongside this info. If no module name is given or the
        bot's name is used then information about the bot itself is shown."""
        if module_name is None:  # If no value is passed along we display the about page for the bot itself.
            if self.bot.user.name.lower() in self.bot.modules.keys():  # Check if the bot has an entry.
                embed = self.bot.modules[self.bot.user.name.lower()].make_about_embed(ctx)  # Make and send response.
                await ctx.send(embed=embed)
            else:
                raise RuntimeError(f"Bot info module not found.")
        elif module_name.lower() in self.bot.modules.keys():  # Check if the passed along value has an entry.
            embed = self.bot.modules[module_name.lower()].make_about_embed(ctx)  # Make and send response.
            await ctx.send(embed=embed)
        else:
            response = f"No information for `{clean(ctx, module_name)}` module was found."
            if module_name not in [mod.replace('modules.', '') for mod in self.bot.extensions.keys()]:
                response += "\nAdditionally no module with this name is loaded."
            await ctx.send(response)

    @commands.command(name="usage", usage="(MODULE NAME)")
    async def usage(self, ctx: commands.Context, *, module_name: str = None):
        """This command explains how a module is intended to be used. If no module name is given it will
        show some basic information about usage of the bot itself."""
        if module_name is None or module_name.lower() in [self.bot.user.name.lower(), "core_commands", "core commands"]:
            pref = self.bot.get_bot_prefix()
            response = (f"**How To Use:**\nThis bot features a variety of commands. You can get a list of all commands "
                        f"you have access to with the `{pref}help` command. In order to use a command your message has "
                        f"to start with the *bot prefix*, the bot prefix is currently set to `{pref}`. Simply type "
                        f"this prefix, followed by a command name, and you will run the command. For more information "
                        f"on individual commands, run `{pref}help` followed by the command name. This will give you "
                        f"info on the command, along with some examples of it and any aliases the command might have. "
                        f"You might not have access to all commands everywhere, the help command will only tell you "
                        f"about commands you have access to in that channel, and commands you can run only in the DMs "
                        f"with the bot. DM only commands will be labeled as such by the help command.\n\nSome commands "
                        f"accept extra input, an example would be how the help command accepts a command name. You can "
                        f"usually see an example of how the command is used on the command's help page. If you use a "
                        f"command incorrectly by missing some input or sending invalid input, it will send you the "
                        f"expected input. This is how to read the expected input:\n\nArguments encased in `<>` are "
                        f"obligatory.\nArguments encased in `()` are optional and can be skipped.\nArguments written "
                        f"in all uppercase are placeholders like names.\nArguments not written in uppercase are exact "
                        f"values.\nIf an argument lists multiple things separated by `/` then any one of them is valid."
                        f"\nThe `<>` and `()` symbols are not part of the command.\n\nSample expected input: `{pref}"
                        f"about (MODULE NAME)`\nHere `{pref}about` is the command, and it takes an optional argument. "
                        f"The argument is written in all uppercase, so it is a placeholder. In other words you are "
                        f"expected to replace 'MODULE NAME' with the actual name of a module. Since the module name is "
                        f"optional, sending just `{pref}about` is also a valid command.")
            await ctx.send(response)
        elif module_name.lower() in self.bot.modules.keys():
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
            if module_name not in [mod.replace('modules.', '') for mod in self.bot.extensions.keys()]:
                response += "\nAdditionally no module with this name is loaded."
            await ctx.send(response)

    @commands.is_owner()
    @commands.command(name="shutdown", aliases=["goodbye", "goodnight"], usage="(TIME BEFORE SHUTDOWN)")
    async def shutdown(self, ctx: commands.Context, countdown: str = None):
        """This command turns the bot off. A delay can be set causing the bot to wait before shutting down. The time
        uses a format of numbers followed by units, see examples for details. Times supported are weeks (w), days (d),
        hours (h), minutes (m) and seconds (s), and even negative numbers. For this command the delay must be between
        0 seconds and 24 hours. Supplying no time will cause the bot to shut down immediately. Once started, a shutdown
        cannot be stopped."""
        if countdown is None:  # If no time is passed along, shut down the bot immediately.
            await ctx.send("Goodbye!")
            await self.bot.close()
            await self.bot.db.close()
        else:
            try:
                time = tbb.parse_time(countdown, 0, 86400, True)  # Parse time to get time in seconds.
                await ctx.send(f"Shutdown will commence in {time} seconds.")
                await asleep(time)
                await ctx.send("Shutting down!")
                await self.bot.logout()
                await self.bot.db.close()
            except ValueError as e:  # If time parser encounters error, and error is exceeding of limit, report back.
                if str(e) in ["Time too short.", "Time too long."]:
                    await ctx.send("The time for this command must be between 0 seconds to 24 hours.")
                else:  # If another error is encountered, log to console.
                    await ctx.send("The time could not be parsed correctly. Check the help command for shutdown for "
                                   "examples of times.")
                    print(f'[{tbb.cur_time()}] {ctx.message.author.id}: {str(e)}')
