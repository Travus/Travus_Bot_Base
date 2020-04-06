from asyncio import sleep as asleep  # For waiting asynchronously.
from os import listdir  # To check files on disk.

from discord import Embed, Activity, ActivityType  # For bot status
from discord.ext import commands  # For implementation of bot commands.

import functions as func  # Shared function library.
from functions import clean  # Shorthand for cleaning output.


def setup(bot: func.TravusBotBase):
    """Setup function ran when module is loaded."""
    bot.add_cog(CoreFunctionalityCog(bot))  # Add cog and command help info.
    bot.add_command_help(CoreFunctionalityCog.prefix, "Core", None, ["$", "bot!", "bot ?", "remove"])
    bot.add_command_help(CoreFunctionalityCog.module, "Core", {"perms": ["Administrator"]}, ["list", "load", "unload", "reload"])
    bot.add_command_help(CoreFunctionalityCog.module_list, "Core", {"perms": ["Administrator"]}, [""])
    bot.add_command_help(CoreFunctionalityCog.module_load, "Core", {"perms": ["Administrator"]}, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.module_unload, "Core", {"perms": ["Administrator"]}, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.module_reload, "Core", {"perms": ["Administrator"]}, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.default, "Core", None, ["list", "add", "remove"])
    bot.add_command_help(CoreFunctionalityCog.default_list, "Core", None, [""])
    bot.add_command_help(CoreFunctionalityCog.default_add, "Core", None, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.default_remove, "Core", None, ["fun", "economy"])
    bot.add_command_help(CoreFunctionalityCog.delete_messages, "Core", {"perms": ["Administrator"]}, ["enable", "y", "disable", "n"])
    bot.add_command_help(CoreFunctionalityCog.command, "Core", {"perms": ["Administrator"]}, ["enable", "disable", "show", "hide"])
    bot.add_command_help(CoreFunctionalityCog.command_enable, "Core", {"perms": ["Administrator"]}, ["balance", "pay"])
    bot.add_command_help(CoreFunctionalityCog.command_disable, "Core", {"perms": ["Administrator"]}, ["balance", "pay"])
    bot.add_command_help(CoreFunctionalityCog.command_show, "Core", {"perms": ["Administrator"]}, ["module", "balance"])
    bot.add_command_help(CoreFunctionalityCog.command_hide, "Core", {"perms": ["Administrator"]}, ["module", "balance"])
    bot.add_command_help(CoreFunctionalityCog.about, "Core", None, ["", "fun"])
    bot.add_command_help(CoreFunctionalityCog.usage, "Core", None, ["", "dev"])
    bot.add_command_help(CoreFunctionalityCog.shutdown, "Core", None, ["", "1h", "1h30m", "10m-30s", "2m30s"])


def teardown(bot: func.TravusBotBase):
    """Teardown function ran when module is unloaded."""
    bot.remove_cog("CoreFunctionalityCog")  # Remove cog and command help info.
    bot.remove_command_help(CoreFunctionalityCog)


