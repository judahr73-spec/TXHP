import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv

# 1. LOAD CONFIGURATION
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
APP_LOG_ID = int(os.getenv('APP_LOG_ID', 0))
MOD_LOG_ID = int(os.getenv('MOD_LOG_ID', 0))

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # This keeps the buttons working even if the bot restarts
        self.add_view(AppButtonView())
        self.add_view(AdminActions())
        # Syncs slash commands with Discord
        await self.tree.sync()

bot = MyBot()

# 2. DATABASE SETUP
def init_db():
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS infractions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mod_id INTEGER, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# 3. APPROVAL SYSTEM (The Buttons for Staff)
class AdminActions(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, custom_id="approve_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "🚨 Application APPROVED"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"✅ {interaction.user.mention} approved this applicant.")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, custom_id="deny_btn")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "🚨 Application DENIED"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"❌ {interaction.user.mention} denied this applicant.")

# 4. APPLICATION MODAL
class TrooperApp(discord.ui.Modal, title='State Trooper Application'):
    name = discord.ui.TextInput(label='Name & Callsign', placeholder='John Doe | 1A-01')
    reason = discord.ui.TextInput(label='Why join?', style=discord.TextStyle.paragraph)
    exp = discord.ui.TextInput(label='Experience', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(APP_LOG_ID)
        if not channel:
            return await interaction.response.send_message("Error: App channel not found.", ephemeral=True)

        embed = discord.Embed(title="🚨 New Trooper Application", color=discord.Color.blue())
        embed.add_field(name="Applicant", value=interaction.user.mention)
        embed.add_field(name="Name", value=self.name.value)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        embed.add_field(name="Experience", value=self.exp.value, inline=False)
        
        await channel.send(embed=embed, view=AdminActions())
        await interaction.response.send_message("Application submitted!", ephemeral=True)

class AppButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply for State Trooper", style=discord.ButtonStyle.primary, custom_id="perm_apply")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TrooperApp())

# 5. COMMANDS
@bot.event
async def on_ready():
    init_db()
    print(f'✅ Connected as {bot.user}')

@bot.tree.command(name="setup_apply", description="Send the recruitment button")
@app_commands.checks.has_permissions(administrator=True)
async def setup_apply(interaction: discord.Interaction):
    embed = discord.Embed(title="Trooper Recruitment", description="Click below to apply.", color=discord.Color.gold())
    await interaction.response.send_message("Setup complete!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=AppButtonView())

@bot.tree.command(name="infract", description="Log an infraction")
async def infract(interaction: discord.Interaction, member: discord.Member, reason: str):
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("INSERT INTO infractions (user_id, mod_id, reason) VALUES (?, ?, ?)", (member.id, interaction.user.id, reason))
    conn.commit()
    conn.close()
    
    log_chan = bot.get_channel(MOD_LOG_ID)
    if log_chan:
        await log_chan.send(f"⚖️ **Infraction** | {member.mention} cited by {interaction.user.mention}: {reason}")
    await interaction.response.send_message(f"Logged infraction for {member.display_name}.", ephemeral=True)

@bot.tree.command(name="history", description="Check a user's record")
async def history(interaction: discord.Interaction, member: discord.Member):
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("SELECT reason, timestamp FROM infractions WHERE user_id = ?", (member.id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return await interaction.response.send_message(f"{member.display_name} has a clean record.")
    
    msg = "\n".join([f"• `{r[1][:10]}`: {r[0]}" for r in rows])
    await interaction.response.send_message(f"**Record for {member.display_name}:**\n{msg}")

bot.run(TOKEN)
