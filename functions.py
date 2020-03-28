import asqlite  # For asynchronous database transactions.
import datetime  # To get current time.
import asyncio  # To make async db connection in custom bot __init__.
from asqlite import Connection as A_Connection, connect as a_connect  # For type-hinting
from typing import Tuple, Dict, List, Union, Callable, Type  # For type-hinting.
from discord import utils, Forbidden, Embed, Colour, Message, User, Member, TextChannel, VoiceChannel, CategoryChannel  # For embeds and deleting messages.
from discord.ext.commands import Command, Cog, Bot, Context, Converter, UserConverter, BadArgument, TextChannelConverter, CommandError, UserInputError  # For type-hinting.
from re import compile, findall  # Regex functions used in clean function for detecting mentions.


class GlobalChannel(Converter):
    """Custom converter that returns user, or channel be it in the current server or another."""
    id = None
    name = None

    async def convert(self, ctx: Context, channel: str) -> Union[TextChannel, VoiceChannel, User]:
        """Converter method used by discord.py."""
        if isinstance(channel, str) and channel.lower() in ["dm", "dms", "pm", "pms"]:
            return ctx.message.author  # Get DM channel if asked for.
        try:
            return await UserConverter().convert(ctx, channel)
        except BadArgument:
            try:
                return await TextChannelConverter().convert(ctx, channel)
            except BadArgument:  # Channel not in server.
                try:
                    converted = ctx.bot.get_channel(int(channel))
                    if converted is None:
                        raise UserInputError(f'Could not identify channel.')
                    return converted
                except ValueError:
                    raise UserInputError(f'Could not identify channel.')


class GlobalTextChannel(Converter):
    """Custom converter that returns user, or text channel be it in the current server or another."""
    id = None
    name = None

    async def convert(self, ctx: Context, channel: str) -> Union[TextChannel, User]:
        """Converter method used by discord.py."""
        if isinstance(channel, str) and channel.lower() in ["dm", "dms", "pm", "pms"]:
            return ctx.message.author  # Get DM channel if asked for.
        try:
            return await UserConverter().convert(ctx, channel)
        except BadArgument:
            try:
                return await TextChannelConverter().convert(ctx, channel)
            except BadArgument:  # Channel not in server.
                try:
                    converted = ctx.bot.get_channel(int(channel))
                    if converted is None or isinstance(converted, VoiceChannel) or isinstance(converted, CategoryChannel):
                        raise UserInputError(f'Could not identify text channel.')
                    return converted
                except ValueError:
                    raise UserInputError(f'Could not identify text channel.')


