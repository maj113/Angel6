import os
from random import randint
from datetime import datetime
from sys import argv, executable, version


import discord
import psutil
from aioconsole import ainput
from requests import get, Timeout
from dotenv import load_dotenv
from discord import _version
from discord import __title__ as d_name
from discord.ext import commands, tasks
from yt_dlp import version as ytver

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHAN_ID = os.getenv("LOGGING_CHANNEL_ID")
JL_CHAN_ID = os.getenv("JOIN_LEAVE_CHANNEL_ID")
GEN_CHAN_ID = os.getenv("GENERAL_CHANNEL_ID")
BOT_VER = "**2.3.1-Rewrite** <https://github.com/maj113/Angel6/releases/latest>"
CREDITS_IMAGE = "https://cdn.discordapp.com/attachments/1083114844875669604/1083121342150361118/1676492485892.png"

intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix="~",
    activity=discord.Game(name="Greatest bot alive"),
    intents=intents,
)


async def set_env_var(env_var_name : str, prompt_text : str, force_reset_env : bool):
    """
    Sets an environment variable if it is not already set or if `force_reset_env` is True.

    Parameters:
        - env_var_name (str): The name of the environment variable.
        - prompt_text (str): The prompt text displayed when the environment variable needs to be set.
        - force_reset_env (bool): If True, the environment variable will be reset even if it is already set.

    Returns:
        - bool: True if the environment variable was set or reset, False otherwise.
    """
    value = os.getenv(env_var_name)
    if value is None:
        value = int(input(prompt_text))
        with open(".env", "a", encoding='utf-8') as envfile:
            envfile.write(f"\n{env_var_name}={value}")
        return True
    if value == "" or force_reset_env:
        value = int(input(prompt_text))
        with open(".env", "r+", encoding='utf-8') as envfile:
            content = envfile.read()
            changed = content.replace(f"{env_var_name}=", f"{env_var_name}={value}")
            envfile.seek(0)
            envfile.write(changed)
            envfile.truncate()
        return True
    return False


async def checkenv():
    """
    Checks the environment variables and prompts the user to set them if necessary.

    Returns:
        - bool: True if the environment variables were set or reset, False otherwise.
    """
    config_options = [
        ("LOGGING_CHANNEL_ID", "Input logging channel ID "),
        ("JOIN_LEAVE_CHANNEL_ID", "Input join/leave channel ID "),
        ("GENERAL_CHANNEL_ID", "Input general channel ID "),
    ]
    for env_var_name, prompt_text in config_options:
        restart_bot = await set_env_var(env_var_name, prompt_text, argv[-1] == "reset")
    return restart_bot


@bot.event
async def on_ready():
    """
    Executes when the bot is ready and connected to the Discord server.
    Performs setup tasks and sends a bot status message to the logging channel.
    """
    print(f"Logged in as:\n{bot.user.name}\n{bot.user.id}")

    if await checkenv():
        print("Setup complete, Rebooting")
        os.execv(executable, ["python3"] + argv)

    embed = discord.Embed(
        title="Bot Settings",
        description="Current bot settings and status",
        color=discord.Color.blurple(),
    )

    # Add information about the bot version
    embed.add_field(name="Bot Version:", value="Angel$IX " + BOT_VER, inline=False)

    # Add information about the logging channel
    log_channel = bot.get_channel(int(LOG_CHAN_ID))
    embed.add_field(
        name=f"Logging Channel: {log_channel.mention}", value="", inline=False
    )

    # Add information about the join/leave channel
    jl_channel = bot.get_channel(int(JL_CHAN_ID))
    embed.add_field(
        name=f"Join/Leave Channel: {jl_channel.mention}", value="", inline=False
    )

    # Add information about the general channel
    gen_channel = bot.get_channel(int(GEN_CHAN_ID))
    embed.add_field(
        name=f"General Channel: {gen_channel.mention}", value="", inline=False
    )

    # Add information about the API latency
    api_latency = f"{(bot.latency * 1000):.0f}ms"
    embed.add_field(name=f"API Latency: {api_latency}", value="", inline=False)

    # Get the member object for the bot creator in the guild and add it to the embed
    guild = bot.guilds[0]
    bot_member = guild.get_member(347387857574428676)
    footer_text = f"Bot made by {bot_member.name}"
    embed.set_footer(text=footer_text)

    # Send the message to the logging channel
    await log_channel.send(embed=embed)
    await log_channel.send(CREDITS_IMAGE)
    if not asbotmain.is_running():
        await asbotmain.start()

# NextCord doesn't support recursive
bot.load_extension("cogs", recursive=True)


