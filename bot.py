import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
APP_LOG_ID = int(os.getenv('APP_LOG_ID', 0))
MOD_LOG_ID = int(os.getenv('MOD_LOG_ID', 0))

# PASTE YOUR TEXAS DPS BANNER LINK HERE
# Suggestion: A Texas flag or a DPS Patrol Car image
BANNER_URL = "https://your-image-link-here.com/texas_dps.png"

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
        await ctx.send(f"✅ Synced {len(synced)} slash commands for Texas DPS!")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS infractions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mod_id INTEGER, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS shifts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, start_time DATETIME, end_time DATETIME)''')
    conn.commit()
    conn.close()

# --- APPLICATION VIEWS ---
class AdminActions(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, custom_id="approve_btn")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "⭐️ Application APPROVED"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"✅ Approved for Texas DPS by {interaction.user.mention}")

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger, custom_id="deny_btn")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ Application DENIED"
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(f"❌ Denied by {interaction.user.mention}")

class TrooperApp(discord.ui.Modal, title='Texas State Trooper Application'):
    name = discord.ui.TextInput(label='Full Name & Callsign', placeholder='e.g., Silas Vassar | 4D-20')
    reason = discord.ui.TextInput(label='Why do you want to join Texas DPS?', style=discord.TextStyle.paragraph)
    exp = discord.ui.TextInput(label='Experience', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(APP_LOG_ID)
        embed = discord.Embed(title="⭐️ New Texas Trooper Application", color=discord.Color.from_rgb(0, 40, 104)) # Texas Blue
        embed.add_field(name="Applicant", value=interaction.user.mention)
        embed.add_field(name="Identity", value=self.name.value)
        embed.add_field(name="Reasoning", value=self.reason.value, inline=False)
        await channel.send(embed=embed, view=AdminActions())
        await interaction.response.send_message("Your application has been submitted to Texas DPS command.", ephemeral=True)

class AppButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Apply for Texas State Trooper", style=discord.ButtonStyle.primary, custom_id="perm_apply")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TrooperApp())

# --- SHIFT MANAGEMENT ---
@bot.tree.command(name="on_duty", description="Clock in for your Texas DPS patrol")
async def on_duty(interaction: discord.Interaction):
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("SELECT id FROM shifts WHERE user_id = ? AND end_time IS NULL", (interaction.user.id,))
    if c.fetchone():
        conn.close()
        return await interaction.response.send_message("⚠️ You are already marked on duty!", ephemeral=True)
    
    c.execute("INSERT INTO shifts (user_id, start_time) VALUES (?, ?)", (interaction.user.id, datetime.now()))
    conn.commit()
    conn.close()
    await interaction.response.send_message(f"🌵 **10-8** | {interaction.user.mention} is now **ON PATROL** (Texas DPS).", ephemeral=False)

@bot.tree.command(name="off_duty", description="Clock out from your Texas DPS patrol")
async def off_duty(interaction: discord.Interaction):
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("SELECT id, start_time FROM shifts WHERE user_id = ? AND end_time IS NULL", (interaction.user.id,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return await interaction.response.send_message("⚠️ You aren't currently on duty!", ephemeral=True)
    
    shift_id, start_time_str = result
    end_time = datetime.now()
    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S.%f')
    
    duration = end_time - start_time
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    c.execute("UPDATE shifts SET end_time = ? WHERE id = ?", (end_time, shift_id))
    conn.commit()
    conn.close()
    
    await interaction.response.send_message(
        f"⭐️ **10-42** | {interaction.user.mention} has finished their patrol.\n**Shift Time:** {hours}h {minutes}m", 
        ephemeral=False
    )

# --- RECRUITMENT ---
@bot.event
async def on_ready():
    init_db()
    print(f'✅ Texas DPS Bot Online: {bot.user}')

@bot.tree.command(name="setup_apply", description="Send the Texas DPS recruitment button")
@app_commands.checks.has_permissions(administrator=True)
async def setup_apply(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Texas Department of Public Safety", 
        description="**Courage, Service, Integrity.**\nJoin the elite ranks of the Texas State Troopers. Click below to begin your application.", 
        color=discord.Color.from_rgb(191, 10, 48) # Texas Red
    )
    embed.set_image(url=BANNER_URL) 
    await interaction.channel.send(embed=embed, view=AppButtonView())
    await interaction.response.send_message("Texas DPS Recruitment post created.", ephemeral=True)

# --- MODERATION ---
@bot.tree.command(name="infract", description="Log a disciplinary action")
async def infract(interaction: discord.Interaction, member: discord.Member, reason: str):
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("INSERT INTO infractions (user_id, mod_id, reason) VALUES (?, ?, ?)", (member.id, interaction.user.id, reason))
    conn.commit()
    conn.close()
    
    log_chan = bot.get_channel(MOD_LOG_ID)
    if log_chan:
        await log_chan.send(f"⚖️ **Citation** | {member.mention} cited by {interaction.user.mention}: {reason}")
    await interaction.response.send_message(f"Disciplinary record updated for {member.display_name}.", ephemeral=True)

bot.run(TOKEN)
