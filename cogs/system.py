from sys import version, argv, executable
from datetime import datetime
from os import getpid, execv

import discord
from discord.ext import commands
from yt_dlp import version as ytver
import psutil

from angel6 import BOT_VER

bot_uptime = datetime.now()
mem_info = psutil.Process(getpid())
total_mem = psutil.virtual_memory().total / float(2**20)
mem = mem_info.memory_info()[0] / float(2**20)
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
            value=f"`{discord._version.__version__}`",
            inline=True,
        )
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def reload(self, ctx):
        """Reloads the Bot cog.

        This command reloads the "cogs.music" extension, allowing for updates to take effect.

        Args:
            ctx (discord.ext.commands.Context): The command context.
        """
        try:
            # will need to make this work with more cogs once i get that working
            self.bot.reload_extension("cogs.music")
            await ctx.reply("Cogs successfully reloaded!")
        except commands.ExtensionError as err:
            await ctx.reply(f"An error occurred while reloading the cog: `{err}`")

    @commands.command(aliases=["reboot"])
    @commands.has_permissions(ban_members=True)
    async def restart(self, ctx, arg=""):
        """restarts the bot"""
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
    bot.add_cog(System(bot))