@bot.event
async def on_message(message):
    """
    Event handler for incoming messages.

    Prints the message content, including attachments if present.
    Then, processes the message for bot commands.

    Parameters:
    - message: The received message object.
    """
    if message.author.id != bot.user.id:
        if message.attachments:
            attachments = "\n".join(a.url for a in message.attachments)
            msgcontent = f"{message.guild}/{message.channel}/{message.author.name}> {message.content}\n{attachments}"
        else:
            msgcontent = f"{message.guild}/{message.channel}/{message.author.name}> {message.content}"

        (msgcontent)
        await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    """
    Event handler for when a member joins a guild.

    Sends a welcome message to the designated join/leave channel, including the member's mention,
    the total number of members in the guild, the member's avatar, and the guild's name and icon.
    If a general channel is specified, sends a direct message to the member with an invitation to that channel.
    Otherwise, sends a default welcome message as a direct message to the member.

    Parameters:
    - member: The member who joined the guild.
    """
    channel = bot.get_channel(int(JL_CHAN_ID))
    embed = discord.Embed(
        colour=discord.Colour.blurple(),
        description=f"{member.mention} joined, Total Members: {len(list(member.guild.members))}",
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(
        text=member.guild,
        icon_url=member.guild.icon.url if member.guild.icon else None
    )
    await channel.send(embed=embed)

    general_channel_id = os.getenv("GENERAL_CHANNEL_ID")
    description = (
        "yo! I'm Mutiny's Personal Bot, proceed to General to talk:)"
        if general_channel_id is None or general_channel_id == ""
        else f"yo! I'm Mutiny's Personal Bot, proceed to <#{int(GEN_CHAN_ID)}> to talk:)"
    )
    mbed = discord.Embed(
        colour=discord.Colour.blurple(),
        title="Glad you could find us!",
        description=description,
    )
    await member.send(embed=mbed)
    #with open('muted.json', "r") as jsonmute:
    #    datamute = json.load(jsonmute)
    #    if member.id in datamute["muted"]:
    #        for guild in bot.guilds:
    #            guildid=(guild.id)
    #        getguild = bot.get_guild(guildid)
    #        mutedRole = discord.utils.get(getguild.roles, name="Muted")
    #        await member.add_roles(mutedRole)


@bot.event
async def on_member_remove(member):
    """
    Event handler for when a member leaves a guild.

    Sends a farewell message to the designated join/leave channel, including the member's mention,
    the updated total number of members in the guild, the member's avatar, and the guild's name and icon.

    Parameters:
    - member: The member who left the guild.
    """
    channel = bot.get_channel(int(JL_CHAN_ID))
    embed = discord.Embed(
        colour=discord.Colour.blurple(),
        description=f"{member.mention} Left us, Total Members: {len(member.guild.members)}",
    )
    embed.set_thumbnail(url=member.avatar.url)
    embed.set_footer(
        text=member.guild,
        icon_url=member.guild.icon.url if member.guild.icon else None
    )
    await channel.send(embed=embed)


@bot.event
async def on_message_delete(message):
    """
    Event handler for when a message is deleted.

    Sends a notification to the designated logging channel,
    including details about the deleted message.

    Parameters:
    - message: The deleted message object.
    """
    deleted = discord.Embed(
        description=f"Message deleted in {message.channel.mention}",
        color=discord.Color.brand_red(),
    ).set_author(name=message.author, icon_url=message.author.avatar.url)

    if message.author.id == bot.user.id:
        return

    channel = bot.get_channel(int(LOG_CHAN_ID))
    if channel is None:
        # LOG_CHAN_ID is not valid or channel is not available
        return

    deleted.add_field(name="Message", value=message.content or "*No content*")
    deleted.timestamp = message.created_at
    await channel.send(embed=deleted)


@bot.event
async def on_guild_channel_create(channel):
    """
    Event handler for when a channel is created in a guild.

    Sends a notification to the designated logging channel,
    including details about the created channel.

    Parameters:
    - channel: The created channel object.
    """
    logging_channel = bot.get_channel(int(LOG_CHAN_ID))
    if not logging_channel:
        # LOG_CHAN_ID is not valid or channel is not available
        return

    async for entry in channel.guild.audit_logs(
        limit=1, action=discord.AuditLogAction.channel_create
    ):
        if entry.target.id == channel.id:
            embed = discord.Embed(
                title="Channel created", color=discord.Colour.brand_green()
            )
            embed.add_field(name="Name", value=channel.name, inline=True)
            embed.add_field(name="Type", value=str(channel.type).title(), inline=True)
            embed.add_field(
                name="Category",
                value=channel.category.name if channel.category else "None",
                inline=True,
            )
            embed.set_footer(
                text=f"ID: {channel.id} • Created by {entry.user}",
                icon_url=entry.user.avatar.url if entry.user.avatar else discord.Embed.Empty,
            )
            await logging_channel.send(embed=embed)


@bot.event
async def on_guild_channel_delete(channel):
    """
    Event handler for when a guild channel is deleted.
    Sends a log message to the logging channel.

    Parameters:
    - channel (discord.abc.GuildChannel): The deleted guild channel.

    Note:
    - Requires a valid logging channel ID in LOG_CHAN_ID constant.
    """

    logging_channel = bot.get_channel(int(LOG_CHAN_ID))

    if not logging_channel:
        # LOG_CHAN_ID is not valid or channel is not available
        return

    async for entry in channel.guild.audit_logs(
        limit=1, action=discord.AuditLogAction.channel_delete
    ):
        if entry.target.id == channel.id:
            embed = discord.Embed(
                title="Channel Deleted", color=discord.Colour.brand_red()
            )
            embed.add_field(name="Name", value=channel.name, inline=True)
            embed.add_field(
                name="Type", value=str(channel.type).title(), inline=True
            )
            embed.add_field(
                name="Category",
                value=channel.category.name if channel.category else "None",
                inline=True,
            )
            embed.set_footer(
                text=f"ID: {channel.id} • Deleted by {entry.user}",
                icon_url=entry.user.avatar.url if entry.user.avatar else discord.Embed.Empty,
            )
            await logging_channel.send(embed=embed)


@bot.event
async def on_user_update(before, after):
    if before.avatar != after.avatar:
        logging_channel = bot.get_channelint(int(LOG_CHAN_ID))
        if logging_channel:
            embed = discord.Embed(
                title="User avatar changed", color=discord.Colour.blurple()
            )
            embed.set_author(
                name=f"{before.name}#{before.discriminator}", icon_url=before.avatar.url
            )
            embed.set_thumbnail(url=after.avatar_url)
            embed.set_footer(text=f"ID: {before.id}")
            await logging_channel.send(embed=embed)


@bot.event
async def on_guild_channel_update(before, after):
    """
    Logs channel updates when a guild channel is modified.

    Parameters:
    - before (discord.abc.GuildChannel): The channel before the update.
    - after (discord.abc.GuildChannel): The channel after the update.
    """

    log_channel = bot.get_channel(int(LOG_CHAN_ID))

    async for entry in before.guild.audit_logs(
        limit=1, action=discord.AuditLogAction.channel_update
    ):
        if entry.target.id == before.id:
            author = entry.user

            # Check if the channel names are the same
            if before.name == after.name and before.category == after.category:
                return

            embed = discord.Embed(title="Channel Update", color=discord.Color.blurple())
            embed.add_field(name="Channel", value=before.mention, inline=False)

            # Compare channel attributes and add changed fields to the embed
            if before.name != after.name:
                embed.add_field(name="Name", value=f"`{before.name}` -> `{after.name}`", inline=False)
            # Does type ever change?
            if before.type != after.type:
                embed.add_field(name="Type", value=f"`{before.type}` -> `{after.type}`", inline=False)
            if before.category != after.category:
                before_category = before.category.name if before.category else "None"
                after_category = after.category.name if after.category else "None"
                embed.add_field(name="Category", value=f"`{before_category}` -> `{after_category}`", inline=False)

            embed.set_footer(text=f"Updated by: {author}", icon_url=author.avatar.url)

            await log_channel.send(embed=embed)


@bot.event
async def on_guild_role_update(before, after):
    """
    Triggered when a role is updated in a guild.

    Parameters:
        before (discord.Role): The role object representing the role before the update.
        after (discord.Role): The role object representing the role after the update.
    """
    log_channel = bot.get_channel(int(LOG_CHAN_ID))

    embed = discord.Embed(
        title=f"Role Updated: `{after.name}`", color=discord.Color.yellow()
    )

    if before.name != after.name:
        embed.add_field(
            name="Name changed", value=f"{before.name} -> {after.name}", inline=False
        )

    if before.permissions != after.permissions:
        permission_changes = []
        for perm, value in before.permissions:
            if getattr(after.permissions, perm) != value:
                permission_changes.append(
                    f"{perm.replace('_', ' ').title()}: {value} ->"
                    f" {getattr(after.permissions, perm)}"
                )
        if permission_changes:
            embed.add_field(
                name="Permissions Changed",
                value="\n".join(permission_changes),
                inline=False,
            )

    await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_create(role):
    """
    Event handler for when a role is created in a guild.

    Args:
        role (discord.Role): The role that was created.

    This event sends a log message to the designated log channel
    when a new role is created in the guild. It fetches the audit
    log entries for role creation and includes the creator's information
    in the log message.
    """
    log_channel = bot.get_channel(int(LOG_CHAN_ID))

    # Fetch the audit log entries for role creation
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
        creator = entry.user

        embed = discord.Embed(
            title=f"Role Created: `{role.name}`",
            description=f"New role created with ID: {role.id}",
            color=discord.Color.brand_green()
        )
        embed.set_footer(text=f"Created by: {creator}")

        await log_channel.send(embed=embed)

@bot.event
async def on_guild_role_delete(role):
    """
    Event handler for when a role is deleted in a guild.

    Args:
        role (discord.Role): The role that was deleted.

    This event sends a log message to the designated log channel
    when a role is deleted in the guild. It fetches the audit log
    entries for role deletion and includes the deleter's information
    in the log message.
    """
    log_channel = bot.get_channel(int(LOG_CHAN_ID))

    # Fetch the audit log entries for role deletion
    async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
        deleter = entry.user

        embed = discord.Embed(
            title=f"Role Deleted: `{role.name}`",
            description=f"Role ID: {role.id}",
            color=discord.Color.brand_red()
        )
        embed.set_footer(text=f"Deleted by: {deleter}")

        await log_channel.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members=True)
