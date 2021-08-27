from contextlib import redirect_stdout  # To return eval output.
from copy import copy  # For copying context.
from io import StringIO  # To return eval output.
from textwrap import indent, wrap  # To format eval output.
from traceback import format_exc  # To return eval output.
from typing import Optional, Union  # For type-hinting.

import aiohttp  # To send info to mystbin.
from aiohttp import ClientSession
from discord import Member, Role  # For type-hinting and exceptions.
from discord.ext import commands  # For implementation of bot commands.

import travus_bot_base as tbb  # TBB functions and classes.


def setup(bot: tbb.TravusBotBase):
    """Setup function ran when module is loaded."""
    bot.add_cog(DevCog(bot))  # Add cog and command help info.
    bot.add_module("Dev", "[Travus](https://github.com/Travus):\n\tEval command\n\tRoleID command\n\tChannelID command"
                          "\n\tLast error command\n\n[Rapptz](https://github.com/Rapptz):\n\tSudo command",
                   DevCog.usage, """This module includes developer functionality that supply information useful for
                   programming, such as IDs, as well as some debug and testing options such as code execution and
                   remote command execution. Also allows checking the most recent error.""",
                   "[Rapptz](https://github.com/Rapptz):\n\tEval example\n\n"
                   "[nerdstep710](https://github.com/nerdstep710):\n\tMystbin example")
    bot.add_command_help(DevCog.eval, "Dev", None, ["return 4 + 7", "return channel.id"])
    bot.add_command_help(DevCog.sudo, "Dev", None, ["travus bot_room help", "118954681241174016 about dev"])
    bot.add_command_help(DevCog.roleids, "Dev", {"perms": ["Manage Roles"]}, ["all bot_room", "all dm", "muted"])
    bot.add_command_help(DevCog.channelids, "Dev", {"perms": ["Manage Channels"]},
                         ["all bot_room", "all dm", "general"])
    bot.add_command_help(DevCog.lasterror, "Dev", {"perms": ["Manage Server"]}, [""])
    bot.add_command_help(DevCog.ping, "Dev", None, [""])


def teardown(bot: tbb.TravusBotBase):
    """Teardown function ran when module is unloaded."""
    bot.remove_cog("DevCog")  # Remove cog and command help info.
    bot.remove_module("Dev")
    bot.remove_command_help(DevCog)


async def mystbin_send(text: str, line_length: int = None) -> Optional[str]:
    """Send the text if it's short enough, otherwise links to a Mystbin of the text."""
    if text is not None:
        if line_length:
            lines = text.split("\n")
            for n in range(len(lines)):
                if len(lines[n]) > line_length:
                    wrapped = wrap(lines[n], width=line_length)
                    lines[n] = ""
                    for w_line in wrapped[:-1]:
                        lines[n] += f"{w_line} ↩\n"
                    lines[n] += wrapped[-1]
            text = "\n".join(lines)
        async with ClientSession() as session:
            key = (await (await session.post("https://mystb.in/documents", data=text.encode())).json())["key"]
            return f"https://mystb.in/{key}"
    else:
        return None


