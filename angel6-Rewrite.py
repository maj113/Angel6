import asyncio
import psutil
import datetime
import random
import sys
import discord
import os
import aioconsole
import requests
from discord import __version__ as d_version
from discord.ext import commands, tasks
from dotenv import load_dotenv
from yt_dlp import version as ytver

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHAN_ID = os.getenv("LOGGING_CHANNEL_ID")
JL_CHAN_ID = os.getenv("JOIN_LEAVE_CHANNEL_ID")
GEN_CHAN_ID = os.getenv("GENERAL_CHANNEL_ID")
BotVer = "**2.3.1-Rewrite** <https://github.com/maj113/Angel6/releases/latest>"
creditsimage = "https://cdn.discordapp.com/attachments/1083114844875669604/1083121342150361118/1676492485892.png"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='~', activity=discord.Game(
    name="Greatest bot alive"), intents=intents)


async def set_env_var(env_var_name, prompt_text):
    value = os.getenv(env_var_name)
    if value == None:
        value = int(input(prompt_text))
        with open(".env", "a") as envfile:
            envfile.write(f"\n{env_var_name}={value}")
        return True
    elif value == "":
        value = int(input(prompt_text))
        with open(".env", "r+") as envfile:
            content = envfile.read()
            changed = content.replace(f"{env_var_name}=", f"{env_var_name}={value}")
            envfile.seek(0)
            envfile.write(changed)
            envfile.truncate()
        return True
    else:
        return False

@bot.event
async def on_ready():
    print(f'Logged in as:\n{bot.user.name}\n{bot.user.id}')
    restartbot = False
    config_options = [
        ("LOGGING_CHANNEL_ID", "Input logging channel ID "),
        ("JOIN_LEAVE_CHANNEL_ID", "Input join/leave channel ID "),
        ("GENERAL_CHANNEL_ID", "Input general channel ID ")
    ]
    for env_var_name, prompt_text in config_options:
        if await set_env_var(env_var_name, prompt_text):
            restartbot = True

    if restartbot is True:
        print("Setup complete, Rebooting")
        os.execv(sys.executable, ['python3'] + sys.argv)

    embed = discord.Embed(title='Bot settings',
                          description='Current bot settings and status',
                          color=discord.Color.blurple())
    embed.add_field(name="**Angel$IX Version:**", value=BotVer, inline=False)
    embed.add_field(name="logging channel", value=LOG_CHAN_ID, inline=False)
    embed.add_field(name="Join leave channel", value=JL_CHAN_ID, inline=False)
    embed.add_field(name="General channel", value=GEN_CHAN_ID, inline=False)
    embed.add_field(name="Current API latency:",
                    value=f'{(bot.latency * 1000):.0f}ms', inline=False)
    channel = bot.get_channel(int(LOG_CHAN_ID))
    await channel.send(creditsimage)
    await channel.send(embed=embed)
    try:
        await asbotmain.start()
    except RuntimeError:
        pass
bot.load_extension("cogs", recursive=True)


@bot.event
async def on_message(message):
    if message.author.id != bot.user.id:
        msgcontent = (
            f"{message.guild}/{message.channel}/{message.author.name}> {message.attachments[0].url if message.attachments else message.content}")
        # channel = bot.get_channel(int(LOG_CHAN_ID))
        print(msgcontent)  # , await channel.send(msgcontent)
        await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    channel = bot.get_channel(int(JL_CHAN_ID))
    embed = discord.Embed(colour=discord.Colour.blurple(
    ), description=f"{member.mention} joined, Total Members: {len(list(member.guild.members))}")
    embed.set_thumbnail(url=f"{member.avatar.url}")
    embed.set_footer(text=f"{member.guild}",
                     icon_url=f"{member.guild.icon.url}")
    await channel.send(embed=embed)
    if os.getenv("GENERAL_CHANNEL_ID") == None or os.getenv(
            "GENERAL_CHANNEL_ID") == "":
        mbed = discord.Embed(
            colour=(discord.Colour.blurple()),
            title='Glad you could find us!',
            description=f"yo! im Mutiny's Personal Bot, proceed to General to talk:)")
        await member.send(embed=mbed)

    else:
        chanID = int(GEN_CHAN_ID)
        mbed = discord.Embed(
            colour=(discord.Colour.blurple()),
            title='Glad you could find us!',
            description=f"yo! im Mutiny's Personal Bot, proceed to <#{chanID}> to talk:)")
        await member.send(embed=mbed)
    """with open('muted.json', "r") as jsonmute:
        datamute = json.load(jsonmute)
        if member.id in datamute["muted"]:
            for guild in bot.guilds:
                guildid=(guild.id)
            getguild = bot.get_guild(guildid)
            mutedRole = discord.utils.get(getguild.roles, name="Muted")
            await member.add_roles(mutedRole)"""
