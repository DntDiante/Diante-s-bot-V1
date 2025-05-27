import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import random
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

tournage_submissions = {}

@bot.event
async def on_ready():
    # --- Statut personnalisé ---
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="des vidéos de Diante"
    )
    await bot.change_presence(activity=activity)

    # --- Sync des commandes slash ---
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commandes slash synchronisées.")
    except Exception as e:
        print(f"❌ Erreur de synchronisation : {e}")
    
    print(f"🤖 Connecté en tant que {bot.user}")

# Variables globales
auto_welcome_channel = None
giveaways = {}
tournage_data = {}

# --- COMMANDES MODÉRATION ---

@bot.tree.command(name="ban", description="Bannir un membre")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🚫 {member} a été banni.")

@bot.tree.command(name="kick", description="Expulser un membre")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member} a été expulsé.")

@bot.tree.command(name="mute", description="Rendre muet un membre")
async def mute(interaction: discord.Interaction, member: discord.Member):
    role = discord.utils.get(interaction.guild.roles, name="Muted")
    if not role:
        role = await interaction.guild.create_role(name="Muted")
        for channel in interaction.guild.channels:
            await channel.set_permissions(role, send_messages=False, speak=False)
    await member.add_roles(role)
    await interaction.response.send_message(f"🔇 {member} a été mute.")

@bot.tree.command(name="demute", description="Rendre la voix à un membre")
async def demute(interaction: discord.Interaction, member: discord.Member):
    role = discord.utils.get(interaction.guild.roles, name="Muted")
    if role in member.roles:
        await member.remove_roles(role)
        await interaction.response.send_message(f"🔊 {member} a été demute.")
    else:
        await interaction.response.send_message("Ce membre n'est pas mute.", ephemeral=True)

@bot.tree.command(name="clear", description="Supprime un nombre de messages dans le salon")
async def clear(interaction: discord.Interaction, amount: int):
    deleted = await interaction.channel.purge(limit=amount + 1)
    await interaction.response.send_message(f"🧹 {len(deleted)-1} messages supprimés.", ephemeral=True)

@bot.tree.command(name="clear-user", description="Supprime les messages d'un membre")
async def clear_user(interaction: discord.Interaction, member: discord.Member, amount: int = 100):
    def is_user(m):
        return m.author == member
    deleted = await interaction.channel.purge(limit=amount, check=is_user)
    await interaction.response.send_message(f"🧹 {len(deleted)} messages de {member} supprimés.", ephemeral=True)

@bot.tree.command(name="lock", description="Verrouille un salon")
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message(f"🔒 {channel.mention} est verrouillé.")

@bot.tree.command(name="unlock", description="Déverrouille un salon")
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    overwrite = channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = True
    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
    await interaction.response.send_message(f"🔓 {channel.mention} est déverrouillé.")

@bot.tree.command(name="pre-ban", description="Bannir un utilisateur par son ID")
async def pre_ban(interaction: discord.Interaction, user_id: str, reason: str = None):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.ban(user, reason=reason)
    await interaction.response.send_message(f"🚫 {user} a été banni par ID.")

@bot.tree.command(name="unban", description="Déban un membre par ID")
async def unban(interaction: discord.Interaction, user_id: str):
    user = await bot.fetch_user(int(user_id))
    await interaction.guild.unban(user)
    await interaction.response.send_message(f"🔓 {user} a été débanni.")

# --- OUTILS ---

@bot.tree.command(name="auto-welcome", description="Configurer le salon de bienvenue")
async def auto_welcome(interaction: discord.Interaction, channel: discord.TextChannel):
    global auto_welcome_channel
    auto_welcome_channel = channel.id
    await interaction.response.send_message(f"✅ Messages de bienvenue activés dans {channel.mention}")

@bot.event
async def on_member_join(member):
    if auto_welcome_channel:
        channel = bot.get_channel(auto_welcome_channel)
        if channel:
            await channel.send(f"🎉 Bienvenue {member.mention} sur le serveur !")

@bot.tree.command(name="invite", description="Génère un lien d'invitation permanent")
async def invite(interaction: discord.Interaction):
    link = await interaction.channel.create_invite(max_age=0, max_uses=0)
    await interaction.response.send_message(f"Voici un lien d'invitation permanent : {link}")

@bot.tree.command(name="mp", description="Envoyer un message privé à un utilisateur sous mon identité")
async def mp(interaction: discord.Interaction, user: discord.User, *, message: str):
    try:
        await user.send(message)
        await interaction.response.send_message(f"Message envoyé à {user}.")
    except:
        await interaction.response.send_message(f"Impossible d'envoyer le message à {user}.", ephemeral=True)

