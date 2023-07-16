from datetime import datetime

import discord
from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["members"])
    async def users(self, ctx):
        """Shows the total number of members, showing bots separately"""
        member_count = len([member for member in ctx.guild.members if not member.bot])
        bot_count = len([member for member in ctx.guild.members if member.bot])
        embed = discord.Embed(
            title=f"Total members in {ctx.guild.name}",
            description=f"**Members: {member_count}**\n**Bots: {bot_count}**",
            color=discord.Color.blurple(),
        )
        await ctx.reply(embed=embed)

    @commands.command(aliases=["AV", "av", "pfp"])
    async def avatar(self, ctx, user: discord.Member = None):
        """Grabs the avatar of a user.

        If no user is mentioned, it retrieves the avatar of the command invoker.
        """
        if user is None:
            user = ctx.message.author

        embed = discord.Embed(
            title=f"{user.display_name}'s Avatar", color=discord.Color.blurple()
        )
        embed.set_image(url=user.avatar.url)

        await ctx.reply(embed=embed)

    @commands.command(pass_context=True)
    async def userinfo(self, ctx, *, user: discord.Member = None):
        """Shows userinfo"""
        if user is None:
            user = ctx.author

        date_format = "%a, %d %b %Y %I:%M %p"
        embed = discord.Embed(color=discord.Color.blurple(), description=user.mention)

        embed.set_author(name=user.display_name, icon_url=user.avatar.url)
        embed.set_thumbnail(url=user.avatar.url)

        embed.add_field(name="Joined", value=user.joined_at.strftime(date_format))

        members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
        join_position = members.index(user) + 1
        if 11 <= join_position <= 13:
            join_position_suffix = "th"
        else:
            join_position_suffix = {1: "st", 2: "nd", 3: "rd"}.get(
                join_position % 10, "th"
            )
        embed.add_field(
            name="Join position", value=f"{join_position}{join_position_suffix}"
        )

        embed.add_field(name="Registered", value=user.created_at.strftime(date_format))
        embed.add_field(name="ID", value=user.id, inline=True)

        if len(user.roles) > 1:
            role_string = " ".join([r.mention for r in user.roles][1:])
            embed.add_field(
                name=f"Roles [{len(user.roles)-1}]", value=role_string, inline=True
            )

        embed.set_footer(
            text=f"Information last updated: {datetime.utcnow().strftime(date_format)}"
        )

        await ctx.reply(embed=embed)

    @commands.command()
    async def serverinfo(self, ctx):
        """Displays server information."""
        name = str(ctx.guild.name)
        description = f"Official {ctx.guild.name} server"
        owner = str(ctx.guild.owner)
        servid = str(ctx.guild.id)
        member_count = str(ctx.guild.member_count)
        channels = (
            f"Text: {len(ctx.guild.text_channels)}\nVoice:"
            f" {len(ctx.guild.voice_channels)}"
        )
        roles = str(len(ctx.guild.roles))
        created = f"{ctx.guild.created_at:%B %d, %Y, %I:%M %p}"
        # Honestly not sure i need to do this, all servers probably have a pfp
        try:
            icon = ctx.guild.icon.url
        except AttributeError:
            icon = None

        embed = discord.Embed(
            title=name + " <3", description=description, color=discord.Color.blurple()
        )

        if icon:
            embed.set_thumbnail(url=icon)

        embed.add_field(name="Owner", value=owner, inline=True)
        embed.add_field(name="Server ID", value=servid, inline=True)
        embed.add_field(name="Channels", value=channels, inline=True)
        embed.add_field(name="Roles", value=roles, inline=True)
        embed.add_field(name="Member Count", value=member_count, inline=True)
        embed.add_field(name="Created", value=created, inline=True)

        embed.set_footer(
            text="Thanks for being a part of our server!",
            icon_url=ctx.author.avatar.url,
        )

        await ctx.reply(embed=embed)

    @commands.command()
    async def invites(self, ctx, user: discord.Member = None):
        """Shows how many people someone has invited"""
        user_name = user or ctx.author
        total_invites = 0
        for invite in await ctx.guild.invites():
            if invite.inviter == user_name:
                total_invites += invite.uses
        embed = discord.Embed(
            title=(
                f"{user_name} has invited"
                f" {total_invites} member{'' if total_invites == 1 else 's'} to the"
                " server!"
            ),
            color=discord.Colour.blurple(),
        )
        embed.set_author(name=user_name.display_name, icon_url=user_name.avatar.url)
        await ctx.reply(embed=embed)

    @commands.command(pass_context=True, aliases=["cred", "credits", "about"])
    async def credit(self, ctx):
        """Shows bot credits."""
        owner = await self.bot.fetch_user(1082831541400518737)
        maintainer = await self.bot.fetch_user(347387857574428676)

        embed = discord.Embed(
            title="Bot Credits:",
            description=(
                f"Owner: {owner.mention}\n"
                f"Bot maintainer: {maintainer.mention}\n"
                "Ask them anything! 24/7. Feel free to add them as a friend."
            ),
            color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)

    @commands.command()
    async def support(self, ctx, *, message: str = None):
        """Shows support server link and latest release."""
        if message in ["release", "changelog"]:
            await ctx.send(
                "Latest bot release: \n"
                " https://github.com/maj113/Angel6/releases/latest"
            )
            return

        embed = discord.Embed(
            title="Support server",
            description=(
                "Need help with the bot? https://discord.gg/yVhHpP9hkc \nWant to"
                " contribute to the bot? https://github.com/maj113/Angel6"
            ),
            color=discord.Color.blurple(),
        )
        embed.set_image(
            url=(
                "https://media.discordapp.net/attachments/736563784318976040/"
                "1087089496450928650/paintdotnet_LFkzPDrQML.png"
            )
        )
        await ctx.reply(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))