@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(int(JL_CHAN_ID))
    embed = discord.Embed(colour=discord.Colour.blurple(
    ), description=f"{member.mention} Left us, Total Members: {len(list(member.guild.members))}")
    embed.set_thumbnail(url=f"{member.avatar.url}")
    embed.set_footer(text=f"{member.guild}",
                     icon_url=f"{member.guild.icon.url}")
    await channel.send(embed=embed)


@bot.event
async def on_message_delete(message):
    deleted = discord.Embed(
        description=f"Message deleted in {message.channel.mention}",
        color=discord.Color.blurple()).set_author(
        name=message.author, icon_url=message.author.avatar.url)
    if message.author.id == bot.user.id:
        return
    channel = bot.get_channel(int(LOG_CHAN_ID))
    deleted.add_field(name="Message", value=message.content)
    deleted.timestamp = message.created_at
    await channel.send(embed=deleted)


@bot.command()
@commands.has_permissions(ban_members=True)
async def reload(ctx):
    """Reload Bot cog"""
    try:
        bot.unload_extension("cogs.music")
        bot.load_extension("cogs.music")
        await ctx.reply('Cogs sucessfully reloaded!')
    except Exception as err:
        await ctx.reply(err)


@bot.command()
@commands.has_permissions(ban_members=True)
async def restart(ctx, arg=""):
    """restarts the bot"""
    await ctx.reply(" Restarting, please allow 5 seconds for this. ")
    os.execv(sys.executable, ['python3'] + sys.argv +
             (['debug']) if arg == 'debug' else '')


@bot.command(aliases=['latency'])
async def ping(ctx):
    """shows the ping"""
    embed = discord.Embed(title="Bot latency:",
                          description=f"**{(bot.latency * 1000):.0f}ms**",
                          color=discord.Color.blurple())
    await ctx.reply(embed=embed)


@bot.command(aliases=['members'])
async def users(ctx):
    """shows total amount of members"""
    count = ctx.guild.member_count
    b = discord.Embed(
        title=f"Total members in {ctx.guild.name}", description=count,
        color=discord.Color.blurple())
    await ctx.reply(embed=b)


@bot.command(aliases=['AV', 'avatar', 'pfp'])
async def av(ctx, *, user: discord.Member = None):
    """grabs user's avatar"""
    if user is None:
        user = ctx.author

    
    embed = discord.Embed(title=f"{user.display_name}'s avatar", 
                          color=discord.Colour.blurple())
    embed.set_image(url=user.avatar.url)

    await ctx.reply(embed=embed)