async def reload(ctx):
    """Reload Bot cog"""
    try:
        # will need to make this work with more cogs once i get that working
        bot.reload_extension("cogs.music")
        await ctx.reply("Cogs successfully reloaded!")
    except commands.ExtensionError as err:
        await ctx.reply(f"An error occurred while reloading the cog: `{err}`")


@bot.command(aliases=["reboot"])
@commands.has_permissions(ban_members=True)
async def restart(ctx, arg=""):
    """restarts the bot"""
    argv.append(arg)
    if arg == "debug":
        await ctx.send("Debug on!")
    if arg == "reset":
        await ctx.send("Reseting environment, check console!")
    await ctx.reply(" Restarting, please allow 5 seconds for this. ")
    os.execv(executable, ["python3"] + argv)


@bot.command(aliases=["latency"])
async def ping(ctx):
    """shows the bot and Discord API latency"""
    start_time = datetime.now()
    embed = discord.Embed(
        title="Pinging...",
        color=discord.Color.brand_red()
    )
    message = await ctx.reply(embed=embed)
    end_time = datetime.now()
    bot_latency = (end_time - start_time).total_seconds() * 1000
    api_latency = bot.latency * 1000
    embed.title = "Ping"
    embed.description = f"**Bot: {bot_latency:.2f}ms**\n**API: {api_latency:.2f}ms**"
    embed.color = discord.Color.brand_green()
    await message.edit(embed=embed)


