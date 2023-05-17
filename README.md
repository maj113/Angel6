# Angel$IX

[![CodeQL](https://github.com/maj113/Angel6/actions/workflows/codeql.yml/badge.svg)](https://github.com/maj113/Angel6/actions/workflows/codeql.yml) 
[![Pylint](https://github.com/maj113/Angel6/actions/workflows/pylint.yml/badge.svg)](https://github.com/maj113/Angel6/actions/workflows/pylint.yml)

Discord bot for my friend's server.

**Mostly usable as of v2.2.2, with ongoing improvements.**

## Bot Functionality

Angel$IX is a versatile Discord bot with the following features:

- Music: Play and manage music in voice channels.
- Fun: Enjoy random cat images, femboy wisdom/tutorial, GIFs, roll dices.
- Moderation: Kick, ban, mute, and warn users.
- Utility: Show bot statistics, display server invites, get information about the server and more.
- Misc: perform various logging functions (**experimental**), check server statistics and show bot's uptime.
- And more!

Please note that this is not an exhaustive list, and the bot may have additional commands or features. For a complete list of commands and detailed usage instructions, refer to the bot's documentation or use the help command in Discord.

## Usage

To set up and run Angel$IX for the first time, follow these steps:

1. Make sure you have **Python 3.11+** and the required dependencies installed.

2. Clone the repository and navigate to the project directory.

3. Rename the `.env_example` file to `.env` and update the necessary values inside it. This file will store your environment variables.

4. Run the `angel6-rewrite.py` script using the following command: `python angel6-rewrite.py` (you may need to launch it with `python3`)

   - The script will perform the first time setup, where you'll be prompted to input various channel IDs.

5. Once the setup is complete, the bot will automatically reboot. You'll see the message "Setup complete, Rebooting" in the console.
    > **Warning**  
    > If the bot goes back to the input logging/join/leave/general channel ID restart the bot manually.  
    > But if the shows `Input channel ID: ` this is okay as it's the channel selector for talking thru the bot

6. The bot is now ready to use. It will log in to Discord and display information about its settings and status.

- The bot version will be displayed.
- The logging channel, join/leave channel, and general channel will be mentioned.
- The API latency will be shown.
- Credits and additional information may also be sent to the logging channel.

You can now interact with the bot using its available commands in Discord.

## TO-DOs:

- Add ytdl playlist support (not heavily requested/used).
- ~~Support py-cord > 2.0.0b4 (fixed in V2.2 [RC1]).~~

## Planned Changes by 2.4.0:

- [x] Fix and optimize first time setup (`.env` file setup).
- [ ] Add logging to the bot:
  - [x] On message delete logging.
  - [ ] On channel create/delete logging.
  - [ ] On user AV change logging.
  - [ ] On adding/removing/changing permission logging.
  - [ ] ...