class TravusBotBase(Bot):
    """Custom bot class with database connection."""

    class _HelpInfo:
        """Class that holds help info for commands."""

        def __init__(self, command: Command, category: str = "no category", restrictions: Dict[str, Union[bool, List[str], str]] = None, examples: List[str] = None):
            """Initialization function loading all necessary information for HelpInfo class."""
            res = restrictions  # Shortening often used variable name.
            self.name = command.qualified_name
            self.description = command.help.replace("\n", " ") if command.help else "No description found."  # Remove newlines from multi-line docstrings.
            self.aliases = list(command.aliases) or []
            self.aliases.append(command.name)
            self.category = category
            self.examples = examples or []
            self.permissions = res["perms"] if isinstance(res, dict) and "perms" in res.keys() else []
            self.roles = res["roles"] if isinstance(res, dict) and "roles" in res.keys() else []
            self.other_restrictions = res["other"] if isinstance(res, dict) and "other" in res.keys() else False
            self.owner_only, self.guild_only, self.dm_only = False, False, False
            for check in command.checks:
                if "is_owner" in str(check):
                    self.owner_only = True
                if "guild_only" in str(check):
                    self.guild_only = True
                if "dm_only" in str(check):
                    self.dm_only = True

        def make_embed(self, prefix: str, ctx: Context) -> Embed:
            """Creates embeds for command based on info stored in class."""
            embed = Embed(colour=Colour(0x4a4a4a), description=f"Category: {self.category.title()}\n\n{self.description}", timestamp=datetime.datetime.utcnow())
            embed.set_author(name=f"{self.name.title()} Command")
            aliases = "\n".join(sorted(self.aliases))  # Make and add aliases blurb.
            embed.add_field(name="Aliases", value=f"```\n{aliases}```", inline=True)
            restrictions = "Bot Owner Only: Yes\n" if self.owner_only else ""  # Make and add restrictions blurb.
            restrictions += "DM Only: Yes\n" if self.dm_only else ""
            restrictions += "" if self.dm_only else "Server Only: Yes" if self.guild_only else "Server Only: No"
            restrictions += ("\nPermissions:\n" + "\n".join(f"   {perm}" for perm in self.permissions)) if self.permissions else ""
            restrictions += ("\nAny role of:\n" + "\n".join([f"   {role}" for role in self.roles])) if self.roles else ""
            restrictions += f"\n{self.other_restrictions}" if self.other_restrictions else ""
            embed.add_field(name="Restrictions", value=f"```{restrictions}```", inline=True)
            examples = "\n".join([f"`{prefix}{self.name} {example}`" for example in self.examples])  # Make and add examples.
            embed.add_field(name="Examples", value=examples or "No examples found.", inline=False)
            embed.set_footer(text=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url)
            return embed

    class _ModuleInfo:
        """Class that holds info for modules."""

        def __init__(self, get_prefix: Callable, name: str, author: str, usage: Union[str, Embed] = None, description: str = None, additional_credits: str = None, image_link: str = None):
            """Initialization function loading all necessary information for ModuleInfo class."""
            self.get_prefix = get_prefix
            self.name = name
            self.author = author.replace("\t", "\u200b\u0009\u200b\u0009\u200b\u0009\u200b\u0009\u200b\u0009")  # Convert tabs to non-skipped spaces.
            self.description = description.replace("\n", " ") if description else "No module description found."  # Remove newline from multi-line strings.
            self.credits = additional_credits.replace("\t", "\u200b\u0009\u200b\u0009\u200b\u0009\u200b\u0009\u200b\u0009") if additional_credits else None
            self.image = image_link
            self.usage = usage

        def make_embed(self, ctx: Context) -> Embed:
            """Creates embeds for module based on info stored in class."""
            embed = Embed(colour=Colour(0x4a4a4a), description=self.description.replace("_prefix_", self.get_prefix()), timestamp=datetime.datetime.utcnow())
            embed.set_author(name=self.name)
            embed.set_footer(text=ctx.message.author.display_name, icon_url=ctx.message.author.avatar_url)
            if self.image:
                embed.set_thumbnail(url=self.image)
            if not self.credits:
                embed.add_field(name="Authored By", value=f"{self.author}")
            else:  # If there are additional credits make both sections inline.
                embed.add_field(name="Authored By", value=f"{self.author}", inline=True)
                embed.add_field(name="Additional Credits", value=f"{self.credits}", inline=True)
            return embed

    def __init__(self, *args, **kwargs):
        """Initialization function loading all necessary information for TravusBotBase class."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.db_con = loop.run_until_complete(a_connect("database.sqlite"))
        loop.run_until_complete(db_set(self.db_con, "PRAGMA foreign_keys = 1", ()))
        self.last_module_error = None
        self.last_error = None
        self.extension_ctx = None
        self.help: Dict[str, TravusBotBase._HelpInfo] = {}
        self.modules: Dict[str, TravusBotBase._ModuleInfo] = {}
        self.prefix = ""
        self.delete_messages = 1
        self.is_connected = 0
        self.has_started = 0
        super().__init__(*args, **kwargs)

    def get_bot_prefix(self) -> str:
        """Returns the current bot prefix, or a mention of the bot in text form followed by a space."""
        if self.prefix is not None:
            return self.prefix
        else:
            return f"@{self.user.display_name}#{self.user.discriminator} "

    def add_module(self, name: str, author: str, cog: Type[Cog] = None, description: str = None, additional_credits: str = None, image_link: str = None):
        """Function that is used to add module info to the bot correctly. Used to minimize developmental errors."""
        usage = None
        if hasattr(cog, "usage") and isinstance(cog.usage, (str, Callable)):
            if isinstance(cog.usage, str):
                usage = cog.usage
            elif isinstance(cog.usage, Callable) and isinstance(cog.usage(), (str, Embed)):
                usage = cog.usage()
        info = self._ModuleInfo(self.get_bot_prefix, name, author, usage, description, additional_credits, image_link)
        if name.lower() not in self.modules.keys():
            self.modules[name.lower()] = info
        else:
            raise RuntimeError(f"A module with the name '{name}' already exists.")

    def remove_module(self, name: str):
        """Function that is used to remove module info to the bot correctly. Used to minimize developmental errors."""
        if name.lower() in self.modules.keys():
            del self.modules[name.lower()]

    def add_commands(self, com_list: List[Command]):
        """Adds multiple commands at once using bot.add_command."""
        for com in com_list:
            self.add_command(com)

    def remove_commands(self, com_list: List[Union[Command, str]]):
        """Removed multiple commands at once using bot.remove_command. Accepts command names or commands."""
        for com in com_list:
            self.remove_command(com.name if isinstance(com, Command) else com)

    async def update_command_states(self):
        """Function that get command state (hidden, disabled) for every command currently loaded."""
        for command in self.commands:
            command_state = await db_get_one(self.db_con, "SELECT state FROM command_states WHERE command = ?", (command.name,))
            if command_state is None:  # If a command has no stat registered, set it to visible and enables.
                command_state = (0,)
                await db_set(self.db_con, "INSERT INTO command_states VALUES (?, ?)", (command.name, 0))
            command_state = int(command_state[0])
            if command_state == 1:  # Set command to be hidden.
                command.enabled = True
                command.hidden = True
            elif command_state == 2:  # Set command to be disabled.
                command.enabled = False
                command.hidden = False
            elif command_state == 3:  # Set command to be hidden and disabled.
                command.enabled = False
                command.hidden = True

    def add_command_help(self, command: Command, category: str = "no category", restrictions: Dict[str, Union[bool, List[str], str]] = None, examples: List[str] = None):
        """Function that is used to add help info to the bot correctly. Used to minimize developmental errors."""
        self.help[command.qualified_name] = self._HelpInfo(command, category, restrictions, examples)

    def remove_command_help(self, command: Union[Command, Cog.__class__, str, List[Union[Command, str]]]):
        """Function that is used to remove command help info from the bot correctly. Used to minimize developmental errors."""
        if isinstance(command, list):  # Remove all in list, if list is passed.
            for com in command:
                if com.qualified_name in self.help.keys():
                    del self.help[com.qualified_name if isinstance(com, Command) else com]
        elif isinstance(command, Command):  # Remove single if only one is passed.
            if command.qualified_name in self.help.keys():
                del self.help[command.qualified_name if isinstance(command, Command) else command]
        elif isinstance(command, Cog):
            for com in command.walk_commands():
                if com.qualified_name in self.help.keys():
                    del self.help[com.qualified_name]


def parse_time(duration: str, minimum: int = None, maximum: int = None, error_on_exceeded: bool = True) -> int:
    """Function that parses time in a NhNmNs format. Supports weeks, days, hours, minutes and seconds, positive and negative amounts and max values.
    Minimum and maximum values can be set (in seconds), and whether a error should occur or the max / min value should be used when these are exceeded."""
    last, t_total = 0, 0
    t_frames = {"w": 604800, "d": 86400, "h": 3600, "m": 60, "s": 1}
    for c in range(len(duration)):  # For every character in time string.
        if duration[c].lower() in t_frames.keys():
            if duration[last:c] != "":
                t_total += int(duration[last:c]) * t_frames[duration[c].lower()]
            last = c + 1
        elif duration[c] not in ["+", "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:  # If character isn't a time frame denomination or valid number.
            raise ValueError("Invalid character encountered during time parsing.")
    if t_total < minimum:  # If total time is less than minimum.
        if error_on_exceeded:
            raise ValueError("Time too short.")
        else:
            t_total = minimum
    if t_total > maximum:  # If total time is more than maximum.
        if error_on_exceeded:
            raise ValueError("Time too long.")
        else:
            t_total = maximum
    return t_total


async def send_in_global_channel(ctx: Context, channel: GlobalTextChannel, msg: str, other_dms: bool = False):
    """Sends a message in any text channel across servers and DMs. Has flag to allow sending to foreign DMs."""
    try:
        if isinstance(channel, (User, Member)) and channel.id != ctx.author.id and not other_dms:
            await ctx.send("Sending messages to another user's DMs is forbidden.")
        elif channel is None or isinstance(channel, (User, Member)) or channel.permissions_for(ctx.author).send_messages:
            await (channel or ctx.channel).send(msg)
        else:
            await ctx.send("You do not have permission to send messages in this channel.")
    except Forbidden:
        await ctx.send("Cannot send messages in given channel.")


async def db_get_one(con: A_Connection, query: str, variable: tuple) -> Union[tuple, None]:
    """Returns the result of a database query and fetch_one."""
    db = await con.cursor()
    await db.execute(query, variable)
    result = await db.fetchone()
    result = tuple(result) if result is not None else None
    await db.close()
    return result


async def db_get_all(con: A_Connection, query: str, variable: tuple) -> Union[List[tuple], None]:
    """Returns the result of a database query and fetch_all."""
    db = await con.cursor()  # Fetch results from database.
    await db.execute(query, variable)
    result = await db.fetchall()
    result = [tuple(val) for val in result] if result is not None else None
    await db.close()
    return result


async def db_set(con: A_Connection, query: str, variable: tuple) -> Union[asqlite.sqlite3.IntegrityError, None]:
    """Executes a database command without fetching anything."""
    try:  # Try executing database query.
        await con.execute(query, variable)
    except asqlite.sqlite3.IntegrityError as e:  # If we hit a database constraint, return error.
        return e
    await con.commit()  # Commit changes and return None as no error was encountered.
    return None


async def db_set_many(con: A_Connection, query: Tuple[str, ...], variables: Tuple[tuple, ...]) -> Union[asqlite.sqlite3.IntegrityError, None]:
    """Executes multiple database commands without fetching anything."""
    if len(query) < len(variables):
        raise RuntimeError("More variables than queries found.")
    elif len(query) > len(variables):
        variables = list(variables)
        while len(query) > len(variables):
            variables.append(())
        variables = tuple(variables)
    try:  # Try executing database queries.
        for query, variable in zip(query, variables):
            await con.execute(query, variable)
    except asqlite.sqlite3.IntegrityError as e:  # If we hit a database constraint, return error.
        return e
    await con.commit()  # Commit changes and return None as no error was encountered.
    return None


async def can_run(com: Command, ctx: Context) -> bool:
    """This function uses command.can_run to see if a command can be run by a user, but does not raise exceptions."""
    try:
        await com.can_run(ctx)
    except CommandError:
        return False
    else:
        return True


def cur_time() -> str:
    """Get current time in YYYY-MM-DD HH:MM format."""
    return str(datetime.datetime.utcnow())[0:16]


async def del_message(msg: Message):
    """Tries to delete a passed message, handling permission errors."""
    if msg.guild:
        try:  # Try to delete message.
            await msg.delete()
        except Forbidden:  # Log to console if missing permission to delete message.
            print(f"[{cur_time()}] Error: Bot does not have required permissions to delete message.")


def clean(ctx: Context, text: str, escape_markdown: bool = True) -> str:
    """Cleans text, escaping mentions and markdown. Tries to change mentions to text."""
    transformations = {}

    def resolve_member(_id):
        """Resolves user mentions."""
        m = ctx.bot.get_user(_id)
        return '@' + m.name if m else '@deleted-user'

    transformations.update(('<@%s>' % member_id, resolve_member(member_id)) for member_id in [int(x) for x in findall(r'<@!?([0-9]+)>', text)])
    transformations.update(('<@!%s>' % member_id, resolve_member(member_id)) for member_id in [int(x) for x in findall(r'<@!?([0-9]+)>', text)])

    if ctx.guild:
        def resolve_channel(_id):
            """Resolves channel mentions."""
            ch = ctx.guild.get_channel(_id)
            return ('<#%s>' % _id), ('#' + ch.name if ch else '#deleted-channel')

        def resolve_role(_id):
            """Resolves role mentions."""
            r = ctx.guild.get_role(_id)
            return '@' + r.name if r else '@deleted-role'

        transformations.update(resolve_channel(channel) for channel in [int(x) for x in findall(r'<#([0-9]+)>', text)])
        transformations.update(('<@&%s>' % role_id, resolve_role(role_id)) for role_id in [int(x) for x in findall(r'<@&([0-9]+)>', text)])

    def repl(obj):
        """Function used in regex substitution."""
        return transformations.get(obj.group(0), '')

    pattern = compile('|'.join(transformations.keys()))
    result = pattern.sub(repl, text)
    if escape_markdown:
        result = utils.escape_markdown(result)
    return utils.escape_mentions(result)


def unembed_urls(text: str) -> str:
    """Finds all URLs in a text and returns a list of them."""
    def repl(obj):
        """Function used in regex substitution."""
        return f"<{obj.group(0).strip('<').strip('>')}>"

    pattern = compile(r"(\b|<)https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_+.~#?&\\/=]*)>?")
    text = pattern.sub(repl, text)
    return text


# ToDo: Update existing code and README to reflect that functions moved into bot class.
