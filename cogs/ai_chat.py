import os
import discord
from discord.ext import commands
from groq import AsyncGroq

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.conversation_history = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Owner shoutout — catch questions about owner/creator
        content_lower = message.content.lower()
        owner_keywords = [
            "who made you", "who created you", "who is your owner",
            "who is your creator", "who owns you", "your owner",
            "your creator", "who developed you", "who programmed you",
            "who owns you twin", 
        ]
        if any(kw in content_lower for kw in owner_keywords):
            await message.channel.send("Xoyris is my owner!")
            return

        should_respond = False
        context_messages = []

        if self.bot.user in message.mentions:
            should_respond = True
            context_messages = await self._build_context_from_thread(message)
        elif message.reference and message.reference.message_id:
            try:
                replied_msg = await message.channel.fetch_message(message.reference.message_id)
                if replied_msg.author.id == self.bot.user.id:
                    should_respond = True
                    context_messages = await self._build_context_from_thread(message)
            except (discord.NotFound, discord.Forbidden):
                pass

        if should_respond:
            async with message.channel.typing():
                try:
                    response = await self._get_ai_response(message.content, context_messages, message.author.id)
                    await message.reply(response, mention_author=False)
                except Exception as e:
                    await message.reply(f"Sorry, I encountered an error: {str(e)}")

    async def _build_context_from_thread(self, message):
        messages = []
        try:
            async for msg in message.channel.history(limit=10, before=message.created_at):
                if msg.author.id == self.bot.user.id or self.bot.user in msg.mentions:
                    role = "assistant" if msg.author.id == self.bot.user.id else "user"
                    content = msg.content.replace(f"<@{self.bot.user.id}>", "").strip()
                    messages.insert(0, {"role": role, "content": content})
        except discord.Forbidden:
            pass
        return messages

    async def _get_ai_response(self, prompt, context_messages, user_id):
        messages = [
            {"role": "system", "content": "You are a helpful, friendly Discord bot. Keep responses concise and engaging."}
        ]
        messages.extend(context_messages)
        messages.append({"role": "user", "content": prompt})

        models_to_try = [
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-120b",
            "llama-3.1-8b-instant",
        ]
        
        for model in models_to_try:
            try:
                chat_completion = await self.client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=0.7,
                    max_tokens=512,
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                if model == models_to_try[-1]:
                    raise e
                continue

async def setup(bot):
    await bot.add_cog(AIChat(bot))