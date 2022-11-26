import logging
import traceback
import asyncio
from functools import partial
import psutil
import itertools
import time
import datetime
import random
from subprocess import run
import sys
import discord
from discord import __version__ as d_version
from discord.ext import commands
import cpuinfo
import yt_dlp
from yt_dlp import utils
from async_timeout import timeout
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHAN_ID = os.getenv("LOGGING_CHANNEL_ID")
JL_CHAN_ID = os.getenv("JOIN_LEAVE_CHANNEL_ID")
GEN_CHAN_ID = os.getenv("GENERAL_CHANNEL_ID")
BotVer = "**2.2.2** <https://github.com/maj113/Angel6/releases/latest>"
# Silence useless bug reports messages

utils.bug_reports_message = lambda: ''

logging.basicConfig(level=logging.INFO)

#improved Music Cog thanks to @RoastSea8 and @EvieePy with removed Lyrics functionality and slight code change




class YTDLError(Exception):
    pass
class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""
    

class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""
    
invoke = False
passed = False

class YTDLSource(discord.PCMVolumeTransformer):
    
    ytdlopts = {
        'extractaudio': True,
        'format': 'bestaudio/best',      
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
    }

    ffmpegopts = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -c:a copy',
    }
    
    ytdl = yt_dlp.YoutubeDL(ytdlopts)
    invoke = False
    passed = False
    
    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.duration = data.get('duration')
        try:
            self.track = data.get('track')
            self.artist = data.get('artist')
            passed = True
        except:
            pass

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()
        to_run = partial(cls.ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        embed = discord.Embed(title="", description=f"Queued [{data['title']}]({data['webpage_url']}) [{ctx.author.mention}]", color=discord.Color.blurple())
        await ctx.send(embed=embed)

        if download:
            source = cls.ytdl.prepare_filename(data)
        else:
            if passed:
                return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title'], 'duration': data['duration'], 'track': data['track'], 'artist': data['artist']}
            else:
                return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title'], 'duration': data['duration']}

        return cls(discord.FFmpegPCMAudio(source), data=data,**cls.ffmpegopts, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(cls.ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url'],**cls.ffmpegopts), data=data, requester=requester)

    
class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = 1
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            embed = discord.Embed(title="Now playing", description=f"[{source.title}]({source.web_url}) [{source.requester.mention}]", color=discord.Color.blurple())
            self.np = await self._channel.send(embed=embed)
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='join', aliases=['connect', 'j'], description="connects to voice")
    async def connect_(self, ctx, *, channel: discord.VoiceChannel = None):
        """Connect to voice.
        Parameters
        ------------
        channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.
        This command also handles moving the bot to different channels.
        """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = discord.Embed(title="", description="No channel to join. Please call `,join` from a voice channel.", color=discord.Color.blurple())
                await ctx.send(embed=embed)
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')
        elif channel:
            return

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')

        if random.randint(0, 1) == 0:
            await ctx.message.add_reaction('👍')
        await ctx.send(f'**Joined `{channel}`**')
    
    @commands.command(name='play', aliases=['sing','p'], description="streams music")
    async def play_(self, ctx, *, search: str):
        """Request a song and add it to the queue.
        This command attempts to join a valid voice channel if the bot is not already in one.
        Uses YTDL to automatically search and retrieve a song.
        Parameters
        ------------
        search: str [Required]
            The song to search and retrieve using YTDL. This could be a simple search, an ID or URL.
        """
        global invoke
        vc = ctx.voice_client

        if ctx.author.voice is None:
            embed = discord.Embed(title="", description="You need to be in a voice channel to play songs", color=discord.Color.blurple())
            return await ctx.send(embed=embed)

        if not vc:
            invoke = True
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        await ctx.typing()

        # If download is False, source will be a dict which will be used later to regather the stream.
        # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)

        await player.queue.put(source)
    
    #@commands.command(name='search')    
    async def _search(self, ctx: commands.Context, *, search: str):
        """Searches YouTube.
        It returns an embed of the first 10 results collected from YouTube.
        Then the user can choose one of the titles by typing a number
        in chat or they can cancel by typing "cancel" in chat.
        Each title in the list can be clicked as a link.
        """
        async with ctx.typing():
            try:
                source =  await YTDLSource.search_source(ctx, search, loop=self.bot.loop, bot=self.bot)
            except YTDLError as err:
                await ctx.reply('An error occurred while processing this request: {}'.format(str(err)))
            else:
                if source == 'sel_invalid':
                    await ctx.reply('Invalid selection')
                elif source == 'cancel':
                    await ctx.reply(':white_check_mark:')
                elif source == 'timeout':
                    await ctx.reply(':alarm_clock: **Time\'s up bud**')
                else:
                    if not ctx.voice_state.voice:
                        await ctx.invoke(self._join)

                    song = Song(source)
                    await ctx.voice_state.songs.put(song)
                    await ctx.reply('Enqueued {}'.format(str(source)))
    
    @commands.command(name='pause', description="pauses music")
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            embed = discord.Embed(title="", description="I am currently not playing anything", color=discord.Color.blurple())
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send("Paused ⏸️")

    @commands.command(name='resume', description="resumes music")
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.blurple())
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send("Resuming ⏯️")

    @commands.command(name='skip', description="skips to next song in queue")
    async def skip_(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.blurple())
            return await ctx.send(embed=embed)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
    
    @commands.command(name='remove', aliases=['rm', 'rem'], description="removes specified song from queue")
    async def remove_(self, ctx, pos : int = None):
        """Removes specified song from queue"""

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.blurple())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if pos is None:
            player.queue._queue.pop()
        else:
            try:
                s = player.queue._queue[pos-1]
                del player.queue._queue[pos-1]
                embed = discord.Embed(title="", description=f"Removed [{s['title']}]({s['webpage_url']}) [{s['requester'].mention}]", color=discord.Color.blurple())
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(title="", description=f'Could not find a track for "{pos}"', color=discord.Color.blurple())
                await ctx.send(embed=embed)
    
    @commands.command(name='clear', aliases=['clr', 'cl', 'cr'], description="clears entire queue")
    async def clear_(self, ctx):
        """Deletes entire queue of upcoming songs."""

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.blurple())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        player.queue._queue.clear()
        await ctx.send('💣 **Cleared**')

    def convert(self, seconds):
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)
        return duration

    @commands.command(name='queue', aliases=['q', 'playlist', 'que'], description="queues song and shows the queue")
    async def queue_info(self, ctx, *, search: str = None):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.blurple())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)

        if search is not None:
            if ctx.author.voice is None:
                embed = discord.Embed(title="", description="You need to be in a voice channel to queue songs", color=discord.Color.blurple())
                return await ctx.send(embed=embed)
            await ctx.typing()
            source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=True)
            await player.queue.put(source)
        else:
            pass

        if player.queue.empty() and vc.is_playing():
            fmt = f"\n__Now Playing__:\n[{vc.source.title}]({vc.source.web_url}) | ` {self.convert(vc.source.duration % (24*3600))} Requested by: {vc.source.requester}`\n\n**0 songs in queue**"
            embed = discord.Embed(title=f'Queue for {ctx.guild.name}', description=fmt, color=discord.Color.blurple())
            embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            return await ctx.send(embed=embed)
        elif player.queue.empty() and not vc.is_playing():
            embed = discord.Embed(title="", description="queue is empty", color=discord.Color.blurple())
            return await ctx.send(embed=embed)

        # Grabs the songs in the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))
        fmt = '\n'.join(f"`{(upcoming.index(_)) + 1}.` [{_['title']}]({_['webpage_url']}) | ` {self.convert(_['duration'] % (24*3600))} Requested by: {_['requester']}`\n" for _ in upcoming)
        if len(upcoming) == 1:
            song = 'song'
        else:
            song = 'songs'
        fmt = f"\n__Now Playing__:\n[{vc.source.title}]({vc.source.web_url}) | ` {self.convert(vc.source.duration % (24*3600))} Requested by: {vc.source.requester}`\n\n__Up Next:__\n" + fmt + f"\n**{len(upcoming)} {song} in queue**"
        embed = discord.Embed(title=f'Queue for {ctx.guild.name}', description=fmt, color=discord.Color.blurple())
        embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar.url)

        await ctx.send(embed=embed)

    def create_embed(self):
        embed = (discord.Embed(title='Now playing', description='```css\n{0.source.title}\n```'.format(self), color=discord.Color.blurple())
                .add_field(name='Duration', value=self.source.duration)
                .add_field(name='Requested by', value=self.requester.mention)
                .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                .set_thumbnail(url=self.source.thumbnail)
                .set_author(name=self.requester.name, icon_url=self.requester.avatar.url))
        return embed

    @commands.command(name='np', aliases=['song', 'current', 'currentsong', 'playing'], description="shows the current playing song")
    async def now_playing_(self, ctx):
        """Display information about the currently playing song."""
        embed = ctx.voice_state.current.create_embed()
        await ctx.reply(embed=embed)


    @commands.command(name='volume', aliases=['vol', 'v'], description="changes client's volume")
    async def change_volume(self, ctx, *, vol: float=None):
        """Change the player volume.
        Parameters
        ------------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I am not currently connected to voice", color=discord.Color.blurple())
            return await ctx.send(embed=embed)
        
        if not vol:
            embed = discord.Embed(title="", description=f"🔊 **{vc.source.volume * 100}%**", color=discord.Color.blurple())
            return await ctx.send(embed=embed)

        if not 0 < vol < 101:
            embed = discord.Embed(title="", description="Please enter a value between 1 and 100", color=discord.Color.blurple())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = discord.Embed(title="", description=f'**`{ctx.author}`** set the volume to **{vol}%**', color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.command(name='leave', aliases=["stop", "dc", "disconnect", "bye", "gtfo"], description="stops music and disconnects from voice")
    async def leave_(self, ctx):
        """Stop the currently playing song and destroy the player.
        !Warning!
            This will destroy the player assigned to your guild, also deleting any queued songs and settings.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.blurple())
            return await ctx.send(embed=embed)

        if random.randint(0, 1) == 0:
            await ctx.message.add_reaction('👋')
        await ctx.send('**Successfully dipped**')

        await self.cleanup(ctx.guild)


