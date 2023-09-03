from asyncio import sleep as asyncsleep
from io import BytesIO
from os import getpid

import discord
from discord.ext import commands, tasks
from matplotlib.pyplot import clf, plot, scatter, xlabel, ylabel, legend, title, xlim, xticks, ylim, savefig, grid
from psutil import cpu_percent, Process

class StatLogger(commands.Cog):
    """
    A Discord bot cog for logging and displaying statistics and performance metrics.

    This cog collects data on bot latency, CPU load, and RAM usage over time and provides a command
    to display the collected data in the form of a graph along with statistics.

    Attributes:
        bot (commands.Bot): The Discord bot instance this cog is associated with.
        latency_data (list): A list to store bot latency data.
        cpu_data (list): A list to store CPU load data.
        ram_data (list): A list to store RAM usage data.
        cpu_load (float): The current CPU load percentage.
        mem_info (psutil.Process): Information about the bot's memory usage.
        ram_usage (float): The current RAM usage in megabytes.
    """
    def __init__(self, bot):
        """
        Initializes the StatLogger cog.

        Args:
            bot (commands.Bot): The Discord bot instance this cog is associated with.
        """

        self.bot = bot

        self.latency_data = []
        self.cpu_data = []
        self.ram_data = []

        self.update_data.start()


    @tasks.loop(minutes=1)
    async def update_data(self):
        """
        A task to update and collect bot statistics data at regular intervals.

        This task collects data on bot latency, CPU load, and RAM usage and stores it in lists.
        It also removes old data to keep the list size within a specified limit.

        Note:
            This method is called automatically as a scheduled task.
        """

        # Make sure the bot is ready before logging anything
        await asyncsleep(1)

        cpu_load = cpu_percent()
        mem_info = Process(getpid())
        ram_usage = mem_info.memory_info()[0] / float(2**20)

        latency = self.bot.latency * 1000  # Convert to milliseconds
        if latency:
            self.latency_data.append(latency)

        self.cpu_data.append(cpu_load)
        self.ram_data.append(ram_usage)

        if len(self.latency_data) > 60:
            self.latency_data.pop(0)
            self.cpu_data.pop(0)
            self.ram_data.pop(0)

    @commands.command()
    async def log(self, ctx):
        """
        Command to generate and send bot statistics graph and data as an embed.

        This command generates a graph of bot statistics over time, including latency, CPU load, and RAM usage.
        It also calculates and displays statistics such as the latest values and averages.

        Args:
            ctx (commands.Context): The context of the command.
        """

        # Generate and send graphs
        clf()
        time_range = list(range(0, len(self.latency_data)))  # Create a range of positive values

        if len(self.latency_data) == 1:
            # Only one data point, plot as a scatter point
            scatter([0], self.latency_data, label="Latency (ms)")
        else:
            # Plot as a line if more than one data point
            plot(time_range, self.latency_data, label="Latency (ms)")

        if len(self.cpu_data) == 1:
            # Only one data point, plot as a scatter point
            scatter([0], self.cpu_data, label="CPU Load (%)")
        else:
            # Plot as a line if more than one data point
            plot(time_range, self.cpu_data, label="CPU Load (%)")

        if len(self.ram_data) == 1:
            # Only one data point, plot as a scatter point
            scatter([0], self.ram_data, label="RAM Usage (MB)")
        else:
            # Plot as a line if more than one data point
            plot(time_range, self.ram_data, label="RAM Usage (MB)")

        xlabel("Time (minutes)")
        ylabel("Value")
        legend()
        title("Bot Stats Over Time")

        # Calculate the average values
        avg_latency = sum(self.latency_data) / len(self.latency_data)
        avg_cpu = sum(self.cpu_data) / len(self.cpu_data)
        avg_ram = sum(self.ram_data) / len(self.ram_data)

        # Determine the maximum value among all data points
        max_value = max(max(self.latency_data), max(self.cpu_data), max(self.ram_data)) + 10

        # Set the Y-axis limits dynamically
        ylim(0, max_value)

        # Set the x-axis limits to 1 hour period
        xlim(0, 60)

        # Set custom x-axis ticks and labels
        xticks([0, 10, 20, 30, 40, 50, 60], ["0", "10", "20", "30", "40", "50", "60"])

        # Add a grid to the graph
        grid(True)

        # Create a buffer for the temporary image file
        img_buffer = BytesIO()
        savefig(img_buffer, format='png', bbox_inches="tight", dpi=300)
        img_buffer.seek(0)

        # Create an embed for the stats
        embed = discord.Embed(
            title="Bot Stats",
            description="Statistics and Performance Metrics",
            color=discord.Color.blurple(),
        )
        embed.set_image(url="attachment://bot_stats.png")
        embed.add_field(name="Latest Latency", value=f"{self.latency_data[-1]:.2f} ms", inline=True)
        embed.add_field(name="Latest CPU Load", value=f"{self.cpu_data[-1]:.2f}%", inline=True)
        embed.add_field(name="Latest RAM Usage", value=f"{self.ram_data[-1]:.2f} MB", inline=True)
        embed.add_field(name="Average Latency", value=f"{avg_latency:.2f} ms", inline=True)
        embed.add_field(name="Average CPU Load", value=f"{avg_cpu:.2f}%", inline=True)
        embed.add_field(name="Average RAM Usage", value=f"{avg_ram:.2f} MB", inline=True)

        # Send the embed along with the graph
        await ctx.send(embed=embed, file=discord.File(img_buffer, filename="bot_stats.png"))

def setup(bot):
    """
    A function to set up and add the StatLogger cog to a Discord bot.

    Args:
        bot (commands.Bot): The Discord bot instance to add the cog to.
    """
    bot.add_cog(StatLogger(bot))