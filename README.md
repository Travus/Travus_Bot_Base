# NOTE: The README is currently not up-to-date, and will be updated as a GitHub wiki soon.

<p align="center"><img src="https://i.imgur.com/EekoTeO.png" alt="Travus Bot Base" width="450"/><br/><br/></p>

This is the Travus Bot Base, a basic starting-point for Discord bots using [Discord.py](https://github.com/Rapptz/discord.py). The bot comes with all the basic functionality you need and is intended to be further extended with functionality specific to your needs. The basic included functionality is listed below. Some useful quality of life functions to make development of additional functions are also included. The bot can technically work in multiple servers at once, but all settings and modules will be global across all servers. It is not intended for use in multiple servers at once, for this, run multiple separate instances of the bot if things do not work as expected.

The intended use-case for this bot base is to be used by small to medium servers as a starting-point to build a bot for their server from. All essential functions such as changing prefix and such are already set up, and additional functionality can be added via 'modules' which can be loaded and unloaded on-the-fly without restarting the bot or disrupting other modules that might be loaded. This bot is not very feature backed, as it is intended to be a starting point to make you own custom bots from, as such it does not come with any bells and whistles outside of generic commands for maintaining bot-wide functionality such as prefixes, command help, turning commands on and off, adding and removing additional functions, and so forth.

### Table of Contents

- [Installation](#installation)
- [Existing Functionality](#existing-functionality)
- [Making Your Own Functionality](#making-your-own-functionality)
- [Additional Customization](#additional-customization)
- [Contact & Credits](#contact--credits)

---
### Installation

> **_NOTE:_**  This bot runs on, and requires [Python](https://www.python.org/) 3.6+

**1: Create a Discord Application with Bot**  
First, you need to set up a Discord Bot account. In order to do this, you need to go to [Discord's Developer Portal](https://discordapp.com/developers/applications/). From here, press the *New Application* button in the top right, and give it a name. Next, on the panel to the left, navigate to the *Bot* tab. Here, click the *Add Bot* button on the right, and confirm.

**2: Set Bot Name, Image & Get the Token**  
Here you can choose the bot's name, and profile image. You can also choose whether only you, or everyone with the invite link - which we will come back to - can invite the bot. Lastly, you can click the *Click to Reveal Token* button, to see your bot token. We will use this token later, so make a note of it. Also make extra sure this token does not get into the wrong hands, as everyone with the token will be able to run code using your bot.

**3: Invite the Bot**  
Lastly, go back to the *General Information* page via the panel on the left. Take the 18 digit number listed as *CLIENT ID* from here, and insert it into the *Client ID* field on [this website](https://discordapi.com/permissions.html). Check the permissions you want to give your bot, and click the link it generates at the bottom of the page. Using this you can invite your bot to your server.

**4: (Optional) Set Up a Virtual Environment**  
It is recommended to run your bot in it's own virtual environment. You should really run most of your projects in separate environments. A virtual environment acts as it's own installation of python, separate from any other virtual environments or installations of Python. This way you can have different projects using different versions of dependencies. If you run all your projects in the same environment you will sooner or later run into issues where different libraries require different versions of the same packages from one another. One way of dealing with this is by using [venv](https://docs.python.org/3/library/venv.html), though alternatives such as pipenv do exist. This step is technically optional, though heavily recommended.

**5: Installing Discord.py**  
Once you have created and activated a virtual environment (Or are following along without one.) we need to install [Discord.py](https://github.com/Rapptz/discord.py) by [Rapptz](https://github.com/Rapptz). This can be done with one of the the following command-line commands:  
Without voice support: `python -m pip install -U discord.py`  
With voice support: `python -m pip install -U discord.py[voice]`

**6: Download the Travus Bot Base**  
There are two ways of downloading the bot base. Since the bot is only a base intended to be expanded upon via modules, it is recommended to use this repository as a template and clone your own version. If you do not wish to use GitHub or git, you can simply download the zipped version and unzip it.

**7: Set Up the Bot**  
Once you have a local (unzipped) copy of the bot base, you can start the *setup.py* file. The first thing you will be asked to is to enter your bot token we found in step 2. It will then ask you to enter a description of your bot, and a list of additional credits. This information will be displayed alongside the bot's profile image, and credits for the bot base when the *about* command is used. Separate entries for this command can be added for modules to credit module authors and display information about modules. See the [section about modules](#making-your-own-functionality) for more information on this.

---
### Existing Functionality
This section will go over the included functionality, it starts with a basic description of the functionality, then lists commands associated with that functionality and explains what they do. Words fully capitalized in the commands are placeholders for real values, words in lower case are set keywords. When sending incomplete commands to the bot it will respond with the syntax it expected as well, this syntax uses the same convention for upper and lower case words and additionally marks required values with <> and optional ones with (). This list of commands will not include these markings as all commands listed here will run given the placeholders are substituted for real values.

**Changing Prefix**  
*A bot prefix is something that users have to start commands with, in order for the bot to recognize it as a command.* The bot base supports both mentioning (pinging) the bot, as well an 1 more additional prefix which can be set by the bot owner and is changeable on-the-fly. It can also be removed at which point the bot will only respond when mentioned. The bot will display the current prefix in it's status. If the secondary prefix has been removed it will indicate only responding to mentions. The default prefix is `!`.

`prefix NEW_PREFIX`  
This will set the prefix to some text or symbol. The new prefix can be multiple characters long, and supports spaces inside the prefix, but not at the start or end of it.

`prefix remove`  
This will remove the secondary prefix until it is set to something new. Doing this will result in the bot only responding when mentioned.

**Deleting Command Triggers**  
I have seen debates between if messages that triggers commands should be deleted or not. Some people prefer having their command triggers removed to reduce clutter, others would like them to stay. This bot base supports both cases, and the behaviour can be toggled on-the-fly by server administrators. Per default this is enabled.

`deletemessages on`  
This will turn trigger message deletion on. Accepted values are `enable`, `on`, `true`, `yes`, `y`, `+` and `1`.

`deletemessages off`  
This will turn trigger message deletion off. Accepted values are `disable`, `off`, `false`, `no`, `n`, `-` and `0`.

**Extend Functionality with Modules**  
One of the main features I emphasized when making this bot base was extendability. More features should be able to be added, changed or removed at any time while disrupting other functionality as little as possible. Discord.py which this bot base is written with has so called *extensions* which allow for loading of external files meant for this purpose. Based on this I made functionality that allows server administrators to load, unload and reload so called *modules*, which are essentially additional python files including commands, or other functionality. By using this you don't need to restart the bot if you need to add, remove or change a module. Additionally, all other modules will be unaffected. This way the bot can continue to function while more functions and commands are created, tested and enabled or removed. See [Making Your Own Functionality](#making-your-own-functionality) for information on making modules. All commands in this category are administrator-only.

`module list`  
This command will show you a list of all currently loaded modules. As well as a list of all available modules the bot can find that are not already loaded.

`module load MODULE_NAME`  
This command will load a module. If the module is not found or an error is encountered while loading the module, the loading is canceled safely and the user informed.

`module unload MODULE_NAME`  
This command will unload a module. Doing so will cause all functionality contained in or reliant on the module in question to stop functioning.

`module reload MODULE_NAME`  
This command will unload, and then load a module. Any errors that are encountered during this will cause the reloading process to cancel safely and the user to be informed.

`module error`  
This command will show the last error that was encountered during the loading or reloading of a module. This can be used for debugging purposes by module maintainers.

**Set Default Modules**  
Logically following after adding, removing and changing functionality with modules is having said modules start with the bot in case it ever does need a restart. This is exactly what default modules are, modules that start alongside the bot. When loading a module fails upon startup then the loading process of that module is canceled safely, logged to the console and available in the module error command.

`default list`  
This command lets the bot owner see a list of all current default modules. A list over all modules can be found with the module list command.

`default add MODULE_NAME`  
This command allows the bot owner to add a default module. It will not immediately load the module if it is not loaded.

`default remove MODULE_NAME`  
This command allows the bot owner to remove a default module. It will not immediately unload the module if it is loaded.

**Disable & Hide Commands**  
I wanted to give people a bit more granular control over the commands they have. In order to give people more control I implemented a feature that allows individual commands to be disabled or hidden. Disabling a command stops the command from being used, and removes the command from the help command. It even stops users from seeing the specific help text relating to the command if they already know the command name. Hiding a command removes it from the help command but does not stop it from being used. If a user already knows it's name they can also still see the specific help text for the command, it's just removed from the list of commands shown by the help command. *These settings are saved per command name.*

`command disable COMMAND_NAME`  
This command allows a server administrator to turn a command off, which also removes it from the help command. Commands in the *Core* category (such as all the commands that come with the bot base) cannot be disabled.

`command enable COMMAND_NAME`  
This command allows a server administrator to turn a command on after it has been turned off.

`command hide COMMAND_NAME`  
This command allows a server administrator to hide a command from the help command. The command can still be used even though it is hidden.

`command show COMMAND_NAME`  
This command allows a server administrator to un-hide a command from the help command after it has been hidden.

**View Module & Bot Information**  
Every bot needs some way of displaying information about itself. In fact it's a so universal feature that this is a requirement in some servers for the bot to even be considered. Additionally since this bot base is meant to be extended with modules there is some need to supply information about modules, as well as give credit to the module authors. This is what the about command does.

`about`  
Using this command on it's own or with the bot's name will display information about the bot itself. This uses the description and additional credits given upon setting up the bot, the bot's profile image, and credits for the bot base. This command can be used by everyone.

`about MODULE_NAME`  
Using the command with a valid module name will show information about the module based on information given by the module creator. They can include a description, an image, a credits section and a additional credits section.

**Shutting Down**  
This function is rather self-explanatory. It allows the bot owner to shut the bot down. Either right away, or with up to a 2 hour delay. There isn't a very big use-case for this, but it's a relatively basic function and was quick to implement.

`shutdown`  
This command lets the bot owner to shut the bot down immediately.

`shutdown 1h30m`  
Passing a time-frame of up to 2 hours along will delay the shutdown. The format for this is `XhXmXs` (hours, minutes, seconds) where X is a positive or negative number. The order does not matter and terms can appear multiple times or not at all. Once the command has been given it cannot be canceled anymore. If the command is run multiple times with different times, it will shut down when the first time runs out. This is meant to be used as a way of allowing users to wrap up any interactive commands or to schedule a restart while the bot owner is unavailable.

**Rich Help Commands**  
One of the biggest issues with making commands intended for other people to use is documenting them in a way that other people can use them confidently. Things that seem obvious to you as the creator are usually a lot less obvious to other, specially if they are not used to using bots already. If commands are correctly set up the bot base will automatically reply with the correct syntax when a command is used with missing arguments, or arguments that fail type checks. Additionally there are the following commands to further document commands.

`help`  
This is the basic help command. If it is used on it's own it will list all commands that have help information registered by the module creator. All commands that come with the bot base also have help information registered. These commands can also be categorized when the help information is registered. The list will not include any disabled or hidden commands, and will also filter out any commands the user of the help command does not have permission to use. The only exception to this is if the command can be used by the user, but only in direct messages. In this case they will still be shown in the list when used in a server, but marked as direct message only. The reverse does not apply due to channel permissions among other things.

`help COMMAND_NAME`  
When passing a command name alongside the help command the command's help information will be displayed. The help information includes a description of the command, a list of aliases for the command, a set of restrictions, such as required roles, and a list of examples of the command being used. The exact content depend on what the module creator has registered. When using the command with a sub-command, it will attempt to show the sub-command's help text, if unavailable, it will try to display the parent command's help text.

`help COG_NAME`  
A cog is a list of commands grouped together. Normally users won't know cog names, but for the sake of completeness passing along a cog with the help command will show a list of all commands in the cog. The same restrictions as the help command on it's own apply.

---
### Making Your Own Functionality

This section will talk about making your own modules to add custom functionality to your bot. Without any modules the bot base itself it not all that useful. I plan on making some modules with basic functionality I think might be useful for a lot of people down the road. Anything more customized has to be created by you however. This is after all a bot base, intended to be a starting point for bots, not an out-of-the-box complete bot. If that is what you are looking for I would recommend a different bot such as [Dyno](https://dyno.gg/).

Lastly, this guide will not go too deeply into the usage of Python or Discord.py. It is assumed you know these or are willing to learn them in order to make your own modules. I will not help you with this beyond the basic examples in this section. There are whole servers dedicated to help people new to python or the discord.py library, such as the [Python Server](https://discord.gg/python) or the [Discord.py Server](https://discord.gg/r3sSKJJ). Note that the Discord.py server will likely not help you unless you have basic Python knowledge, so start with that. If you have questions about the *Travus Bot Base* in particular, see the [contact section](#contact--credits). Please do not bother then Discord.py server with them.

This section will consist of 4 parts. First a basic Discord.py extension adding 2 basic commands. This would already work as a module, but would lack functionality such as command help text. Secondly a rewritten version of the first part, but using a cog. Using cogs is optional, but using them has become recommended. The third part adds *Travus Bot Base* functionality to it, such as command help text. Lastly the fourth part goes over the included functions you can use while making your modules.

Feel free to examine the [core_functions](core_commands.py) file to see how the included commands are implemented. This file is essentially just a module that is always loaded, not listed, and cannot be unloaded or reloaded.

**Basic Discord.py Extension**  
```python
# We import the commands extension from Discord.py.
# We also import the Member class so that we can convert user input.
from discord.ext import commands
from discord import Member

# We make a setup function which takes 1 argument which is the bot object.
# This function is run when loading the module. We add the commands here.
def setup(bot):
    bot.add_command(ping)
    bot.add_command(greet)

# We make a teardown function which takes 1 argument which is the bot object.
# This function is run when unloading the module. We remove commands here.
def teardown(bot):
    bot.remove_command("ping")
    bot.remove_command("greet")

# We make the ping command that just responds with pong.
@commands.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")

# We make the greet command, which we make server-only.
# We also ask for another argument here, and discord.py converts it.
# Wrong or missing input is handled by the bot base automatically.
# The current implementation will however not respond to the error yet.
@commands.guild_only()
@commands.command(name="greet")
async def greet(ctx, other: Member):
    await ctx.send(f"{ctx.author.mention} greets {other.mention}!")
```

**Basic Discord.py Extension With Cog**  
```python
from discord.ext import commands
from discord import Member

# Instead of adding the commands in the setup function, we're adding the cog.
def setup(bot):
    bot.add_cog(SampleCog(bot))

# Same as in setup, we're working with the cog instead of individual commands.
def teardown(bot):
    bot.remove_cog("SampleCog")

# We're making the cog here. It inherits from cog in the commands extension.
class SampleCog(commands.cog):

    # We're making a init method which saves the bot variable.
    # In this sample none of the commands are actually using it.
    # But for the sake of the sample, we'll save it anyways.
    # If we aren't using cogs we need to save this by other means.
    def __init__(self, bot):
        self.bot = bot
    
    # The ping command now lives inside the cog.
    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send("Pong!")
    
    # The greet command now lives inside the cog.
    @commands.guild_only()
    @commands.command(name="greet")
    async def greet(self, ctx, other: Member):
        await ctx.send(f"{ctx.author.mention} greets {other.mention}!")
```

**Full Travus Bot Base Implementation**  
```python
# We're now also importing the function file included with the bot base.
from discord.ext import commands
from discord import Member
import functions as func

# We're now registering module info for the about command during setup.
# We're also registering command help information during setup.
# For more detailed info on these functions, see the next section.
def setup(bot):
    bot.add_cog(SampleCog(bot))
    func.add_module(bot, "Sample Name", "Author", "Sample Description")
    func.add_command_help(bot, SampleCog.ping, "Category", None, [""])
    func.add_command_help(bot, SampleCog.greet, "Category", {"guild_only": True}, ["Travus"])

# Remember to remove the module info and command help during teardown.
# For more detailed info on these functions, see the next section.
def teardown(bot):
    bot.remove_cog("SampleCog")
    func.remove_module(bot, "Sample Name")
    func.remove_command_help(bot, [SampleCog.ping, SampleCog.greet])

class SampleCog(commands.cog):

    def __init__(self, bot):
        self.bot = bot
    
    # We added a doc-string, this will be used as a description in the help command.
    # New-lines are automatically replaced with spaces in the help description.
    @commands.command(name="ping")
    async def ping(self, ctx):
        """This command responds with pong."""
        await ctx.send("Pong!")

    # We've added a doc-string here too, used for the help description.
    # We've also added a 'usage' part to the command line.
    # This is used to generate the expected syntax if user input is wrong.
    # The user will be informed what was expected if input is wrong or missing.
    @commands.guild_only()
    @commands.command(name="greet", usage="<USER>")
    async def greet(self, ctx, other: Member):
        """This command greets another person, pinging them in the process."""
        await ctx.send(f"{ctx.author.mention} greets {other.mention}!")
```

**Helper Functions Included**  
This section has a list over functions included in the function file, what they do, what arguments they take, and what they return if they return anything. Any reference to 'commands' in this section refers to 'discord.ext.commands'.

`add_command_help(bot, command, category, restrictions, examples)`  
This function adds command help info based on the info in the command, such as aliases, and the information passed in as arguments. The restrictions dictionary takes any combination of the 4 keys listed below it.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object  
> **command:** `commands.Command` - The command for which the help info is. Do not call the command.  
> **category:** `str` - The category name this command should appear under. All commands with the same value here will appear in the same list. Defaults to `"no category"`.  
> **restrictions:** `Dict[str, Union[bool, List[str]]]` - Restriction info, a dictionary with any of the 4 following strings as the key. Defaults to `None`.  
>      **"guild_only":** `bool` - If this is set to `True` the command will be shown as server-only. Defaults to `False`.  
>      **"owner":** `bool` - If this is set to `True` the command will be shown as owner-only. Defaults to `False`.  
>      **"perms":** `List[str]` - List of required permissions as strings. This will make an itemized list if set.  
>      **"roles":** `List[str]` - List of permitted roles as strings. This will make an itemized list if set.  
> **examples:** `List[str]` - List of sample arguments, one string for each example. The rest of the command will be automatically generated. If the command does not take any arguments, pass along a list including only an empty string. Defaults to `None`.  

<br/>

`remove_command_help(bot, command)`  
This function removes command help info from one or multiple commands by name or command reference. If a list with multiple commands or names is passed along, it will remove all of them.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object.  
> **command:** `Union[commands.Command, str, List[Union[command.Command, str]]]` - Command, command name, or list of multiple commands or command names for which to remove help information.  

<br/>

`add_module(bot, name, author, description, additional_credits, image_link)`  
This function adds module information for a module. This information can then be found when using the `about` command with the module name. This will not load modules, just add their information.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object.  
> **name:** `str` - Module name that will be used to view this information with the `about` command. Can be something other than the file name.  
> **author:** `str` - The contents of the author blurb. Use `\n` for new-lines and `\t` for indents, this is converted to working indents as leading space is normally voided.  
> **description:** `str` - Module description, new-lines are automatically converted to spaces to allow for multi-line strings. Defaults to `None`.  
> **additional_credits:** `str` - The contents of the additional contents blurb. Use `\n` for new-lines and `\t` for indents, this is converted to working indents as leading space is normally voided. If set to `None` this section will not be displayed. Defaults to `None`.  
> **image_link:** `str` - Link to the image to be used. If set to `None` no image will be used. Defaults to `None`.  

<br/>

`remove_module(bot, name)`  
This function will remove module information by name. Once removed it can no longer by accessible with the `about` command. This does not unload the module, just remove it's information.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object.  
> **name:** `str` - Name of the module to be removed. This should not be the file name, but the name given to the module when added with the `add_module` function.  

<br/>

`add_commands(bot, com_list)`  
This function works similarly to `commands.Bot.add_command`, except this function takes a list of commands and adds all of them instead of just one.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object.  
> **com_list:** `List[commands.Command]` - List of commands to be added. Do not call the commands.  

<br/>

`remove_commands(bot, com_list)`  
This function works similarly to `commands.Bot.remove_command`, except this function takes a list of commands and removed all of them instead of just one.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object.  
> **com_list:** `List[Union[commands.Command, str]]` - List of command names or commands to be removed.  

<br/>

`update_command_states(bot)`  
This function goes over all commands and sets their state, such as hidden or disabled from the database. This is automatically called when loading and reloading modules, so it usually does not need to be called. The only time this really needs to be called is if commands are added to the bot outside of the setup function. This is a coroutine, and has to be awaited.
> **Argument:**  
> **bot**: `commands.Bot` - The bot object.  

<br/>

`parse_time(duration, minimum, maximum, error_on_exceeded)`  
This function takes a string time input such as `2h30m30s` (2 hour, 30 minutes and 30 seconds) and returns the amount of seconds it corresponds to. Accepted values are weeks (`w`), days (`d`), hours (`h`), minutes (`m`) and seconds (`s`) followed by a number. Negative numbers are accepted. Repeat values are also accepted. A minimum and maximum value can be set, if error_on_exceeded is set to `True` then an error will be raised if this happens, otherwise the return value will be overwritten with the maximum or minimum value if the result exceeds the limit.
> **Arguments:**  
> **duration:** `str` - The string to parse. Should follow the format described in the command description above.  
> **minimum:** `int` - The minimum amount of time in seconds seconds. Behaviour when parsed input is less decided by `error_on_exceeded` value. If set to `None` there is no minimum. Defaults to `None`.  
> **maximum:** `int` - The maximum amount of time in seconds seconds. Behaviour when parsed input is more decided by `error_on_exceeded` value. If set to `None` there is no maximum. Defaults to `None`.  
> **error_on_exceeded:** `bool` - If set to `True` then a `ValueError` will be raised if minimum or maximum are exceeded. If set to `False` then the minimum or maximum values will be used when exceeded. Defaults to `True`.  
  
> **Return Value:**  
> int: The parsed time in seconds.  

<br/>

`db_get_one(bot, query, variable)`  
This function is a wrapper that handles asynchronously getting the first matching row as a tuple from the database. This is a coroutine, and has to be awaited.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object.  
> **query:** `str` - The SQLite query you wish to execute. Variables should be represented as `?`.  
> **variable:** `tuple` - A tuple of arguments in the order they appear in the query.  
  
> **Return Values:**  
> **tuple:** Returns a tuple with the selected values.  
> **None:** If no results are found, `None` is returned.  

<br/>

`db_get_all(bot, query, variable)`  
This function is a wrapper that handles asynchronously getting all matching rows as tuples from the database. This is a coroutine, and has to be awaited.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object.  
> **query:** `str` - The SQLite query you wish to execute. Variables should be represented as `?`.  
> **variable:** `tuple` - A tuple of arguments in the order they appear in the query.
  
> **Return Values:**  
> **List[tuple]:** Returns a list of tuples, every tuple has the values for one row.  
> **None:** If no results are found, `None` is returned.  

<br/>

`db_set(bot, query, viariable)`  
This function is a wrapper that handles asynchronously running a database transaction and committing to the database. This is a coroutine, and has to be awaited.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object.  
> **query:** `str` - The SQLite query you wish to execute. Variables should be represented as `?`.  
> **variable:** `tuple` - A tuple of arguments in the order they appear in the query.
  
> **Return Values:**  
> **asqlite.sqlite3.IntegrityError:** Returns the error if a database integrity error is encountered.  
> **None:** Returns `None` if no errors are encountered.  

<br/>

`db_set_many(bot, query, variables)`  
This function is a wrapper that handles asynchronously running multiple database transaction and committing to the database. If any of the transactions fail, none of them will be committed. This is a coroutine, and has to be awaited.
> **Arguments:**  
> **bot:** `commands.Bot` - The bot object.  
> **query:** `Tuple[str]` - A tuple of SQLite queries you wish to execute. Variables should be represented as `?`.  
> **variables:** `Tuple[tuple]` - A tuple made up of tuples containing arguments. The tuples are in the order of the queries, and the arguments in the order they appear in their respective query.  
  
> **Return Values:**  
> **asqlite.sqlite3.IntegrityError:** Returns the error if a database integrity error is encountered.  
> **None:** Returns `None` if no errors are encountered.  

<br/>

`can_run(com, ctx)`  
This function works similarly to `commands.Command.can_run`, except it will not raise any errors, only return if a command can be run given a context. This is a coroutine, and has to be awaited.
> **Arguments:**  
> **com:** `commands.Command` - The command which should be checked.  
> **ctx:** `commands.Context` - The context for which to check it.  
  
> **Return Value:**  
> **bool:** Returns `True` if the command can be run in the given context otherwise returns `False`.  

<br/>

`get_bot_prefix(bot)`  
Returns the bot prefix as text, if no prefix is set it will correctly return bot ping as a prefix.
> **Argument:**  
> **bot:** `commands.Bot` - The bot object.  
  
> **Return Value:**  
> **str:** The current set prefix or a bot mention as text.  

<br/>

`cur_time()`  
Returns the current time in YYYY-MM-DD HH:MM format.
> **Return Value:**  
> **str:** Current time in YYYY-MM-DD HH:MM format.  

<br/>

`del_message(msg)`  
Deletes a given message, if message is not in a DM channel. Logs to console if deletion failed due to lacking permissions. This is a coroutine, and has to be awaited.
> **Argument:**  
> **ctx:** `discord.Message` - The message that should be deleted.  


---
### Additional Customization

For additional customization of features that come with the bot base, the code can be edited. I will not go very in-depth on this, as it is expected you know what you are doing if you are going to do so. Some simple examples of this I image are going to be wanted are listed below.

**Changing Requirements for Existing Commands**  
Are you unhappy with the existing requirements? Do you want to restrict module loading to bot owner only? Do you want to let server administrators set default modules and prefix? Use manage server or a role instead of administrator for some commands? Let everyone see the module list? Well, you can do any of these things, and much more!

Simply go to the [core commands file](core_commands.py) and locate the command in question. Above the command you will find decorators that set the requirements, such as `@commands.is_owner()`. Here you can simply add, remove or change the requirements by using [Discord.py checks](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#checks). If the command has subcommands, make sure you make sure the checks are also replaced for the subcommands.

**Changing the Maximum Time for the Shutdown Command.**  
Do you want to schedule shutdown for more than 2 hours? Well, i don't know why you would want to do that, but you sure can make it so.

Simply go to the shutdown command in the [core command file](core_commands.py). It's the last command in the file. Next find this line: `time = func.parse_time(countdown, 0, 7200, True)`, and simply replace the `7200` with the amount of seconds the maximum time should be. The default is 2 hours.

**Set Custom Status Message**  
Do you want to set a custom status message instead of it's prefix? You can do that if you want.

This needs to be changed near the end of the `on_ready` section in the [main file](main.py). How to set the status is described in the [Discord.py documentation](https://discordpy.readthedocs.io/en/latest/faq.html#how-do-i-set-the-playing-status). Secondly you need to remove the line that changes the status when the prefix is changed in the prefix command in the [core_commands file](core_commands.py).

---
### Contact & Credits

**Contact**  
If you need to get in contact with me for any reason, feel free to send me a message via Discord, Twitter, or leave an issue on this repository if applicable. That said, your best bet is probably to reach me on Discord. If the fact that I made a bot base for Discord bots didn't give it away, I use Discord *a lot*.  
> Discord: Travus#8888  
> Twitter: @RealTravus  
> [Open a GitHub Issue](https://github.com/Travus/Travus_Bot_Base/issues/new)  

**Credits**  
The *Travus Bot Base* is made by [Travus](https://github.com/Travus).  
[Discord.py](https://github.com/Rapptz/discord.py) is made by [Rapptz](https://github.com/Rapptz) and the other contributors to the project.  
[asqlite](https://gist.github.com/Rapptz/c1ff9fc7dc15194f305eb13e6cb57de1) is made by [Rapptz](https://github.com/Rapptz).

The *Travus Bot Base* is made under the [MIT License](LICENSE.md), meaning you are welcome to change, redistribute, and use it however you see fit. I am not liable for any problems you may encounter by misusing the bot base.
