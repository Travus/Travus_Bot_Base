from contextlib import redirect_stdout  # To return eval output.
from copy import copy  # For copying context.
from io import StringIO  # To return eval output.
from textwrap import indent  # To format eval output.
from traceback import format_exc  # To return eval output.

import discord
from discord import DMChannel, Interaction, Member, Role, app_commands
from discord.ext import commands  # For implementation of bot commands.

import travus_bot_base as tbb  # TBB functions and classes.


async def setup(bot: tbb.TravusBotBase):
    """Setup function ran when module is loaded."""
    cog = DevCog(bot)
    await bot.add_cog(cog)  # Add cog and command help info.
    # Dev is a shipped TBB module with intentional access to the core command toggle lists.
    # pylint: disable-next=protected-access
    bot._core_slash_commands.extend([cog.slash_ping, cog.slash_lasterror, cog.slash_roleids, cog.slash_channelids])
    # pylint: disable-next=protected-access
    bot._core_prefix_commands.extend([cog.ping, cog.lasterror, cog.roleids, cog.channelids])
    bot.add_module(
        "Dev",
        "[Travus](https://github.com/Travus):\n\tEval command\n\tRoleID command\n\tChannelID command\n\tLast error "
        "command\n\tPing command\n\n[Rapptz](https://github.com/Rapptz):\n\tSudo command",
        DevCog.usage,
        """This module includes developer functionality that supply information useful for programming, such as IDs,
        as well as some debug and testing options such as code execution and remote command execution. Also allows
        checking the most recent error.""",
        "[Rapptz](https://github.com/Rapptz):\n\tEval example",
    )
    bot.add_command_help(DevCog.eval, "Dev", None, ["return 4 + 7", "return channel.id"])
    bot.add_command_help(DevCog.sudo, "Dev", None, ["travus bot_room help", "118954681241174016 about dev"])
    bot.add_command_help(DevCog.roleids, "Dev", {"perms": ["Manage Roles"]}, ["all bot_room", "all dm", "muted"])
    bot.add_command_help(DevCog.lasterror, "Dev", {"perms": ["Administrator"]}, [""])
    bot.add_command_help(DevCog.ping, "Dev", None, [""])
    bot.add_command_help(DevCog.sync, "Dev", None, ["", "guild"])
    bot.add_command_help(DevCog.slash_ping, "Dev", None, [""])
    bot.add_command_help(DevCog.slash_lasterror, "Dev", None, [""])
    bot.add_command_help(DevCog.slash_roleids, "Dev", None, ["", "@Moderator"])
    bot.add_command_help(DevCog.slash_channelids, "Dev", None, ["", "#general"])
    bot.add_command_help(
        DevCog.channelids, "Dev", {"perms": ["Manage Channels"]}, ["all bot_room", "all dm", "general"]
    )


async def teardown(bot: tbb.TravusBotBase):
    """Teardown function ran when module is unloaded."""
    dev_command_names = ["ping", "lasterror", "roleids", "channelids"]
    # Dev is a shipped TBB module with intentional access to the core command toggle lists.
    # pylint: disable-next=protected-access
    bot._core_slash_commands = [com for com in bot._core_slash_commands if com.name not in dev_command_names]
    # pylint: disable-next=protected-access
    bot._core_prefix_commands = [com for com in bot._core_prefix_commands if com.name not in dev_command_names]
    await bot.remove_cog("DevCog")
    bot.remove_module("Dev")
    bot.remove_command_help(DevCog)


