import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import google.generativeai as genai
import asyncio
import os

# ===== TOKENS FROM GITHUB SECRETS =====
TOKEN = os.getenv("DISCORD_TOKEN") or "YOUR_DISCORD_BOT_TOKEN"
GEMINI_API_KEY = os.getenv("GEMINI_KEY") or "YOUR_GEMINI_API_KEY"

# Config
SUPPORT_ROLE_ID = None
TICKET_CATEGORY_ID = None

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash',
    system_instruction="You are BroOS Support Bot made by Reyaansh. Help with BroOS OS, coding, Discord. Be short friendly. If you don't know answer, say I_CANNOT_FIND. Knowledge: BroOS is custom OS in Assembly, GitHub BROCommitsOS, boot via copy.sh/v86."
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ===== VIEWS =====
class HelpOptionsView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FAQSelect())

    @discord.ui.button(label="💬 Talk with a Support Team", style=discord.ButtonStyle.red, custom_id="talk_support_btn")
    async def talk_support(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        existing = discord.utils.get(guild.channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"You already have ticket: {existing.mention}", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        if SUPPORT_ROLE_ID:
            role = guild.get_role(SUPPORT_ROLE_ID)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        category = guild.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID else None
        channel = await guild.create_text_channel(name=f"ticket-{interaction.user.name}", overwrites=overwrites, category=category)
        embed = discord.Embed(title="Support Team Connected", description=f"{interaction.user.mention} Explain your issue, team will help!", color=0xff0000)
        await channel.send(embed=embed, view=CloseView())
        await interaction.response.send_message(f"Done! Go to {channel.mention}", ephemeral=True)

class FAQSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="How to boot BroOS?", emoji="💻"),
            discord.SelectOption(label="GitHub Build Failed?", emoji="🔧"),
            discord.SelectOption(label="Bot Commands", emoji="🤖"),
            discord.SelectOption(label="YouTube Upload?", emoji="▶️"),
        ]
        super().__init__(placeholder="Choose common issue...", options=options, custom_id="faq_select_menu")
    async def callback(self, interaction: discord.Interaction):
        answers = {
            "How to boot BroOS?": "1. Download BroOS.img from Actions\n2. Go to copy.sh/v86\n3. Select file -> Start!",
            "GitHub Build Failed?": "Check boot.asm exists in main folder and blank.yml has nasm command.",
            "Bot Commands": "Use? + question like `? how to boot?` or use /support command.",
            "YouTube Upload?": "Record v86 screen, then YouTube app -> + -> Upload."
        }
        await interaction.response.send_message(answers[self.values[0]], ephemeral=True)

class CloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_final")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Closing in 5 sec...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

async def ask_ai(q):
    try:
        r = model.generate_content(q)
        t = r.text
        if "I_CANNOT_FIND" in t or len(t) < 5:
            return None
        return t
    except:
        return None

@bot.event
async def on_ready():
    print(f"ONLINE as {bot.user}")
    await bot.tree.sync()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if bot.user.mentioned_in(message) or message.content.startswith("?") or isinstance(message.channel, discord.DMChannel):
        q = message.content.replace(f"<@{bot.user.id}>", "").strip().lstrip("?").strip()
        if not q:
            await message.reply("Ask me anything! Ex: `? how to boot BroOS?`")
            return
        async with message.channel.typing():
            ai = await ask_ai(q)
        if ai:
            await message.reply(f"{ai}\n\n-# Not helpful? Choose below 👇", view=HelpOptionsView())
        else:
            embed = discord.Embed(title="Couldn't find answer 😅", description=f"You asked: `{q}`\n\nChoose option or talk to team:", color=0xffa500)
            await message.reply(embed=embed, view=HelpOptionsView())
    await bot.process_commands(message)

@bot.tree.command(name="support", description="Open support panel")
async def support_panel(interaction: discord.Interaction):
    embed = discord.Embed(title="BroOS AI Support", description="Ask with `? your question`\nIf AI fails, click **Talk with a Support Team**", color=0x5865F2)
    await interaction.response.send_message(embed=embed, view=HelpOptionsView())

@bot.event
async def setup_hook():
    bot.add_view(HelpOptionsView())
    bot.add_view(CloseView())

bot.run(TOKEN)
