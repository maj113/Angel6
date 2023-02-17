import asyncio, psutil, time, datetime, random, sys, discord, os, aioconsole
from discord import __version__ as d_version
from discord.ext import commands, tasks
from dotenv import load_dotenv
from yt_dlp import version as ytver

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHAN_ID = os.getenv("LOGGING_CHANNEL_ID")
JL_CHAN_ID = os.getenv("JOIN_LEAVE_CHANNEL_ID")
GEN_CHAN_ID = os.getenv("GENERAL_CHANNEL_ID")
BotVer = "**2.3-Rewrite** <https://github.com/maj113/Angel6/releases/latest>"
creditsimage="https://media.discordapp.net/attachments/997647296189698129/1075817805691236543/1676492485892.jpg?width=1000&height=625"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='~',activity = discord.Game(name="Greatest bot alive"), intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as:\n{bot.user.name}\n{bot.user.id}')
    restartbot = False

    if os.getenv("LOGGING_CHANNEL_ID") == "" :
        logginginput = int(input("Input logging channel ID "))
        with open(".env", "r") as envfile:
            content1 = envfile.read()
            changed = content1.replace("LOGGING_CHANNEL_ID=", ''.join(["LOGGING_CHANNEL_ID=", str(logginginput)]))
            with open('.env','w') as envfile:
                envfile.write(changed)
        restartbot = True
    
    if os.getenv("LOGGING_CHANNEL_ID") == None :
        logginginput = int(input("Input logging channel ID "))
        with open(".env", "a") as envfile:
            envfile.write(f"\nLOGGING_CHANNEL_ID={logginginput}")
        restartbot = True
    
    if os.getenv("JOIN_LEAVE_CHANNEL_ID") == None :
        joinleaveinput = int(input("Input join/leave channel ID "))
        with open(".env", "a") as envfile:
            envfile.write(f"\nJOIN_LEAVE_CHANNEL_ID={joinleaveinput}")
        restartbot = True

    if os.getenv("JOIN_LEAVE_CHANNEL_ID") == "" :
        joinleaveinput = int(input("Input join/leave channel ID "))
        with open(".env", "r") as envfile:
            content1 = envfile.read()
            changed = content1.replace("JOIN_LEAVE_CHANNEL_ID=", ''.join(["JOIN_LEAVE_CHANNEL_ID=", str(joinleaveinput)]))
            with open('.env','w') as envfile:
                envfile.write(changed)
        restartbot = True

    if os.getenv("GENERAL_CHANNEL_ID") == None :
        generalinput = int(input("Input general channel ID "))
        with open(".env", "a") as envfile:
            envfile.write(f"\nGENERAL_CHANNEL_ID={generalinput}")
        restartbot = True

    if os.getenv("GENERAL_CHANNEL_ID") == "" :
        generalinput = int(input("Input general channel ID "))
        with open(".env", "r") as envfile:
            content1 = envfile.read()
            changed = content1.replace("GENERAL_CHANNEL_ID=", ''.join(["GENERAL_CHANNEL_ID=", str(generalinput)]))
            with open('.env','w') as envfile:
                envfile.write(changed)
        restartbot = True
    
    if restartbot == True:
        print("Setup complete, Rebooting")
        restart_program()
    
    embed = discord.Embed(title = 'Bot settings', description = 'Current bot settings and status', color=discord.Color.blurple())
    embed.add_field(name="**Angel$IX Version:**", value=BotVer, inline=False)
    embed.add_field(name="logging channel", value=LOG_CHAN_ID, inline=False)
    embed.add_field(name="Join leave channel", value=JL_CHAN_ID, inline=False)
    embed.add_field(name="General channel", value=GEN_CHAN_ID, inline=False)
    embed.add_field(name="Current API latency:", value=f'{(bot.latency * 1000):.0f}ms', inline=False)
    channel = bot.get_channel(int(LOG_CHAN_ID))
    await channel.send(creditsimage)
    await channel.send(embed=embed)       
    try: await asbotmain.start()
    except RuntimeError:
        pass