@bot.command(pass_context=True)
async def userinfo(ctx, *, user: discord.Member = None):
    """Shows userinfo"""
    if user is None:
        user = ctx.author
    
    date_format = "%a, %d %b %Y %I:%M %p"
    embed = discord.Embed(color=discord.Color.blurple(),
                          description=user.mention)
    
    embed.set_author(name=user.display_name, icon_url=user.avatar.url)
    embed.set_thumbnail(url=user.avatar.url)
    
    embed.add_field(name="Joined", value=user.joined_at.strftime(date_format))
    
    members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
    join_position = members.index(user) + 1
    join_position_suffix = ""
    if join_position % 10 == 1 and join_position != 11:
        join_position_suffix = "st"
    elif join_position % 10 == 2 and join_position != 12:
        join_position_suffix = "nd"
    elif join_position % 10 == 3 and join_position != 13:
        join_position_suffix = "rd"
    else:
        join_position_suffix = "th"
    embed.add_field(name="Join position", value=f"{join_position}{join_position_suffix}")
    
    embed.add_field(name="Registered", value=user.created_at.strftime(date_format))
    embed.add_field(name="ID", value=user.id, inline=True)
    
    if len(user.roles) > 1:
        role_string = ' '.join([r.mention for r in user.roles][1:])
        embed.add_field(name="Roles [{}]".format(len(user.roles)-1), value=role_string, inline=False)

    embed.set_footer(text=f"Information last updated: {datetime.datetime.utcnow().strftime(date_format)}")
    
    await ctx.reply(embed=embed)


@bot.command()
async def serverinfo(ctx):
    """displays server information"""
    name = str(ctx.guild.name)
    description = f"Official {ctx.guild.name} server"
    owner = str(ctx.guild.owner)
    servid = str(ctx.guild.id)
    memberCount = str(ctx.guild.member_count)
    icon = str(ctx.guild.icon.url) if ctx.guild.icon else None
    embed = discord.Embed(
        title=name + " <3",
        description=description,
        color=discord.Color.blurple()
    )
    if icon:
        embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value=owner, inline=True)
    embed.add_field(name="Server ID", value=servid, inline=True)
    embed.add_field(name="Member Count", value=memberCount, inline=True)
    embed.add_field(name="Created", value=f"{ctx.guild.created_at:%B %d, %Y, %I:%M %p}", inline=True)
    await ctx.reply(embed=embed)


@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """kicks a user"""

    if member == ctx.author:
        await ctx.reply(f"Can't kick yourself idiot")
    elif member.top_role >= ctx.author.top_role:
        await ctx.reply(f"Yo, you can only kick members lower than yourself lmao ")
    else:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="kicked",
            description=f"{member.mention} was kicked out for {reason}")
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
            await channel.set_permissions(muted_role, speak=False, send_messages=False, read_message_history=True, read_messages=True, create_private_threads=False, create_public_threads=False)

    await member.add_roles(muted_role, reason=reason)

    embed = discord.Embed(
        title="Muted",
        description=f"{member.mention} has been muted{' for ' + reason if reason else ''}",
        color=discord.Color.blurple())
    await ctx.reply(embed=embed)
    try:
        await member.send(f"You were muted{' for ' + reason if reason else ''}")
    except:
        pass
    """with open('muted.json', "r") as jsonmute:
        datamute = json.load(jsonmute)
        datamute["muted"].append(member.id)
    with open('muted.json', "w") as jsonmuteafter:
        json.dump(datamute, jsonmuteafter)""" 


@bot.command()
@commands.has_permissions(kick_members=True)
async def unmute(ctx, member: discord.Member):
    """Unmutes a user"""
    mutedRole = discord.utils.get(ctx.guild.roles, name="Muted")

    if mutedRole not in member.roles:
        await ctx.reply(f"{member.name} is not muted.")
        return

    await member.remove_roles(mutedRole)
    await ctx.reply(f"Unmuted {member.mention}")
    await member.send(f'Unmuted in {ctx.guild.name}. Welcome back!')


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    """Bans the specified user"""
    if member is None:
        return await ctx.reply("You need to specify who to ban.")

    if member == ctx.author:
        return await ctx.reply("Can't ban yourself, idiot.")

    if member.top_role >= ctx.author.top_role:
        return await ctx.reply("You can only ban members lower than yourself.")

    try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="bye lol",
            description=f"{member.mention + ' got banned' if reason is None else member.mention + ' got banned: ' + reason} "
        )
            await ctx.channel.send(embed=embed)
    except discord.errors.Forbidden as err:
        await ctx.reply(f"Can't ban the member, I don't have the necessary permissions. Please make sure I have the 'ban members' permission and that I am higher on the role list than the member you're trying to ban. \nError: {err}")


