import random
import discord
from discord.ext import commands
from utils.items import FISH_ITEMS, RARITIES
from utils.storage import config_manager

class Fishing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="fish")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def fish(self, ctx):
        """Go fishing to catch fish"""
        if random.random() < 0.15:
            embed = discord.Embed(
                title="🎣 Fishing Result",
                description="You caught **nothing**... Better luck next time!",
                color=0x808080
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.send(embed=embed)
            return

        # Catch 1-5 fish at once
        num_fish = random.randint(1, 5)

        caught_fish = []
        caught_msgs = []
        for _ in range(num_fish):
            fish_item = random.choice(FISH_ITEMS)
            value = random.randint(*fish_item["value_range"])
            caught_fish.append({"item": fish_item, "value": value})
            config_manager.add_to_inventory(ctx.author.id, fish_item["name"], value)

        # ── Random catch messages by tier ──────────────────────────
        # Tiers: regular <→ starfish <→ golden fish
        _RARITY_TIERS = {
            "Common": "regular", "Uncommon": "regular",
            "Rare": "starfish",
            "Epic": "golden", "Legendary": "golden",
        }
        _CATCH_MSGS = {
            "regular": [
                "🐟 You caught a tiny **{name}**!",
                "🐟 Splash! A chonky **{name}** squirms at your line!",
                "🐟 Whoa! A sleek **{name}** bolts past your hook!",
                "🐟 Something nibbled—you reeled in a small **{name}**!",
                "🐟 A curious **{name}** swam into your trap!",
            ],
            "starfish": [
                "✨ Incredible! You caught a **{name}**!",
                "✨ Your line went taut—you landed a shimmering **{name}**!",
                "✨ A brilliant flash! It's a rare **{name}**!",
                "✨ Wait—this doesn't happen often! A **{name}**!",
            ],
            "golden": [
                "🌟 LEGENDARY! A magnificent **{name}** breaches the water!",
                "🌟 The water erupts in gold! You caught a **{name}**!",
                "🌟 Unreal! A golden **{name}**—the waters are blessed today!",
                "🌟 Your fishing pole bows deep! A legendary **{name}** is on the line!",
                "🌟 The crowd gasps! An iridescent **{name}** surfaces!",
            ],
        }

        for catch in caught_fish:
            fi = catch["item"]
            tier = _RARITY_TIERS.get(fi["rarity"], "regular")
            msg_template = random.choice(_CATCH_MSGS[tier])
            caught_msgs.append(msg_template.format(name=fi["name"]))

        # ── Build embed from random catch messages ────────────────
        # Group quantities per fish type while preserving randomised order
        fish_count_map = {}
        for msg, catch_ in zip(caught_msgs, caught_fish):
            name = catch_["item"]["name"]
            fish_count_map.setdefault(name, []).append(msg)

        description_parts = []
        for name, msgs in fish_count_map.items():
            shown = msgs[0]           # first message for the label
            extras = len(msgs) - 1   # how many repeats to compress
            if extras > 0:
                shown += f" (and {extras} more!)"
            description_parts.append(shown)

        embed = discord.Embed(
            title="🎣 Fishing Result",
            description="\n".join(description_parts),
            color=0x00ff00
        )
        embed.set_footer(text=f"Requested by {ctx.author}")

        await ctx.send(embed=embed)

    @fish.error
    async def fish_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏳ Cooldown",
                description=f"Try again in {int(error.retry_after)} seconds!",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="ping")
    async def ping(self, ctx):
        """Check the bot's latency"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: {latency}ms",
            color=0x00ff00
        )
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Fishing(bot))