bot.load_extension("cogs.music")

@bot.event
async def on_member_join(member):
    channel = bot.get_channel(int(JL_CHAN_ID))    
    embed = discord.Embed(colour=discord.Colour.blurple(), description=f"{member.mention} joined, Total Members: {len(list(member.guild.members))}")
    embed.set_thumbnail(url=f"{member.avatar.url}")
    embed.set_footer(text=f"{member.guild}", icon_url=f"{member.guild.icon.url}")
    await channel.send(embed=embed)
    if os.getenv("GENERAL_CHANNEL_ID") == None or os.getenv("GENERAL_CHANNEL_ID") == "" :
        mbed = discord.Embed(
        colour = (discord.Colour.blurple()),
        title = 'Glad you could find us!',
        description =f"yo! im Mutiny's Personal Bot, proceed to General to talk:)")
        await member.send(embed=mbed)   
    
    else:
        chanID = int(GEN_CHAN_ID)
        mbed = discord.Embed(
            colour = (discord.Colour.blurple()),
            title = 'Glad you could find us!',
            description =f"yo! im Mutiny's Personal Bot, proceed to <#{chanID}> to talk:)")
        await member.send(embed=mbed)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(int(JL_CHAN_ID))
    embed = discord.Embed(colour=discord.Colour.blurple(), description=f"{member.mention} Left us, Total Members: {len(list(member.guild.members))}")
    embed.set_thumbnail(url=f"{member.avatar.url}")
    embed.set_footer(text=f"{member.guild}", icon_url=f"{member.guild.icon.url}")
    await channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    deleted = discord.Embed(
        description=f"Message deleted in {message.channel.mention}", 
        color=discord.Color.blurple()).set_author(name=message.author, icon_url=message.author.avatar.url)
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

def restart_program():
    os.execv(sys.executable, ['python3'] + sys.argv)     

@bot.command()
@commands.has_permissions(ban_members=True)
async def restart(ctx):
    """restarts the bot"""
    await ctx.reply(" Restarting, please allow 5 seconds for this. ")
    restart_program()

@bot.command(aliases=['latency'])
async def ping(ctx):
    """shows the ping"""
    embed = discord.Embed(title="Bot latency:",color=discord.Color.blurple(),description=f"**{(bot.latency * 1000):.0f}ms**")
    await ctx.reply(embed=embed)

@bot.command(aliases=['members'])
async def users(ctx):
    """shows total amount of members"""
    count=ctx.guild.member_count
    b=discord.Embed(title=f"Total members in {ctx.guild.name}",description=count,color=discord.Color.blurple())
    await ctx.reply(embed=b)

@bot.command(aliases=['AV','avatar','pfp'])
async def av(ctx, *,  user : discord.Member=None):
    """grabs users avatar"""
    if user == None:
        user = ctx.author
    userAvatarUrl = user.avatar.url
    await ctx.reply(userAvatarUrl)

@bot.command(pass_context=True)
async def userinfo(ctx, *, user : discord.Member=None): # b'\xfc'
    """Shows userinfo"""
    if user is None:
        user = ctx.author      
    date_format = "%a, %d %b %Y %I:%M %p"
    embed = discord.Embed(color=discord.Color.blurple(), description=user.mention)
    embed.set_author(name=str(user), icon_url=user.avatar.url)
    embed.set_thumbnail(url=user.avatar.url)
    embed.add_field(name="Joined", value=user.joined_at.strftime(date_format))
    members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
    embed.add_field(name="Join position", value=str(members.index(user)+1))
    embed.add_field(name="Registered", value=user.created_at.strftime(date_format))
    embed.add_field(name="ID", value=user.id, inline=True)
    if len(user.roles) > 1:
        role_string = ' '.join([r.mention for r in user.roles][1:])
        embed.add_field(name="Roles [{}]".format(len(user.roles)-1), value=role_string, inline=False)
    perm_string = ', '.join([str(p[0]).replace("_", " ").title() for p in user.guild_permissions if p[1]]) #I don't like the guild permissions part, way too much info, useless
    embed.add_field(name="Guild permissions", value=perm_string, inline=False)
    return await ctx.reply(embed=embed)