@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, id="0"):
    """unbans a user"""
    if id == "0":
        await ctx.reply("You need to provide an ID to unban!")
    else:
        try:
            id = int(id)
            user = await bot.fetch_user(id)
            await ctx.guild.unban(user)
            await ctx.reply(f'{user} has been unbanned')
        except ValueError:
            await ctx.reply("ID must be an integer")
        except discord.errors.NotFound:
            await ctx.reply("User not found")


@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member: discord.Member = None, *, reason=None):
    """warns a user"""
    if member is None or member == ctx.author:
        await ctx.reply("You need to specify someone to warn!")
        return
    embed2 = discord.Embed(
        title="Warned🗡️",
        description=f"You were warned.{' Now behave.' if reason is None else f' Reason: {reason}'}",
        color=discord.Colour.blurple()
    )
    embed = discord.Embed(
        title="Warned",
        description=f"{member.mention} was warned{'.' if reason is None else f', reason: {reason}'}",
        color=discord.Colour.blurple()
    )
    await ctx.reply(embed=embed)
    await member.send(embed=embed2)


@bot.command(aliases=['clear'])
@commands.has_permissions(ban_members=True)
async def wipe(ctx, amount=20):
    """wipes 20 messages or the number specified"""
    await ctx.channel.purge(limit=amount)
    await ctx.channel.send(f"Cleanup Complete, deleted {amount} messages")


@bot.command(pass_context=True)
@commands.has_permissions(ban_members=True)
async def role(ctx, user: discord.Member, role: discord.Role):
    """Gives user a role"""
    if role >= ctx.author.top_role:
        await ctx.reply(f"Can't give {role} since its higher than {ctx.author.top_role}")
        return
    await user.add_roles(role)
    await ctx.reply(f"{user.name} has been given: {role.name}")


@bot.command(pass_context=True)
@commands.has_permissions(ban_members=True)
async def rmrole(ctx, user: discord.Member, role: discord.Role):
    """Removes user's role away"""
    if role == ctx.author.top_role and user == ctx.author:
        await ctx.reply(f"Can't remove role \"{role}\" as it's your highest role")
        return
    await user.remove_roles(role)
    await ctx.reply(f"{user.name} was removed from role: {role.name}")

start_time = datetime.datetime.now()