@bot.tree.command(name="send-message", description="Envoyer un message sous mon identité")
async def send_message(interaction: discord.Interaction, channel: discord.TextChannel, *, message: str):
    await channel.send(message)
    await interaction.response.send_message(f"Message envoyé dans {channel.mention}.")

@bot.tree.command(name="recréer-salon", description="Supprime et recrée un salon")
async def recreate_channel(interaction: discord.Interaction, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    new_channel = await channel.clone()
    await channel.delete()
    await interaction.response.send_message(f"{new_channel.mention} a été recréé.")

@bot.tree.command(name="freset-pseudo", description="Réinitialise le pseudo d'un membre")
async def freset_pseudo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    await member.edit(nick=None)
    await interaction.response.send_message(f"Le pseudo de {member} a été réinitialisé.")

@bot.tree.command(name="random-pseudo", description="Change le pseudo d'un membre aléatoirement")
async def random_pseudo(interaction: discord.Interaction, member: discord.Member):
    pseudo = "User" + str(random.randint(1000, 9999))
    await member.edit(nick=pseudo)
    await interaction.response.send_message(f"Le pseudo de {member} a été changé en {pseudo}.")

@bot.tree.command(name="froleall", description="Attribuer un rôle à tous les membres (bots/humains)")
async def froleall(interaction: discord.Interaction, role: discord.Role):
    count = 0
    for member in interaction.guild.members:
        try:
            await member.add_roles(role)
            count += 1
        except:
            pass
    await interaction.response.send_message(f"Le rôle {role} a été attribué à {count} membres.")

@bot.tree.command(name="frole-temp", description="Attribuer un rôle temporaire à un membre")
async def frole_temp(interaction: discord.Interaction, member: discord.Member, role: discord.Role, duration: int):
    await member.add_roles(role)
    await interaction.response.send_message(f"Le rôle {role} a été attribué temporairement à {member} pendant {duration} secondes.")
    await asyncio.sleep(duration)
    await member.remove_roles(role)

# --- GIVEAWAYS ---

@bot.tree.command(name="giveaway", description="Créer un giveaway")
async def giveaway(interaction: discord.Interaction, duration: int, prize: str):
    embed = discord.Embed(title="🎉 Giveaway !", description=f"Prix : **{prize}**\nRéagis avec 🎉 pour participer !", color=0x00ffcc)
    message = await interaction.channel.send(embed=embed)
    await message.add_reaction("🎉")
    giveaways[message.id] = {"channel": interaction.channel.id, "prize": prize, "host": interaction.user.id}
    await interaction.response.send_message("Giveaway lancé !")

@bot.tree.command(name="giveaway-end", description="Terminer un giveaway")
async def giveaway_end(interaction: discord.Interaction, message_id: int):
    if message_id not in giveaways:
        await interaction.response.send_message("Giveaway non trouvé.", ephemeral=True)
        return
    channel = bot.get_channel(giveaways[message_id]["channel"])
    message = await channel.fetch_message(message_id)
    users = await message.reactions[0].users().flatten()
    users = [u for u in users if not u.bot]
    if not users:
        await interaction.response.send_message("Personne n'a participé au giveaway.", ephemeral=True)
        return
    winner = random.choice(users)
    await channel.send(f"🎉 Félicitations {winner.mention}, tu as gagné **{giveaways[message_id]['prize']}** !")
    del giveaways[message_id]
    await interaction.response.send_message("Giveaway terminé.")

@bot.tree.command(name="giveaway-participants", description="Afficher la liste des participants d'un giveaway")
async def giveaway_participants(interaction: discord.Interaction, message_id: int):
    if message_id not in giveaways:
        await interaction.response.send_message("Giveaway non trouvé.", ephemeral=True)
        return
    channel = bot.get_channel(giveaways[message_id]["channel"])
    message = await channel.fetch_message(message_id)
    users = await message.reactions[0].users().flatten()
    users = [u for u in users if not u.bot]
    participants = ", ".join(u.name for u in users)
    await interaction.response.send_message(f"Participants : {participants}")

@bot.tree.command(name="giveaway-reroll", description="Relancer un giveaway")
async def giveaway_reroll(interaction: discord.Interaction, message_id: int):
    if message_id not in giveaways:
        await interaction.response.send_message("Giveaway non trouvé.", ephemeral=True)
        return
    channel = bot.get_channel(giveaways[message_id]["channel"])
    message = await channel.fetch_message(message_id)
    users = await message.reactions[0].users().flatten()
    users = [u for u in users if not u.bot]
    if not users:
        await interaction.response.send_message("Personne n'a participé au giveaway.", ephemeral=True)
        return
    winner = random.choice(users)
    await channel.send(f"🎉 Nouveau gagnant : {winner.mention} !")
    await interaction.response.send_message("Giveaway relancé.")

# --- DIVERS ---

@bot.tree.command(name="ping", description="Affiche la latence du bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong ! Latence : {round(bot.latency * 1000)}ms")

@bot.tree.command(name="jslow", description="Ajouter/modifier le slowmode d'un salon")
async def jslow(interaction: discord.Interaction, seconds: int, channel: discord.TextChannel = None):
    channel = channel or interaction.channel
    await channel.edit(slowmode_delay=seconds)
    await interaction.response.send_message(f"Slowmode réglé à {seconds} secondes dans {channel.mention}")

@bot.tree.command(name="top-counter", description="Afficher le classement des compteurs")
async def top_counter(interaction: discord.Interaction):
    # Exemple de top-counter fictif, à adapter
    await interaction.response.send_message("Classement des compteurs non implémenté.")

# --- COMMANDE /TOURNAGE AVEC INSCRIPTIONS, PREUVES ET VALIDATION ---

class TournageView(View):
    def __init__(self, tournage_id):
        super().__init__(timeout=None)
        self.tournage_id = tournage_id

    @discord.ui.button(label="Participer", style=discord.ButtonStyle.primary, custom_id="participer_btn")
    async def participer(self, interaction: discord.Interaction, button: Button):
        # Enregistrer la participation, envoyer instructions
        tournage = tournage_data[self.tournage_id]
        tournage['participants'].add(interaction.user.id)
        await interaction.response.send_message(
            f"Tu es inscrit au tournage ! Envoie ta preuve dans le salon {bot.get_channel(tournage['salon_preuves']).mention}",
            ephemeral=True
        )

@bot.tree.command(name="tournage", description="Lancer une session d'inscription pour tournage")
@app_commands.describe(description="Texte d'inscription", preuve="Faut-il une preuve ?", salon_preuve="Salon pour envoyer les preuves")
async def tournage(interaction: discord.Interaction, description: str, preuve: bool = False, salon_preuve: discord.TextChannel = None):
    embed = discord.Embed(title="🎬 Inscription au tournage", description=description, color=discord.Color.blue())
    view = discord.ui.View()

    class InscriptionButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Participer", style=discord.ButtonStyle.green)

        async def callback(self, button_interaction: discord.Interaction):
            if require_proof:
                await button_interaction.response.send_message(
                    "Merci de vouloir participer ! Veuillez envoyer une photo dans le salon : {}. Une fois cela fait, cliquez sur les trois petits points de votre message > Applications > Preuve Tournage.".format(proof_channel.mention),
                    ephemeral=True
                )
                tournage_submissions[button_interaction.user.id] = {
                    "user": button_interaction.user,
                    "channel": proof_channel.id,
                    "status": "pending"
                }
            else:
                await button_interaction.response.send_message("Votre candidature a été prise en compte !", ephemeral=True)
                await interaction.user.send(f"✅ {button_interaction.user} a rejoint le tournage.")

    view.add_item(InscriptionButton())
    await interaction.response.send_message(embed=embed, view=view)

# --- APPLICATION CONTEXT MENU POUR PREUVE ---

@bot.tree.context_menu(name="Preuve Tournage")
async def preuve_tournage(interaction: discord.Interaction, message: discord.Message):
    if interaction.user.id not in tournage_submissions:
        await interaction.response.send_message("Vous ne vous êtes pas inscrit à un tournage.", ephemeral=True)
        return

    submission = tournage_submissions[interaction.user.id]
    proof_channel = bot.get_channel(submission["channel"])

    # Envoyer la preuve dans le salon défini pour les preuves
    await proof_channel.send(
        f"📝 Preuve reçue de {interaction.user.mention} :",
        file=await message.attachments[0].to_file() if message.attachments else None
    )

    await interaction.user.send("✅ Votre preuve a été soumise. Un admin va examiner votre demande.")
    await interaction.response.send_message("Preuve envoyée avec succès !", ephemeral=True)

# Run bot
bot.run("MTM2MzU1OTYzNzE4NTU5MzU5Ng.GFI02W.WqK7yrnRIpuechTjJlaTPJzCIzu_wb0l-0fvkY")
