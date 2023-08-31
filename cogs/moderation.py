import discord
from discord.ext import commands

from angel6 import LOG_CHAN_ID


class Moderation(commands.Cog):
    """
    A class representing a moderation cog with various moderation commands.

    This cog provides a set of commands for moderating server activities,
    including kicking, muting, unmuting, banning, unbanning, warning, message wiping,
    and managing roles.
    """
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """kicks a user"""

        if member == ctx.author:
            await ctx.reply("Can't kick yourself! ...baka!!")
        elif member.top_role >= ctx.author.top_role:
            await ctx.reply("Yo, you can only kick members lower than yourself lmao")
        else:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="kicked",
                description=f"{member.mention} was kicked out for {reason}",
            )
            await ctx.channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        """mutes a user"""
        if member == ctx.author:
            await ctx.reply("You cannot mute yourself.")
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.reply(f"You cannot mute {member.mention}.")
            return

        guild = ctx.guild
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            for channel in guild.channels:
                await channel.set_permissions(
                    muted_role,
                    speak=False,
                    send_messages=False,
                    read_message_history=True,
                    read_messages=True,
                    create_private_threads=False,
                    create_public_threads=False,
                )

        try:
            await member.add_roles(muted_role, reason=reason)
        except discord.errors.Forbidden:
            await ctx.reply("I don't have permission to mute this user.")
            return

        embed = discord.Embed(
            title="Muted",
            description=(
                f"{member.mention} has been muted{' for ' + reason if reason else ''}"
            ),
            color=discord.Color.blurple(),
        )
        await ctx.reply(embed=embed)

        try:
            await member.send(f"You were muted{' for ' + reason if reason else ''}")
        except discord.errors.Forbidden:
            # If member has DMs disaled, we don't want to error out
            pass

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmutes a user"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        if not muted_role:
            await ctx.reply("Muted role not found.")
            return

        if muted_role not in member.roles:
            await ctx.reply(f"{member.name} is not muted.")
            return

        await member.remove_roles(muted_role)
        await ctx.reply(f"Unmuted {member.mention}")
        await member.send(f"Unmuted in {ctx.guild.name}. Welcome back!")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member = None, *, reason: str = None):
        """Bans the specified user"""
        if not member:
            return await ctx.reply("You need to specify who to ban.")

        if member == ctx.author:
            return await ctx.reply("Can't ban yourself, idiot.")

        if member.top_role >= ctx.author.top_role:
            return await ctx.reply("You can only ban members lower than yourself.")

        try:
            await member.ban(reason=reason)
        except (discord.errors.Forbidden, discord.errors.HTTPException) as err:
            return await ctx.reply(
                f"Failed to ban {member.mention}."
                f"Please check my permissions and role hierarchy.\nError: {err}"
            )

        ban_reason = "was banned" if not reason else f"was banned for {reason}"
        embed = discord.Embed(
            title="Bye Bye",
            description=f"{member.mention} {ban_reason}.",
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Unbans a user."""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            await ctx.reply(f"{user} has been unbanned.")
        except discord.errors.Forbidden:
            await ctx.reply("I don't have permissions to unban that user.")
        except discord.errors.NotFound:
            await ctx.reply("I couldn't find that user in the ban list.")
        except commands.BadArgument:
            await ctx.reply("Please provide a valid user ID.")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member = None, *, reason=None):
        """Warns a user and logs the warning to a specified channel"""
        if not member or member == ctx.author:
            await ctx.reply("You need to specify someone to warn!")
            return

        embed2 = discord.Embed(
            title="Warned🗡️",
            description=(
                "You were"
                f" warned.{' Now behave.' if not reason else f' Reason: {reason}'}"
            ),
            color=discord.Colour.blurple(),
        )

        embed = discord.Embed(
            title="Warned",
            description=(
                f"{member.mention} was"
                f" warned{'.' if not reason else f', reason: {reason}'}"
            ),
            color=discord.Colour.blurple(),
        )

        await ctx.reply(embed=embed)
        try:
            await member.send(embed=embed2)
        except discord.errors.Forbidden:
            # If member has DMs disaled, we don't want to error out
            pass

        if not LOG_CHAN_ID:
            log_channel = self.bot.get_channel(int(LOG_CHAN_ID))
            log_embed = discord.Embed(
                title="Member Warned",
                description=(
                    f"{ctx.author.mention} warned"
                    f" {member.mention}{'.' if not reason else f', reason: {reason}'}"
                ),
                color=discord.Colour.blurple(),
            )
            await log_channel.send(embed=log_embed)

    @commands.command(aliases=["clear"])
    @commands.has_permissions(ban_members=True)
    async def wipe(self, ctx, amount: int = 20):
        """wipes 20 messages or the number specified"""
        if amount <= 0 or amount > 10000:  # Check that amount is within range
            return await ctx.send("Amount must be between 1 and 10000.")
        await ctx.channel.purge(limit=amount)
        await ctx.channel.send(f"Cleanup Complete, deleted {amount} messages")

    @commands.command(pass_context=True)
    @commands.has_permissions(ban_members=True)
    async def role(
        self, ctx, action: str, user: discord.Member, user_role: discord.Role = None
    ):
        """Add or remove a role from a user."""
        if action not in ["add", "remove"]:
            await ctx.reply("Invalid action specified. Use 'add' or 'remove'.")
            return

        if not user_role:
            await ctx.reply(f"Make sure to specify what role to {action}!")
            return

        if user_role >= ctx.author.top_role:
            await ctx.reply(
                f"Can't {action} {user_role} since it's higher than"
                f" {ctx.author.top_role}."
            )
            return

        if action == "add":
            await user.add_roles(user_role)
            await ctx.reply(
                embed=discord.Embed(
                    title="Role Added",
                    description=(
                        f"{user.mention} was given the {user_role.mention} role."
                    ),
                    color=discord.Color.green(),
                )
            )
        elif action == "remove":
            if user_role == ctx.author.top_role and user == ctx.author:
                await ctx.reply(
                    f"Can't remove role \"{user_role}\" as it's your highest role."
                )
                return

            await user.remove_roles(user_role)
            await ctx.reply(
                embed=discord.Embed(
                    title="Role Removed",
                    description=(
                        f"{user.mention} was removed from the {user_role.mention} role."
                    ),
                    color=discord.Color.red(),
                )
            )


def setup(bot):
    bot.add_cog(Moderation(bot))
