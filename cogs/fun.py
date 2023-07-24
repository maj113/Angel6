from random import randint
from os import path
import json
from requests import get, Timeout

import discord
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["IQ", "iq"])
    async def smart(self, ctx):
        """Average server IQ"""
        embed = discord.Embed(
            title=f"Average {ctx.guild.name} IQ",
            description=f"{randint(-10 , 130 )}",
            color=discord.Color.blurple(),
        )
        await ctx.reply(embed=embed)

    @commands.command("roll")
    async def roll(self, ctx, args: str = ""):
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
                dice_to_roll, number_of_sides = self.parse_input(args)
            else:
                dice_to_roll = 1
                number_of_sides = 6
        except ValueError:
            await ctx.reply(
                f"I didn't understand your input: `{args}`.\nTry `~roll help` for"
                " supported options."
            )
            return

        max_dice_size = 150
        max_sides = 100000000
        if not 0 <= dice_to_roll <= max_dice_size:
            embed = discord.Embed(
                title="Error",
                description=(
                    "Invalid dice amount. Dice amount must be between 0 and"
                    f" {max_dice_size}."
                ),
                color=discord.Color.brand_red(),
            )
            await ctx.reply(embed=embed)
            return

        if not 0 <= number_of_sides <= max_sides:
            embed = discord.Embed(
                title="Error",
                description=(
                    "Invalid number of sides. The number of sides must be between 0 and"
                    f" {max_sides}."
                ),
                color=discord.Color.brand_red(),
            )
            await ctx.reply(embed=embed)
            return

        results = []

        for _ in range(dice_to_roll):
            results.append(self.roll_a_dice(number_of_sides))

        result_string = ", ".join([f"`{result}`" for result in results])

        embed = discord.Embed(
            title=f"{ctx.author.name} rolled {dice_to_roll}d{number_of_sides}!",
            description=result_string,
            color=discord.Color.blurple(),
        )

        await ctx.reply(embed=embed)

    def parse_input(self, parsed_input: str):
        """
        Parse the input to extract the number of dice to roll and the number of sides on each dice.

        Args:
            parsed_input (str): The input to parse. It should be in the format 'NdM', where N is the
                                number of dice and M is the number of sides on each dice.

        Returns:
            tuple: A tuple containing the number of dice to roll and the number of sides on each dice.
        """
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

    def roll_a_dice(self, sides: int):
        """
        Roll a dice with the specified number of sides.

        Args:
            sides (int): The number of sides on the dice.

        Returns:
            int: The result of the dice roll, a random number between 1 and the number of sides.
        """
        return randint(1, sides)

    @commands.command(pass_context=True, aliases=["fem"])  # :skull:
    async def femboy(self, ctx):
        """Femboy Wisdom/Tutorial"""
        embed = discord.Embed(
            title="Chakal's Wisdom On Femboys",
            description=(
                "How can you be a feminine looking boy? Simple. \nGrow your hair out,"
                " exercise regularly (I run/jog to remain slim, and I do squats/tap"
                " dance to exercise my thighs/butt), trim your facial hair, do whatever"
                " you can to help out your skin, and consider taking HRT.\n Learn how"
                " to do makeup, it is a fucking amazing tool. Experiment with different"
                " outfits, my favorite for andro people is just leggings beneath"
                " feminine jean shorts, it is common for females in the UK and looks"
                " feminine, but not so feminine that it will look weird in"
                " public.\nConsider taking speech therapy, or just watching some videos"
                " and working at getting a more feminine voice.\nAt the end of the day,"
                " though, you can practically look like a girl, with the most luscious"
                " hair, smallest eyebrows, red lips, and longest lashes; you can have"
                " the perfect body type, be an hourglass with a big ass, thick"
                " thighs/hips and a skinny waist; you can sound like the girliest woman"
                " in the world; you can wear booty shorts and a half shirt and look"
                " damn good in it; you can be a master at feminine makeup.\nBut it all"
                " means nothing if you fail to act feminine. For looks catch the eye,"
                " but personality catches the heart.\nThere comes a point when you must"
                " ask yourself if you want to be a femboy, or simply be a feminine"
                " looking man.\nSo, how can you be a femboy?\nAct feminine. Femboys are"
                " made, not born.  -Chakal"
            ),
            color=discord.Color.blurple(),
        )
        embed2 = discord.Embed(
            title="Miro's Wisdom On Femboys",
            description=(
                "Hey, some guys like being cute and pastel, trans guys included, and"
                " some transgender people don't really feel the need to change their"
                " bodies either. So that's an option. Maybe you're a really feminine"
                " guy who's fine with having a female body.\n Or, maybe you just really"
                " like the femboy aesthetic. Or maybe you're attracted to femboys. Idk,"
                " I'm not you. It's gonna take a little experimentation to find out.\n"
                " 1) Get some clothes you feel comfortable in. Try out that femboy"
                " look. Do you feel cute? Does it feel right? Whether you are cis or"
                " trans, you should be able to wear clothes that make you feel good"
                " about yourself. So do that. Whatever the answers are to the other"
                " questions, this will almost certainly make you feel a little"
                " better.\n 2) Do some googling. Learn about fem trans boys, demiboys,"
                " and non-binary people. Read some things from their perspectives. Does"
                " any of it resonate with you?\n3) Try some things. It's normal for us"
                " to question our identities and grow and change through the years, and"
                " it's normal to not fully understand yourself right away. If you think"
                " you might be trans, maybe try a different name or pronouns. if you"
                " don't have supportive people around willing to help you experiment,"
                " then you can introduce yourself the way you want online, with"
                " strangers you'll never have to interact with again. It takes a lot of"
                " the pressure off, too, if you're nervous. Maybe it'll feel right and"
                " you'll know. Maybe it'll feel wrong and you'll realize you're a girl."
                " Maybe you'll still be confused and have to try some new things. Have"
                " patience, it can take time.\n4) Own it. Whatever your identity is,"
                " dress the way you like and be who you are and if anyone gives you"
                " shit about it, just show them how high you can kick their balls up"
                " their ass in your adorable little pink skirt.  -Miro"
            ),
            color=discord.Color.blurple(),
        )
        await ctx.reply(embed=embed)
        await ctx.send(embed=embed2)

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def taglist(self, ctx, action=None, name=None, content=None):
        """Add, remove, edit, or peek at tags in the tags dictionary

        Parameters:
        - action (str): The action to perform on the tags. Possible values are: "add", "remove", "edit", "peek".
        - name (str): The name of the tag.
        - content (str): The content of the tag (used in add and edit actions).
        """
        if not path.exists("taglist.json"):
            with open("taglist.json", "w", encoding="utf-8") as file:
                json.dump({}, file)

        with open("taglist.json", "r", encoding="utf-8") as file:
            tags = json.load(file)

        embed = discord.Embed()
        color = discord.Color.blurple()

        if action == "add":
            if not name or not content:
                await ctx.send("Please provide both the name and content for the tag.")
                return

            if name in tags:
                embed.description = (
                    f"A tag with the name `{name}` already exists. Editing its content"
                    " instead."
                )
                color = discord.Color.yellow()
            else:
                embed.description = f"Added tag `{name}` with content: `{content}`"
                color = discord.Color.brand_green()
            tags[name] = content

        elif action == "remove":
            if not name:
                await ctx.send("Please provide the name of the tag to remove.")
                return

            if name in tags:
                del tags[name]
                embed.description = f"Removed tag `{name}`."
                color = discord.Color.brand_red()
            else:
                embed.description = f"Could not find a tag with the name `{name}`."

        elif action == "edit":
            if not name or not content:
                await ctx.send(
                    "Please provide both the name and content for the tag to edit."
                )
                return

            if name in tags:
                embed.description = f"Edited tag `{name}` with new content: `{content}`"
            else:
                embed.description = f"Could not find a tag with the name `{name}`."
            tags[name] = content

        elif action == "peek":
            if not name:
                await ctx.send("Please provide the name of the tag to peek at.")
                return

            if name in tags:
                embed.title = f"Content of tag `{name}`:"
                embed.description = f"`{tags[name]}`"
                color = discord.Color.blurple()
            else:
                embed.description = f"Could not find a tag with the name `{name}`."

        elif not action:
            if not tags:  # Check if there are no tags in the dictionary
                embed.title = "Taglist is empty."
                embed.description = "There are no tags available."
                embed.color = discord.Color.yellow()
                await ctx.send(embed=embed)
                return

            embed.title = "Available tags:"
            for tag_name in tags:
                command = f'`~tagsend "{tag_name}"`'
                embed.add_field(name=tag_name, value=f"{command}", inline=False)

        else:
            await ctx.send(
                "Invalid action. Please use 'add', 'remove', 'edit', or 'peek'."
            )
            return

        embed.color = color

        with open("taglist.json", "w", encoding='utf-8') as file:
            json.dump(tags, file, indent=4)

        await ctx.send(embed=embed)

    @commands.command(pass_context=True, aliases=["tag"])
    async def tagsend(self, ctx, tag_name=""):
        """Sends content that's in the tag list"""
        with open("taglist.json", "r", encoding='utf-8') as file:
            tags = json.load(file)

        tag_name = tag_name.lower()
        if tag_name == "list" or not tag_name:
            await self.taglist(ctx)
            return

        if tag_name in tags:
            await ctx.message.delete()
            await ctx.send(discord.utils.escape_mentions(tags[tag_name]))
        else:
            tag_name = discord.utils.escape_mentions(tag_name)
            embed = discord.Embed(
                description=(
                    f"Invalid tag `{tag_name}`. Use `~taglist` to see available"
                    " options."
                ),
                color=discord.Color.brand_red(),
            )
            await ctx.reply(embed=embed)

    @commands.command(pass_context=True)
    async def img(self, ctx, img_type="cat"):
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
                caturl = get(
                    "https://api.nekosapi.com/v2/images/random?filter[ageRating]=sfw",
                    timeout=3,
                )
                catimg = caturl.json()["data"]["attributes"]["file"]
            else:
                error_embed = discord.Embed(
                    title="Error:",
                    description=(
                        "Invalid argument. Supported image APIs are: 'cat', 'anime'"
                    ),
                    color=discord.Color.brand_red(),
                )
                await ctx.reply(embed=error_embed)
                return

            embed = discord.Embed(color=discord.Color.blurple())
            embed.set_image(url=catimg)
            await ctx.reply(embed=embed)

        except Timeout as err:
            error_embed = discord.Embed(
                title="Error:",
                description=(
                    f"Failed to fetch image. Please try again later.\nError: {err}"
                ),
                color=discord.Color.brand_red(),
            )
            await ctx.reply(embed=error_embed)


def setup(bot):
    """Add the Fun cog to the bot.

    This function is called by the bot to add the Fun cog to its extensions.

    Parameters:
        bot (discord.ext.commands.Bot): The Discord bot instance.
    """
    bot.add_cog(Fun(bot))
