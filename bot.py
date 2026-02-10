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

BANNER_URL = "https://i.ytimg.com/vi/KPOCXUSUKHY/hq720.jpg?sqp=-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD&rs=AOn4CLBFnzt0x0bFcCqGr0ZebXJ6s_JwdQ"
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.add_view(AppButtonView())
        self.add_view(AdminActions())

bot = MyBot()

# --- SYNC COMMAND ---
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

# --- VIEWS & MODALS ---
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
        if not channel:
            return await interaction.response.send_message("❌ Error: Application log channel not found. Tell an Admin to check the ID!", ephemeral=True)
            
        embed = discord.Embed(title="⭐️ New Texas Trooper Application", color=discord.Color.from_rgb(0, 40, 104))
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

# --- SHIFT MANAGEMENT & LEADERBOARD ---
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
    await interaction.response.send_message(f"🌵 **10-8** | {interaction.user.mention} is now **ON PATROL**.", ephemeral=False)

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
    # Handle both time formats to prevent errors
    try:
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S.%f')
    except:
        start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
    
    duration = end_time - start_time
    c.execute("UPDATE shifts SET end_time = ? WHERE id = ?", (end_time, shift_id))
    conn.commit()
    conn.close()
    
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    await interaction.response.send_message(f"⭐️ **10-42** | {interaction.user.mention} finished patrol. **Time:** {hours}h {minutes}m", ephemeral=False)

@bot.tree.command(name="leaderboard", description="View the top troopers by patrol hours")
async def leaderboard(interaction: discord.Interaction):
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    # This sums up the total time for each user
    c.execute("SELECT user_id, SUM(strftime('%s', end_time) - strftime('%s', start_time)) as total FROM shifts WHERE end_time IS NOT NULL GROUP BY user_id ORDER BY total DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return await interaction.response.send_message("No patrol data recorded yet!", ephemeral=True)

    lb_text = ""
    for i, row in enumerate(rows, 1):
        user = bot.get_user(row[0]) or f"Unknown Trooper ({row[0]})"
        total_seconds = row[1]
        hours = total_seconds // 3600
        lb_text += f"**{i}.** {user} - `{hours} Hours` \n"

    embed = discord.Embed(title="⭐️ Texas DPS Patrol Leaderboard", description=lb_text, color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="reset_hours", description="ADMIN ONLY: Reset all patrol hours")
@app_commands.checks.has_permissions(administrator=True)
async def reset_hours(interaction: discord.Interaction):
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("DELETE FROM shifts")
    conn.commit()
    conn.close()
    await interaction.response.send_message("🚨 All patrol hours have been reset for the new month.", ephemeral=True)

# --- RECRUITMENT & START ---
@bot.event
async def on_ready():
    init_db()
    print(f'✅ Texas DPS Bot Online: {bot.user}')

@bot.tree.command(name="setup_apply", description="Send the Texas DPS recruitment button")
@app_commands.checks.has_permissions(administrator=True)
async def setup_apply(interaction: discord.Interaction):
    embed = discord.Embed(title="Texas Department of Public Safety", description="**Courage, Service, Integrity.**\nClick below to begin your application.", color=discord.Color.from_rgb(191, 10, 48))
    embed.set_image(url=BANNER_URL) 
    await interaction.channel.send(embed=embed, view=AppButtonView())
    await interaction.response.send_message("Recruitment post created.", ephemeral=True)

bot.run(TOKEN)
