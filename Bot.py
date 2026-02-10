import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv

# 1. LOAD CONFIGURATION
# load_dotenv() looks for a .env file locally. 
# On Railway, it will pull from the "Variables" tab automatically.
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
# We convert these to integers because Discord IDs are numbers
APP_LOG_ID = int(os.getenv('APP_LOG_ID', 0))
MOD_LOG_ID = int(os.getenv('MOD_LOG_ID', 0))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. DATABASE INITIALIZATION
def init_db():
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    # Create table for infractions if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS infractions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, 
                  mod_id INTEGER, 
                  reason TEXT, 
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# 3. APPLICATION MODAL (The Pop-up Form)
class TrooperApp(discord.ui.Modal, title='State Trooper Application'):
    name = discord.ui.TextInput(
        label='Full Name & Callsign', 
        placeholder='e.g. Hunter Smith | 1-A-05',
        required=True
    )
    reason = discord.ui.TextInput(
        label='Why do you want to join the State Troopers?', 
        style=discord.TextStyle.paragraph,
        placeholder='Tell us about your motivation...',
        min_length=20
    )
    experience = discord.ui.TextInput(
        label='Past Experience', 
        style=discord.TextStyle.paragraph,
        placeholder='List any previous departments or RP experience.',
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(APP_LOG_ID)
        if not channel:
            return await interaction.response.send_message("Error: App Log Channel not found.", ephemeral=True)

        embed = discord.Embed(title="🚨 New Trooper Application", color=discord.Color.blue())
        embed.add_field(name="Applicant", value=interaction.user.mention, inline=True)
        embed.add_field(name="Name/Callsign", value=self.name.value, inline=True)
        embed.add_field(name="Reasoning", value=self.reason.value, inline=False)
        embed.add_field(name="Experience", value=self.experience.value, inline=False)
        embed.set_footer(text=f"User ID: {interaction.user.id}")
        
        await channel.send(embed=embed)
        await interaction.response.send_message("Success! Your application has been sent to command.", ephemeral=True)

# 4. PERSISTENT BUTTON VIEW
class AppButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Important for Railway so button doesn't "die"

    @discord.ui.button(label="Apply for State Trooper", style=discord.ButtonStyle.success, custom_id="apply_btn_permanent")
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TrooperApp())

# 5. BOT EVENTS
@bot.event
async def on_ready():
    init_db()
    # This makes the button work even after the bot restarts
    bot.add_view(AppButtonView())
    print(f'✅ Police Bot Online: {bot.user.name}')

# 6. COMMANDS
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_apply(ctx):
    """Sends the recruitment embed with the apply button"""
    embed = discord.Embed(
        title="San Andreas State Trooper Recruitment", 
        description="We are looking for dedicated individuals to join our ranks. Click below to apply.", 
        color=discord.Color.gold()
    )
    embed.set_image(url="https://i.imgur.com/your_cool_police_banner.png") # Optional
    await ctx.send(embed=embed, view=AppButtonView())

@bot.command()
@commands.has_permissions(manage_messages=True)
async def infract(ctx, member: discord.Member, *, reason: str):
    """Logs a strike against a member"""
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("INSERT INTO infractions (user_id, mod_id, reason) VALUES (?, ?, ?)", 
              (member.id, ctx.author.id, reason))
    conn.commit()
    conn.close()

    log_channel = bot.get_channel(MOD_LOG_ID)
    
    embed = discord.Embed(title="⚖️ Infraction Issued", color=discord.Color.red())
    embed.add_field(name="Subject", value=member.mention, inline=True)
    embed.add_field(name="Issued By", value=ctx.author.mention, inline=True)
    embed.add_field(name="Reason", value=reason, inline=False)
    
    if log_channel:
        await log_channel.send(embed=embed)
    await ctx.send(f"✅ Infraction recorded for {member.mention}.")

@bot.command()
async def history(ctx, member: discord.Member):
    """Views a user's infraction history"""
    conn = sqlite3.connect('justice.db')
    c = conn.cursor()
    c.execute("SELECT reason, timestamp FROM infractions WHERE user_id = ? ORDER BY timestamp DESC", (member.id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return await ctx.send(f"🛡️ {member.display_name} has a clean record.")

    description = ""
    for i, row in enumerate(rows, 1):
        description += f"**{i}.** `{row[1][:10]}` - {row[0]}\n"

    embed = discord.Embed(title=f"Record for {member.display_name}", description=description, color=discord.Color.orange())
    await ctx.send(embed=embed)

# 7. START BOT
if __name__ == "__main__":
    bot.run(TOKEN)
