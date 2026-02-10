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

BANNER_URL = "data:image/jpeg;base64,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"

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
