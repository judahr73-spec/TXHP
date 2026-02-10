import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv

# 1. SETUP & CONFIG
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
APP_LOG_CHANNEL_ID = 1470615416312430633  # Replace with your channel ID for apps
MOD_LOG_CHANNEL_ID = 1234567890  # Replace with your channel ID for infractions

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. DATABASE SETUP (Infractions)
def init_db():
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS infractions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, 
                  mod_id INTEGER, 
                  reason TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# 3. APPLICATION MODAL UI
class TrooperApp(discord.ui.Modal, title='State Trooper Application'):
    name = discord.ui.TextInput(label='Full Name/Callsign', placeholder='John Doe | 1-A-01')
    reason = discord.ui.TextInput(label='Why do you want to join?', style=discord.TextStyle.paragraph)
    experience = discord.ui.TextInput(label='Past Experience', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(APP_LOG_CHANNEL_ID)
        embed = discord.Embed(title="New Trooper Application", color=discord.Color.blue())
        embed.add_field(name="Applicant", value=interaction.user.mention)
        embed.add_field(name="Name", value=self.name.value, inline=False)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        embed.add_field(name="Experience", value=self.experience.value, inline=False)
        
        await channel.send(embed=embed)
        await interaction.response.send_message("Application submitted successfully!", ephemeral=True)

class AppButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply for State Trooper", style=discord.ButtonStyle.primary, custom_id="apply_btn")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TrooperApp())

# 4. BOT EVENTS & COMMANDS
@bot.event
async def on_ready():
    init_db()
    print(f'Logged in as {bot.user.name}')
    # Persistent button remains active after bot restarts
    bot.add_view(AppButton())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_apply(ctx):
    """Sends the application button to the current channel"""
    embed = discord.Embed(title="State Trooper Recruitment", description="Click the button below to start your application.", color=discord.Color.gold())
    await ctx.send(embed=embed, view=AppButton())

@bot.command()
@commands.has_permissions(manage_messages=True)
async def infract(ctx, member: discord.Member, *, reason: str):
    """Logs a strike against a user"""
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("INSERT INTO infractions (user_id, mod_id, reason) VALUES (?, ?, ?)", 
              (member.id, ctx.author.id, reason))
    conn.commit()
    conn.close()

    embed = discord.Embed(title="Infraction Logged", color=discord.Color.red())
    embed.add_field(name="Trooper/User", value=member.mention)
    embed.add_field(name="Reason", value=reason)
    embed.set_footer(text=f"Issued by {ctx.author}")
    
    log_channel = bot.get_channel(MOD_LOG_CHANNEL_ID)
    await log_channel.send(embed=embed)
    await ctx.send(f"Infraction recorded for {member.display_name}.")

@bot.command()
async def history(ctx, member: discord.Member):
    """Checks the infraction history of a user"""
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("SELECT reason, timestamp FROM infractions WHERE user_id = ?", (member.id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return await ctx.send(f"{member.display_name} has a clean record.")

    history_text = "\n".join([f"• [{r[1]}] {r[0]}" for r in rows])
    await ctx.send(f"**Infraction History for {member.display_name}:**\n{history_text}")

bot.run(TOKEN)