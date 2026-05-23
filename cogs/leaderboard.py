import discord
from discord.ext import commands
from utils.storage import config_manager

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Track message counts for leaderboard"""
        # Ignore bot messages and DMs
        if message.author.bot or not message.guild:
            return
        
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        username = message.author.name
        
        # Increment message count using config manager
        config_manager.increment_user_messages(guild_id, user_id, username)
    
    @commands.hybrid_command(name="leaderboard", description="Show the server leaderboard for message counts")
    async def leaderboard(self, ctx):
        """Display the leaderboard for the current server"""
        guild_id = str(ctx.guild.id)
        
        # Get leaderboard data for this guild
        guild_data = config_manager.get_guild_leaderboard(guild_id)
        
        # Check if server has any data
        if not guild_data:
            embed = discord.Embed(
                title="📊 Leaderboard",
                description="No leaderboard data found for this server.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        # Get users and sort by message count (descending)
        users = []
        for user_id, user_data in guild_data.items():
            users.append({
                "user_id": user_id,
                "username": user_data["username"],
                "messages": user_data["messages"]
            })
        
        # Sort by message count (highest first) and take top 10
        users.sort(key=lambda x: x["messages"], reverse=True)
        top_users = users[:10]
        
        # Create embed
        embed = discord.Embed(
            title=f"🏆 {ctx.guild.name} Leaderboard",
            color=discord.Color.gold()
        )
        
        if top_users:
            leaderboard_text = ""
            for i, user in enumerate(top_users, 1):
                leaderboard_text += f"{i}. {user['username']} — {user['messages']} messages\n"
            
            embed.description = leaderboard_text
        else:
            embed.description = "No data available"
        
        embed.set_footer(text="Message counts updated in real-time")
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot))