import discord
import os
import json
from discord import app_commands

TOKEN = os.environ["TOKEN"]

# ⬇️ Diese 2 IDs anpassen (Rechtsklick auf Channel → ID kopieren)
ANMELDE_CHANNEL_ID = 353906178650144782   # Channel wo die Anmeldenachricht steht
LOG_CHANNEL_ID     = 353906178650144782   # Geheimer Admin-Channel

MAX_PLAYERS = 24

# --- Datenpersistenz ---
DATA_FILE = "teilnehmer.json"

def lade_teilnehmer():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def speichere_teilnehmer(daten):
    with open(DATA_FILE, "w") as f:
        json.dump(daten, f)

teilnehmer = lade_teilnehmer()  # {discord_id: {"discord": name, "mc": mc_name}}

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# --- Hilfsfunktion: Anmeldenachricht updaten ---
async def update_anmelde_nachricht():
    try:
        with open("setup_msg.json", "r") as f:
            data = json.load(f)
        channel = bot.get_channel(data["channel_id"])
        msg = await channel.fetch_message(data["message_id"])
        embed = discord.Embed(
            title="⚔️ VARO Anmeldung",
            description=f"Klicke den Button um dich anzumelden!\n\n**Plätze:** {len(teilnehmer)}/{MAX_PLAYERS}",
            color=discord.Color.green()
        )
        await msg.edit(embed=embed, view=AnmeldeView())
    except:
        pass  # Falls Nachricht nicht gefunden wird, einfach überspringen

# --- Anmelde-Modal ---
class AnmeldeModal(discord.ui.Modal, title="VARO Anmeldung"):
    minecraft_name = discord.ui.TextInput(
        label="Dein Minecraft Name",
        placeholder="z.B. Notch",
        max_length=16
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        if user_id in teilnehmer:
            await interaction.response.send_message(
                f"❌ Du bist bereits als **{teilnehmer[user_id]['mc']}** angemeldet!",
                ephemeral=True
            )
            return

        if len(teilnehmer) >= MAX_PLAYERS:
            await interaction.response.send_message(
                "❌ Das VARO ist bereits voll!", ephemeral=True
            )
            return

        mc = self.minecraft_name.value
        teilnehmer[user_id] = {"discord": str(interaction.user), "mc": mc}
        speichere_teilnehmer(teilnehmer)

        # Bestätigung an den User
        await interaction.response.send_message(
            f"✅ Erfolgreich angemeldet als **{mc}**! ({len(teilnehmer)}/{MAX_PLAYERS})",
            ephemeral=True
        )

        # Plätze in der Anmeldenachricht aktualisieren
        await update_anmelde_nachricht()

        # Log in Admin-Channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="📋 Neue Anmeldung",
                color=discord.Color.green()
            )
            embed.add_field(name="Discord", value=str(interaction.user), inline=True)
            embed.add_field(name="Minecraft", value=mc, inline=True)
            embed.add_field(name="Plätze", value=f"{len(teilnehmer)}/{MAX_PLAYERS}", inline=True)
            await log_channel.send(embed=embed)

# --- Anmelde-Button ---
class AnmeldeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Jetzt anmelden ⚔️", style=discord.ButtonStyle.green, custom_id="anmelden")
    async def anmelden(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnmeldeModal())

# --- /setup Command (nur einmal ausführen!) ---
@tree.command(name="setup", description="Postet die Anmeldenachricht (nur einmal nötig!)")
async def setup(interaction: discord.Interaction):
    if interaction.channel_id != ANMELDE_CHANNEL_ID:
        await interaction.response.send_message(
            f"❌ Nur in <#{ANMELDE_CHANNEL_ID}> nutzbar!", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="⚔️ VARO Anmeldung",
        description=f"Klicke den Button um dich anzumelden!\n\n**Plätze:** {len(teilnehmer)}/{MAX_PLAYERS}",
        color=discord.Color.green()
    )
    msg = await interaction.channel.send(embed=embed, view=AnmeldeView())

    with open("setup_msg.json", "w") as f:
        json.dump({"message_id": msg.id, "channel_id": interaction.channel_id}, f)

    await interaction.response.send_message("✅ Anmeldenachricht gepostet!", ephemeral=True)

# --- Bot Start ---
@bot.event
async def on_ready():
    bot.add_view(AnmeldeView())  # Button bleibt nach Neustart aktiv
    await tree.sync()
    print(f"✅ Bot online: {bot.user} | {len(teilnehmer)} Anmeldungen geladen")

bot.run(TOKEN)
