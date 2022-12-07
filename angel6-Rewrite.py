import logging, asyncio, functools, psutil, math, time, datetime, random, sys, discord, yt_dlp, os, itertools
from subprocess import run
from discord import __version__ as d_version
from discord.ext import commands
from yt_dlp import utils
from async_timeout import timeout
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHAN_ID = os.getenv("LOGGING_CHANNEL_ID")
JL_CHAN_ID = os.getenv("JOIN_LEAVE_CHANNEL_ID")
GEN_CHAN_ID = os.getenv("GENERAL_CHANNEL_ID")
BotVer = "**2.2.3** <https://github.com/maj113/Angel6/releases/latest>"
# Silence useless bug reports messages

utils.bug_reports_message = lambda: ''


#Enable debug options if launch argument "debug" is passed
DebuggingOpts = {
    "ytdllogging" : False,
    "ytdlquiet" : True,
    "LogLevel" : logging.INFO
}
if sys.argv[-1] == "debug" or sys.argv[-1] == "d":
    DebuggingOpts["ytdllogging"] = True
    DebuggingOpts["ytdlquiet"] = False
    DebuggingOpts["LogLevel"] = logging.DEBUG

logging.basicConfig(level=DebuggingOpts["LogLevel"])
class VoiceError(Exception):
    pass

class YTDLError(Exception):
    pass

class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'extractaudio': True,
        'format': 'bestaudio/best',      
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': DebuggingOpts["ytdllogging"],
        'logtostderr': DebuggingOpts["ytdllogging"],
        'quiet': DebuggingOpts["ytdlquiet"],
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 1):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))
        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)
    pass


    @staticmethod
    def parse_duration(duration: int):
        if duration == 0:
            return "LIVE"
        
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        
        duration_formated = []
        if days > 0:
            duration_formated.append(f'{days}d')
        if hours > 0:
            duration_formated.append(f'{hours}h')
        if minutes > 0:
            duration_formated.append(f'{minutes}m')
        if seconds > 0:
            duration_formated.append(f'{seconds}s')
        
        return " ".join(duration_formated)

class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester
    
    def create_embed(self):
        embed = (discord.Embed(title='Now playing', description='```css\n{0.source.title}\n```'.format(self), color=discord.Color.blurple())
                .add_field(name='Duration', value=self.source.duration)
                .add_field(name='Requested by', value=self.requester.mention)
                .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                .set_thumbnail(url=self.source.thumbnail)
                .set_author(name=self.requester.name, icon_url=self.requester.avatar.url))
        return embed

class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]

