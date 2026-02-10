import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
APP_LOG_ID = int(os.getenv('APP_LOG_ID', 0))
MOD_LOG_ID = int(os.getenv('MOD_LOG_ID', 0))

# PASTE YOUR IMAGE LINK HERE
BANNER_URL = "https://your-image-link-here.com/image.png"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(AppButtonView())
        self.add_view(AdminActions())

bot = MyBot()

# --- SYNC COMMAND (Run !sync in Discord) ---
@bot.command()
@commands.is_owner()
async def sync(ctx):
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} slash commands!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS infractions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mod_id INTEGER, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# --- VIEWS & MODALS ---
class AdminActions(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, custom_id="approve_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "🚨 Application APPROVED"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"✅ Approved by {interaction.user.mention}")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, custom_id="deny_btn")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "🚨 Application DENIED"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"❌ Denied by {interaction.user.mention}")

class TrooperApp(discord.ui.Modal, title='State Trooper Application'):
    name = discord.ui.TextInput(label='Name & Callsign')
    reason = discord.ui.TextInput(label='Why join?', style=discord.TextStyle.paragraph)
    exp = discord.ui.TextInput(label='Experience', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(APP_LOG_ID)
        embed = discord.Embed(title="🚨 New Application", color=discord.Color.blue())
        embed.add_field(name="Applicant", value=interaction.user.mention)
        embed.add_field(name="Details", value=f"**Name:** {self.name.value}\n**Exp:** {self.exp.value}")
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        await channel.send(embed=embed, view=AdminActions())
        await interaction.response.send_message("Application sent!", ephemeral=True)

class AppButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Apply for State Trooper", style=discord.ButtonStyle.primary, custom_id="perm_apply")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TrooperApp())

# --- SLASH COMMANDS ---
@bot.event
async def on_ready():
    init_db()
    print(f'✅ Bot Online: {bot.user}')

@bot.tree.command(name="setup_apply", description="Send the recruitment button")
@app_commands.checks.has_permissions(administrator=True)
async def setup_apply(interaction: discord.Interaction):
    embed = discord.Embed(
        title="San Andreas State Trooper Recruitment", 
        description="Are you ready to protect and serve? Click the button below to start your journey.", 
        color=discord.Color.gold()
    )
    # This adds the image you asked for
    embed.set_image(url=BANNER_URL) 
    
    await interaction.channel.send(embed=embed, view=AppButtonView())
    await interaction.response.send_message("Recruitment post created.", ephemeral=True)

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

@bot.tree.command(name="check_record", description="View a member's history")
async def check_record(interaction: discord.Interaction, member: discord.Member):
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("SELECT reason, timestamp FROM infractions WHERE user_id = ?", (member.id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return await interaction.response.send_message(f"{member.display_name} has a clean record.", ephemeral=True)
    
    history = "\n".join([f"• `{r[1][:10]}`: {r[0]}" for r in rows])
    await interaction.response.send_message(f"**Records for {member.display_name}:**\n{history}", ephemeral=True)

bot.run(TOKEN)