@bot.command()
async def serverinfo(ctx):
    """displays server information"""
    name = str(ctx.guild.name)
    description = f"Official {ctx.guild.name} server"
    owner = str(ctx.guild.owner)
    id = str(ctx.guild.id)
    memberCount = str(ctx.guild.member_count)
    icon = str(ctx.guild.icon.url)
    embed = discord.Embed(
        title=name + " <3",
        description=description,
        color=discord.Color.blurple()
    )
    embed.set_thumbnail(url=icon)#FIXME: this is way too basic should fix
    embed.add_field(name="Owner", value=owner, inline=True)
    embed.add_field(name="Server ID", value=id, inline=True)
    embed.add_field(name="Member Count", value=memberCount, inline=True)
    embed.add_field(name="Created", value=ctx.guild.created_at.strftime(
            "%B %d, %Y, %I:%M %p"), inline=True)
    await ctx.reply(embed=embed)

@bot.command()
@commands.has_permissions(kick_members =True)
async def kick(ctx, member : discord.Member, *, reason=None):
    """kicks a user"""
    
    if member == ctx.author:
        await ctx.reply(f"Can't kick yourself idiot")
    elif member.top_role >= ctx.author.top_role:
        await ctx.reply(f"Yo, you can only kick members lower than yourself lmao ")
    else:
        await member.kick(reason=reason)
        embed = discord.Embed(title="kicked", description=f"{member.mention} was kicked out for {reason}")
        await ctx.channel.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    """mutes a user"""
    embed=discord.Embed(title="Muted", description=f"{member.mention} was muted {'for: ' + reason if reason != None else ''}", color=discord.Color.blurple())
    guild = ctx.guild
    mutedRole = discord.utils.get(guild.roles, name="Muted")
    
    if member == ctx.author:
        await ctx.reply(f"Can't mute yourself idiot")
        return
    
    elif member.top_role >= ctx.author.top_role:
        await ctx.reply(f"Nice try, ayo {member.mention}, {ctx.author.mention} just tried muting you")
        return

    if not mutedRole:
        mutedRole = await guild.create_role(name="Muted")

        for channel in guild.channels:
            await channel.set_permissions(mutedRole, speak=False, send_messages=False, read_message_history=True, read_messages=True, create_private_threads=False, create_public_threads=False)

    await member.add_roles(mutedRole, reason=reason)
    await ctx.reply(embed=embed)
    await member.send(f"You were muted {'for: ' + reason if reason != None else ''}")

@bot.command()
@commands.has_permissions(kick_members =True)
async def unmute(ctx, member: discord.Member):
    """unmutes a user"""
    mutedRole = discord.utils.get(ctx.guild.roles, name="Muted")

    await member.remove_roles(mutedRole)
    await ctx.reply(f"Unmuted {member.mention}")
    await member.send(f'Unmuted in {ctx.guild.name} welcome back')

@bot.command()
@commands.has_permissions(ban_members =True)
async def ban(ctx, member : discord.Member=None, *, reason=None):
    """Bans the specified user"""
    try:
        if member == None:
            await ctx.reply("You need to specify who to ban. ")
        elif member == ctx.author:
            await ctx.reply(f"Can't ban yourself idiot")
        elif  member.top_role >= ctx.author.top_role:
            await ctx.reply(f"You can only ban members lower than yourself")
        else:
            await member.ban(reason=reason)
            embed = discord.Embed(title="bye lol", description=f"{member.mention + 'got banned' if reason == None else member.mention + 'got banned: ' + reason} ")
            await ctx.channel.send(embed=embed)
    except discord.errors.Forbidden as err:
        await ctx.reply(f"Can't ban the member, make sure the bot is higher on the role list and that the bot has the necessary permissions.\n Error: {err}")

