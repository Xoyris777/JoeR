import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show all available commands")
    async def help(self, ctx):
        """Show help for all available commands"""
        command_count = len([cmd for cmd in self.bot.walk_commands() if not cmd.hidden])

        embed = discord.Embed(
            title="🤖 JoeR Bot — Help",
            description=f"JoeR has **{command_count}** commands.\nChoose a category to explore:",
            color=0x5865F2
        )

        embed.add_field(
            name="📊 Leaderboard",
            value="`.leaderboard` — Show the server leaderboard for message counts",
            inline=False
        )
        embed.add_field(
            name="💰 Economy",
            value=(
                "`.daily` — Claim your daily reward of 100 coins\n"
                "`.work` — Work to earn random coins (10 - 50)\n"
                "`.balance` — Check your current coin balance\n"
                "`.inventory` — View your fishing inventory"
            ),
            inline=False
        )
        embed.add_field(
            name="💬 AI Chat",
            value="Mention the bot or reply to its messages to chat with AI",
            inline=False
        )
        embed.add_field(
            name="🎣 Fishing",
            value=(
                "`.fish` — Go fishing to catch fish!\n"
                "`.sell [amount/all/fishname]` — Sell fish (sell all, a quantity, or by name)\n"
                "`.sell [fishname] [amount]` — Sell a specific fish by quantity\n"
                "`.rate / .marketrate` — Check the current fish market rate\n"
                "`.ping` — Check bot latency"
            ),
            inline=False
        )
        embed.add_field(
            name="👋 Welcome / Leave",
            value=(
                "`.welcome-channel-set` #channel — Set the welcome message channel\n"
                "`.welcome-message-set` `\"<msg>\"` — Set a custom welcome message\n"
                "`.leave-channel-set` #channel — Set the leave/goodbye message channel\n"
                "`.leave-message-set` `\"<msg>\"` — Set a custom leave message"
            ),
            inline=False
        )

        embed.set_footer(text=f"Requested by {ctx.author}")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
