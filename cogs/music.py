import os
import asyncio
import logging
from itertools import islice
from random import shuffle
from sys import argv

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL, utils

if os.name != "nt":
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logging.warning("Using uvloop")

utils.bug_reports_message = lambda: ""
debugging_opts = {
    "ytdllogging": False,
    "ytdlerringore": False,
    "ytdlquiet": True,
    "log_level": logging.WARN,
    "ffmpeg_ll": "quiet",
}

if "debug" in argv:
    debugging_opts["ytdllogging"] = True
    debugging_opts["ytdlquiet"] = False
    debugging_opts["log_level"] = logging.INFO
    debugging_opts["ffmpeg_ll"] = "info"

logging.basicConfig(
    level=debugging_opts["log_level"],
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.FileHandler("log.txt", mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


class VoiceError(Exception):
    """Exception raised for errors related to voice operations.

    This exception is used to handle errors specifically related to voice operations in the bot.
    Examples include errors during voice connection, voice playback, or voice state management.
    """



class YTDLError(Exception):
    """Exception raised for errors related to YouTube-DL operations.

    This exception is used to handle errors specifically related to YT-DLP operations in the bot.
    Examples include errors during YouTube-DL source creation,
    video extraction, or download processes.
    """



class YTDLSource(discord.FFmpegOpusAudio):
    YTDL_OPTIONS = {
        # Never touch the disk, we only need the json data so simulate is fine
        "verbose": debugging_opts["ytdllogging"],
        "simulate": True,
        "extract_flat": True,
        # There are better formats however using OPUS avoids transcoding
        "format": "bestaudio[ext=opus]/bestaudio",
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": debugging_opts["ytdlerringore"],
        "logtostderr": debugging_opts["ytdllogging"],
        "quiet": debugging_opts["ytdlquiet"],
        "no_warnings": False,
        "default_search": "ytsearch",
        # Since we only process the json there's no need for dash, hls or subs
        # Using "android_creator" seems to be the fastest one while still allowing all formats
        # Since we don't handle downloading we dont need configs, webpage data or JS
        # Comments aren't required, don't processs
        "extractor_args": {
            "youtube": {
                "skip": ["dash", "hls", "translated_subs"],
                "player_client": ["android_creator"],
                "player_skip": ["configs", "webpage", "js"],
                "max_comments": [0],
            }
        },
    }

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 15",
        "options": (
            f"-loglevel {debugging_opts['ffmpeg_ll']} -vn -c:a libopus -ar 48000 -b:a"
            " 512k"
        ),
    }

    ytdl = YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: str, *, data: dict):
        super().__init__(source, **YTDLSource.FFMPEG_OPTIONS)
        self.source = source
        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data
        self.uploader = data.get("uploader")
        # Might delete uploader_url since it None in a lot of cases
        self.uploader_url = data.get("uploader_url")
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        duration = data.get("duration")
        self.duration = self.parse_duration(int(duration)) if duration else "LIVE"
        self.url = data.get("webpage_url")
        self.stream_url = data.get("url")

    def __str__(self):
        return f"**{self.title}** by **{self.uploader}**"

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str):
        """
        Creates a YTDLSource instance from a search query or URL.

        Args:
            cls (class): The class object of the YTDLSource.
            ctx (commands.Context): The context object of the command.
            search (str): The search query or URL to be processed.

        Returns:
            A YTDLSource instance.

        Raises:
            YTDLError: If the search query or URL couldn't be processed.
        """

        search = search.strip().replace("<", "").replace(">", "")
        data = await asyncio.to_thread(cls.ytdl.extract_info, search, False)

        if not data:
            raise YTDLError(f"Couldn't find anything that matches `{search}`")

        entries = data.get("entries")
        info = entries[0] if entries else data

        return cls(ctx, info["url"], data=info)

    @staticmethod
    def parse_duration(duration: int):
        """Converts a duration in seconds to a human-readable string.

        Args:
            duration: The duration of the video in seconds.

        Returns:
            A string representing the duration in the format "Xd Xh Xm Xs",
            where X is the number of days, hours, minutes, and seconds respectively.
        """

        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = hours // 24, hours % 24
        duration_formatted = []
        if days > 0:
            duration_formatted.append(f"{days}d")
        if hours > 0:
            duration_formatted.append(f"{hours}h")
        if minutes > 0:
            duration_formatted.append(f"{minutes}m")
        if seconds > 0:
            duration_formatted.append(f"{seconds}s")
        return " ".join(duration_formatted)