@bot.command(aliases=["members"])
async def users(ctx):
    """Shows the total number of members, showing bots separately"""
    member_count = len([member for member in ctx.guild.members if not member.bot])
    bot_count = len([member for member in ctx.guild.members if member.bot])
    embed = discord.Embed(
        title=f"Total members in {ctx.guild.name}",
        description=f"**Members: {member_count}**\n**Bots: {bot_count}**",
        color=discord.Color.blurple()
    )
    await ctx.reply(embed=embed)


@bot.command(aliases=["AV", "av", "pfp"])
async def avatar(ctx, user: discord.Member = None):
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


@bot.command(pass_context=True)
async def userinfo(ctx, *, user: discord.Member = None):
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
        join_position_suffix = {1: "st", 2: "nd", 3: "rd"}.get(join_position % 10, "th")
    embed.add_field(
        name="Join position", value=f"{join_position}{join_position_suffix}"
    )

    embed.add_field(name="Registered", value=user.created_at.strftime(date_format))
    embed.add_field(name="ID", value=user.id, inline=True)

    if len(user.roles) > 1:
        role_string = " ".join([r.mention for r in user.roles][1:])
        embed.add_field(
            name=f"Roles [{len(user.roles)-1}]", value=role_string, inline=False
        )

    embed.set_footer(
        text=(
            "Information last updated:"
            f" {datetime.utcnow().strftime(date_format)}"
        )
    )

    await ctx.reply(embed=embed)


@bot.command()
async def serverinfo(ctx):
    """Displays server information."""
    name = str(ctx.guild.name)
    description = f"Official {ctx.guild.name} server"
    owner = str(ctx.guild.owner)
    servid = str(ctx.guild.id)
    member_count = str(ctx.guild.member_count)
    channels = (
        f"Text: {len(ctx.guild.text_channels)}\nVoice: {len(ctx.guild.voice_channels)}"
    )
    roles = str(len(ctx.guild.roles))
    created = f"{ctx.guild.created_at:%B %d, %Y, %I:%M %p}"
    icon = str(ctx.guild.icon.url) if ctx.guild.icon else None

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
        text="Thanks for being a part of our server!", icon_url=ctx.author.avatar.url
    )

    await ctx.reply(embed=embed)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """kicks a user"""

    if member == ctx.author:
        await ctx.reply("Can't kick yourself! ...baka!!")
    elif member.top_role >= ctx.author.top_role:
        await ctx.reply("Yo, you can only kick members lower than yourself lmao")
    else:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="kicked", description=f"{member.mention} was kicked out for {reason}"
        )
        await ctx.channel.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, *, reason=None):
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
        pass
    #with open('muted.json', "r") as jsonmute:
    #    datamute = json.load(jsonmute)
    #    datamute["muted"].append(member.id)
    #with open('muted.json', "w") as jsonmuteafter:
    #    json.dump(datamute, jsonmuteafter)


