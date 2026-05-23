import discord
from discord.ext import commands
from utils.storage import config_manager

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="log")
    async def log(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for command logging (owner only)"""
        # Check owner permission inline
        from bot import OWNER_ID
        if ctx.author.id != OWNER_ID:
            await ctx.send("❌ This command is owner-only.")
            return
            
        if channel is None:
            config_manager.set_log_channel(ctx.guild.id, "")
            await ctx.send("❌ Command logging disabled.")
        else:
            config_manager.set_log_channel(ctx.guild.id, channel.id)
            await ctx.send(f"✅ Command logging enabled. Logs will be sent to {channel.mention}.")

async def setup(bot):
    await bot.add_cog(Logs(bot))