@bot.command()
@commands.has_permissions(ban_members=True)   
async def unban(ctx, id = "0") :
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
async def warn(ctx, member : discord.Member=None, *, reason=None):
    """warns a user"""
    if member == None:
        await ctx.reply("You need to specify who to warn!")
    elif member == ctx.author:
        await ctx.reply(f"Can't warn yourself idiot")
    embed2=discord.Embed(title="Warned🗡️", description=f"{'You were warned.' + ' Now behave.' if reason == None else (' | Reason: ' + reason)}", color=discord.Colour.blurple())
    embed=discord.Embed(title="Warned", description=f"{member.mention + ' was warned' if reason == None else member.mention +  ' was warned, reason: ' + reason}", color=discord.Colour.blurple())
    await ctx.reply (embed=embed)
    await member.send(embed=embed2)

@bot.command(aliases=['clear'])
@commands.has_permissions(ban_members =True)
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
    if role == ctx.author.top_role and user == ctx.author :
        await ctx.reply(f"Can't remove role \"{role}\" as it's your highest role")
        return
    await user.remove_roles(role)
    await ctx.reply(f"{user.name} was removed from role: {role.name}")

start_time = time.time()
@bot.command(pass_context=True)
async def uptime(ctx):
    """shows bot uptime"""
    current_time = time.time()
    difference = int(round(current_time - start_time))
    text = str(datetime.timedelta(seconds=difference))
    embed = discord.Embed(colour=discord.Color.blurple())
    embed.add_field(name="Uptime", value=text)
    embed.set_footer(text="Angel$IX")
    try:
        await ctx.reply(embed=embed)
    except discord.HTTPException:
        await ctx.reply("Current uptime: " + text)

#im proud of this 
meminfo = psutil.Process(os.getpid())
totmem = psutil.virtual_memory().total / float(2 ** 20)  
mem = meminfo.memory_info()[0] / float(2 ** 20) 

@bot.command(pass_context=True, aliases=['info', 'debug'])
async def stats(ctx):
    """shows bot stats"""
    bedem = discord.Embed(title = 'System Resource Usage and statistics', description = 'See bot host statistics.', color=discord.Color.blurple()) 
    bedem.add_field(name = "Angel$IX version", value =BotVer, inline = False)
    bedem.add_field(name = 'CPU Usage', value = f'{psutil.cpu_percent()}%', inline = False)
    bedem.add_field(name = 'Total Memory', value = f'{totmem:.0f}MB', inline = False)
    bedem.add_field(name = 'Memory Usage', value = f'{mem:.0f}MB', inline = False)
    #bedem.add_field(name = 'CPU name', value = cpuinfo.get_cpu_info()['brand_raw'], inline = False) way too slow
    bedem.add_field(name = 'Discord.py Version', value = d_version, inline = False)
    bedem.add_field(name = 'Python Version', value = sys.version, inline = False)
    bedem.add_field(name = 'YTdl Version', value = ytver.__version__, inline = False)
    await ctx.reply(embed = bedem)

@bot.command()
async def invites(ctx, user : discord.Member=None):
    """Shows how many people someone has invited"""
    totalInvites = 0
    for i in await ctx.guild.invites():
        if i.inviter == (ctx.author if user == None else user):
            totalInvites += i.uses
    await ctx.reply(f"{'You have' if user == None else user} invited {totalInvites} member{'' if totalInvites == 1 else 's'} to the server!")

@bot.command(aliases=['iq'])
async def IQ(ctx):
    """Average server IQ"""
    embed=discord.Embed(title=f"Average {ctx.guild.name} IQ", description=f"{random.randint(-10 , 130 )}", color=discord.Color.blurple())
    await ctx.reply(embed=embed)

