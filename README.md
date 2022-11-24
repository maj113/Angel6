# Angel6
Discord bot for my friends server.
**the bot still has issues, its hardcoded for one specific server, ytdl playback is flaky with bad internet, code is a mess.**

# TO-DOs:
-Implement slash commands (wont happen any time soon, bot would need to be completely rewritten). **As the state of Slash commands API is still a mess, buggy and slower i will not be implementing this**

-Add ytdl playlist support (might happen but its not a heavily requested/used feature).

~~-Support py-cord > 2.0.0b4 (currently py-cord 2.0.0b4 is supported but anything newer wont work).~~ This has been fixed in V2.2 [RC1]

-Make it more universal (currently the bot has hardcoded channel IDs, server name, shouldnt be to hard to implement but since no one else uses it im not gonna fix it *yet*). **This is getting worked on, should be mostly done till 2023**

~~-Fix \~invites command, it shows invites correctly only if used by the message author, if specifying a message.mention it just returns null~~ (*mostly*) Fixed in V2.2 [RC1]

# Planned Changes by 2.2.2:
-Improve Ytdl sound quality - *some changes for better quality are present in RC1*

-Improve FFMPEG postprocessing and fixing re-encoding

-~~Support for Python 3.11 - most likely not worth it, would probably need a complete rewrite CBA~~ Done, no rewrite needed, **Needs py-cord >= 2.3**

-Fix and optimize first time setup AKA .env file setup

-Add some sort of logging to the bot. currently it just displays Ascii art, configured channels and API latency

-Better (Mobile friendly Ascii art) *We may just use a custom banner/GIF*
