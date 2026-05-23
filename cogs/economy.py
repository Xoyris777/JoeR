import discord
from discord.ext import commands
from utils.storage import config_manager
from db.database import get_rate
import time

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="balance")
    async def balance(self, ctx):
        balance = config_manager.get_balance(ctx.author.id)

        embed = discord.Embed(
            title="💰 Balance",
            description=f"**{ctx.author.display_name}'s Wallet**",
            color=0xffd700
        )
        embed.add_field(name="Current Balance", value=f"💵 {balance} coins", inline=False)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="inventory")
    async def inventory(self, ctx):
        """View your fishing inventory"""
        user_id = ctx.author.id
        inv = config_manager.get_inventory(user_id)

        embed = discord.Embed(
            title="🎒 Inventory",
            description=f"**{ctx.author.display_name}'s Fish Collection**",
            color=0x9932cc
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)

        if not inv:
            embed.add_field(
                name="Empty",
                value="Your inventory is empty! Go fishing with `.fish` to catch something.",
                inline=False
            )
            embed.color = 0x808080
        else:
            total_fish = 0
            for item_name, values in inv.items():
                count = len(values)
                total_fish += count
                embed.add_field(name=item_name, value=f"x{count}", inline=True)

            embed.set_footer(text=f"Total fish: {total_fish} | Requested by {ctx.author}")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="daily")

    async def daily(self, ctx):
        """Get your daily reward"""
        can_claim, remaining_seconds = config_manager.can_claim_daily(ctx.author.id)
        
        if not can_claim:
            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60
            seconds = remaining_seconds % 60
            await ctx.send(f"⏳ You can claim your daily reward in **{hours}h {minutes}m {seconds}s**.")
            return
        
        reward = 100  # Fixed daily reward
        new_balance = config_manager.add_balance(ctx.author.id, reward)
        config_manager.set_last_daily(ctx.author.id, int(time.time()))
        
        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=f"You claimed your daily reward of **{reward} coins**!\nYour new balance is **{new_balance} coins**.",
            color=0x00ff00
        )
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="sell", aliases=["sellfish"])
    async def sell(self, ctx, *, arg: str = "all"):
        """
        Sell fish from your inventory.
        Usage: .sell all | .sell [fishname] | .sell [fishname] <amount>
        """
        user_id = ctx.author.id
        inventory = config_manager.get_inventory(user_id)

        if not inventory:
            embed = discord.Embed(
                title="🎣 Sell Fish",
                description="Your inventory is empty! Go fishing first.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        from utils.items import RARITIES, FISH_ITEMS
        FISH_LOOKUP = {f["name"]: f for f in FISH_ITEMS}
        fish_lookup = FISH_LOOKUP  # alias for brevity

        total_fish = sum(len(v) for v in inventory.values())

        # ── .sell all ──────────────────────────────────────────────
        if arg.lower() == "all":
            sell_map = {name: list(values) for name, values in inventory.items()}

        # ── .sell <amount> (pure number) ───────────────────────────
        elif arg.isdigit():
            qty = int(arg)
            if qty <= 0:
                embed = discord.Embed(
                    title="🎣 Sell Fish",
                    description="Invalid amount. Use a positive number.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            if qty > total_fish:
                embed = discord.Embed(
                    title="🎣 Sell Fish",
                    description=f"You only have **{total_fish}** fish in your inventory.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return
            sell_map = {}
            sold = 0
            for item_name, values in inventory.items():
                if sold >= qty:
                    break
                take = min(len(values), qty - sold)
                sell_map[item_name] = values[:take]
                sold += take

        # ── .sell <fishname> [<amount>] ───────────────────────────
        else:
            parts = arg.strip().split()
            fish_name = parts[0]
            requested_qty = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1

            if fish_name not in inventory or not inventory[fish_name]:
                embed = discord.Embed(
                    title="🎣 Sell Fish",
                    description=f"You don't own any **{fish_name}**!\n"
                                f"Use `.inventory` to check what you have.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return

            available = len(inventory[fish_name])
            if requested_qty > available:
                embed = discord.Embed(
                    title="🎣 Sell Fish",
                    description=f"You only have **{available}x {fish_name}**. Trying to sell **{requested_qty}**.",
                    color=0xff0000
                )
                await ctx.send(embed=embed)
                return

            sell_map = {fish_name: inventory[fish_name][:requested_qty]}

        # ── Calculate earnings and remove from inventory ───────────
        rate = await get_rate()
        total_value = 0
        items_sold_lines = []

        for item_name, values in sell_map.items():
            fi = fish_lookup.get(item_name)
            count = len(values)
            for base_value in values:
                sell_val = int(base_value * RARITIES[fi["rarity"]]["multiplier"] * rate)
                total_value += sell_val

            emoji = RARITIES[fi["rarity"]]["emoji"] if fi else "❓"
            items_sold_lines.append(f"{emoji} **{item_name}** ×{count}")

            config_manager.remove_from_inventory(user_id, item_name, count=count)

        new_balance = config_manager.add_balance(user_id, total_value)

        embed = discord.Embed(
            title="🎣 Fish Sold!",
            color=0x00ff00
        )
        embed.add_field(
            name="🐟 Fish Sold",
            value="\n".join(items_sold_lines) if items_sold_lines else "None",
            inline=False
        )
        embed.add_field(name="💰 Total Earned", value=f"**{total_value}** coins", inline=True)
        embed.add_field(name="📈 Market Rate", value=f"**{rate:.2f}x**", inline=True)
        embed.add_field(name="💵 New Balance", value=f"**{new_balance}** coins", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}")

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="rate", aliases=["marketrate"])
    async def rate(self, ctx):
        """Check the current fish sell market rate"""
        current_rate = await get_rate()
        embed = discord.Embed(
            title="📈 Fish Market Rate",
            description=(
                f"Current sell rate: **{current_rate:.2f}x**\n"
                f"Fish prices are multiplied by this rate.\n"
                f"Rate updates every 10 seconds."
            ),
            color=0x0099ff
        )
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="work")
    async def work(self, ctx):
        """Work to earn coins"""
        import random
        earnings = random.randint(10, 50)
        new_balance = config_manager.add_balance(ctx.author.id, earnings)
        
        jobs = [
            "You worked as a barista and earned",
            "You completed freelance design work and earned", 
            "You helped a neighbor move and earned",
            "You tutored someone and earned",
            "You did yard work and earned",
            "You walked dogs and earned",
            "You delivered food and earned"
        ]
        job = random.choice(jobs)
        
        embed = discord.Embed(
            title="💼 Work",
            description=f"{job} **{earnings} coins**!\nYour new balance is **{new_balance} coins**.",
            color=0x0099ff
        )
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economy(bot))