@bot.command('roll')
async def roll(ctx,*args):
    """Rolls a dice in user specified format"""
    args = "".join(args)
    
    # sanitize input - remove trailing spaces
    args=args.strip()

    args=args.replace(' ', '')

    if args == 'help':
        await ctx.reply("`~roll` - rolls a 6 sided dice\n"\
                        "`~roll 4` - rolls a 4 sided dice\n"\
                        "`~roll 2d6` - rolls two 6-sided dice\n"\
                        )
        return
        
    diceToRoll=1
    numberOfSides=6

    if args:
        try:
            (diceToRoll,numberOfSides)=parseInput(args)
        except:
            await ctx.reply('I didn\'t understand your input: `' + args + '`.\n try `~roll help` for supported options')
            return
    
    maxdicesize = 150
    maxsides =  100000000
    if  diceToRoll > maxdicesize:
        await ctx.reply(f"Too many dices, max is: {maxdicesize}")
        return
    elif diceToRoll < 0:
         await ctx.reply(f"Dice amount can't be negative")
         return
    if numberOfSides > maxsides:
        await ctx.reply(f"Too many sides, max is: {maxsides}")
        return
    elif numberOfSides < 0:
        await ctx.reply(f"Sides can't be negative")  
        return
    
    await ctx.send('Rolling `' + str(diceToRoll) + '` dice with `' + str(numberOfSides) + '` sides')

    results = []
    
    for _ in range(0, diceToRoll):
        results.insert(0, '['+str(rolladice(numberOfSides))+']')

    resultString = ',  '.join(results)
    
    await ctx.reply('Results: ' + resultString)

def parseInput(input):
    split=input.split('d')

    # remove empty items
    split=[x for x in split if x]

    if len(split) == 1:
        
        diceToRoll = 1
        sidedDice = int(split[0])
    
    else:
        
        diceToRoll = int(split[0])
        sidedDice = int(split[1])

    return diceToRoll, sidedDice
    
def rolladice(sides):
    return random.randint(1, sides)

@bot.command(pass_context=True, aliases=['cred','credits','about'])
async def credit(ctx):
    """Shows bot credits"""
    owner = await bot.fetch_user(978854415786184745)
    maintainer = await bot.fetch_user(347387857574428676)
    """Displays who created and maintained the bot"""
    await ctx.reply(creditsimage)
    embed=discord.Embed(title=f"Made by: {owner}, Maintained by: {maintainer}", description="ask them anything! 24/7\n Feel free to add them as a friend", color=discord.Color.blurple())
    await ctx.send(embed=embed)

@bot.command(pass_context=True, aliases=['fem']) # :skull:
async def femboy(ctx):
    """Femboy Wisdom/Tutorial"""
    embed=discord.Embed(title="Chakal's Wisdom On Femboys",description="How can you be a feminine looking boy? Simple. \nGrow your hair out, exercise regularly (I run/jog to remain slim, and I do squats/tap dance to exercise my thighs/butt), trim your facial hair, do whatever you can to help out your skin, and consider taking HRT.\n Learn how to do makeup, it is a fucking amazing tool. Experiment with different outfits, my favorite for andro people is just leggings beneath feminine jean shorts, it is common for females in the UK and looks feminine, but not so feminine that it will look weird in public.\nConsider taking speech therapy, or just watching some videos and working at getting a more feminine voice.\nAt the end of the day, though, you can practically look like a girl, with the most luscious hair, smallest eyebrows, red lips, and longest lashes; you can have the perfect body type, be an hourglass with a big ass, thick thighs/hips and a skinny waist; you can sound like the girliest woman in the world; you can wear booty shorts and a half shirt and look damn good in it; you can be a master at feminine makeup.\nBut it all means nothing if you fail to act feminine. For looks catch the eye, but personality catches the heart.\nThere comes a point when you must ask yourself if you want to be a femboy, or simply be a feminine looking man.\nSo, how can you be a femboy?\nAct feminine. Femboys are made, not born.  -Chakal", color=discord.Color.blurple())
    embed2=discord.Embed(title="Miro's Wisdom On Femboys",description="Hey, some guys like being cute and pastel, trans guys included, and some transgender people don’t really feel the need to change their bodies either. So that’s an option. Maybe you’re a really feminine guy who’s fine with having a female body.\n Or, maybe you just really like the femboy aesthetic. Or maybe you’re attracted to femboys. Idk, I’m not you. It’s gonna take a little experimentation to find out.\n 1) Get some clothes you feel comfortable in. Try out that femboy look. Do you feel cute? Does it feel right? Whether you are cis or trans, you should be able to wear clothes that make you feel good about yourself. So do that. Whatever the answers are to the other questions, this will almost certainly make you feel a little better.\n 2) Do some googling. Learn about fem trans boys, demiboys, and non-binary people. Read some things from their perspectives. Does any of it resonate with you?\n3) Try some things. It’s normal for us to question our identities and grow and change through the years, and it’s normal to not fully understand yourself right away. If you think you might be trans, maybe try a different name or pronouns. if you don’t have supportive people around willing to help you experiment, then you can introduce yourself the way you want online, with strangers you’ll never have to interact with again. It takes a lot of the pressure off, too, if you’re nervous. Maybe it’ll feel right and you’ll know. Maybe it’ll feel wrong and you’ll realize you’re a girl. Maybe you’ll still be confused and have to try some new things. Have patience, it can take time.\n4) Own it. Whatever your identity is, dress the way you like and be who you are and if anyone gives you shit about it, just show them how high you can kick their balls up their ass in your adorable little pink skirt -Miro.", color=discord.Color.blurple())
    await ctx.send(embed=embed)
    await ctx.reply(embed=embed2)

