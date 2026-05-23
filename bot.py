import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db.database import init_db
from utils.storage import config_manager

load_dotenv(override=True)

# ==================== OWNER SETTINGS ====================
# Paste your Discord User ID here (right-click your profile and select "Copy ID")
OWNER_ID = 1474331599066628140  # <-- Replace with your owner ID
# ========================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # required for on_member_join / on_member_remove
bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Override setup_hook so cogs load before the gateway connects
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

bot.setup_hook = load_cogs

bot.owner_id = OWNER_ID

def is_owner():
    """Check if the command user is the bot owner"""
    def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)

# Make is_owner available to cogs
__all__ = ['is_owner']

@bot.event
async def on_ready():
    await init_db()
    synced = await bot.tree.sync()
    print(f"JoeR is online! Logged in as {bot.user}")
    print(f"Loaded {len(bot.commands)} prefix commands")
    print(f"Synced {len(synced)} slash commands")

@bot.event
async def on_command(ctx):
    """Log every command usage to the configured log channel"""
    if not ctx.guild:
        return
    
    log_channel_id = config_manager.get_log_channel(str(ctx.guild.id))
    if not log_channel_id:
        return
    
    channel = ctx.bot.get_channel(int(log_channel_id))
    if channel:
        embed = discord.Embed(
            title="📝 Command Used",
            description=f"**Command:** {ctx.command.name}\n**User:** {ctx.author} (`{ctx.author.id}`)\n**Channel:** {ctx.channel.mention}",
            color=0x5865F2,
            timestamp=discord.utils.utcnow()
        )
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

bot.run(os.getenv("DISCORD_TOKEN"))