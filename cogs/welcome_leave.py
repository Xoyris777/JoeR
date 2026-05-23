"""
Welcome / Leave message cog.

Provides:
  Commands (slash + prefix via hybrid):
    .welcome-channel-set  #channel  - set where welcome embeds are posted
    .welcome-message-set  "message" - set custom welcome message (use {member} / {server})
    .leave-channel-set    #channel  - set where leave embeds are posted
    .leave-message-set    "message" - set custom leave message (use {member} / {server})

  Events:
    on_member_join          - sends welcome embed
    on_member_remove        - sends leave / goodbye embed
"""

import logging
log = logging.getLogger(__name__)

import discord
from discord.ext import commands
from utils.storage import config_manager

# ── Default text used when no custom message has been set ────────────
DEFAULT_WELCOME = "Welcome to **{server}**, {member}! You are member #{count}."
DEFAULT_LEAVE   = "**{member}** has left **{server}**. We now have {count} members."


# ── Cog ─────────────────────────────────────────────────────────────
class WelcomeLeave(commands.Cog):
    """Handles server join / leave messages."""

    def __init__(self, bot):
        self.bot = bot

    # ── Commands ───────────────────────────────────────────────────

    @commands.hybrid_command(name="welcome-channel-set",
                             description="Set the channel where welcome messages are sent")
    @discord.app_commands.describe(channel="The text channel for welcome messages")
    async def welcome_channel_set(self, ctx, channel: discord.TextChannel):
        """Set the welcome message channel for this server."""
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.", ephemeral=True)
            return
        if not ctx.author.guild_permissions.manage_guild and ctx.author.id != getattr(ctx.bot, "owner_id", None):
            await ctx.send("You need **Manage Server** permission to use this command.", ephemeral=True)
            return
        config_manager.set_welcome_channel(ctx.guild.id, str(channel.id))
        await ctx.send(f"✅ Welcome channel set to {channel.mention}.", ephemeral=True)

    @commands.hybrid_command(name="welcome-message-set",
                             description="Set a custom welcome message")
    @discord.app_commands.describe(message="Custom message. Use {member} , {server} , {count}")
    async def welcome_message_set(self, ctx, *, message: str):
        """Set a custom welcome message for this server."""
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.", ephemeral=True)
            return
        if not ctx.author.guild_permissions.manage_guild and ctx.author.id != getattr(ctx.bot, "owner_id", None):
            await ctx.send("You need **Manage Server** permission to use this command.", ephemeral=True)
            return
        config_manager.set_welcome_message(ctx.guild.id, message)
        await ctx.send("✅ Custom welcome message saved.", ephemeral=True)

    @commands.hybrid_command(name="leave-channel-set",
                             description="Set the channel where leave messages are sent")
    @discord.app_commands.describe(channel="The text channel for leave messages")
    async def leave_channel_set(self, ctx, channel: discord.TextChannel):
        """Set the leave message channel for this server."""
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.", ephemeral=True)
            return
        if not ctx.author.guild_permissions.manage_guild and ctx.author.id != getattr(ctx.bot, "owner_id", None):
            await ctx.send("You need **Manage Server** permission to use this command.", ephemeral=True)
            return
        config_manager.set_leave_channel(ctx.guild.id, str(channel.id))
        await ctx.send(f"✅ Leave channel set to {channel.mention}.", ephemeral=True)

    @commands.hybrid_command(name="leave-message-set",
                             description="Set a custom leave/goodbye message")
    @discord.app_commands.describe(message="Custom message. Use {member} , {server} , {count}")
    async def leave_message_set(self, ctx, *, message: str):
        """Set a custom leave message for this server."""
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.", ephemeral=True)
            return
        if not ctx.author.guild_permissions.manage_guild and ctx.author.id != getattr(ctx.bot, "owner_id", None):
            await ctx.send("You need **Manage Server** permission to use this command.", ephemeral=True)
            return
        config_manager.set_leave_message(ctx.guild.id, message)
        await ctx.send("✅ Custom leave message saved.", ephemeral=True)

    # ── Events ─────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Send a welcome embed when a new member joins."""
        try:
            if member.bot:
                return  # ignore bot joins

            guild = member.guild
            channel_id = config_manager.get_welcome_channel(guild.id)
            if not channel_id:
                return
            channel = guild.get_channel(int(channel_id))
            if not isinstance(channel, discord.TextChannel):
                return
            if not channel.permissions_for(guild.me).send_messages:
                log.warning("Missing Send Messages permission in welcome channel %s (%s)", channel.name, channel.id)
                return

            custom_msg = config_manager.get_welcome_message(guild.id) or DEFAULT_WELCOME

            try:
                description = custom_msg.format(
                    member=member.mention,
                    server=guild.name,
                    count=guild.member_count or len(guild.members),
                )
            except (KeyError, IndexError):
                description = DEFAULT_WELCOME.format(member=member.mention, server=guild.name, count=guild.member_count or len(guild.members))

            embed = discord.Embed(
                title="👋 Welcome to the Server!",
                description=description,
                color=0x5865F2,
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member #{guild.member_count or len(guild.members)}")

            await channel.send(embed=embed)
            log.info("Sent welcome embed for %s in guild %s", member.id, guild.id)

        except Exception as exc:
            log.error("Error in on_member_join for guild %s: %s", getattr(member, "guild", None), exc, exc_info=True)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Send a goodbye embed when a member leaves."""
        try:
            if member.bot:
                return

            guild = member.guild
            channel_id = config_manager.get_leave_channel(guild.id)
            if not channel_id:
                return
            channel = guild.get_channel(int(channel_id))
            if not isinstance(channel, discord.TextChannel):
                return
            if not channel.permissions_for(guild.me).send_messages:
                log.warning("Missing Send Messages permission in leave channel %s (%s)", channel.name, channel.id)
                return

            custom_msg = config_manager.get_leave_message(guild.id) or DEFAULT_LEAVE

            try:
                description = custom_msg.format(
                    member=str(member),
                    server=guild.name,
                    count=guild.member_count or len(guild.members),
                )
            except (KeyError, IndexError):
                description = DEFAULT_LEAVE

            embed = discord.Embed(
                title="👋 Goodbye!",
                description=description,
                color=0xED4242,
            )
            embed.set_footer(text=f"{guild.name} | {guild.member_count or len(guild.members)} members remaining")

            await channel.send(embed=embed)
            log.info("Sent leave embed for %s in guild %s", member.id, guild.id)

        except Exception as exc:
            log.error("Error in on_member_remove for guild %s: %s", getattr(member, "guild", None), exc, exc_info=True)


async def setup(bot):
    await bot.add_cog(WelcomeLeave(bot))