class DevCog(commands.Cog):
    """Cog that holds dev functionality."""

    def __init__(self, bot: tbb.TravusBotBase):
        """Initialization function loading bot object for cog."""
        self.bot = bot
        self._last_result = None

    @staticmethod
    def usage() -> str:
        """Returns the usage text."""
        return (
            "**How To Use The Dev Module:**\nThis module is used for development purposes, such as retrieving "
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
            "the bot. Lastly, if the argument is omitted then the response is sent in the current channel."
        )

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
        discord message the response will be uploaded as a text file, online paste, or similar."""
        stdout = StringIO()
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        }
        env.update(globals())
        try:
            exec(f"async def function():\n{indent(self.cleanup_code(body), '  ')}", env)  # pylint: disable=exec-used
        except Exception as e:
            response = f"{e.__class__.__name__}: {e}"
            return await self.bot.send_long_text(ctx, response)
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
                response = value
            else:
                self._last_result = ret
                response = f"{value}{ret}"
        if response:
            await self.bot.send_long_text(ctx, response)

    @commands.is_owner()
    @commands.guild_only()
    @commands.command(name="sudo", usage="<USER> (CHANNEL) <COMMAND>")
    async def sudo(self, ctx: commands.Context, user: Member, channel: tbb.GlobalTextChannel | None, *, cmd: str):
        """This command lets you run commands as another user, optionally in other channels. If the channel argument is
        skipped and the bot fails to parse the argument as a channel it will ignore the channel argument and move on to
        parsing the command instead. In this case the command will be sent from the channel you are currently in."""
        if isinstance(channel, DMChannel):
            await ctx.send("Cannot sudo into DMs.")
            return
        new_msg = copy(ctx.message)
        new_msg.channel = channel or ctx.channel  # type: ignore[assignment]  # Converter resolves to real channel type.
        new_msg.author = new_msg.channel.guild.get_member(user.id)  # type: ignore[union-attr]  # DM filtered above.
        if new_msg.author is None:
            await ctx.send("Target user is not in target server.")
            return
        assert ctx.prefix is not None
        new_msg.content = ctx.prefix + cmd
        new_ctx = await self.bot.get_context(new_msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.command(name="roleids", aliases=["roleid"], usage="<ROLE/all> (OUTPUT CHANNEL/dm)")
    async def roleids(self, ctx: commands.Context, role: Role | str, resp_channel: tbb.GlobalTextChannel | None):
        """This command gives you role IDs of one or all roles in the server depending on if a role or `all` is passed
        along. You can also pass along a channel, in this server or otherwise, in which case the response is sent in
        that channel. Sending `dm` instead of a channel will send you the result in direct messages."""
        assert ctx.guild is not None
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
    async def channelids(
        self,
        ctx: commands.Context,
        channel: tbb.GlobalChannel | str,
        resp_channel: tbb.GlobalTextChannel | None,
    ):
        """This command gives you channel IDs of one or all channels in the server depending on if a channel or `all`
        is passed along. You can also pass along a second channel, in this server or otherwise, in which case the
        response is sent in that channel. Sending `dm` instead of a second channel will send you the result in direct
        messages."""
        assert ctx.guild is not None
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
                response = f"{channel.name}: {channel.id}"  # type: ignore[union-attr]
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

    @commands.is_owner()
    @commands.command(name="sync", usage="(guild)")
    async def sync(self, ctx: commands.Context, scope: str | None = None):
        """This command manually syncs the slash command tree with Discord. Use `guild` to sync only to the current
        server. Without arguments it syncs globally. This is a recovery tool for when automatic sync fails."""
        if scope and scope.lower() == "guild":
            if ctx.guild is None:
                await ctx.send("Cannot sync to guild from DMs.")
                return
            await ctx.send("Syncing command tree to guild, this may take a moment...")
            await self.bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"Command tree synced to guild `{ctx.guild.name}`.")
        else:
            await ctx.send("Syncing command tree globally, this may take a moment...")
            await self.bot.tree.sync()
            await ctx.send("Command tree synced globally.")

    @app_commands.command(name="ping", description="Shows the bot's latency to Discord.")
    async def slash_ping(self, interaction: Interaction):
        """This command shows the latency from the bot to Discord's servers. Can be used to check if the bot is
        responsive."""
        await self.bot.send_response(interaction, f"Pong! ({round(self.bot.latency * 1000, 2)}ms)")

    @app_commands.command(name="lasterror", description="Shows the last error the bot encountered.")
    @app_commands.guild_only()
    @app_commands.default_permissions(administrator=True)
    async def slash_lasterror(self, interaction: Interaction):
        """This command shows the last error the bot has encountered. Errors encountered while loading modules will
        not be listed by this command. To see the last error encountered while loading modules see the `/module
        lasterror` command. This command retains this information until another error replaces it, or the bot shuts
        down."""
        if self.bot.last_error:
            error = tbb.clean_no_ctx(self.bot, interaction.guild, self.bot.last_error)
            await self.bot.send_response(interaction, error)
        else:
            await self.bot.send_response(interaction, "There have not been any errors since the last restart.")

    @app_commands.command(name="roleids", description="Shows role IDs for one or all roles in the server.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_roles=True)
    @app_commands.describe(role="Role to get the ID for, or omit for all roles.")
    async def slash_roleids(self, interaction: Interaction, role: Role | None = None):
        """This command gives you role IDs of one or all roles in the server. If a role is provided, shows only that
        role's ID. If omitted, shows all role IDs."""
        assert interaction.guild is not None
        if role is None:
            paginator = commands.Paginator()
            for _role in reversed(interaction.guild.roles):
                paginator.add_line(f"{_role.name}: {_role.id}")
            for page in paginator.pages:
                await self.bot.send_response(interaction, page)
        else:
            await self.bot.send_response(interaction, f"```{role.name}: {role.id}```")

    @app_commands.command(name="channelids", description="Shows channel IDs for one or all channels in the server.")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.describe(channel="Channel to get the ID for, or omit for all channels.")
    async def slash_channelids(self, interaction: Interaction, channel: discord.abc.GuildChannel | None = None):
        """This command gives you channel IDs of one or all channels in the server. If a channel is provided, shows
        only that channel's ID. If omitted, shows all channel IDs."""
        assert interaction.guild is not None
        if channel is None:
            paginator = commands.Paginator()
            for _channel in interaction.guild.channels:
                paginator.add_line(f"{_channel.name}: {_channel.id}")
            for page in paginator.pages:
                await self.bot.send_response(interaction, page)
        else:
            name = getattr(channel, "name", str(channel.id))
            await self.bot.send_response(interaction, f"```{name}: {channel.id}```")
