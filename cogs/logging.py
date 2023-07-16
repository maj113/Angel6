import discord
from discord.ext import commands
from angel6 import LOG_CHAN_ID, JL_CHAN_ID, GEN_CHAN_ID


class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        Handles errors that occur during command execution.

        Parameters:
        - ctx (commands.Context): The context of the command.
        - error (Exception): The error that occurred.

        """
        if isinstance(self, error, commands.MissingPermissions):
            # Handle MissingPermissions error
            embed = discord.Embed(
                title="Permission Error",
                description=(
                    "You don't have the required permissions to execute this command."
                ),
                color=discord.Color.brand_red(),
            )
            await ctx.reply(embed=embed)
        elif isinstance(error, commands.CommandNotFound):
            # Handle CommandNotFound error
            embed = discord.Embed(
                title="Command Not Found",
                description="The command you entered does not exist.",
                color=discord.Color.brand_red(),
            )
            await ctx.reply(embed=embed)
        else:
            # Handle other errors
            embed = discord.Embed(
                title="An error occurred: ",
                description=f"`{error}`",
                color=discord.Color.brand_red(),
            )
            channel = self.bot.get_channel(int(LOG_CHAN_ID))
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Event handler for when a member joins a guild.

        Sends a welcome message to the designated join/leave channel, the total number of members,
        the member's avatar, and the guild's name and icon.
        If a general channel is specified, sends a DM to the member with an invite to that channel.
        Otherwise, sends a default welcome message as a DM to the member.

        Parameters:
        - member: The member who joined the guild.
        """
        channel = self.bot.get_channel(int(JL_CHAN_ID))
        embed = discord.Embed(
            colour=discord.Colour.blurple(),
            description=(
                f"{member.mention} joined, Total Members:"
                f" {len(list(member.guild.members))}"
            ),
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text=member.guild, icon_url=member.guild.icon.url or None)
        await channel.send(embed=embed)

        description = (
            f"yo! I'm Mutiny's Personal Bot, proceed to <#{int(GEN_CHAN_ID)}> to talk:)"
        )

        mbed = discord.Embed(
            colour=discord.Colour.blurple(),
            title="Glad you could find us!",
            description=description,
        )
        await member.send(embed=mbed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """
        Event handler for when a member leaves a guild.

        Sends a farewell message to the designated join/leave channel,
        the updated total number of members, the member's avatar, and the guild's name and icon.

        Parameters:
        - member: The member who left the guild.
        """
        channel = self.bot.get_channel(int(JL_CHAN_ID))
        embed = discord.Embed(
            colour=discord.Colour.blurple(),
            description=(
                f"{member.mention} Left us, Total Members: {len(member.guild.members)}"
            ),
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(
            text=member.guild,
            icon_url=member.guild.icon.url if member.guild.icon else None,
        )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
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

        if message.author.id == self.bot.user.id:
            return

        channel = self.bot.get_channel(int(LOG_CHAN_ID))
        if not channel:
            # LOG_CHAN_ID is not valid or channel is not available
            return

        deleted.add_field(name="Message", value=message.content or "*No content*")
        deleted.timestamp = message.created_at
        await channel.send(embed=deleted)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """
        Event handler for when a message is edited.

        Parameters:
        - before: The message object before the edit.
        - after: The message object after the edit.
        """
        if before.author.id == self.bot.user.id:
            return

        logging_channel = self.bot.get_channel(int(LOG_CHAN_ID))
        if logging_channel and before.content != after.content:
            embed = discord.Embed(
                title=f"Message edited in {before.channel.mention}",
                description=(
                    f"Message edited\n `{before.content}` -> `{after.content}` "
                ),
                color=discord.Color.blurple(),
            )
            embed.add_field(
                name="Message:", value=f"[Link]({after.jump_url})", inline=False
            )
            embed.set_author(
                name=before.author.display_name, icon_url=before.author.avatar.url
            )
            await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """
        Event handler for when a channel is created in a guild.

        Sends a notification to the designated logging channel,
        including details about the created channel.

        Parameters:
        - channel: The created channel object.
        """
        logging_channel = self.bot.get_channel(int(LOG_CHAN_ID))
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
                embed.add_field(
                    name="Type", value=str(channel.type).title(), inline=True
                )
                embed.add_field(
                    name="Category",
                    value=channel.category.name or "None",
                    inline=True,
                )
                embed.set_footer(
                    text=f"ID: {channel.id} • Created by {entry.user}",
                    icon_url=entry.user.avatar.url or None,
                )
                await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """
        Event handler for when a guild channel is deleted.
        Sends a log message to the logging channel.

        Parameters:
        - channel (discord.abc.GuildChannel): The deleted guild channel.

        Note:
        - Requires a valid logging channel ID in LOG_CHAN_ID constant.
        """

        logging_channel = self.bot.get_channel(int(LOG_CHAN_ID))

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
                    value=channel.category.name or "None",
                    inline=True,
                )
                embed.set_footer(
                    text=f"ID: {channel.id} • Deleted by {entry.user}",
                    icon_url=entry.user.avatar.url or None,
                )
                await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """
        Event handler for when a user updates their profile (including avatar).
        Sends a log message to the logging channel if the avatar is changed.

        Parameters:
        - before (discord.User): The user before the update.
        - after (discord.User): The user after the update.

        Note:
        - Requires a valid logging channel ID in LOG_CHAN_ID constant.
        """

        if before.avatar != after.avatar:
            logging_channel = self.bot.get_channel(int(LOG_CHAN_ID))
            if logging_channel:
                embed = discord.Embed(
                    title="User avatar changed", color=discord.Colour.blurple()
                )
                embed.set_author(name=before.name, icon_url=before.avatar.url)
                embed.set_thumbnail(url=after.avatar.url)
                embed.set_footer(text=f"ID: {after.id}")
                await logging_channel.send(embed=embed)
        # Needs pycord 2.4.1.dev138 or newer otherwise it can't handle the new username system
        if before.display_name != after.display_name:
            logging_channel = self.bot.get_channel(int(LOG_CHAN_ID))
            if logging_channel:
                embed = discord.Embed(
                    title="User display name changed", color=discord.Colour.blurple()
                )
                embed.set_author(name=before.name, icon_url=after.avatar.url)
                embed.description = f"`{before.display_name}` -> `{after.display_name}`"
                embed.set_footer(text=f"ID: {after.id}")
                await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """
        Event handler for when a member's information is updated.

        Parameters:
        - before: The member object before the update.
        - after: The member object after the update.
        """

        # Check if the nickname has changed
        if before.nick != after.nick:
            logging_channel = self.bot.get_channel(int(LOG_CHAN_ID))
            if logging_channel:
                embed = discord.Embed(
                    title="Member nickname changed",
                    description=f"`{before.nick}` -> `{after.nick}`",
                    color=discord.Color.blurple(),
                )
                embed.set_author(name=before.display_name, icon_url=before.avatar.url)
                embed.set_footer(text=f"ID: {after.id}")
                await logging_channel.send(embed=embed)

        # Check if the roles have changed
        if before.roles != after.roles:
            added_roles = [
                role.name for role in after.roles if role not in before.roles
            ]
            removed_roles = [
                role.name for role in before.roles if role not in after.roles
            ]

            logging_channel = self.bot.get_channel(int(LOG_CHAN_ID))
            if logging_channel:
                for role in added_roles:
                    embed = discord.Embed(
                        title="Role Added",
                        description=f"Added role: `{role}`",
                        color=discord.Color.green(),
                    )
                    embed.set_author(name=after.display_name, icon_url=after.avatar.url)
                    embed.set_footer(text=f"ID: {after.id}")
                    await logging_channel.send(embed=embed)

                for role in removed_roles:
                    embed = discord.Embed(
                        title="Role Removed",
                        description=f"Removed role: `{role}`",
                        color=discord.Color.red(),
                    )
                    embed.set_author(name=after.display_name, icon_url=after.avatar.url)
                    embed.set_footer(text=f"ID: {after.id}")
                    await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """
        Logs channel updates when a guild channel is modified.

        Parameters:
        - before (discord.abc.GuildChannel): The channel before the update.
        - after (discord.abc.GuildChannel): The channel after the update.
        """

        log_channel = self.bot.get_channel(int(LOG_CHAN_ID))

        async for entry in before.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.channel_update
        ):
            if entry.target.id == before.id:
                author = entry.user

                # Check if the channel names are the same
                if before.name == after.name and before.category == after.category:
                    return

                embed = discord.Embed(
                    title="Channel Update", color=discord.Color.blurple()
                )
                embed.add_field(name="Channel", value=before.mention, inline=False)

                # Compare channel attributes and add changed fields to the embed
                if before.name != after.name:
                    embed.add_field(
                        name="Name",
                        value=f"`{before.name}` -> `{after.name}`",
                        inline=False,
                    )
                # Does type ever change?
                if before.type != after.type:
                    embed.add_field(
                        name="Type",
                        value=f"`{before.type}` -> `{after.type}`",
                        inline=False,
                    )
                if before.category != after.category:
                    before_category = before.category.name or "None"
                    after_category = after.category.name or "None"
                    embed.add_field(
                        name="Category",
                        value=f"`{before_category}` -> `{after_category}`",
                        inline=False,
                    )
                embed.set_footer(
                    text=f"Updated by: {author}", icon_url=author.avatar.url
                )

                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """
        Event handler for when a member is banned from the guild.

        Parameters:
        - guild: The guild the member was banned from.
        - user: The user who was banned.
        """

        logging_channel = self.bot.get_channel(int(LOG_CHAN_ID))
        if logging_channel:
            ban_entry = await guild.audit_logs(
                limit=1, action=discord.AuditLogAction.ban
            ).flatten()
            ban_author = ban_entry[0].user

            embed = discord.Embed(
                title="Member Banned",
                description=f"User: {user.mention}",
                color=discord.Color.red(),
            )
            embed.add_field(name="Banned by", value=ban_author.name, inline=False)
            embed.set_footer(text=f"ID: {user.id}")

            await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        """
        Event handler for when a member is unbanned from the guild.

        Parameters:
        - guild: The guild the member was unbanned from.
        - user: The user who was unbanned.
        """
        logging_channel = self.bot.get_channel(int(LOG_CHAN_ID))
        if logging_channel:
            unban_entry = await guild.audit_logs(
                limit=1, action=discord.AuditLogAction.unban
            ).flatten()
            unban_author = unban_entry[0].user

            embed = discord.Embed(
                title="Member Unbanned",
                description=f"User: {user.mention}",
                color=discord.Color.green(),
            )
            embed.add_field(name="Unbanned by", value=unban_author.name, inline=False)
            embed.set_footer(text=f"ID: {user.id}")

            await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """
        Triggered when a role is updated in a guild.

        Parameters:
            before (discord.Role): The role object representing the role before the update.
            after (discord.Role): The role object representing the role after the update.
        """
        log_channel = self.bot.get_channel(int(LOG_CHAN_ID))

        embed = discord.Embed(
            title=f"Role Updated: `{after.name}`", color=discord.Color.yellow()
        )

        if before.name != after.name:
            embed.add_field(
                name="Name changed",
                value=f"{before.name} -> {after.name}",
                inline=False,
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

    @commands.Cog.listener()
    async def on_guild_role_create(self, created_role):
        """
        Event handler for when a role is created in a guild.

        Args:
            role (discord.Role): The role that was created.

        This event sends a log message to the designated log channel
        when a new role is created in the guild. It fetches the audit
        log entries for role creation and includes the creator's information
        in the log message.
        """
        log_channel = self.bot.get_channel(int(LOG_CHAN_ID))

        # Fetch the audit log entries for role creation
        async for entry in created_role.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.role_create
        ):
            creator = entry.user

            embed = discord.Embed(
                title=f"Role Created: `{created_role.name}`",
                description=f"New role created with ID: {created_role.id}",
                color=discord.Color.brand_green(),
            )
            embed.set_footer(text=f"Created by: {creator}")

            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, deleted_role):
        """
        Event handler for when a role is deleted in a guild.

        Args:
            role (discord.Role): The role that was deleted.

        This event sends a log message to the designated log channel
        when a role is deleted in the guild. It fetches the audit log
        entries for role deletion and includes the deleter's information
        in the log message.
        """
        log_channel = self.bot.get_channel(int(LOG_CHAN_ID))

        # Fetch the audit log entries for role deletion
        async for entry in deleted_role.guild.audit_logs(
            limit=1, action=discord.AuditLogAction.role_delete
        ):
            deleter = entry.user

            embed = discord.Embed(
                title=f"Role Deleted: `{deleted_role.name}`",
                description=f"Role ID: {deleted_role.id}",
                color=discord.Color.brand_red(),
            )
            embed.set_footer(text=f"Deleted by: {deleter}")

            await log_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Logging(bot))
