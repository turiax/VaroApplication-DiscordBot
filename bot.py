import discord
import os
from discord.ext import commands
from discord import app_commands

TOKEN = os.environ["TOKEN"]
MAX_PLAYERS = 144

bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)
teilnehmer = {}  # {discord_id: minecraft_name}

# --- Anmelde-Modal (Popup-Formular) ---
class AnmeldeModal(discord.ui.Modal, title="VARO Anmeldung"):
    minecraft_name = discord.ui.TextInput(
        label="Dein Minecraft Name",
        placeholder="z.B. Notch",
        max_length=16
    )

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if user_id in teilnehmer:
            await interaction.response.send_message(
                "❌ Du bist bereits angemeldet!", ephemeral=True
            )
            return

        if len(teilnehmer) >= MAX_PLAYERS:
            await interaction.response.send_message(
                "❌ Leider ist das VARO bereits voll!", ephemeral=True
            )
            return

        teilnehmer[user_id] = self.minecraft_name.value
        await interaction.response.send_message(
            f"✅ Erfolgreich angemeldet als **{self.minecraft_name.value}**!", ephemeral=True
        )
        print(f"Angemeldet: {interaction.user.name} → {self.minecraft_name.value}")

# --- Anmelde-Button ---
class AnmeldeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Jetzt anmelden 🗡️", style=discord.ButtonStyle.green)
    async def anmelden(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnmeldeModal())

# --- /anmeldung Command (postet den Button) ---
@tree.command(name="anmeldung", description="Startet die VARO Anmeldung")
async def anmeldung(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚔️ VARO Anmeldung",
        description=f"Klicke den Button um dich anzumelden!\n\n**Plätze:** 0/{MAX_PLAYERS}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, view=AnmeldeView())

# --- /teilnehmer Command (zeigt Liste) ---
@tree.command(name="teilnehmer", description="Zeigt alle angemeldeten Spieler")
async def teilnehmer_liste(interaction: discord.Interaction):
    if not teilnehmer:
        await interaction.response.send_message("Noch niemand angemeldet.")
        return

    liste = "\n".join(
        [f"{i+1}. {mc}" for i, mc in enumerate(teilnehmer.values())]
    )
    embed = discord.Embed(
        title=f"⚔️ Teilnehmer ({len(teilnehmer)}/{MAX_PLAYERS})",
        description=liste,
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

# --- Bot starten ---
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot online: {bot.user}")

bot.run(TOKEN)