@bot.command()
async def support(ctx, *, message = None):
    """shows support server link"""
    if message == "release" or message == "changelog":
        await ctx.reply("Latest Bot release: \n https://github.com/maj113/Angel6/releases/latest")
        return
    embed=discord.Embed(title="Support server",description="Need help with the bot? https://discord.gg/ctsjpMQXEe \nWant to contribute to the bot? <https://github.com/maj113/Angel6>", color=discord.Color.blurple())
    await ctx.reply(embed=embed)
    await ctx.send("https://cdn.discordapp.com/attachments/997647296189698129/1075442911040262205/paintdotnet_LFkzPDrQML.png")

@bot.command(pass_context=True, aliases=['vio', 'violated'])
async def violation(ctx):
    """That one there was a violation"""
    await ctx.reply("https://tenor.com/view/that-one-there-was-a-violation-that1there-was-violation-violation-that-one-there-was-a-violation-personally-i-wouldnt-have-it-that1there-was-a-violation-personally-i-wouldnt-have-it-gif-20040456")

@bot.command(pass_context=True, aliases=['germany', 'bahzz'])
async def german(ctx):
    """Random German Gif"""
    #why does this exist?
    await ctx.reply("https://giphy.com/gifs/fifa-Vd8wLaK3lNDNMuGaUL \n SHUT THE FUCK UP BAHZZ VIVA LA GERMANY AAJAJJAJAJAJA")


def clsscr():
    os.system('cls' if os.name == 'nt' else print("\x1B[2J"))

async def helperasbot():
    for server in bot.guilds:
        for channel in server.channels:
            if str(channel.type) == 'text':
                print(f"    {channel.name} : {channel.id}")

#FIXME: one line if statement 
@bot.command(pass_context=True)
@commands.has_permissions(ban_members=True)
async def asbot(ctx, *, arg = None):
    """start or stop the asbot function"""
    if arg == "stop":
        if asbotmain.is_running() == False: return await ctx.reply("**`asbotmain()`** is not running!")
        await ctx.reply("Stopped task **`asbotmain()`** successfully")
        print(f"Warning: asbotmain() was stopped externally by {ctx.author} !!!"), asbotmain.cancel()
    elif arg == "start":
        if asbotmain.is_running() == True: return await ctx.reply("**`asbotmain()`** is already running!")
        await ctx.reply("Started task **`asbotmain()`** successfully")
        print(f"Warning: asbotmain() was started externally by {ctx.author} !!!"), asbotmain.start()
    else: await ctx.reply(embed=discord.Embed(title="`asbotmain()` state:"+f"{' **running**' if asbotmain.is_running() == True else ' **stopped**'}", color=discord.Color.blurple()))

#FIXME: get rid of global
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
        await channel1.send("⠀") #This is a Unicode "U+2800/Braille Pattern Blank" character

async def main():
    await bot.start(TOKEN)                                 
asyncio.get_event_loop().run_until_complete(main())