@bot.command()
@commands.has_permissions(kick_members=True)
async def unmute(ctx, member: discord.Member):
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


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason: str = None):
    """Bans the specified user"""
    if member is None:
        return await ctx.reply("You need to specify who to ban.")

    if member == ctx.author:
        return await ctx.reply("Can't ban yourself, idiot.")

    if member.top_role >= ctx.author.top_role:
        return await ctx.reply("You can only ban members lower than yourself.")

    try:
        await member.ban(reason=reason)
    except (discord.errors.Forbidden, discord.errors.HTTPException) as err:
        return await ctx.reply(
            f"Failed to ban {member.mention}. Please check my permissions and role hierarchy.\nError: {err}"
        )

    ban_reason = 'was banned' if reason is None else f"was banned for {reason}"
    embed = discord.Embed(
        title="Bye Bye",
        description=f"{member.mention} {ban_reason}.",
        color=discord.Color.blurple(),
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    """Unbans a user."""
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.reply(f"{user} has been unbanned.")
    except discord.errors.Forbidden:
        await ctx.reply("I don't have permissions to unban that user.")
    except discord.errors.NotFound:
        await ctx.reply("I couldn't find that user in the ban list.")
    except commands.BadArgument:
        await ctx.reply("Please provide a valid user ID.")


@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member = None, *, reason=None):
    """Warns a user and logs the warning to a specified channel"""
    if member is None or member == ctx.author:
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
    except discord.errors.HTTPException:
        pass

    if not LOG_CHAN_ID:
        log_channel = bot.get_channel(int(LOG_CHAN_ID))
        log_embed = discord.Embed(
            title="Member Warned",
            description=(
                f"{ctx.author.mention} warned"
                f" {member.mention}{'.' if not reason else f', reason: {reason}'}"
            ),
            color=discord.Colour.blurple(),
        )
        await log_channel.send(embed=log_embed)


@bot.command(aliases=["clear"])
@commands.has_permissions(ban_members=True)
async def wipe(ctx, amount: int = 20):
    """wipes 20 messages or the number specified"""
    if amount <= 0 or amount > 10000:  # Check that amount is within range
        return await ctx.send("Amount must be between 1 and 10000.")
    await ctx.channel.purge(limit=amount)
    await ctx.channel.send(f"Cleanup Complete, deleted {amount} messages")


@bot.command(pass_context=True)
@commands.has_permissions(ban_members=True)
async def role(ctx, action: str, user: discord.Member, user_role: discord.Role):
    """Add or remove a role from a user."""
    if action not in ["add", "remove"]:
        await ctx.reply("Invalid action specified. Use 'add' or 'remove'.")
        return

    if user_role >= ctx.author.top_role:
        await ctx.reply(
            f"Can't {action} {user_role} since it's higher than {ctx.author.top_role}."
        )
        return

    if action == "add":
        await user.add_roles(user_role)
        await ctx.reply(
            embed=discord.Embed(
                title="Role Added",
                description=f"{user.mention} was given the {user_role.mention} role.",
                color=discord.Color.green(),
            )
        )
    elif action == "remove":
        if user_role == ctx.author.top_role and user == ctx.author:
            await ctx.reply(f"Can't remove role \"{user_role}\" as it's your highest role.")
            return

        await user.remove_roles(user_role)
        await ctx.reply(
            embed=discord.Embed(
                title="Role Removed",
                description=f"{user.mention} was removed from the {user_role.mention} role.",
                color=discord.Color.red(),
            )
        )


bot_uptime = datetime.now()


@bot.command(pass_context=True)
async def uptime(ctx):
    """shows bot uptime"""
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
    embed.set_footer(text="Angel$IX", icon_url=bot.user.avatar.url)
    await ctx.reply(embed=embed)


# im proud of this
mem_info = psutil.Process(os.getpid())
total_mem = psutil.virtual_memory().total / float(2 ** 20)
mem = mem_info.memory_info()[0] / float(2 ** 20)
WRAPPER_USED = d_name.capitalize()


