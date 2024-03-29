from sys import version, argv, executable
from datetime import datetime
from os import getpid, execv, listdir, path

import discord
from discord.ext import commands
from yt_dlp import version as ytver
import psutil

from angel6 import BOT_VER

bot_uptime = datetime.now()
mem_info = psutil.Process(getpid())
total_mem = psutil.virtual_memory().total / float(2**20)
mem = mem_info.memory_info()[0] / float(2**20)
# pylint: disable=E1101
discord_version = discord.__version__
WRAPPER_USED = discord.__title__.capitalize()


class System(commands.Cog):
    """A class representing a system cog with various commands related to system information."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def uptime(self, ctx):
        """Shows the bot's uptime.

        This command displays how long the bot has been running since it was started.

        Args:
            ctx (discord.ext.commands.Context): The command context.
        """
        current_time = datetime.now()
        difference = current_time - bot_uptime
        hours, remainder = divmod(int(difference.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        text = f"{hours}h {minutes}m {seconds}s"
        embed = discord.Embed(colour=discord.Color.blurple())
        embed.add_field(name="Uptime", value=text)
        embed.add_field(
            name="Bot started at", value=bot_uptime.strftime("%Y-%m-%d %H:%M:%S")
        )
        embed.set_footer(text="Angel$IX", icon_url=self.bot.user.avatar.url)
        await ctx.reply(embed=embed)

    @commands.command(pass_context=True, aliases=["info", "debug"])
    async def stats(self, ctx):
        """Shows the bot's statistics and system resource usage.

        This command displays various statistics about the bot and the host system,
        including CPU usage, memory usage, Python version, and more.

        Args:
            ctx (discord.ext.commands.Context): The command context.
        """
        embed = discord.Embed(
            title="System Resource Usage and Statistics",
            description="See bot host statistics.",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Angel$IX version", value=BOT_VER, inline=False)
        embed.add_field(
            name="CPU Usage", value=f"`{psutil.cpu_percent()}%`", inline=True
        )
        embed.add_field(
            name="Memory Usage", value=f"`{mem:.0f}MB/{total_mem:.0f}MB`", inline=True
        )
        embed.add_field(name="API Wrapper:", value=f"`{WRAPPER_USED}`", inline=True)
        embed.add_field(name="Python Version", value=f"`{version}`", inline=False)
        embed.add_field(
            name="YTdl Version", value=f"`{ytver.__version__}`", inline=True
        )
        embed.add_field(
            name=f"{WRAPPER_USED} Version",
            value=f"`{discord_version}`",
            inline=True,
        )
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def cog(self, ctx, option: str = None, cog_name: str = None):
        """Performs actions on a cog or shows cog status.

        Available options:
        - reload: Reloads the specified cog.
        - start: Loads and adds the specified cog.
        - stop: Unloads and stops the specified cog.
        - status: Displays the status of all cogs (enabled or not).

        Args:
            ctx (discord.ext.commands.Context): The command context.
            option (str): The action to perform on the cog (reload, add, stop, status).
            cog_name (str, optional): The name of the cog to perform the action on.
        """
        embed = discord.Embed()
        if option in ["status", None]:
            cogs_status = "\n".join(
                f"{cog[:-3]:<15} {'✅' if f'cogs.{cog[:-3]}' in self.bot.extensions else '❌'}"
                for cog in listdir("cogs") if cog.endswith(".py")
            )
            embed = discord.Embed(
                title="Cog Status",
                description=f"```\n{cogs_status}\n```",
                color=discord.Color.blurple(),
            )
            await ctx.reply(embed=embed)
            return

        if option not in ["reload", "start", "stop", "status"]:
            embed = discord.Embed(
                title="Invalid Option",
                description="Please provide a valid option (reload, start, stop, status).",
                color=discord.Color.brand_red(),
            )
            await ctx.reply(embed=embed)
            return

        if not cog_name:
            embed = discord.Embed(
                title="Cog Name Missing",
                description="Please provide the name of the cog.",
                color=discord.Color.brand_red(),
            )
            await ctx.reply(embed=embed)
            return

        if cog_name == "system" and option != "reload":
            error_embed = discord.Embed(
                title="Cog Blacklisted",
                description="The 'system' cog is blacklisted since it provides the 'cog' command.",
                color=discord.Color.brand_red(),
            )
            await ctx.reply(embed=error_embed)
            return

        cog_path = f"cogs/{cog_name}"
        if option == "reload":
            if path.exists(f"{cog_path}.py"):
                self.bot.reload_extension(f"cogs.{cog_name}")
                embed = discord.Embed(
                    title="Cog Reloaded",
                    description=f"The cog `{cog_name}` has been successfully reloaded!",
                    color=discord.Color.brand_green(),
                )
            else:
                embed = discord.Embed(
                    title="Cog Not Found",
                    description=f"The cog `{cog_name}` does not exist.",
                    color=discord.Color.brand_red(),
                )

        elif option == "start":
            try:
                self.bot.load_extension(f"cogs.{cog_name}")
                embed = discord.Embed(
                    title="Cog Added",
                    description=f"The cog `{cog_name}` has been successfully added!",
                    color=discord.Color.brand_green(),
                )
            except commands.ExtensionError as err:
                embed = discord.Embed(
                    title="Cog Load Error",
                    description=f"An error occurred while loading the cog: `{err}`",
                    color=discord.Color.brand_red(),
                )

        elif option == "stop":
            if f"cogs.{cog_name}" in self.bot.extensions:
                self.bot.unload_extension(f"cogs.{cog_name}")
                embed = discord.Embed(
                    title="Cog Unloaded",
                    description=f"The cog `{cog_name}` has been successfully unloaded!",
                    color=discord.Color.brand_green(),
                )
            else:
                embed = discord.Embed(
                    title="Cog Not Found",
                    description=f"The cog `{cog_name}` is not currently loaded.",
                    color=discord.Color.brand_red(),
                )

        await ctx.reply(embed=embed)

    @commands.command(aliases=["reboot"])
    @commands.has_permissions(ban_members=True)
    async def restart(self, ctx, arg=""):
        """Restarts the bot.

        This command restarts the bot process, optionally with a specific argument.

        Args:
            ctx (discord.ext.commands.Context): The command context.
            arg (str, optional): An additional argument to pass when restarting. Defaults to "".
        """
        argv.append(arg)
        if arg == "debug":
            await ctx.send("Debug on!")
        if arg == "reset":
            await ctx.send("Reseting environment, check console!")
        await ctx.reply(" Restarting, please allow 5 seconds for this. ")
        execv(executable, ["python3"] + argv)

    @commands.command(aliases=["latency"])
    async def ping(self, ctx):
        """shows the bot and Discord API latency"""
        start_time = datetime.now()
        embed = discord.Embed(title="Pinging...", color=discord.Color.brand_red())
        message = await ctx.reply(embed=embed)
        end_time = datetime.now()
        bot_latency = (end_time - start_time).total_seconds() * 1000
        api_latency = self.bot.latency * 1000
        embed.title = "Ping"
        embed.description = (
            f"**Bot: {bot_latency:.2f}ms**\n**API: {api_latency:.2f}ms**"
        )
        embed.color = discord.Color.brand_green()
        await message.edit(embed=embed)


def setup(bot):
    """Add the System cog to the bot.

    This function is called by the bot to add the System cog to its extensions.

    Parameters:
        bot (discord.ext.commands.Bot): The Discord bot instance.
    """
    bot.add_cog(System(bot))