class CoreFunctionalityCog(commands.Cog):
    """Cog that holds default functionality."""

    def __init__(self, bot: func.TravusBotBase):
        """Initialization function loading bot object for cog."""
        self.bot = bot

    async def _module_operation(self, ctx: commands.Context, operation: str, mod: str):
        """To avoid code duplication in the except blocks all module command functionality is grouped together."""
        old_help = dict(self.bot.help)  # Save old help and module info in case something goes wrong and needs to be restored.
        old_modules = dict(self.bot.modules)
        self.bot.extension_ctx = ctx  # Save context in case loaded module has use for it.
        try:
            if operation == "load":  # Try loading the module.
                if f"{mod}.py" in listdir("modules"):  # Check if module is there preemptive to differentiate errors more easily.
                    self.bot.load_extension(f"modules.{mod}")
                    await self.bot.update_command_states()
                    await ctx.send(f"Module `{clean(ctx, mod)}` successfully loaded.")
                    print(f"[{func.cur_time()}] {ctx.message.author.id} loaded '{mod}' module.")
                else:
                    await ctx.send(f"No `{clean(ctx, mod)}` module was found.")
            elif operation == "unload":
                self.bot.unload_extension(f"modules.{mod}")
                await ctx.send(f"Module `{clean(ctx, mod)}` successfully unloaded.")
                print(f"[{func.cur_time()}] {ctx.message.author.id} unloaded '{mod}' module.")
            elif operation == "reload":  # Try reloading the module.
                if f"{mod}.py" in listdir("modules"):  # Check if module is even still there before we reload.
                    self.bot.reload_extension(f"modules.{mod}")
                    await self.bot.update_command_states()
                    await ctx.send(f"Module `{clean(ctx, mod)}` successfully reloaded.")
                    print(f"[{func.cur_time()}] {ctx.message.author.id} reloaded '{mod}' module.")
                else:
                    if mod in self.bot.modules:
                        await ctx.send(f"The `{clean(ctx, mod)}` module file is no longer found on disk. Reload canceled.")
                    else:
                        await ctx.send(f"No `{clean(ctx, mod)}` module was found.")
        except commands.ExtensionAlreadyLoaded:  # If module was already loaded.
            await ctx.send(f"The `{clean(ctx, mod)}` module was already loaded.")
        except commands.ExtensionNotLoaded:  # If module wasn't loaded to begin with.
            await ctx.send(f"No `{clean(ctx, mod)}` module is loaded.")
        except Exception as e:  # If module crashed while loading, restore old help and module info.
            self.bot.help = old_help
            self.bot.modules = old_modules
            await ctx.send("**Error! Something went really wrong! Contact module maintainer.**\nError printed to console and stored in module error command.")
            if isinstance(e, commands.ExtensionNotFound):  # Clarify error further in case it was an import error.
                e = e.__cause__
            print(f"[{func.cur_time()}] {ctx.message.author.id} tried loading '{mod}' module, and it failed:\n\n{str(e)}")
            self.bot.last_module_error = f"The `{clean(ctx, mod)}` module failed while loading. The error was:\n\n{clean(ctx, str(e))}"
        finally:  # Reset context as loading has concluded.
            self.bot.extension_ctx = None

    @commands.is_owner()
    @commands.command(name="prefix", usage="<NEW PREFIX/remove>")
    async def prefix(self, ctx: commands.Context, *, new_prefix: str):
        """This command changes the bot prefix. The default prefix is `!`. Prefixes can be everything from symbols to words or a
        combination of the two, and can even include spaces, though they cannot start or end with spaces since Discord removes empty
        space at the start and end of messages. The prefix is saved across reboots. Setting the prefix to `remove` will remove the prefix.
        The bot will always listen to pings as if they were a prefix, regardless of if there is another prefix set or not."""
        self.bot.prefix = new_prefix if new_prefix.lower() != "remove" else None  # Is user sends 'remove' prefix is set to None.
        await func.db_set(self.bot.db_con, "UPDATE settings SET value = ? WHERE flag = 'prefix'", (new_prefix if new_prefix.lower() != "remove" else "",))  # Database entry is empty if no prefix.
        await self.bot.change_presence(activity=Activity(type=ActivityType.listening, name=f"prefix: {new_prefix}" if new_prefix.lower() != "remove" else "pings only"))  # Set status.
        if new_prefix.lower() != "remove":  # Give feedback to user.
            await ctx.send(f"The bot prefix has successfully been changed to `{new_prefix}`.")
        else:
            await ctx.send("The bot is now only listens to pings.")

    @commands.has_permissions(administrator=True)
    @commands.group(invoke_without_command=True, name="module", aliases=["modules"], usage="<list/load/unload/reload/error>")
    async def module(self, ctx: commands.Context):
        """This command can load, unload, reload and list available modules. It can also show any errors that occur during the loading
        process. Modules contain added functionality, such as commands. The intended purpose for modules is to extend the bot's functionality
        in semi-independent packages so that parts of the bot's functionality can be removed or restarted without affecting the rest of the
        bot's functionality. See the help text for the subcommands for more info."""
        raise commands.BadArgument(f"No sub-command given for {ctx.command.name}.")

    @commands.has_permissions(administrator=True)
    @module.command(name="list")
    async def module_list(self, ctx: commands.Context):
        """This command lists all currently loaded and available modules. For the bot to find new modules they need to be placed
        inside the modules folder inside the bot directory. Modules listed by this command can be loaded, unloaded and reloaded by
        the respective commands for this. See help text for `module load`, `module unload` and `module reload` for more info on this."""
        loaded_modules = [f"`{clean(ctx, mod.replace('modules.', ''))}`" for mod in self.bot.extensions.keys() if mod != "core_commands"]  # Get all loaded modules bar core_functions.
        available_modules = [f'`{clean(ctx, mod.replace(".py", ""))}`' for mod in listdir("modules") if mod.endswith(".py") and f"`{mod.replace('.py', '')}`" not in loaded_modules]
        await ctx.send(f"Loaded modules: {'None' if not loaded_modules else ', '.join(loaded_modules)}\nAvailable Modules: {'None' if not available_modules else ', '.join(available_modules)}")

    @commands.has_permissions(administrator=True)
    @module.command(name="load", aliases=["l"], usage="<MODULE NAME>")
    async def module_load(self, ctx: commands.Context, *, mod: str):
        """This command loads modules. Modules should be located inside the module folder in the bot directory. The `module list`
        command can be used to show all modules available for loading. Once a module is loaded the functionality defined in the
        module file will be added to the bot. If an error is encountered during the loading process the user will be informed and
        the `module error` command can then be used to see the error details. The module will then not be loaded. If you want modules
        to stay loaded after restarts, see the `default` command."""
        await self._module_operation(ctx, "load", mod)

    @commands.has_permissions(administrator=True)
    @module.command(name="unload", aliases=["ul"], usage="<MODULE NAME>")
    async def module_unload(self, ctx: commands.Context, *, mod: str):
        """This command unloads modules. When a loaded module is unloaded it's functionality will be removed. You can use the
        `module list` command to see all currently loaded modules. This will not prevent default modules from being loaded when
        the bot starts. See the `default` command for removing modules starting with the bot."""
        await self._module_operation(ctx, "unload", mod)

    @commands.has_permissions(administrator=True)
    @module.command(name="reload", aliases=["rl"], usage="<MODULE NAME>")
    async def module_reload(self, ctx: commands.Context, *, mod: str):
        """This command reloads a module that is currently loaded. This will unload and load the module in one command. If
        the module is no longer present or the loading process encounters an error the module will not be reloaded and the
        functionality from before the reload will be retained and the user informed, the `module error` command can then be
        used to see the error details. You can use the module list command to see all currently loaded modules."""
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
        """This command is used to add, remove or list default modules. Modules contain added functionality, such as commands.
        Default modules are loaded automatically when the bot starts and as such any functionality in them will be available
        as soon as the bot is online. For more info see the help text of the subcommands."""
        raise commands.BadArgument(f"No sub-command given for {ctx.command.name}.")

    @commands.is_owner()
    @default.command(name="list")
    async def default_list(self, ctx: commands.Context):
        """This command lists all current default modules. For more information on modules see the help text for the `module`
        command. All modules in this list start as soon as the bot is launched. For a list of all available or loaded modules
        see the `module list` command."""
        result = await func.db_get_all(self.bot.db_con, "SELECT module FROM default_modules", ())  # Get all default modules from database and display them.
        result = [f"`{clean(ctx, val[0])}`" for val in result] if len(result) > 0 else None
        await ctx.send(f"Default modules: {'None' if result is None else ', '.join(result)}")

    @commands.is_owner()
    @default.command(name="add", usage="<MODULE NAME>")
    async def default_add(self, ctx: commands.Context, *, mod: str):
        """This command adds a module to the list of default modules. Modules in this list are loaded automatically once the
        bot starts. This command does not load modules if they are not already loaded until the bot is started the next time.
        For that, see the `module load` command. For a list of existing default modules, see the `default list` command. For more
        info on modules see the help text for the `module` command."""
        if f"{mod}.py" in listdir("modules"):  # Check if such a module even exists.
            response = await func.db_set(self.bot.db_con, "INSERT INTO default_modules VALUES (?)", (mod,))  # Add the default module to the database.
            if not response:  # If no error occurred while adding the module to the database report back.
                await ctx.send(f"The `{clean(ctx, mod)}` module is now a default module.")
            else:  # If an error occurred while adding the module to the database, then it already existed. Report error.
                await ctx.send(f"The `{clean(ctx, mod)}` module is already a default module.")
        else:
            await ctx.send(f"No `{clean(ctx, mod)}` module was found.")

    @commands.is_owner()
    @default.command(name="remove", usage="<MODULE NAME>")
    async def default_remove(self, ctx: commands.Context, *, mod: str):
        """This command removes a module from the list of default modules. Once removed from this list the module will no
        longer automatically be loaded when the bot starts. This command will not unload commands that are already loaded.
        For that, see the `module unload` command. For a list of existing default modules, see the `default list` command.
        For more info on modules see the help text for the `module` command."""
        result = await func.db_get_one(self.bot.db_con, "SELECT module FROM default_modules WHERE module = ?", (mod,))  # See if the module is a default module to begin with.
        if result:
            await func.db_set(self.bot.db_con, "DELETE FROM default_modules WHERE module = ?", (mod,))  # Remove it from the default module database.
            await ctx.send(f"Removed `{clean(ctx, mod)}` module from default modules.")
        else:
            await ctx.send(f"No `{clean(ctx, mod)}` module in default modules.")  # Report back if it isn't in the database to begin with.

    @commands.has_permissions(administrator=True)
    @commands.command(name="deletemessages", aliases=["deletemsgs", "deletecommands", "deletecmds", "delmessages", "delmsgs", "delcommands", "delcmds"], usage="<enable/disable>")
    async def delete_messages(self, ctx: commands.Context, operation: str):
        """This command sets the behaviour for deletion of command triggers. If this is enabled then messages that trigger
        commands will be deleted. Is this is disabled then the bot will not delete messages that trigger commands. Per
        default this is enabled. This setting is saved across restarts."""
        op = operation.lower()
        if op in ["enable", "true", "on", "yes", "y", "+", "1"]:  # Values interpreted as true.
            await func.db_set(self.bot.db_con, "UPDATE settings SET value = ? WHERE flag = ?", ("1", "delete_messages"))  # Update database.
            self.bot.delete_messages = 1
            self.bot.delete_messages = 1
            await ctx.send("Now deleting user commands.")
        elif op in ["disable", "false", "off", "no", "n", "-", "0"]:  # Values interpreted as false.
            await func.db_set(self.bot.db_con, "UPDATE settings SET value = ? WHERE flag = ?", ("0", "delete_messages"))  # Update database.
            self.bot.delete_messages = 0
            await ctx.send("No longer deleting user commands.")
        else:
            raise commands.BadArgument("Operation not supported.")

    @commands.has_permissions(administrator=True)
    @commands.group(invoke_without_command=True, name="command", aliases=["commands"], usage="<enable/disable/show/hide>")
    async def command(self, ctx: commands.Context):
        """This command disables, enables, hides and shows other commands. Hiding commands means they don't show up in the
        overall help command list. Disabling a command means it can't be used. Disabled commands also do not show up in the
        overall help command list and the specific help text for the command will not be viewable. Core commands cannot be
        disabled. These settings are saved across restarts."""
        raise commands.BadArgument(f"No sub-command given for {ctx.command.name}.")

    async def _command_get_state(self, command_name: str) -> int:
        """Helper function for command command that gets the state of the command."""
        response = await func.db_get_one(self.bot.db_con, "SELECT state FROM command_states WHERE command = ?", (self.bot.all_commands[command_name].name,))  # Get command state frm database.
        if response is None:
            await func.db_set(self.bot.db_con, "INSERT INTO command_states VALUES (?, ?)", (command_name, 0))  # Set to visible and enabled if no state is set for command.
            response = (0,)
        return response[0]

    @commands.has_permissions(administrator=True)
    @command.command(name="enable", usage="<COMMAND NAME>")
    async def command_enable(self, ctx: commands.Context, *, command_name: str):
        """This command enables commands which have previously been disabled. This will allow them to be used again.
        It will also add the command back into the list of commands shown by the help command and re-enable the
        viewing of it's help text given the command has help text and it has not otherwise been hidden."""
        if command_name in self.bot.all_commands.keys():  # Check if command exists and get it's state.
            state = await self._command_get_state(command_name)
            if self.bot.all_commands[command_name].enabled:  # If command is already enabled, report back.
                await ctx.send(f"The `{clean(ctx, command_name)}` command is already enabled.")
            else:
                state = 0 if state == 2 else 1  # Set new state, update database and enable command.
                self.bot.all_commands[command_name].enabled = True
                await func.db_set(self.bot.db_con, "UPDATE command_states SET state = ? WHERE command = ?", (state, self.bot.all_commands[command_name].name))
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
            state = await self._command_get_state(command_name)
            if command_name in self.bot.help.keys() and self.bot.help[command_name].category.lower() == "core":  # Check if command is in core category.
                await ctx.send("Core commands cannot be disabled.")
            else:
                if not self.bot.all_commands[command_name].enabled:  # Check if the command is already disabled.
                    await ctx.send(f"The `{clean(ctx, command_name)}` command is already disabled.")
                else:
                    state = 2 if state == 0 else 3  # Set new state, update database and enable command.
                    self.bot.all_commands[command_name].enabled = False
                    await func.db_set(self.bot.db_con, "UPDATE command_states SET state = ? WHERE command = ?", (state, self.bot.all_commands[command_name].name))
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
            state = await self._command_get_state(command_name)
            if not self.bot.all_commands[command_name].hidden:  # Check if command i already visible.
                await ctx.send(f"The `{clean(ctx, command_name)}` command is already shown.")
            else:
                state = 0 if state == 1 else 2  # Set new state, update database and enable command.
                self.bot.all_commands[command_name].hidden = False
                await func.db_set(self.bot.db_con, "UPDATE command_states SET state = ? WHERE command = ?", (state, self.bot.all_commands[command_name].name))
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
            state = await self._command_get_state(command_name)
            if self.bot.all_commands[command_name].hidden:  # Check if command is already hidden.
                await ctx.send(f"The `{clean(ctx, command_name)}` command is already hidden.")
            else:
                state = 1 if state == 0 else 3  # Set new state, update database and enable command.
                self.bot.all_commands[command_name].hidden = True
                await func.db_set(self.bot.db_con, "UPDATE command_states SET state = ? WHERE command = ?", (state, self.bot.all_commands[command_name].name))
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
                embed = self.bot.modules[self.bot.user.name.lower()].make_embed(ctx)  # Make and send response.
                await ctx.send(embed=embed)
            else:
                raise RuntimeError(f"Bot info module not found.")
        elif module_name.lower() in self.bot.modules.keys():  # Check if the passed along value has an entry.
            embed = self.bot.modules[module_name.lower()].make_embed(ctx)  # Make and send response.
            await ctx.send(embed=embed)
        else:
            response = f"No information for `{clean(ctx, module_name)}` module was found."  # Prepare error message for missing entry.
            if module_name not in [mod.replace('modules.', '') for mod in self.bot.extensions.keys()]:
                response += "\nAdditionally no module with this name is loaded."  # Add additional info to the error if no such module is loaded.
            await ctx.send(response)

    @commands.command(name="usage", usage="(MODULE NAME)")
    async def usage(self, ctx: commands.Context, *, module_name: str = None):
        """This command explains how a module is intended to be used. If no module name is given it will
        show some basic information about usage of the bot itself."""
        if module_name is None:
            pref = self.bot.get_bot_prefix()
            response = f"**How To Use:**\nThis bot features a variety of commands. You can get a list of all commands " \
                       f"you have access to with the `{pref}help` command. In order to use a command your message has " \
                       f"to start with the *bot prefix*, the bot prefix is currently set to `{pref}`. Simply type this " \
                       f"prefix, followed by a command name, and you will run the command. For more information on " \
                       f"individual commands, run `{pref}help` followed by the command name. This will give you info on " \
                       f"the command, along with some examples of it and any aliases the command might have. You might " \
                       f"not have access to all commands everywhere, the help command will only tell you about commands " \
                       f"you have access to in that channel, and commands you can run only in the DMs with the bot. " \
                       f"DM only commands will be labeled as such by the help command.\n\nSome commands accept extra " \
                       f"input, an example would be how the help command accepts a command name. You can usually see an " \
                       f"example of how the command is used on the command's help page. If you use a command incorrectly " \
                       f"by missing some input or sending invalid input, it will send you the expected input. This is " \
                       f"how to read the expected input:\n\nArguments encased in `<>` are obligatory.\nArguments encased " \
                       f"in `()` are optional and can be skipped.\nArguments written in all uppercase are placeholders " \
                       f"like names.\nArguments not written in uppercase are exact values.\nIf an argument lists multiple " \
                       f"things separated by `/` then any one of them is valid.\nThe `<>` and `()` symbols are not part " \
                       f"of the command.\n\nSample expected input: `{pref}about (MODULE NAME)`\nHere `{pref}about` is the " \
                       f"command, and it takes an optional argument. The argument is written in all uppercase, so it is a " \
                       f"placeholder. In other words you are expected to replace 'MODULE NAME' with the actual name of a " \
                       f"module. Since the module name is optional, sending just `{pref}about` is also a valid command."
            await ctx.send(response)
        elif module_name.lower() in self.bot.modules.keys():
            usage = self.bot.modules[module_name.lower()].usage
            if isinstance(usage, str):
                await ctx.send(usage if len(usage) < 1950 else f"{usage[:1949]}...")
            elif isinstance(usage, Embed):
                await ctx.send(embed=usage)
            else:
                await ctx.send(f"The `{clean(ctx, module_name)}` module does not have its usage defined.")
        else:
            response = f"No information for `{clean(ctx, module_name)}` module was found."  # Prepare error message for missing entry.
            if module_name not in [mod.replace('modules.', '') for mod in self.bot.extensions.keys()]:
                response += "\nAdditionally no module with this name is loaded."  # Add additional info to the error if no such module is loaded.
            await ctx.send(response)

    @commands.is_owner()
    @commands.command(name="shutdown", aliases=["goodbye", "goodnight"], usage="(TIME BEFORE SHUTDOWN)")
    async def shutdown(self, ctx: commands.Context, countdown: str = None):
        """This command turns the bot off. A delay can be set causing the bot to wait before shutting down. The time
        uses a format of numbers followed by units, see examples for details. Times supported are weeks (w), days (d),
        hours (h), minutes (m) and seconds (s), and even negative numbers. For this command the delay must be between
        0 seconds and 2 hours. Supplying no time will cause the bot to shut down immediately. Once started, a shutdown
        cannot be stopped."""
        if countdown is None:  # If no time is passed along, shut down the bot immediately.
            await ctx.send("Goodbye!")
            await self.bot.close()
            exit(0)
        else:
            try:
                time = func.parse_time(countdown, 0, 7200, True)  # Parse time to get time in seconds, error if time exceeds limits.
                await ctx.send(f"Shutdown will commence in {time} seconds.")  # Report back, wait and shutdown.
                await asleep(time)
                await ctx.send("Shutting down!")
                await self.bot.close()
                exit(0)
            except ValueError as e:  # If time parser encounters error, and error is exceeding of limit, report back.
                if str(e) in ["Time too short.", "Time too long."]:
                    await ctx.send("The time for this command must be between 0 seconds to 2 hours.")
                else:  # If another error is encountered, log to console.
                    await ctx.send("The time could not be parsed correctly. Check the help command for shutdown for examples of times.")
                    print(f'[{func.cur_time()}] {ctx.message.author.id}: {str(e)}')

# ToDo: Add usage command to README