intents = discord.Intents().all()

bot = commands.Bot(command_prefix='~', intents=intents)
status = ['Jamming out to music!', 'Eating!', 'Sleeping!']

def restart_program():
    os.execv(sys.executable, ['python3'] + sys.argv)     

@bot.command()
@commands.has_permissions(kick_members=True)
async def restart(ctx):
    """restarts the bot"""
    await ctx.reply(" Restarting, please allow 5 seconds for this. ")
    restart_program()

@bot.command()
async def ping(ctx):
    """shows the ping"""
    await ctx.reply(f'Here {(bot.latency * 1000):.0f} ms')


@bot.event
async def on_ready():
    print('Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))
    await bot.change_presence(activity=discord.Game(name="Mutiny's Official Bot"))

    #specifies Ascii art location for boot-up message
    file = open(os.path.join(os.path.dirname(__file__), 'Ascii1.txt'), 'rt')
    content = file.read()
    file.close()
    if os.getenv("LOGGING_CHANNEL_ID") == "" :
        logginginput = int(input("Input logging channel ID ")).strip()
        with open(".env", "r") as envfile:
            content1 = envfile.read()
            changed = content1.replace("LOGGING_CHANNEL_ID=", ''.join(["LOGGING_CHANNEL_ID=", str(logginginput)]))
            with open('.env','w') as envfile:
                envfile.write(changed)
        restart_program()
    
    elif os.getenv("LOGGING_CHANNEL_ID") == None :
        logginginput = int(input("Input logging channel ID ")).strip()
        channel = bot.get_channel(logginginput)
        with open(".env", "a") as envfile:
            envfile.write(f"\nLOGGING_CHANNEL_ID={logginginput}")
        restart_program()
    
    if os.getenv("JOIN_LEAVE_CHANNEL_ID") == None :
        logginginput = input("Input join/leave channel ID ").strip()
        with open(".env", "a") as envfile:
            envfile.write(f"\nJOIN_LEAVE_CHANNEL_ID={logginginput}")
        restart_program()

    elif os.getenv("JOIN_LEAVE_CHANNEL_ID") == "" :
        logginginput = int(input("Input join/leave channel ID ")).strip()
        channel = bot.get_channel(logginginput)
        with open(".env", "r") as envfile:
            content1 = envfile.read()
            changed = content1.replace("JOIN_LEAVE_CHANNEL_ID=", ''.join(["JOIN_LEAVE_CHANNEL_ID=", str(logginginput)]))
            with open('.env','w') as envfile:
                envfile.write(changed)
        restart_program()

    if os.getenv("GENERAL_CHANNEL_ID") == None :
        logginginput = input("Input general channel ID ").strip()
        with open(".env", "a") as envfile:
            envfile.write(f"\nGENERAL_CHANNEL_ID={logginginput}")
        restart_program()

    elif os.getenv("GENERAL_CHANNEL_ID") == "" :
        logginginput = int(input("Input general channel ID ")).strip()
        channel = bot.get_channel(logginginput)
        with open(".env", "r") as envfile:
            content1 = envfile.read()
            changed = content1.replace("GENERAL_CHANNEL_ID=", ''.join(["GENERAL_CHANNEL_ID=", str(logginginput)]))
            with open('.env','w') as envfile:
                envfile.write(changed)
        restart_program()


    else:
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


@bot.command()
async def users(ctx,):
    """shows total amount of members"""
    guild = ctx.guild
    members = 0
    for member in guild.members:
        members+=1
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
    embed = discord.Embed(color=0xdfa3ff, description=user.mention)
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
        title=name + "<3",
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
            await channel.set_permissions(mutedRole, speak=False, send_messages=False, read_message_history=True, read_messages=True)

    await member.add_roles(mutedRole, reason=reason)
    await ctx.reply(embed=embed)
    await member.send(f"You were muted for {reason}")

@bot.command()
@commands.has_permissions(kick_members =True)
async def kick(ctx, member : discord.Member, *, reason=None):
    """kicks a user"""
    
    if member == ctx.author:
            await ctx.reply(f"Can't kick yourself idiot")
            return

    elif member.top_role >= ctx.author.top_role:
        await ctx.reply(f"Yo, you can only kick members lower than yourself lmao ")
        return
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
ytdlfunc = run("youtube-dl --version", shell=True, capture_output=True).stdout.decode('ascii')

@bot.command(pass_context=True, aliases=['info', 'debug'])
async def stats(ctx):
    """shows bot stats"""
    bedem = discord.Embed(title = 'System Resource Usage and statistics', description = 'See bot host statistics.', color=discord.Color.blurple()) 
    bedem.add_field(name = "Angel$IX version", value =BotVer, inline = False)
    bedem.add_field(name = 'CPU Usage', value = f'{psutil.cpu_percent()}%', inline = False)
    bedem.add_field(name = 'Total Memory', value = f'{totmem:.0f}MB', inline = False)
    bedem.add_field(name = 'Memory Usage', value = f'{mem:.0f}MB', inline = False)
    bedem.add_field(name = 'CPU name', value = cpuinfo.get_cpu_info()['brand_raw'], inline = False)
    bedem.add_field(name = 'Discord.py Version', value = d_version, inline = False)
    bedem.add_field(name = 'Python Version', value = sys.version, inline = False)
    bedem.add_field(name = 'YTdl Version', value = ytdlfunc.strip(), inline = False)
    await ctx.reply(embed = bedem)

@bot.command()
@commands.has_permissions(ban_members =True)
async def ban(ctx, member : discord.Member, *, reason=None):
    """bans the specified user"""
    
    if member == ctx.author:
        await ctx.reply(f"Can't ban yourself idiot")
        return

    elif  member.top_role >= ctx.author.top_role:
        await ctx.reply(f"You can only ban members lower than yourself")
        return
    
    else:
        await member.ban(reason=reason)
        await member.ban()
        embed = discord.Embed(title="bye lol", description=f"{member.mention} got banned: {reason} ")
        await ctx.channel.send(embed=embed)

@bot.command()
@commands.has_permissions(ban_members =True)   
async def unban(ctx, id: int=0) :
    """unbans a user"""
    if id == 0:
        await ctx.reply("You need to provide an ID to unban!")
        return    

    else:
        user = await bot.fetch_user(id)
        await ctx.guild.unban(user)
        await ctx.reply(f'{user} has been unbanned')
                
@bot.command()
@commands.has_permissions(ban_members =True)
async def wipe(ctx, amount=0):
    """wipes x amount of messages"""
    await ctx.channel.purge(limit=amount)
    await ctx.channel.send(f"Cleanup Complete.")

@bot.command()
@commands.has_permissions(kick_members=True)
async def warn(ctx, member : discord.Member=None, *, reason=None):
    """warns a user"""
    if member == ctx.author:
        await ctx.reply(f"Can't warn yourself idiot")
        return
    elif member == None:
        await ctx.reply("You need to specify who to warn!")
        return
    else:
        if reason == None:
            embed2 =discord.Embed(title="Warned🗡️", description=f"You were warned, now behave.")
            embed =discord.Embed(title="Warned", description=f"{member.mention} was warned")
        else:
            embed2 =discord.Embed(title="Warned🗡️", description=f"You were warned | Reason: {reason}")
            embed =discord.Embed(title="Warned", description=f"{member.mention} was warned | Reason: {reason}")
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
    
@bot.command()
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
        """Removes users role away"""
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
    await bot.add_cog(Music(bot))  # change to whatever you need
    await bot.start(TOKEN)                                 

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())