@bot.command(pass_context=True, aliases=["info", "debug"])
async def stats(ctx):
    """Shows bot stats"""
    embed = discord.Embed(
        title="System Resource Usage and Statistics",
        description="See bot host statistics.",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Angel$IX version", value=BOT_VER, inline=False)
    embed.add_field(name="CPU Usage", value=f"`{psutil.cpu_percent()}%`", inline=True)
    embed.add_field(
        name="Memory Usage", value=f"`{mem:.0f}MB/{total_mem:.0f}MB`", inline=True
    )
    embed.add_field(name="API Wrapper:", value=f"`{WRAPPER_USED}`", inline=True)
    embed.add_field(name="Python Version", value=f"`{version}`", inline=False)
    embed.add_field(name="YTdl Version", value=f"`{ytver.__version__}`", inline=True)
    embed.add_field(name=f"{WRAPPER_USED} Version", value=f"`{_version.__version__}`", inline=True)
    await ctx.reply(embed=embed)


@bot.command()
async def invites(ctx, user: discord.Member = None):
    """Shows how many people someone has invited"""
    user_name = user or ctx.author
    total_invites = 0
    for invite in await ctx.guild.invites():
        if invite.inviter == user_name:
            total_invites += invite.uses
    embed = discord.Embed(
        title=(
            f"{user_name} has invited"
            f" {total_invites} member{'' if total_invites == 1 else 's'} to the server!"
        ),
        color=discord.Colour.blurple(),
    )
    embed.set_author(name=user_name.display_name, icon_url=user_name.avatar.url)
    await ctx.reply(embed=embed)


@bot.command(aliases=["IQ"])
async def iq(ctx):
    """Average server IQ"""
    embed = discord.Embed(
        title=f"Average {ctx.guild.name} IQ",
        description=f"{randint(-10 , 130 )}",
        color=discord.Color.blurple(),
    )
    await ctx.reply(embed=embed)


@bot.command("roll")
async def roll(ctx, args: str = ""):
    """Rolls a dice in the user-specified format"""

    # Sanitize input - remove trailing spaces
    args = args.strip().replace(" ", "")

    if args == "help":
        await ctx.reply(
            "`~roll` - rolls a 6-sided dice\n"
            "`~roll 4` - rolls a 4-sided dice\n"
            "`~roll 2d6` - rolls two 6-sided dice\n"
        )
        return

    try:
        if args != "":
            dice_to_roll, number_of_sides = parse_input(args)
        else:
            dice_to_roll = 1
            number_of_sides = 6
    except ValueError:
        await ctx.reply(
            f"I didn't understand your input: `{args}`.\nTry `~roll help` for supported options."
        )
        return

    max_dice_size = 150
    max_sides = 100000000
    if not 0 <= dice_to_roll <= max_dice_size:
        embed = discord.Embed(
            title="Error",
            description=f"Invalid dice amount. Dice amount must be between 0 and {max_dice_size}.",
            color=discord.Color.brand_red(),
        )
        await ctx.reply(embed=embed)
        return

    if not 0 <= number_of_sides <= max_sides:
        embed = discord.Embed(
            title="Error",
            description=f"Invalid number of sides. The number of sides must be between 0 and {max_sides}.",
            color=discord.Color.brand_red(),
        )
        await ctx.reply(embed=embed)
        return

    results = []

    for _ in range(dice_to_roll):
        results.append(roll_a_dice(number_of_sides))

    result_string = ", ".join([f"`{result}`" for result in results])

    embed = discord.Embed(
        title=f"{ctx.author.name} rolled {dice_to_roll}d{number_of_sides}!",
        description=result_string,
        color=discord.Color.blurple(),
    )

    await ctx.reply(embed=embed)


def parse_input(parsed_input):
    split = parsed_input.split("d")

    # Remove empty items
    split = [x for x in split if x]

    if len(split) == 1:
        dice_to_roll = 1
        sided_dice = int(split[0])
    else:
        dice_to_roll = int(split[0])
        sided_dice = int(split[1])

    return dice_to_roll, sided_dice


def roll_a_dice(sides):
    return randint(1, sides)


@bot.command(pass_context=True, aliases=["cred", "credits", "about"])
async def credit(ctx):
    """Shows bot credits"""
    owner = await bot.fetch_user(1082831541400518737)
    maintainer = await bot.fetch_user(347387857574428676)

    embed = discord.Embed(
        title="Bot Creator",
        description=(
            f"{owner.mention}\nAsk them anything! 24/7. Feel free to add them as a"
            " friend."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text=f"Bot Maintainer: {maintainer}")

    await ctx.reply(CREDITS_IMAGE)
    await ctx.send(embed=embed)


@bot.command(pass_context=True, aliases=["fem"])  # :skull:
async def femboy(ctx):
    """Femboy Wisdom/Tutorial"""
    embed = discord.Embed(
        title="Chakal's Wisdom On Femboys",
        description=(
            "How can you be a feminine looking boy? Simple. \nGrow your hair out,"
            " exercise regularly (I run/jog to remain slim, and I do squats/tap dance"
            " to exercise my thighs/butt), trim your facial hair, do whatever you can"
            " to help out your skin, and consider taking HRT.\n Learn how to do makeup,"
            " it is a fucking amazing tool. Experiment with different outfits, my"
            " favorite for andro people is just leggings beneath feminine jean shorts,"
            " it is common for females in the UK and looks feminine, but not so"
            " feminine that it will look weird in public.\nConsider taking speech"
            " therapy, or just watching some videos and working at getting a more"
            " feminine voice.\nAt the end of the day, though, you can practically look"
            " like a girl, with the most luscious hair, smallest eyebrows, red lips,"
            " and longest lashes; you can have the perfect body type, be an hourglass"
            " with a big ass, thick thighs/hips and a skinny waist; you can sound like"
            " the girliest woman in the world; you can wear booty shorts and a half"
            " shirt and look damn good in it; you can be a master at feminine"
            " makeup.\nBut it all means nothing if you fail to act feminine. For looks"
            " catch the eye, but personality catches the heart.\nThere comes a point"
            " when you must ask yourself if you want to be a femboy, or simply be a"
            " feminine looking man.\nSo, how can you be a femboy?\nAct feminine."
            " Femboys are made, not born.  -Chakal"
        ),
        color=discord.Color.blurple(),
    )
    embed2 = discord.Embed(
        title="Miro's Wisdom On Femboys",
        description=(
            "Hey, some guys like being cute and pastel, trans guys included, and some"
            " transgender people don't really feel the need to change their bodies"
            " either. So that's an option. Maybe you're a really feminine guy who's"
            " fine with having a female body.\n Or, maybe you just really like the"
            " femboy aesthetic. Or maybe you're attracted to femboys. Idk, I'm not you."
            " It's gonna take a little experimentation to find out.\n 1) Get some"
            " clothes you feel comfortable in. Try out that femboy look. Do you feel"
            " cute? Does it feel right? Whether you are cis or trans, you should be"
            " able to wear clothes that make you feel good about yourself. So do that."
            " Whatever the answers are to the other questions, this will almost"
            " certainly make you feel a little better.\n 2) Do some googling. Learn"
            " about fem trans boys, demiboys, and non-binary people. Read some things"
            " from their perspectives. Does any of it resonate with you?\n3) Try some"
            " things. It's normal for us to question our identities and grow and change"
            " through the years, and it's normal to not fully understand yourself right"
            " away. If you think you might be trans, maybe try a different name or"
            " pronouns. if you don't have supportive people around willing to help you"
            " experiment, then you can introduce yourself the way you want online, with"
            " strangers you'll never have to interact with again. It takes a lot of the"
            " pressure off, too, if you're nervous. Maybe it'll feel right and you'll"
            " know. Maybe it'll feel wrong and you'll realize you're a girl. Maybe"
            " you'll still be confused and have to try some new things. Have patience,"
            " it can take time.\n4) Own it. Whatever your identity is, dress the way"
            " you like and be who you are and if anyone gives you shit about it, just"
            " show them how high you can kick their balls up their ass in your adorable"
            " little pink skirt.  -Miro"
        ),
        color=discord.Color.blurple(),
    )
    await ctx.reply(embed=embed)
    await ctx.send(embed=embed2)


@bot.command()
async def support(ctx, *, message: str = None):
    """Shows support server link and latest release."""
    if message in ["release", "changelog"]:
        await ctx.send(
            "Latest bot release: \n https://github.com/maj113/Angel6/releases/latest"
        )
        return

    embed = discord.Embed(
        title="Support server",
        description=(
            "Need help with the bot? https://discord.gg/yVhHpP9hkc \nWant to contribute"
            " to the bot? https://github.com/maj113/Angel6"
        ),
        color=discord.Color.blurple(),
    )
    embed.set_image(
        url="https://media.discordapp.net/attachments/736563784318976040/1087089496450928650/paintdotnet_LFkzPDrQML.png"
    )
    await ctx.reply(embed=embed)


gif_links = {
    "violation": "https://tenor.com/view/violation-gif-24043912",
    "germany": "https://giphy.com/gifs/fifa-Vd8wLaK3lNDNMuGaUL \n SHUT THE FUCK UP BAHZZ VIVA LA GERMANY AAJAJJAJAJAJA"

}


@bot.command()
async def giflist(ctx):
    """List available gifs"""
    embed = discord.Embed(title="Available Gifs:", color=discord.Color.blurple())
    for key in gif_links.items():
        command = f"`~gifsend {key[0]}`"
        embed.add_field(name=key[0], value=command, inline=False)
    await ctx.reply(embed=embed)


@bot.command(pass_context=True, aliases=["GIF", "gifsend", "jiff"])
async def gif(ctx, gif_type=""):
    """Sends a gif thats in the the GIF list"""
    if gif_type == "":
        await ctx.reply(
            "Please provide a GIF name. Use '~giflist' to see available options."
        )
        return
    gif_type = gif_type.lower()

    if gif_type in gif_links:
        await ctx.message.delete()
        await ctx.send(gif_links[gif_type])
    else:
        gif_type = discord.utils.escape_mentions(gif_type)
        await ctx.reply(
            f"Invalid GIF '{gif_type}'. Use '~giflist' to see available options."
        )


@bot.command(pass_context=True)
async def img(ctx, img_type="cat"):
    """Sends a random image based on the specified type.
    
    Parameters:
    - img_type (str): The type of image to send. Default is "cat".
    
    Possible types:
    - "cat": Sends a random cat image.
    - "anime" or "neko": Sends a random SFW anime or neko image.
    """

    try:
        if img_type == "cat":
            caturl = get("https://api.thecatapi.com/v1/images/search", timeout=1)
            catimg = caturl.json()[0]["url"]
        elif img_type in ["anime", "neko"]:
            caturl = get("https://api.nekosapi.com/v2/images/random?filter[ageRating]=sfw", timeout=2)
            catimg = caturl.json()["data"]["attributes"]["file"]
        else:
            error_embed = discord.Embed(title="Error:",
                                        description="Invalid argument. supported image API's are: 'cat', 'anime",
                                        color=discord.Color.brand_red())
            await ctx.reply(embed=error_embed)
            return
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_image(url=catimg)
        await ctx.reply(embed=embed)
    except Timeout as err:
        error_embed = discord.Embed(title="Error:",
                                    description=f"Failed to fetch image. Please try again later.\nError: {err}",
                                    color=discord.Color.brand_red())
        await ctx.reply(embed=error_embed)

def clsscr():
    """
    Clears the console screen.

    Uses the appropriate command based on the operating system:
    - On Windows (nt), it uses 'cls' to clear the console screen.
    - On other systems, it uses 'clear' to clear the console screen.
    """
    os.system("cls" if os.name == "nt" else "clear")


async def helperasbot():
    """
    Prints the names and IDs of text channels in the first guild.

    Retrieves the first guild from the bot instance.
    For each text channel, prints the channel name and its corresponding ID.
    """
    server = bot.guilds[0]
    text_channels = server.text_channels
    for channel in text_channels:
        print(f"    {channel.name} : {channel.id}")


@bot.command(pass_context=True)
@commands.has_permissions(ban_members=True)
async def asbot(ctx, *, arg=None):
    """start or stop the asbot function"""
    if arg not in ("start", "stop", None):
        await ctx.reply("Invalid argument. Use `start` or `stop`.")
    elif arg == "stop" and asbotmain.is_running():
        await ctx.reply("Stopped task **`asbotmain()`** successfully")
        clsscr()
        print(f"Warning: asbotmain() was stopped externally by {ctx.author} !!!")
        asbotmain.cancel()
    elif arg == "start" and not asbotmain.is_running():
        await ctx.reply("Started task **`asbotmain()`** successfully")
        print(f"Warning: asbotmain() was started externally by {ctx.author} !!!")
        asbotmain.start()
    elif arg is None:
        await ctx.reply(
            embed=discord.Embed(
                title="`asbotmain()` state:"
                + f"{'**running**' if asbotmain.is_running() else '**stopped**'}",
                color=discord.Color.blurple(),
            )
        )
    else:
        await ctx.reply(
            embed=discord.Embed(
                title=f"⚠️ Warning! Cannot {arg} the asbot extension",
                description=(
                    "The extension is already"
                    f" {'**running**' if asbotmain.is_running() else '**stopped**'}"
                ),
                color=discord.Color.yellow(),
            )
        )


@tasks.loop()
async def asbotmain():
    """Send messages as a bot in a specified text channel.

    Usage:
        - Input the channel ID to start sending messages.
        - Type "show" to select a different channel.
        - Type "asbotstop" to stop sending messages.

    Prints error messages if the input is invalid or the channel is a voice channel.
    """

    chan_id_alt = await ainput("Input channel ID: ")
    if chan_id_alt == "show":
        clsscr()
        await helperasbot()
        return
    clsscr()
    try:
        channel1 = bot.get_channel(int(chan_id_alt))
        if not isinstance(channel1, discord.TextChannel):
            print("Selected channel does not exist or isn't a text channel")
            return
    except ValueError:
        print("Error; Wrong ID provided or an unexpected exception occurred, try again")
        return
    while True:
        message = await ainput(f"[{str(channel1).strip()}] Message: ")
        if message == "show":
            clsscr()
            await helperasbot()
            break
        if message == "asbotstop":
            asbotmain.cancel()
            clsscr()
            print("Stopped task")
            break
        try:
            await channel1.send(message)
        except discord.errors.HTTPException:
            # This is a Unicode "U+2800/Braille Pattern Blank" character
            await channel1.send("⠀")



try:
    bot.run(TOKEN)
except discord.errors.LoginFailure:
    print(
        "NO TOKEN FOUND OR WRONG TOKEN SPECIFIED,\nmake sure that the env file is"
        " named '.env' and that there is a token present"
    )
    # gracefully exit, don't quit with error code 1
    exit()
