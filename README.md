Discord Bot Token	In a .env file at the project root as DISCORD_TOKEN	Used in bot.py:70 via os.getenv("DISCORD_TOKEN")
Groq API Key	In the same .env file as GROQ_API_KEY	Used in cogs/ai_chat.py:9 via os.getenv("GROQ_API_KEY")
Owner ID	Directly in bot.py at line 12	OWNER_ID = 1474331599066628140 — replace with your own Discord User ID