class Song:
    __slots__ = ("source", "requester")

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester

    def create_embed(self):
        """Creates a `discord.Embed` object for the current song.

        Returns:
            A `discord.Embed` object with the title "Now playing", a code-formatted
            description of the song title, and fields for the song duration, the
            user who requested the song, the uploader of the video, the video URL,
            and the video thumbnail. The embed also includes an author field with
            the name and avatar of the user who requested the song.
        """
        embed = discord.Embed(
            title="Now playing",
            description=f"```css\n{self.source.title}\n```",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Duration", value=self.source.duration)
        embed.add_field(name="Requested by", value=self.requester.mention)
        embed.add_field(
            name="Uploader",
            value=f"[{self.source.uploader}]({self.source.uploader_url})",
            inline=True,
        )
        embed.add_field(name="URL", value=f"[Click]({self.source.url})")
        embed.set_thumbnail(url=self.source.thumbnail)
        embed.set_author(name=self.requester.name, icon_url=self.requester.avatar.url)
        return embed


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(islice(self._queue, item.start, item.stop, item.step))
        return self._queue[item]

    def shuffle(self):
        shuffle(self._queue)

    def __len__(self):
        return len(self._queue)

    def clear(self):
        self._queue.clear()

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
        self.skip_votes = set()
        self.audio_player = asyncio.create_task(self.audio_player_task())

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        """Plays audio from the queued songs continuously in the background until stopped.

        Dequeues the next song from the queue,
        creates a playable audio stream from the song's source
        URL using FFmpeg, and starts playing the audio through the voice connection.
        If looping is disabled, sends an embed message to the channel
        indicating that the current song is playing.
        """
        while True:
            self.now = None
            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    # pylint: disable=E1101
                    async with asyncio.timeout(180):  # 3 minutes
                        # NOTICE: this must not be called when looping is enabled
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    await self.stop()
                    self.exists = False
                    return

                await self._ctx.send(embed=self.current.create_embed())

            self.now = discord.FFmpegOpusAudio(
                self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS, bitrate=512
            )
            self.voice.play(self.now, after=self.play_next_song)
            self.next.clear()
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
    """
    A class representing a Discord bot cog focused on music functionality.

    This cog provides various music commands to manage and control playback in a voice channel.
    It includes features such as joining a voice channel, playing songs, managing the queue,
    controlling playback (play, pause, resume, stop), voting to skip songs, and more.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member , before, after):
        """
        Event listener for when a member's voice state changes.

        This method triggers cleanup if the bot itself leaves a voice channel.

        Parameters:
            member (discord.Member): The member whose voice state changed.
            before: The previous voice state of the member.
            after: The updated voice state of the member.
        """
        if before.channel != after.channel and not after.channel and member == self.bot.user:
            voice_state = self.voice_states.get(member.guild.id)

            if voice_state:
                asyncio.create_task(voice_state.stop())
                # TODO: Cheek if cog.unload is needed
                logging.warning("Bot quit, stopping audio player")

    def get_voice_state(self, ctx: commands.Context):
        """
        Get or create the VoiceState associated with a context.

        This method retrieves the VoiceState associated with the given context.
        If a VoiceState does not exist for the context, it creates and associates
        a new VoiceState instance.

        Parameters:
            ctx (commands.Context): The context for which to get the VoiceState.

        Returns:
            VoiceState: The VoiceState associated with the context.

        """
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        """
        Unload method called when the cog is removed.

        This method stops playback for all voice states associated with the cog.

        """
        for state in self.voice_states.values():
            asyncio.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        """
        Check whether the command can be invoked in the current context.

        This method ensures that the command is not invoked in DM channels.

        Parameters:
            ctx (commands.Context): The context of the command.

        Returns:
            bool: True if the command can be invoked, False otherwise.

        Raises:
            commands.NoPrivateMessage: If the command is invoked in a DM channel.

        """
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in DM channels."
            )

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        """
        Method called before a command is invoked.

        This method sets the voice state for the command context.

        Parameters:
            ctx (commands.Context): The context of the command.

        """
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        """
        Handle errors that occur during command execution.

        This method sends an error message to the channel when a command error occurs.

        Parameters:
            ctx (commands.Context): The context of the command.
            error (commands.CommandError): The error that occurred.

        """
        await ctx.reply(f"An error occurred: {error}")

    async def checkloop(self, ctx, stop=False):
        """
        Check and handle loop skipping functionality for a Discord voice channel.

        Args:
            ctx (commands.Context): The context object of the command.
            stop (bool, optional): Whether to stop playback entirely. Defaults to False.
        """

        should_disable_loop = ctx.voice_state.loop
        if should_disable_loop:
            ctx.voice_state.loop = False
        if not stop:
            await ctx.message.add_reaction("⏭")
            ctx.voice_state.skip()
            return
        ctx.voice_state.voice.stop()

    @commands.command(name="join", invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                await ctx.reply(
                    "I'm already connected to a different voice channel"
                    f" ({ctx.voice_client.channel.name})."
                )
                return
        else:
            destination = ctx.author.voice.channel
            ctx.voice_state.voice = await destination.connect()

    @commands.command(name="summon")
    async def _summon(
        self, ctx: commands.Context, *, channel: discord.VoiceChannel = None
    ):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError(
                "You are neither connected to a voice channel nor specified a channel"
                " to join."
            )

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return
        # reconnect=False since we need to handle force disconnect without it trying to reconnect
        ctx.voice_state.voice = await destination.connect(reconnect=False)

    @commands.command(name="leave", aliases=["disconnect", "quit"])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.guild.voice_client and not ctx.voice_state.voice:
            return await ctx.reply("Not connected to any voice channel.")

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name="now", aliases=["current", "playing"])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""
        if not ctx.voice_state.current:
            await ctx.reply("Nothing is playing at the moment")
            return
        embed = ctx.voice_state.current.create_embed()
        await ctx.reply(embed=embed)

    @commands.command(name="toggle", aliases=["tog", "resume", "pause"])
    @commands.has_permissions(manage_guild=True)
    async def _toggle(self, ctx: commands.Context):
        """Toggles between pause and resume for the currently playing song."""

        if not ctx.voice_state.voice:
            await ctx.reply("I am not currently connected to a voice channel.")
            return

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction("⏯")
        elif ctx.voice_state.is_playing:
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction("⏯")
        else:
            await ctx.reply("I am not currently playing anything.")

    @commands.command(name="stop")
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        if ctx.voice_state.is_playing:
            await Music.checkloop(self, ctx, True)

        ctx.voice_state.songs.clear()
        await ctx.message.add_reaction("⏹")

    @commands.command(name="skip", aliases=["s"])
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.reply("Not playing any music right now...")

        voter = ctx.message.author
        if (
            voter == ctx.voice_state.current.requester
            or ctx.author.guild_permissions.manage_messages
        ):
            await ctx.message.add_reaction("⏭")
            # Temporarily disable loop if enabled
            await Music.checkloop(self, ctx)

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction("⏭")
                await Music.checkloop(self, ctx)
            else:
                await ctx.reply(f"Skip vote added, currently at **{total_votes}/3**")
        else:
            await ctx.reply("You have already voted to skip this song.")

    @commands.command(name="queue")
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.reply("Queue is empty!")

        if page < 1:
            return await ctx.reply("Page number cannot be less than 1.")

        items_per_page = 10
        try:
            pages = (len(ctx.voice_state.songs) + items_per_page - 1) // items_per_page
        except TypeError:
            return await ctx.reply("Invalid page number!")

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = []
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue.append(f"`{i+1}.` [**{song.source.title}**]({song.source.url})")
        queue = "\n".join(queue)

        embed = discord.Embed(
            description=f"**{len(ctx.voice_state.songs)} tracks:**\n\n{queue}",
            color=discord.Colour.blurple(),
        )
        embed.set_footer(text=f"Viewing page {page}/{pages}")
        await ctx.reply(embed=embed)

    @commands.command(name="shuffle")
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.reply("Empty queue.")

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction("✅")

    @commands.command(name="remove")
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.reply("Empty queue.")

        if index < 1 or index > len(ctx.voice_state.songs):
            return await ctx.reply("Invalid index.")

        ctx.voice_state.songs.pop(index - 1)
        await ctx.message.add_reaction("✅")

    @commands.command(name="loop")
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.reply("Nothing being played at the moment.")

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction("✅" if ctx.voice_state.loop else "❎")

    @commands.command(name="play", aliases=["p"])
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        
        If there are songs in the queue, this will be queued until 
        the other songs finish playing.
        Automatically searches from various sites if no URL is provided.
        Supported sites list: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
        """

        if not ctx.guild.voice_client:
            await ctx.invoke(self._join)

        try:
            source = await YTDLSource.create_source(ctx, search)
        except YTDLError as err:
            await ctx.reply(f"An error occurred while processing this request: {err}")
            return

        song = Song(source)
        await ctx.voice_state.songs.put(song)
        await ctx.reply(f"Enqueued {source}")

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        """
        Ensures the voice state before invoking the command.

        This function checks if the command invoker is connected to a voice channel
        and if the bot is not already in a voice channel.
        If the conditions are not met, it raises a `commands.CommandError`.

        Parameters:
        - ctx (commands.Context): The context object representing the command invocation.

        Raises:
        - commands.CommandError: If the invoker is not connected to a voice channel
        - commands.CommandError: If the bot is already in a voice channel.
        """
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError("You are not connected to any voice channel.")

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError("Bot is already in a voice channel.")


def setup(bot):
    """Add the Music cog to the bot.

    This function is called by the bot to add the Music cog to its extensions.

    Parameters:
        bot (discord.ext.commands.Bot): The Discord bot instance.
    """
    bot.add_cog(Music(bot))