class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True

        self._loop = False
        self._volume = 1
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value
    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None
            if self.loop == False:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return
                
                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed())
            
            #If the song is looped
            elif self.loop == True:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)
            
            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.reply('An error occurred: {}'.format(str(error)))

    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != bot.user.id:
            print(f"{message.guild}/{message.channel}/{message.author.name}>{message.content}")
            if message.embeds:
                print(message.embeds[0].to_dict())

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='summon')
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect','quit'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.reply('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume', aliases=['vol'])
    @commands.is_owner()
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.reply('Nothing being played at the moment.')

        if 0 > volume > 100:
            return await ctx.reply('Volume must be between 0 and 100')
        else:
            player = ctx.voice_client
            player.source.volume = volume / 100
            await ctx.reply('Volume of the player set to {}%'.format(volume))

    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""
        if ctx.voice_state.current == None:
            await ctx.reply("Nothing is playing at the moment")
            return
        embed = ctx.voice_state.current.create_embed()
        await ctx.reply(embed=embed)

    @commands.command(name='pause', aliases=['pa'])
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""
        print(">>>Pause Command:")
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume', aliases=['re', 'res'])
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip', aliases=['s'])
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.reply('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester or ctx.author.guild_permissions.manage_messages:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.reply('Skip vote added, currently at **{}/3**'.format(total_votes))

        else:
            await ctx.reply('You have already voted to skip this song.')

    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):

        """Shows the player's queue
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.reply('Queue is empty!.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1,song)

        embed = (discord.Embed(description=f'**{len(ctx.voice_state.songs)} tracks:**\n\n{queue}'))
        embed.set_footer(text=f'Viewing page {page}/{pages}')
        await ctx.reply(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.reply('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.reply('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.reply('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        print(ctx.voice_state.loop)
        if ctx.voice_state.loop == True:
            await ctx.message.add_reaction('✅')
        else:
            await ctx.message.add_reaction('❎') #when looping disabled
    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        async with ctx.typing():
            try:
                source = await YTDLSource.create_source(ctx, search, loop=bot.loop) #I don't think self is needed here, removed
            except YTDLError as err:
                await ctx.reply('An error occurred while processing this request: {}'.format(str(err)))
            else:
                if not ctx.voice_state.voice:
                    await ctx.invoke(self._join)

                song = Song(source)
                await ctx.voice_state.songs.put(song)
                await ctx.reply('Enqueued {}'.format(str(source)))


            
    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')

intents = discord.Intents().all()

activity = discord.Game(name="Best Bot ever!!!!")
bot = commands.Bot(command_prefix='~', intents=intents, activity=activity,status_act=discord.Status.do_not_disturb)


def restart_program():
    os.execv(sys.executable, ['python3'] + sys.argv)     

@bot.command()
@commands.has_permissions(ban_members=True)
async def restart(ctx):
    """restarts the bot"""
    await ctx.reply(" Restarting, please allow 5 seconds for this. ")
    restart_program()

@bot.command()
async def ping(ctx):
    """shows the ping"""
    embed = discord.Embed(title="Bot latency:",color=discord.Color.blurple(),description=f"**{(bot.latency * 1000):.0f}ms**")
    await ctx.reply(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as:\n{bot.user.name}\n{bot.user.id}')
    file = open(os.path.join(os.path.dirname(__file__), 'Ascii1.txt'), 'rt')
    content = file.read()
    file.close()
    restartbot = False

    if os.getenv("LOGGING_CHANNEL_ID") == "" :
        logginginput = int(input("Input logging channel ID ").strip())
        with open(".env", "r") as envfile:
            content1 = envfile.read()
            changed = content1.replace("LOGGING_CHANNEL_ID=", ''.join(["LOGGING_CHANNEL_ID=", str(logginginput)]))
            with open('.env','w') as envfile:
                envfile.write(changed)
        restartbot = True
    
    if os.getenv("LOGGING_CHANNEL_ID") == None :
        logginginput = int(input("Input logging channel ID ").strip())
        with open(".env", "a") as envfile:
            envfile.write(f"\nLOGGING_CHANNEL_ID={logginginput}")
        restartbot = True
    
    if os.getenv("JOIN_LEAVE_CHANNEL_ID") == None :
        joinleaveinput = int(input("Input join/leave channel ID ").strip())
        with open(".env", "a") as envfile:
            envfile.write(f"\nJOIN_LEAVE_CHANNEL_ID={joinleaveinput}")
        restartbot = True

    if os.getenv("JOIN_LEAVE_CHANNEL_ID") == "" :
        joinleaveinput = int(input("Input join/leave channel ID ").strip())
        with open(".env", "r") as envfile:
            content1 = envfile.read()
            changed = content1.replace("JOIN_LEAVE_CHANNEL_ID=", ''.join(["JOIN_LEAVE_CHANNEL_ID=", str(joinleaveinput)]))
            with open('.env','w') as envfile:
                envfile.write(changed)
        restartbot = True

    if os.getenv("GENERAL_CHANNEL_ID") == None :
        generalinput = int(input("Input general channel ID ").strip())
        with open(".env", "a") as envfile:
            envfile.write(f"\nGENERAL_CHANNEL_ID={generalinput}")
        restartbot = True

    if os.getenv("GENERAL_CHANNEL_ID") == "" :
        generalinput = int(input("Input general channel ID ").strip())
        with open(".env", "r") as envfile:
            content1 = envfile.read()
            changed = content1.replace("GENERAL_CHANNEL_ID=", ''.join(["GENERAL_CHANNEL_ID=", str(generalinput)]))
            with open('.env','w') as envfile:
                envfile.write(changed)
        restartbot = True
    
    if restartbot == True:
        restart_program()
    
    embed = discord.Embed(title = 'Bot settings', description = 'Current bot settings and status', color=discord.Color.blurple())
    embed.add_field(name="**Angel$IX Version:**", value=BotVer, inline=False)
    embed.add_field(name="logging channel", value=LOG_CHAN_ID, inline=False)
    embed.add_field(name="Join leave channel", value=JL_CHAN_ID, inline=False)
    embed.add_field(name="General channel", value=GEN_CHAN_ID, inline=False)
    embed.add_field(name="Current API latency:", value=f'{(bot.latency * 1000):.0f}ms', inline=False)
    ID = int(LOG_CHAN_ID)
    channel = bot.get_channel(ID)
    await channel.send(content)
    await channel.send(embed=embed)       


@bot.event
async def on_member_join(member):
    ID = int(JL_CHAN_ID)
    channel = bot.get_channel(ID)    
    embed = discord.Embed(colour=discord.Colour.blurple(), description=f"{member.mention} joined, Total Members: {len(list(member.guild.members))}")
    embed.set_thumbnail(url=f"{member.avatar.url}")
    embed.set_footer(text=f"{member.guild}", icon_url=f"{member.guild.icon.url}")
    await channel.send(embed=embed)
    if os.getenv("GENERAL_CHANNEL_ID") == None or os.getenv("GENERAL_CHANNEL_ID") == "" :
        mbed = discord.Embed(
        colour = (discord.Colour.blurple()),
        title = 'Glad you could find us!',
        description =f"yo! im Dyztopian D3lirium's Personal Bot, proceed to General to talk:)")
        await member.send(embed=mbed)   
    
    else:
        chanID = int(GEN_CHAN_ID)
        mbed = discord.Embed(
            colour = (discord.Colour.blurple()),
            title = 'Glad you could find us!',
            
            description =f"yo! im Dyztopian D3lirium's Personal Bot, proceed to <#{chanID}> to talk:)")
        await member.send(embed=mbed)

@bot.event
async def on_member_remove(member):
    ID = int(JL_CHAN_ID)
    channel = bot.get_channel(ID)
    embed = discord.Embed(colour=discord.Colour.blurple(), description=f"{member.mention} Left us, Total Members: {len(list(member.guild.members))}")
    embed.set_thumbnail(url=f"{member.avatar.url}")
    embed.set_footer(text=f"{member.guild}", icon_url=f"{member.guild.icon.url}")
    await channel.send(embed=embed)

@bot.command(aliases=["members"])
async def users(ctx):
    """shows total amount of members"""
    a=ctx.guild.member_count
    b=discord.Embed(title=f"Total members in {ctx.guild.name}",description=a,color=discord.Color.blurple())
    await ctx.reply(embed=b)

#there's probably a better way to check if a user has been mentioned
@bot.command()
async def av(ctx, *,  avamember : discord.Member=None):
    """grabs users avatar"""
    if avamember is None:
        avamember = ctx.author
        userAvatarUrl = avamember.avatar.url
        await ctx.reply(userAvatarUrl)
        await ctx.send("^^")
    else:
        userAvatarUrl = avamember.avatar.url
        await ctx.reply(userAvatarUrl)
        await ctx.send("^^")

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
    embed.set_thumbnail(url=icon)#this is way too basic should fix
    embed.add_field(name="Owner", value=owner, inline=True)
    embed.add_field(name="Server ID", value=id, inline=True)
    embed.add_field(name="Member Count", value=memberCount, inline=True)
    embed.add_field(name="Created", value=ctx.guild.created_at.strftime(
            "%B %d, %Y, %I:%M %p"), inline=True)
    await ctx.reply(embed=embed)
    
@bot.command()
@commands.has_permissions(manage_messages=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    """mutes a user"""
    embed=discord.Embed(title="Muted", description=f"{member.mention} was muted for {reason}")
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
    await member.send(f"You were muted for {reason}")

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

@bot.command()
@commands.has_permissions(kick_members =True)
async def unmute(ctx, member: discord.Member):
    """unmutes a user"""
    mutedRole = discord.utils.get(ctx.guild.roles, name="Muted")

    await member.remove_roles(mutedRole)
    await ctx.reply(f"Unmuted {member.mention}")
    await member.send(f'Unmuted in {ctx.guild.name} welcome back')

#im proud of this 
meminfo = psutil.Process(os.getpid())
totmem = psutil.virtual_memory().total / float(2 ** 20)  
mem = meminfo.memory_info()[0] / float(2 ** 20) 
ytdlfunc = run("yt-dlp --version", shell=True, capture_output=True).stdout.decode('ascii')

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
    bedem.add_field(name = 'YTdl Version', value = ytdlfunc.strip(), inline = False)
    await ctx.reply(embed = bedem)

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
            if reason == None:
                embed = discord.Embed(title="bye lol", description=f"{member.mention} got banned ")
            else:
                embed = discord.Embed(title="bye lol", description=f"{member.mention} got banned: {reason} ")
            await ctx.channel.send(embed=embed)
    except discord.errors.Forbidden:
        await ctx.reply("Can't ban the member, make sure the bot is higher on the role list and that the bot has the necessary permissions. ")


@bot.command()
@commands.has_permissions(ban_members =True)   
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

@bot.command(aliases=["clear"])
@commands.has_permissions(ban_members =True)
async def wipe(ctx, amount=20):
    """wipes 20 messages or the number specified"""
    await ctx.channel.purge(limit=amount)
    await ctx.channel.send(f"Cleanup Complete.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member : discord.Member=None, *, reason=None):
    """warns a user"""
    if member == None:
        await ctx.reply("You need to specify who to warn!")
    elif member == ctx.author:
        await ctx.reply(f"Can't warn yourself idiot")
    else:
        if reason == None:
            embed2=discord.Embed(title="Warned🗡️", description=f"You were warned, now behave.")
            embed=discord.Embed(title="Warned", description=f"{member.mention} was warned")
        else:
            embed2=discord.Embed(title="Warned🗡️", description=f"You were warned | Reason: {reason}")
            embed=discord.Embed(title="Warned", description=f"{member.mention} was warned | Reason: {reason}")
        await ctx.reply (embed=embed)
        await member.send(embed=embed2)

@bot.command()
async def invites(ctx, user : discord.Member=None):
    """Shows how many people someone has invited"""
    if user == None:
        totalInvites = 0
        for i in await ctx.guild.invites():
            if i.inviter == ctx.author:
                totalInvites += i.uses
        await ctx.reply(f"You've invited {totalInvites} member{'' if totalInvites == 1 else 's'} to the server!")
    else:
        totalInvites = 0
        member = user
        for i in await ctx.guild.invites():
            if i.inviter == member:
                totalInvites += i.uses
        await ctx.reply(f"{member} has invited {totalInvites} member{'' if totalInvites == 1 else 's'} to the server!")
    
@bot.command(aliases=["iq"])
async def IQ(ctx):
    """Average server IQ"""
    embed=discord.Embed(title=f"Average {ctx.guild.name} IQ", description=f"{random.randint(-10 , 130 )}", color=discord.Color.blurple())
    await ctx.reply(embed=embed)

@bot.command('roll')
async def roll(ctx,*args):
    """Rolls a dice in user specified format"""
    args = "".join(args)
    
    print("args is:" + str(args))
    
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
    
    await ctx.send('Rolling `' + str(diceToRoll) + '` dice with `' + str(numberOfSides) + '` sides')

    results = []
    
    for _ in range(0, diceToRoll):
        print('rolling a ' + str(numberOfSides) + ' sided dice')
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

    if diceToRoll > 150:
        raise Exception('too many dice')
    
    if sidedDice > 100000000:
        raise Exception('too many sides')
    
    return diceToRoll, sidedDice
    
def rolladice(sides):
    return random.randint(1, sides)

@bot.command(pass_context=True, aliases=['cred','credits','about'])
async def credit(ctx):
    """Shows bot credits"""
    owner = await bot.fetch_user(978854415786184745)
    maintainer = await bot.fetch_user(347387857574428676)
    """Displays who created and maintained the bot"""
    file = open(os.path.join(os.path.dirname(__file__), 'Ascii1.txt'), 'rt')
    content = file.read()
    file.close()
    await ctx.send(content)
    embed=discord.Embed(title=f"Made by: {owner}, Maintained by: {maintainer}", description="ask them anything! 24/7\n Feel free to add them as a friend")
    await ctx.reply(embed=embed)

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

@bot.command(pass_context=True, aliases=["fem"]) # :skull:
async def femboy(ctx):
    """Femboy Wisdom/Tutorial"""
    embed=discord.Embed(title="Chakal's Wisdom On Femboys",description="How can you be a feminine looking boy? Simple. \nGrow your hair out, exercise regularly (I run/jog to remain slim, and I do squats/tap dance to exercise my thighs/butt), trim your facial hair, do whatever you can to help out your skin, and consider taking HRT.\n Learn how to do makeup, it is a fucking amazing tool. Experiment with different outfits, my favorite for andro people is just leggings beneath feminine jean shorts, it is common for females in the UK and looks feminine, but not so feminine that it will look weird in public.\nConsider taking speech therapy, or just watching some videos and working at getting a more feminine voice.\nAt the end of the day, though, you can practically look like a girl, with the most luscious hair, smallest eyebrows, red lips, and longest lashes; you can have the perfect body type, be an hourglass with a big ass, thick thighs/hips and a skinny waist; you can sound like the girliest woman in the world; you can wear booty shorts and a half shirt and look damn good in it; you can be a master at feminine makeup.\nBut it all means nothing if you fail to act feminine. For looks catch the eye, but personality catches the heart.\nThere comes a point when you must ask yourself if you want to be a femboy, or simply be a feminine looking man.\nSo, how can you be a femboy?\nAct feminine. Femboys are made, not born.  -Chakal")
    embed2=discord.Embed(title="Miro's Wisdom On Femboys",description="Hey, some guys like being cute and pastel, trans guys included, and some transgender people don’t really feel the need to change their bodies either. So that’s an option. Maybe you’re a really feminine guy who’s fine with having a female body.\n Or, maybe you just really like the femboy aesthetic. Or maybe you’re attracted to femboys. Idk, I’m not you. It’s gonna take a little experimentation to find out.\n 1) Get some clothes you feel comfortable in. Try out that femboy look. Do you feel cute? Does it feel right? Whether you are cis or trans, you should be able to wear clothes that make you feel good about yourself. So do that. Whatever the answers are to the other questions, this will almost certainly make you feel a little better.\n 2) Do some googling. Learn about fem trans boys, demiboys, and non-binary people. Read some things from their perspectives. Does any of it resonate with you?\n3) Try some things. It’s normal for us to question our identities and grow and change through the years, and it’s normal to not fully understand yourself right away. If you think you might be trans, maybe try a different name or pronouns. if you don’t have supportive people around willing to help you experiment, then you can introduce yourself the way you want online, with strangers you’ll never have to interact with again. It takes a lot of the pressure off, too, if you’re nervous. Maybe it’ll feel right and you’ll know. Maybe it’ll feel wrong and you’ll realize you’re a girl. Maybe you’ll still be confused and have to try some new things. Have patience, it can take time.\n4) Own it. Whatever your identity is, dress the way you like and be who you are and if anyone gives you shit about it, just show them how high you can kick their balls up their ass in your adorable little pink skirt -Miro.")
    await ctx.send(embed=embed)
    await ctx.reply(embed=embed2)
    
@bot.command(pass_context=True)
async def support(ctx):
    """shows support server link"""
    embed=discord.Embed(title="Support server",description="Need help with the bot? \nWant to contribute to the bot?", color=discord.Color.blurple())
    await ctx.send(embed=embed)
    await ctx.reply("https://discord.gg/ctsjpMQXEe \n https://github.com/maj113/Angel6")

    
@bot.command(pass_context=True, aliases=["vio", "violated"])
async def violation(ctx):
    """That one there was a violation"""
    await ctx.reply("https://tenor.com/view/that-one-there-was-a-violation-that1there-was-violation-violation-that-one-there-was-a-violation-personally-i-wouldnt-have-it-that1there-was-a-violation-personally-i-wouldnt-have-it-gif-20040456")

@bot.command(pass_context=True)
async def german(ctx):
    """Random German Gif"""
    #why does this exist?
    await ctx.reply("https://giphy.com/gifs/fifa-Vd8wLaK3lNDNMuGaUL \n SHUT THE FUCK UP BAHZZ VIVA LA GERMANY AAJAJJAJAJAJA")

async def main():
    # if you need to, initialize other things, such as aiohttp
    bot.add_cog(Music(bot))
    await bot.start(TOKEN)                                 
asyncio.get_event_loop().run_until_complete(main())
