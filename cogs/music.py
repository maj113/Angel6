import asyncio
import logging
from itertools import islice
from random import shuffle
from sys import argv

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL, utils

utils.bug_reports_message = lambda: ""
DebuggingOpts = {
    "ytdllogging": False,
    "ytdlerringore": False,
    "ytdlquiet": True,
    "LogLevel": logging.INFO,
}
if argv[-1] == "debug" or argv[-1] == "d":
    DebuggingOpts["ytdllogging"] = True
    DebuggingOpts["ytdlquiet"] = False
    DebuggingOpts["LogLevel"] = logging.DEBUG

logging.basicConfig(
    level=DebuggingOpts["LogLevel"],
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
    pass


class YTDLError(Exception):
    """Exception raised for errors related to YouTube-DL operations.

    This exception is used to handle errors specifically related to YouTube-DL operations in the bot.
    Examples include errors during YouTube-DL source creation, 
    video extraction, or download processes.
    """
    pass


class YTDLSource(discord.FFmpegOpusAudio):
    YTDL_OPTIONS = {
        "extractaudio": True,
        "format": "bestaudio[ext=opus]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
        "restrictfilenames": True,
        "noplaylist": True,
        "ssl_verify": False,
        "ignoreerrors": DebuggingOpts["ytdlerringore"],
        "logtostderr": DebuggingOpts["ytdllogging"],
        "quiet": DebuggingOpts["ytdlquiet"],
        "no_warnings": True,
        "default_search": "ytsearch",
    }

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 15",
        "options": "-loglevel quiet -vn -c:a libopus -ar 48000 -b:a 512k",
    }

    ytdl = YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: str, *, data: dict):
        super().__init__(source, pipe=True)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data
        self.uploader = data.get("uploader")
        self.uploader_url = data.get("uploader_url")
        date = data.get("upload_date")
        self.upload_date = date[6:8] + "." + date[4:6] + "." + date[0:4]
        self.title = data.get("title")
        self.thumbnail = data.get("thumbnail")
        self.description = data.get("description")
        duration = data.get("duration")
        self.duration = (
            self.parse_duration(int(duration)) if duration else "LIVE"
        )
        self.tags = data.get("tags")
        self.url = data.get("webpage_url")
        self.views = data.get("view_count")
        self.likes = data.get("like_count")
        self.stream_url = data.get("url")

    def __str__(self):
        return f"**{self.title}** by **{self.uploader}**"

    @classmethod
    async def create_source(
        cls,
        ctx: commands.Context,
        search: str,
    ):
        """
        Creates a YTDLSource instance from a search query or URL.

        Args:
            cls (class): The class object of the YTDLSource.
            ctx (commands.Context): The context object of the command.
            search (str): The search query or URL to be processed.
            loop (asyncio.AbstractEventLoop): The event loop to be used for async operations. 
            Defaults to None.

        Returns:
            A YTDLSource instance.

        Raises:
            YTDLError: If the search query or URL couldn't be processed.
        """

        search = search.strip().replace("<", "").replace(">", "")
        data = await asyncio.to_thread(cls.ytdl.extract_info, search, False, False)
        if data is None:
            raise YTDLError(f"Couldn't find anything that matches `{search}`")

        entries = data.get("entries")
        process_info = entries[0] if entries else data
        webpage_url = process_info["webpage_url"]
        processed_info = await asyncio.to_thread(
            cls.ytdl.extract_info, webpage_url, False
        )  # FIXME: slowdowns here... should improve till release 2.5
        if processed_info is None:
            raise YTDLError(f"Couldn't fetch `{webpage_url}`")

        entries = processed_info.get("entries")
        info = entries[0] if entries else processed_info
        return cls(
            ctx,
            discord.FFmpegOpusAudio(info["url"], **YTDLSource.FFMPEG_OPTIONS),
            data=info,
        )

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

    def __del__(self):
        self.audio_player.cancel()

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
            self.next.clear()  # FIXME: significant performance slowdowns here
            self.now = None
            if not self.loop:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with asyncio.timeout(180):  # 3 minutes
                        self.current = (
                            await self.songs.get()
                        )  # NOTICE: this must not be called when looping is enabled
                except asyncio.TimeoutError:
                    asyncio.create_task(self.stop())
                    self.exists = False
                    return

                self.now = await discord.FFmpegOpusAudio.from_probe(
                    self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS
                )
                self.voice.play(self.now, after=self.play_next_song)
                await self.current.source.channel.send(
                    embed=self.current.create_embed()
                )
            # Fix code duplication
            # If the song is looped
            elif self.loop:
                self.now = await discord.FFmpegOpusAudio.from_probe(
                    self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS
                )
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
            asyncio.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage(
                "This command can't be used in DM channels."
            )

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
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

        destination = ctx.author.voice.channel
        if ctx.voice_state.voice:
            await destination.connect(reconnect=False)
            return
        if ctx.voice_client and ctx.voice_client.channel != destination:
            await ctx.reply(
                "I'm already connected to a voice channel"
                f" ({ctx.voice_client.channel.name})."
            )
            return
        ctx.voice_state.voice = await destination.connect(reconnect=False)

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
        if ctx.voice_state.current is None:
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
            await Music.checkloop(self, ctx, False, True)

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
            # Check if loop is enabled and temporarily disable it to allow the skip command to work
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
        if ctx.voice_state.loop is True:
            await ctx.message.add_reaction("✅")
        else:
            await ctx.message.add_reaction("❎")  # when looping disabled

    @commands.command(name="play", aliases=["p"])
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: 
        https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md
        """
        try:
            source_task = asyncio.create_task(
                YTDLSource.create_source(ctx, search)
            )
        except YTDLError as err:
            await ctx.reply(f"An error occurred while processing this request: {err}")
        else:
            if ctx.voice_state.voice and not ctx.guild.voice_client:
                #  okay so comment time; this is how the bot will be set when its force disconnected (e.g. from discord) which leaves voice_state.voice in an unclean state
                #  that not only messes with the fact that the bot still thinks it's connected, but also the playback is still in progress
                #  we have to make sure playback is stopped and set voice_state.voice to None which should in theory fix the problem
                await ctx.invoke(self._stop)
                ctx.voice_state.voice = None
                logging.warning(
                    "experimental support for unclean voice_state.voice handling, might"
                    " be unstable"
                )

            if not ctx.guild.voice_client:
                await ctx.invoke(self._join)
            await asyncio.gather(source_task)
            source = source_task.result()
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
    bot.add_cog(Music(bot))