class DevCog(commands.Cog):
    """Cog that holds dev functionality."""

    def __init__(self, bot: tbb.TravusBotBase):
        """Initialization function loading bot object for cog."""
        self.bot = bot
        self._last_result = None

    @staticmethod
    async def _mystbin_send(ctx: commands.Context, text: str):
        """Send the text if it's short enough, otherwise links to a Mystbin of the text."""
        if text is not None:
            if len(text) > 1950:
                lines = text.split("\n")
                for n in range(len(lines)):
                    if len(lines[n]) > 198:
                        wrapped = wrap(lines[n], width=198)
                        lines[n] = ""
                        for w_line in wrapped[:-1]:
                            lines[n] += f"{w_line} ↩\n"
                        lines[n] += wrapped[-1]
                text = "\n".join(lines)
                async with aiohttp.ClientSession() as session:
                    key = (await (await session.post("https://mystb.in/documents", data=text.encode())).json())["key"]
                    await ctx.send(f"https://mystb.in/{key}")
            else:
                await ctx.send(f"```py\n{text}\n```")

    @staticmethod
    def usage() -> str:
        """Returns the usage text."""
        return ("**How To Use The Dev Module:**\nThis module is used for development purposes, such as retrieving "
                "channel and role IDs, running commands on behalf of other users, and running code. The commands in "
                "this module are a bit more advanced than most others, this command will elaborate more on how to use "
                "them. For more info on what the commands do, check their help entry.\n\n*Sudo Command*\nThis command "
                "takes up to 3 arguments. The first is a user. The second argument is a channel, but this can be "
                "omitted. The bot will try to resolve the channel, if this fails it will fall back to the channel the "
                "command was used in, then it will consider the second argument to be the third, namely the command "
                "to be executed. This means in practice that unless the command starts with something that would "
                "resolve as a channel the second argument can be omitted if the current channel is the target channel."
                "\n\n*Eval Command*\nThis command runs code. Code can be either be passed directly following the "
                "command, or in a single or multi-line code block. Multi-line code blocks both with and without "
                "syntax highlighting are supported, however the start and end of the code block (i.e. \\`\\`\\`) has "
                "to be on separate lines from the code. The bot will respond with all regular output streams and the "
                "return value if there is one. If there is no output, the bot will not respond.\n\n*Roleids/"
                "Channelids Commands*\nThese commands both work similarly. The first argument should either be the "
                "keyword `all` or alternatively the reference to either a channel or role based on which command is "
                "used. Then optionally a channel can be given as a second argument, and the response will be sent in "
                "this channel. The channel can be in another server entirely as long as both the user and the bot "
                "have access there. If the keyword `dm` is used then the response will be sent in the user's DMs with "
                "the bot. Lastly, if the argument is omitted then the response is sent in the current channel.")

    @staticmethod
    def cleanup_code(content: str) -> str:
        """Automatically removes code blocks from the code."""
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])
        return content.strip("` \n")

    # noinspection PyBroadException
    @commands.is_owner()
    @commands.command(name="eval", aliases=["exec"], usage="<CODE TO EXECUTE>")
    async def eval(self, ctx: commands.Context, *, body: str):
        """This command evaluates code sent via Discord, and sends back any return value and output in a discord python
        code block. This can be single-line or multi-line via a code block. If the output is too long to fit in a
        discord message a mystbin link with the response will be sent. Mystbin output will be line-wrapped to make it
        more readable."""
        stdout = StringIO()
        env = {"bot": self.bot, "ctx": ctx, "channel": ctx.channel, "author": ctx.author, "guild": ctx.guild,
               "message": ctx.message, "_": self._last_result}
        env.update(globals())
        try:
            exec(f'async def function():\n{indent(self.cleanup_code(body), "  ")}', env)
        except Exception as e:
            response = f"{e.__class__.__name__}: {e}"
            return await self._mystbin_send(ctx, response)
        function = env["function"]
        try:
            with redirect_stdout(stdout):
                ret = await function()
        except Exception:
            value = stdout.getvalue()
            response = f"{value}{format_exc()}"
        else:
            value = stdout.getvalue()
            if ret is None:
                response = value or None
            else:
                self._last_result = ret
                response = f"{value}{ret}"
        await self._mystbin_send(ctx, response)

    @commands.is_owner()
    @commands.guild_only()
    @commands.command(name="sudo", usage="<USER> (CHANNEL) <COMMAND>")
    async def sudo(self, ctx: commands.Context, user: Member, channel: Optional[tbb.GlobalTextChannel], *, cmd: str):
        """This command lets you run commands as another user, optionally in other channels. If the channel argument is
        skipped and the bot fails to parse the argument as a channel it will ignore the channel argument and move on to
        parsing the command instead. In this case the command will be sent from the channel you are currently in."""
        if isinstance(channel, Member):
            await ctx.send("Cannot sudo into DMs. ")
            return
        new_ctx = copy(ctx.message)
        new_ctx.channel = channel or ctx.channel
        new_ctx.author = new_ctx.channel.guild.get_member(user.id)
        if new_ctx.author is None:
            await ctx.send("Target user is not in target server.")
            return
        new_ctx.content = ctx.prefix + cmd
        new_ctx = await self.bot.get_context(new_ctx, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.command(name="roleids", aliases=["roleid"], usage="<ROLE/all> (OUTPUT CHANNEL/dm)")
    async def roleids(self, ctx: commands.Context, role: Union[Role, str],
                      resp_channel: Optional[tbb.GlobalTextChannel]):
        """This command gives you role IDs of one or all roles in the server depending on if a role or `all` is passed
        along. You can also pass along a channel, in this server or otherwise, in which case the response is sent in
        that channel. Sending `dm` instead of a channel will send you the result in direct messages."""
        paginator = commands.Paginator()
        if isinstance(role, str) and role.lower() == "all":
            for _role in reversed(ctx.guild.roles):
                paginator.add_line(f"{_role.name}: {_role.id}")
            for page in paginator.pages:
                await tbb.send_in_global_channel(ctx, resp_channel, page)
        elif isinstance(role, str):
            raise commands.BadArgument("Role could not be parsed and string is not 'all'.")
        else:
            response = f"{role.name}: {role.id}"
            await tbb.send_in_global_channel(ctx, resp_channel, f"```{response}```")

    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    @commands.command(name="channelids", aliases=["channelid"], usage="<CHANNEL/all> (OUTPUT CHANNEL/dm)")
    async def channelids(self, ctx: commands.Context, channel: Union[tbb.GlobalChannel, str],
                         resp_channel: Optional[tbb.GlobalTextChannel]):
        """This command gives you channel IDs of one or all channels in the server depending on if a channel or `all`
        is passed along. You can also pass along a second channel, in this server or otherwise, in which case the
        response is sent in that channel. Sending `dm` instead of a second channel will send you the result in direct
        messages."""
        response = ""
        paginator = commands.Paginator()
        if isinstance(channel, str) and channel.lower() == "all":
            for _channel in ctx.guild.text_channels:
                paginator.add_line(f"{_channel.name}: {_channel.id}")
            for _channel in ctx.guild.voice_channels:
                paginator.add_line(f"{_channel.name}: {_channel.id}")
            for page in paginator.pages:
                await tbb.send_in_global_channel(ctx, resp_channel, page)
        elif isinstance(channel, str):
            raise commands.BadArgument("Channel could not be parsed and string is not 'all'.")
        else:
            if hasattr(channel, "name") and hasattr(channel, "id"):
                response = f"{channel.name}: {channel.id}"
        await tbb.send_in_global_channel(ctx, resp_channel, f"```{response}```")

    @commands.has_permissions(administrator=True)
    @commands.command(name="lasterror", aliases=["lerror", "_error"])
    async def lasterror(self, ctx: commands.Context):
        """This command shows the last error the bot has encountered. Errors encountered while loading modules will
        not be listed by this command. To see the last error encountered while loading modules see the `module error`
        command. This command retains this information until another error replaces it, or the bot shuts down."""
        if self.bot.last_error:
            await ctx.send(tbb.clean(ctx, self.bot.last_error))
        else:
            await ctx.send("There have not been any errors since the last restart.")

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        """This command shows the latency from the bot to Discord's servers. Can be used to check if the bot is
        responsive."""
        await ctx.send(f"Pong! ({round(self.bot.latency * 1000, 2)}ms)")