@bot.command(pass_context=True)
async def uptime(ctx):
    """shows bot uptime"""
    current_time = datetime.datetime.now()
    difference = current_time - start_time
    hours, remainder = divmod(int(difference.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    text = f"{hours}h {minutes}m {seconds}s"
    embed = discord.Embed(colour=discord.Color.blurple())
    embed.add_field(name="Uptime", value=text)
    embed.add_field(name="Bot started at", value=start_time.strftime("%Y-%m-%d %H:%M:%S"))
    embed.set_footer(text="Angel$IX")
    await ctx.reply(embed=embed)

# im proud of this
meminfo = psutil.Process(os.getpid())
totmem = psutil.virtual_memory().total / float(2 ** 20)
mem = meminfo.memory_info()[0] / float(2 ** 20)


@bot.command(pass_context=True, aliases=['info', 'debug'])
async def stats(ctx):
    """shows bot stats"""
    bedem = discord.Embed(
        title='System Resource Usage and statistics',
        description='See bot host statistics.', color=discord.Color.blurple())
    bedem.add_field(name="Angel$IX version", value=BotVer, inline=False)
    bedem.add_field(name='CPU Usage', value=f'`{psutil.cpu_percent()}%`', inline=True)
    bedem.add_field(name='Memory Usage', value=f'`{mem:.0f}MB/{totmem:.0f}MB`', inline=True)
    # bedem.add_field(name='CPU name', value=cpuinfo.get_cpu_info()['brand_raw'], inline=False) way too slow
    bedem.add_field(name='Discord.py Version', value=f'`{d_version}`', inline=True)
    bedem.add_field(name='Python Version', value=f'`{sys.version}`', inline=False)
    bedem.add_field(name='YTdl Version', value=f'`{ytver.__version__}`', inline=False)
    await ctx.reply(embed=bedem)


@bot.command()
async def invites(ctx, user: discord.Member = None):
    """Shows how many people someone has invited"""
    user_name = ctx.author if user is None else user
    totalInvites = 0
    for invite in await ctx.guild.invites():
        if invite.inviter == user_name:
            totalInvites += invite.uses
    embed = discord.Embed(title=f"{user_name} has invited {totalInvites} member{'' if totalInvites == 1 else 's'} to the server!",color=discord.Colour.blurple())
    embed.set_author(name=user_name.display_name, icon_url=user_name.avatar.url)
    await ctx.reply(embed=embed)


@bot.command(aliases=['iq'])
async def IQ(ctx):
    """Average server IQ"""
    embed = discord.Embed(
        title=f"Average {ctx.guild.name} IQ",
        description=f"{random.randint(-10 , 130 )}",
        color=discord.Color.blurple())
    await ctx.reply(embed=embed)


@bot.command('roll')
async def roll(ctx, *args):
    """Rolls a dice in user specified format"""
    args = "".join(args)

    # sanitize input - remove trailing spaces
    args = args.strip()

    args = args.replace(' ', '')

    if args == 'help':
        await ctx.reply("`~roll` - rolls a 6 sided dice\n"
                        "`~roll 4` - rolls a 4 sided dice\n"
                        "`~roll 2d6` - rolls two 6-sided dice\n"
                        )
        return

    diceToRoll = 1
    numberOfSides = 6

    if args:
        try:
            (diceToRoll, numberOfSides) = parseInput(args)
        except:
            await ctx.reply('I didn\'t understand your input: `' + args + '`.\n try `~roll help` for supported options')
            return

    maxdicesize = 150
    maxsides = 100000000
    if diceToRoll < 0 or diceToRoll > maxdicesize:
        await ctx.reply(f"Invalid dice amount. Dice amount must be between 0 and {maxdicesize}")
        return

    if numberOfSides < 0 or numberOfSides > maxsides:
        await ctx.reply(f"Invalid number of sides. The number of sides must be between 0 and {maxsides}")
        return

    results = []

    for _ in range(0, diceToRoll):
        results.insert(0, rolladice(numberOfSides))

    resultString = ', '.join([f'`{result}`' for result in results])

    embed = discord.Embed(title=f"{ctx.author.name} rolled {diceToRoll}d{numberOfSides}!", description=resultString, color=discord.Colour.blurple())

    await ctx.reply(embed=embed)


def parseInput(input):
    split = input.split('d')

    # remove empty items
    split = [x for x in split if x]

    if len(split) == 1:

        diceToRoll = 1
        sidedDice = int(split[0])

    else:

        diceToRoll = int(split[0])
        sidedDice = int(split[1])

    return diceToRoll, sidedDice


def rolladice(sides):
    return random.randint(1, sides)


@bot.command(pass_context=True, aliases=['cred', 'credits', 'about'])
async def credit(ctx):
    """Shows bot credits"""
    owner = await bot.fetch_user(978854415786184745)
    maintainer = await bot.fetch_user(347387857574428676)

    embed = discord.Embed(
        title=f"Bot Creator",
        description=f"{owner.mention}\nAsk them anything! 24/7. Feel free to add them as a friend.",
        color=discord.Color.blurple()
    )
    embed.set_footer(text=f"Bot Maintainer: {maintainer}")

    await ctx.reply(creditsimage)
    await ctx.send(embed=embed)


@bot.command(pass_context=True, aliases=['fem'])  # :skull:
async def femboy(ctx):
    """Femboy Wisdom/Tutorial"""
    embed = discord.Embed(title="Chakal's Wisdom On Femboys", description="How can you be a feminine looking boy? Simple. \nGrow your hair out, exercise regularly (I run/jog to remain slim, and I do squats/tap dance to exercise my thighs/butt), trim your facial hair, do whatever you can to help out your skin, and consider taking HRT.\n Learn how to do makeup, it is a fucking amazing tool. Experiment with different outfits, my favorite for andro people is just leggings beneath feminine jean shorts, it is common for females in the UK and looks feminine, but not so feminine that it will look weird in public.\nConsider taking speech therapy, or just watching some videos and working at getting a more feminine voice.\nAt the end of the day, though, you can practically look like a girl, with the most luscious hair, smallest eyebrows, red lips, and longest lashes; you can have the perfect body type, be an hourglass with a big ass, thick thighs/hips and a skinny waist; you can sound like the girliest woman in the world; you can wear booty shorts and a half shirt and look damn good in it; you can be a master at feminine makeup.\nBut it all means nothing if you fail to act feminine. For looks catch the eye, but personality catches the heart.\nThere comes a point when you must ask yourself if you want to be a femboy, or simply be a feminine looking man.\nSo, how can you be a femboy?\nAct feminine. Femboys are made, not born.  -Chakal", color=discord.Color.blurple())
    embed2 = discord.Embed(title="Miro's Wisdom On Femboys", description="Hey, some guys like being cute and pastel, trans guys included, and some transgender people don’t really feel the need to change their bodies either. So that’s an option. Maybe you’re a really feminine guy who’s fine with having a female body.\n Or, maybe you just really like the femboy aesthetic. Or maybe you’re attracted to femboys. Idk, I’m not you. It’s gonna take a little experimentation to find out.\n 1) Get some clothes you feel comfortable in. Try out that femboy look. Do you feel cute? Does it feel right? Whether you are cis or trans, you should be able to wear clothes that make you feel good about yourself. So do that. Whatever the answers are to the other questions, this will almost certainly make you feel a little better.\n 2) Do some googling. Learn about fem trans boys, demiboys, and non-binary people. Read some things from their perspectives. Does any of it resonate with you?\n3) Try some things. It’s normal for us to question our identities and grow and change through the years, and it’s normal to not fully understand yourself right away. If you think you might be trans, maybe try a different name or pronouns. if you don’t have supportive people around willing to help you experiment, then you can introduce yourself the way you want online, with strangers you’ll never have to interact with again. It takes a lot of the pressure off, too, if you’re nervous. Maybe it’ll feel right and you’ll know. Maybe it’ll feel wrong and you’ll realize you’re a girl. Maybe you’ll still be confused and have to try some new things. Have patience, it can take time.\n4) Own it. Whatever your identity is, dress the way you like and be who you are and if anyone gives you shit about it, just show them how high you can kick their balls up their ass in your adorable little pink skirt -Miro.", color=discord.Color.blurple())
    await ctx.send(embed=embed)
    await ctx.reply(embed=embed2)


@bot.command()
async def support(ctx, *, message: str = None):
    """Shows support server link and latest release."""
    if message in ["release", "changelog"]:
        await ctx.send("Latest bot release: \n https://github.com/maj113/Angel6/releases/latest")
        return

    embed = discord.Embed(
        title="Support server",
        description="Need help with the bot? https://discord.gg/ctsjpMQXEe \nWant to contribute to the bot? <https://github.com/maj113/Angel6>",
        color=discord.Color.blurple()
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/1082901963718541354/1085636944639295568/paintdotnet_LFkzPDrQML.png")
    await ctx.reply(embed=embed)
    

gif_links = {
    'violation': 'https://tenor.com/view/that-one-there-was-a-violation-that1there-was-violation-violation-that-one-there-was-a-violation-personally-i-wouldnt-have-it-that1there-was-a-violation-personally-i-wouldnt-have-it-gif-20040456',
    'germany': 'https://giphy.com/gifs/fifa-Vd8wLaK3lNDNMuGaUL \n SHUT THE FUCK UP BAHZZ VIVA LA GERMANY AAJAJJAJAJAJA',
}

@bot.command()
async def giflist(ctx):
    """List available gifs"""
    embed = discord.Embed(title="Available Gifs:",
                          color=discord.Color.blurple())
    for gif_type, gif_link in gif_links.items():
        command = f"`~gifsend {gif_type}`"
        embed.add_field(name=gif_type, 
                        value=command, inline=False)
    await ctx.reply(embed=embed)

@bot.command(pass_context=True, aliases=['GIF', 'gifsend', 'jiff'])
async def gif(ctx, gif_type=''):
    """Sends a gif thats in the the GIF list"""
    if gif_type == '':
        await ctx.reply("Please provide a GIF name. Use '~giflist' to see available options.")
        return
    gif_type = gif_type.lower()
    
    if gif_type in gif_links:
        await ctx.reply(gif_links[gif_type])
    else:
        await ctx.reply(f"Invalid GIF type '{gif_type}'. Use '~giflist' to see available options.")

@bot.command(pass_context=True)
async def cat(ctx):
    """sends a random cat image"""
    try:
        caturl = requests.get('https://api.thecatapi.com/v1/images/search')
        catimg = caturl.json()[0]['url']
        await ctx.reply(catimg)
    except Exception as e:
        print(e)
        await ctx.reply("Failed to fetch cat image. Please try again later.")


def clsscr():
    os.system('cls' if os.name == 'nt' else print("\x1B[2J"))


async def helperasbot():

    for server in bot.guilds:
        for channel in server.channels:
            if channel.type == discord.ChannelType.text:
                print(f"    {channel.name} : {channel.id}")


@bot.command(pass_context=True)
@commands.has_permissions(ban_members=True)
async def asbot(ctx, *, arg=None):
    """start or stop the asbot function"""
    if arg == "stop":
        if asbotmain.is_running():
            await ctx.reply("Stopped task **`asbotmain()`** successfully")
            clsscr()
            print(f"Warning: asbotmain() was stopped externally by {ctx.author} !!!")
            asbotmain.cancel()
        else:
            await ctx.reply("**`asbotmain()`** is not running!")
    elif arg == "start":
        if asbotmain.is_running():
            await ctx.reply("**`asbotmain()`** is already running!")
        else:
            await ctx.reply("Started task **`asbotmain()`** successfully")
            print(f"Warning: asbotmain() was started externally by {ctx.author} !!!")
            asbotmain.start()
    else:
        await ctx.reply(embed=discord.Embed(
            title="`asbotmain()` state:"+f"{' **running**' if asbotmain.is_running() else ' **stopped**'}", color=discord.Color.blurple()))

# FIXME: get rid of global
isinit = False


@tasks.loop()
async def asbotmain():
    global isinit
    if isinit == False:
        global chanID2
        chanID2 = await aioconsole.ainput("Input channel ID: ")
        if chanID2 == "show":
            clsscr()
            await helperasbot()
            return
        clsscr()
        try:
            global channel1
            channel1 = bot.get_channel(int(chanID2))
            if str(channel1.type) != 'text':
                print("Selected channel is a Voice channel, try again")
                isinit = False
                return
        except AttributeError:
            print("AttributeError; Wrong ID provided, try again")
            isinit = False
            return
        except ValueError:
            print("ValueError; ID should be a Integer, try again")
            isinit = False
            return
        isinit = True
    message = await aioconsole.ainput(f"[{discord.utils.get(bot.get_all_channels(), id=int(chanID2))}] Message: ")
    if message == "sel":
        clsscr()
        await helperasbot()
        isinit = False
        return
    if message == "asbotstop":
        asbotmain.cancel()
        clsscr()
        print("Stopped task")
    try:
        await channel1.send(message)
    except discord.errors.HTTPException:
        # This is a Unicode "U+2800/Braille Pattern Blank" character
        await channel1.send("⠀")


async def main():
    try:
        await bot.start(TOKEN)
    except TypeError:
        print("NO TOKEN FOUND, make sure that the env file is named '.env' and that there is a token present")
        await bot.close()
if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
