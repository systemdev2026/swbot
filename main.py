import discord
from discord import app_commands
from discord.ext import commands
import config
from flask import Flask
from threading import Thread
intents = discord.Intents.default()
intents.members = True
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


#Часть кода для бота
bot = commands.Bot(command_prefix="/", intents=intents)

GUILD_ID = config.GUILD_ID 
MY_GUILD = discord.Object(id=GUILD_ID)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if not isinstance(message.channel, discord.Thread) and message.interaction is None:
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        except discord.NotFound:
            pass

    await bot.process_commands(message)
#ban
@bot.tree.command(name="ban", description="Панель бана игрока")
@app_commands.describe(
    user="Введите имя или текст",
    type="Выберите: день или час",
    value="Количество или 'all' для навсегда",
    reason="Причина бана"
)
@app_commands.choices(type=[
    app_commands.Choice(name="День", value="day"),
    app_commands.Choice(name="Час", value="hour")
])
async def ban(
    interaction: discord.Interaction, 
    user: str, 
    type: app_commands.Choice[str], 
    value: str, 
    reason: str = "не указана"
):
    allowed_roles = ["admin", "owner","media+","stadmin","curator"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True)
        return

    t_val = type.value
    v_val = value.lower()
    if t_val == 'day' and v_val == 'all':
        desc = f"👤 Пользователь **{user}** был забанен **навсегда**.\n\n**📝 Причина:** {reason}"
    else:
        word = "день" if t_val == "day" else "час"
        desc = f"👤 Пользователь **{user}** был забанен на **{v_val} {word}**.\n\n**📝 Причина:** {reason}"

    embed = discord.Embed(description=desc, color=discord.Color.red())

    await interaction.response.send_message(embed=embed, delete_after=10)

#unban
@bot.tree.command(name="unban", description="Панель разбана")
@app_commands.describe(user="Введите ник")
async def unban(interaction: discord.Interaction, user: str):
    allowed_roles = ["admin", "owner","media+","stadmin","curator"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True)
        return
    embed = discord.Embed(
        description=f"✅ Пользователь **{user}** был **разбанен**.",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=embed, delete_after=10)

#check
@bot.tree.command(name="check", description="Начать проверку игрока (создает ветку)")
@app_commands.describe(username="Ник игрока для проверки")
async def check(interaction: discord.Interaction, username: str):
    allowed_roles = ["admin", "owner","media+","stadmin"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True)
        return

    await interaction.response.send_message(f"🚀 Вызвана проверка для: **{username}**")
    
    base_message = await interaction.original_response()

    thread = await base_message.create_thread(
        name=f"проверка-{username}",
        auto_archive_duration=60 
    )

    embed = discord.Embed(
        title="📢 Проверка на нарушение правил 📢",
        description=(
            f"**{username}**, ожидайте связи с админом.\n\n"
            "> В случае отсутствия микрофона сообщите админу.\n\n"
            "**⚠️ Уход или отказ от проверки карается баном!**"
        ),
        color=discord.Color.gold() 
    )

    await thread.send(embed=embed)

#checkstop
@bot.tree.command(name="checkstop", description="Завершить проверку игрока")
@app_commands.describe(username="Ник игрока, для которого нужно завершить проверку")
async def checkstop(interaction: discord.Interaction, username: str):
    allowed_roles = ["admin", "owner","media+","stadmin"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True)
        return

    target_thread_name = f"проверка-{username}"
    
    thread = discord.utils.get(interaction.guild.threads, name=target_thread_name)

    if thread:
        await thread.delete()
        await interaction.response.send_message(f"✅ Ветка проверки пользователя **{username}** удалена.", delete_after=10)
    else:
        await interaction.response.send_message(f"❌ Активная прооверка для **{username}** не найдена. Проверьте правильность написания.", ephemeral=True)

#lp
@bot.tree.command(name="lp", description="Управление правами")
@app_commands.describe(user="Ник игрока", action="Действие", rank="Ранг")
@app_commands.choices(action=[
    app_commands.Choice(name="set", value="set"),
    app_commands.Choice(name="remove", value="remove")
])
@app_commands.choices(rank=[
    app_commands.Choice(name="Admin", value="admin"),
    app_commands.Choice(name="Moderator", value="moder"),
    app_commands.Choice(name="Curator", value="curator"),
    app_commands.Choice(name="Stadmin", value="stadmin"),
    app_commands.Choice(name="Stmoder", value="stmoder"),
    app_commands.Choice(name="Media", value="media"),
    app_commands.Choice(name="Media+", value="media+")

])
async def lp(interaction: discord.Interaction, user: str, action: app_commands.Choice[str], rank: app_commands.Choice[str]):
    allowed_roles = ["admin", "owner","curator"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True)
        return

    rank_names = {
        "admin": "Администратор",
        "moder": "Модератор",
        "curator": "Куратор",
        "stadmin": "Главный администратор",
        "stmoder": "Главный модератор",
        "media": "Медиа",
        "media+": "Медиа+"

    }
    
    rank_display = rank_names.get(rank.value)
    
    if action.value == "set":
        embed = discord.Embed(description=f"✅ Игроку **{user}** установлен ранг **{rank_display}**", color=0x00ff00)
    else:
        embed = discord.Embed(description=f"🔥 У игрока **{user}** удален ранг **{rank_display}**", color=0xffa500)

    await interaction.response.send_message(embed=embed, delete_after=10)


#grant
DONATE_RANKS = [
    app_commands.Choice(name="Hero", value="Hero"),
    app_commands.Choice(name="Magister", value="Magister"),
    app_commands.Choice(name="Imperator", value="Imperator"),
    app_commands.Choice(name="Helper", value="Helper"),
    app_commands.Choice(name="Dragon", value="Dragon"),
    app_commands.Choice(name="Wave", value="Wave"),
    app_commands.Choice(name="Blizzard", value="Blizzard"),
    app_commands.Choice(name="Gale", value="Gale")
]

@bot.tree.command(name="grant", description="Выдать или забрать донат")
@app_commands.describe(
    action="Выберите: выдать или забрать",
    user="Выберите игрока",
    rank="Выберите ранг"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Set", value="set"),
    app_commands.Choice(name="Remove", value="remove")
])
@app_commands.choices(rank=DONATE_RANKS)
async def grant(
    interaction: discord.Interaction, 
    action: app_commands.Choice[str], 
    user: str, 
    rank: app_commands.Choice[str]
):
    allowed_roles = ["admin", "owner","media+","stadmin","curator"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True)
        return
    if action.value == "set":
        message_text = f"🎁 Игрок **{user}** получил донат: **{rank.name}**."
        color = discord.Color.green()
    else:
        message_text = f"🗑️ У игрока **{user}** был отозван донат: **{rank.name}**."
        color = discord.Color.red()

    embed = discord.Embed(description=message_text, color=color)
    
    await interaction.response.send_message(embed=embed, delete_after=10)


#case
CASE_TYPES = [
    app_commands.Choice(name="Donate Case", value="donate_case"),
    app_commands.Choice(name="Items Case", value="items_case"),
    app_commands.Choice(name="Value Case", value="value_case"), 
    app_commands.Choice(name="DodiCoin Case", value="dodicoin_case"),
    app_commands.Choice(name="Special Case", value="special_case")
]

@bot.tree.command(name="case", description="Управление кейсами игроков")
@app_commands.describe(
    action="Выберите: выдать или забрать",
    user="Введите ник игрока",
    case_type="Выберите тип кейса",
    amount="Введите количество"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Set", value="set"),
    app_commands.Choice(name="Remove", value="remove")
])
@app_commands.choices(case_type=CASE_TYPES)
async def case(
    interaction: discord.Interaction, 
    action: app_commands.Choice[str], 
    user: str, 
    case_type: app_commands.Choice[str],
    amount: int
):
    allowed_roles = ["admin", "owner","media+","stadmin","curator"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True)
        return

    case_name = case_type.name

    if action.value == "set":
        msg = f"🎁 Игрок **{user}** получил кейсы: **{case_name}**\n**Количество:** {amount} шт."
        color = discord.Color.blue()
    else:
        msg = f"🗑️ У игрока **{user}** были изъяты кейсы: **{case_name}**\n**Количество:** {amount} шт."
        color = discord.Color.dark_grey()
    embed = discord.Embed(description=msg, color=color)
    await interaction.response.send_message(embed=embed, delete_after=10)



#warn
@bot.tree.command(name="warn", description="Выдать предупреждение игроку")
@app_commands.describe(
    username="Ник игрока",
    reason="Причина варна"
)
async def warn(
    interaction: discord.Interaction, 
    username: str, 
    reason: str = "Не указана"
):
   
    allowed_roles= ["moderator", "stmoderator", "admin", "stadmin", "curator", "media", "media+", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    desc = (
        f"📢Предупреждение выдано **{username}**📢\n\n"
        f"**Причина:** {reason}\n"
        f"`3 предупреждения = бан 30 дней`"
    )
    embed = discord.Embed(description=desc, color=discord.Color.red())
    
    await interaction.response.send_message(embed=embed, delete_after=10)



#kick
@bot.tree.command(name="kick", description="Кикнуть игрока с игры")
@app_commands.describe(
    username="Введите ник игрока",
    reason="Причина кика"
)
async def kick(
    interaction: discord.Interaction, 
    username: str, 
    reason: str = "Не указана"
):
    allowed_roles= ["moderator", "stmoderator", "admin", "stadmin", "curator", "media", "media+", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    embed = discord.Embed(
        description=f"👞 Игрок **{username}** был **кикнут** с игры.\n\n**📝 Причина:** {reason}",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, delete_after=10)


#kill
@bot.tree.command(name="kill", description="Ударить молнией (убить) игрока")
@app_commands.describe(
    username="Введите ник игрока",
    reason="Причина"
)
async def kill(
    interaction: discord.Interaction, 
    username: str, 
    reason: str = "Не указана"
):
    allowed_roles= ["moderator", "stmoderator", "admin", "stadmin", "curator", "media", "media+", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return


    desc = (
        f"⚡ **Игрок {username} был поражен молнией!** ⚡\n\n"
        f"**📝 Причина наказания:** {reason}\n"
        f"💀 *Покойся с миром...*"
    )

    embed = discord.Embed(description=desc, color=discord.Color.dark_purple())
    await interaction.response.send_message(embed=embed, delete_after=15)


#mute
@bot.tree.command(name="mute", description="Выдать мут игроку (запрет на чат)")
@app_commands.describe(
    user="Введите имя игрока",
    type="Выберите: день, час или минута",
    value="Количество времени",
    reason="Причина мута"
)
@app_commands.choices(type=[
    app_commands.Choice(name="День", value="day"),
    app_commands.Choice(name="Час", value="hour"),
    app_commands.Choice(name="Минута", value="min")
])
async def mute(
    interaction: discord.Interaction, 
    user: str, 
    type: app_commands.Choice[str], 
    value: str, 
    reason: str = "не указана"
):
    allowed_roles = ["moderator", "stmoderator", "admin", "stadmin", "curator", "media", "media+", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    t_val = type.value
    v_val = value.lower()
    
    time_names = {
        "day": "день(ей)",
        "hour": "час(ов)",
        "min": "минут(ы)"
    }
    
    word = time_names.get(t_val)
    
    embed = discord.Embed(
        description=(
            f"🔇 **Пользователь {user} получил мут**\n\n"
            f"**⏰ Срок:** {v_val} {word}\n"
            f"**📝 Причина:** {reason}"
        ),
        color=discord.Color.red() 
    )
    
    await interaction.response.send_message(embed=embed, delete_after=10)


#unmute
@bot.tree.command(name="unmute", description="Панель размута")
@app_commands.describe(user="Введите ник игрока")
async def unmute(interaction: discord.Interaction, user: str):
    allowed_roles= ["moderator", "stmoderator", "admin", "stadmin", "curator", "media", "media+", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    embed = discord.Embed(
        description=f"🔊 С пользователя **{user}** были **сняты** все ограничения чата (unmute).",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, delete_after=10)




#set
@bot.tree.command(name="set", description="Заполнить выделенную территорию блоком")
@app_commands.describe(
    block_id="Введите ID или название блока"
)
async def set_block(
    interaction: discord.Interaction, 
    block_id: str
):
    allowed_roles = ["admin", "stadmin", "curator", "media+","owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return


    desc = (
        f"✅ Вся выделенная территория была успешно заполнена.\n"
        f"🧱 **Блок:** `{block_id}`"
    )

    embed = discord.Embed(
        description=desc, 
        color=discord.Color.from_rgb(34, 139, 34) 
    )
    
    embed.set_author(name="WorldEdit System", icon_url="https://cdn-icons-png.flaticon.com/512/3523/3523951.png")

    await interaction.response.send_message(embed=embed, delete_after=10)



#info
@bot.tree.command(name="info", description="Получить информацию о наказаниях игрока")
@app_commands.describe(username="Ник игрока")
async def info(interaction: discord.Interaction, username: str):
    allowed_roles= ["moderator", "stmoderator", "admin", "stadmin", "curator", "media", "media+", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    desc = f"📊 Вы получили информацию об игроке **{username}**"

    embed = discord.Embed(
        description=desc,
        color=discord.Color.blue()
    )

    await interaction.response.send_message(embed=embed, delete_after=10)
    

#ipinfo
@bot.tree.command(name="ipinfo", description="Получить информацию по конкретному IP-адресу")
@app_commands.describe(ip="Введите IP-адрес для проверки")
async def ipinfo(interaction: discord.Interaction, ip: str):
    allowed_roles= ["admin", "stadmin", "curator", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    desc = (
        f"🌐 **Анализ IP-адреса:** `{ip}`\n\n"
        f"🔎 Информация об IP запрошена.\n"
        f"📊 Результат будет выведен в консоль администратора.\n\n"
    )

    embed = discord.Embed(
        description=desc,
        color=discord.Color.blue()
    )
    
    embed.set_author(name="Network Intelligence")

    await interaction.response.send_message(embed=embed, delete_after=10)




#banip
@bot.tree.command(name="banip", description="Забанить игрока по IP")
@app_commands.describe(
    ip="Введите IP или ник игрока",
    reason="Причина бана по IP"
)
async def banip(
    interaction: discord.Interaction, 
    ip: str, 
    reason: str = "не указана"
):
    allowed_roles= ["admin", "stadmin", "curator", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    desc = (
        f"🚫 **Блокировка по IP**\n\n"
        f"👤 **IP:** `{ip}`\n"
        f"📝 **Причина:** {reason}\n\n"
        f"🔒 Доступ с данного адреса полностью ограничен."
    )

    embed = discord.Embed(
        description=desc, 
        color=discord.Color.dark_red() )
    
    embed.set_author(name="Security System")

    await interaction.response.send_message(embed=embed, delete_after=10)


#unbanip
@bot.tree.command(name="unbanip", description="Разблокировать IP-адрес")
@app_commands.describe(
    ip="Введите IP или ник игрока для разбана",
)
async def unbanip(
    interaction: discord.Interaction, 
    ip: str, 
):
    allowed_roles= ["admin", "stadmin", "curator", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return
    desc = (
        f"🌐 **Разблокировка по IP**\n\n"
        f"✅ **IP** `{ip}`\n"
        f"🔓 Доступ с данного адреса был **восстановлен**.\n"

    )

    embed = discord.Embed(
        description=desc, 
        color=discord.Color.green() 
    )
    
    await interaction.response.send_message(embed=embed, delete_after=10)

#gm
@bot.tree.command(name="gm", description="Сменить игровой режим")
@app_commands.describe(
    mode="Выберите режим игры",
    username="Ник игрока (оставьте пустым для себя)"
)
@app_commands.choices(mode=[
    app_commands.Choice(name="Выживание (0)", value=0),
    app_commands.Choice(name="Творческий (1)", value=1),
    app_commands.Choice(name="Наблюдатель (3)", value=3)
])
async def gm(
    interaction: discord.Interaction, 
    mode: app_commands.Choice[int], 
    username: str = None
):
    allowed_roles = ["admin", "stadmin", "curator", "media+", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    
    is_owner = interaction.user.id == interaction.guild.owner_id
    if not (is_owner or any(target in user_roles for target in allowed_roles)):
        await interaction.response.send_message("❌ У вас нет прав для смены режима игры.", ephemeral=True)
        return

    if mode.value == 0:
        mname = 'режим выживания'
    elif mode.value == 1:
        mname = 'творческий режим'
    else:
        mname = 'режим наблюдателя'

    if username:
        desc = f"🎮 Вы перевели игрока **{username}** в **{mname}**."
    else:
        desc = f"🎮 Вы теперь в **{mname}**."

    embed = discord.Embed(description=desc, color=discord.Color.blue())
    
    await interaction.response.send_message(embed=embed, delete_after=10)







#reports
@bot.tree.command(name="reports", description="Вывести отчеты по жалобам за период")
@app_commands.describe(
    start_date="Дата начала",
    end_date="Дата конца"
)
async def reports(
    interaction: discord.Interaction, 
    start_date: str, 
    end_date: str
):
    allowed_roles= ["admin", "stadmin", "curator", "owner","media","media+","moderator","stmoderator"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return
    
    desc = (
        f"📋 **Выгрузка репортов на игроков**\n"
        f"📅 **Период:** с `{start_date}` по `{end_date}`\n\n"
        f"🔍 Запрос на получение отчетов по жалобам был успешно обработан.\n"
    )

    embed = discord.Embed(
        title="Система отчетов по жалобам",
        description=desc, 
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed, delete_after=30)



#invsee
@bot.tree.command(name="invsee", description="Посмотреть инвентарь игрока")
@app_commands.describe(username="Ник игрока, чей инвентарь нужно проверить")
async def invsee(interaction: discord.Interaction, username: str):
    allowed_roles= ["admin", "stadmin", "curator", "owner","media","media+","moderator","stmoderator"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return
    desc = (
        f"🎒 **Инвентарь игрока:** `{username}`\n\n"
    )

    embed = discord.Embed(
        description=desc,
        color=discord.Color.from_rgb(46, 204, 113) 
    )
    
    await interaction.response.send_message(embed=embed, delete_after=10)





#blacklist
@bot.tree.command(name="blacklist", description="Управление черным списком проекта")
@app_commands.describe(
    action="Выберите действие",
    username="Ник игрока",
    reason="Причина"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Добавить (add)", value="add"),
    app_commands.Choice(name="Удалить (remove)", value="remove")
])
async def blacklist(
    interaction: discord.Interaction, 
    action: app_commands.Choice[str], 
    username: str, 
    reason: str = "не указана"
):
    allowed_roles= ["admin", "stadmin", "curator", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    if action.value == 'add':
        desc = (
            f"🛑 Пользователь **{username}** был добавлен в чёрный список проекта **Secret World**.\n"
            f"📄 Причина: **{reason}**"
        )
        embed_color = discord.Color.from_rgb(0, 0, 0) 
    
    else:
        desc = f"✅ Пользователь **{username}** был удалён из чёрного списка проекта **Secret World**."
        embed_color = discord.Color.green()

    embed = discord.Embed(description=desc, color=embed_color)
    
    await interaction.response.send_message(embed=embed, delete_after=10)





#tp
@bot.tree.command(name="tp", description="Телепортироваться к игроку")
@app_commands.describe(username="Ник игрока, к которому вы хотите телепортироваться")
async def tp(interaction: discord.Interaction, username: str):
    allowed_roles = ["admin", "stadmin", "curator", "owner","media+","stmoderator"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return


    desc = f"✨ Вы телепортировались к пользователю **{username}**"

    embed = discord.Embed(
        description=desc,
        color=discord.Color.from_rgb(155, 89, 182) 
    )
    await interaction.response.send_message(embed=embed, delete_after=10)




#tpcoords
@bot.tree.command(name="tpcoords", description="Телепортироваться по координатам")
@app_commands.describe(
    x="Координата X",
    y="Координата Y",
    z="Координата Z"
)
async def tpcoords(
    interaction: discord.Interaction, 
    x: str, 
    y: str, 
    z: str
):
    allowed_roles = ["admin", "stadmin", "curator", "owner", "media+"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return


    desc = f"📍 Вы телепортировались по координатам: **{x}** **{y}** **{z}**"

    embed = discord.Embed(
        description=desc,
        color=discord.Color.from_rgb(155, 89, 182)
    )
    

    await interaction.response.send_message(embed=embed, delete_after=10)


#tphere
@bot.tree.command(name="tphere", description="Телепортировать игрока к себе")
@app_commands.describe(username="Ник игрока, которого нужно телепортировать к вам")
async def tphere(interaction: discord.Interaction, username: str):
    allowed_roles = ["admin", "stadmin", "curator", "owner", "media+"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return
    desc = f"🧲 Вы телепортировали пользователя **{username}** к себе."

    embed = discord.Embed(
        description=desc,
        color=discord.Color.from_rgb(155, 89, 182) 
    )
    
    await interaction.response.send_message(embed=embed, delete_after=10)



#checkhelp
@bot.tree.command(name="checkhelp", description="Отправить инструкцию по проверке")
@app_commands.describe(type="Выберите ситуацию игрока")
@app_commands.choices(type=[
    app_commands.Choice(name="1 - Нет микрофона", value=1),
    app_commands.Choice(name="2 - Нет телефона", value=2),
    app_commands.Choice(name="3 - Игра с телефона", value=3),
    app_commands.Choice(name="4 - Игра с ПК", value=4)
])
async def checkhelp(interaction: discord.Interaction, type: app_commands.Choice[int]):
    allowed_roles = ["admin", "stadmin", "curator", "owner", "media+"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    t = type.value
    embed = discord.Embed(color=discord.Color.blue())
    
    if t == 1:
        embed.title = "🎧 У тебя нет микрофона?"
        embed.description = (
            "> **Не беда!** Выполни шаги:\n\n"
            "**📱 1. Скачай приложение _CheckPack_**\n"
            "**🔑 2. Введи уникальный код**\n"
            "**💬 3. Ожидай администратора**\n\n"
            "⚠️ *Любая попытка обмана = блокировка*"
        )
    elif t == 2:
        embed.title = "📵 У тебя нет телефона?"
        embed.description = (
            "> **Ничего страшного!**\n\n"
            "**💻 1. Скачай приложение GameAccess**\n"
            "**🖱️ 2. Доступ к игре**\n"
            "**🔑 3. Подтверди код**\n"
            "**💬 4. Ожидай администратора**"
        )
    else:
        device = "телефона" if t == 3 else "компьютера"
        embed.title = f"📲 Ты играешь с {device}?"
        embed.description = (
            "> **Всё встроено в игру!**\n\n"
            "**🔔 1. Жди появления окна проверки**\n"
            "**🔑 2. Введи код и нажми 'Готово'**\n"
            "**💬 3. Ожидай администратора**"
        )

    await interaction.response.send_message(embed=embed)


# dispatch
@bot.tree.command(name="dispatch", description="Передать данные нарушителя в органы")
@app_commands.describe(
    username="Ник нарушителя",
    ip="IP-адрес",
    reason="Суть нарушения"
)
async def dispatch(
    interaction: discord.Interaction, 
    username: str, 
    ip: str, 
    reason: str
):
    allowed_roles = ["owner", "curator"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ Доступ заблокирован. Требуется уровень доступа: OWNER/CURATOR", ephemeral=True)
        return

    desc = (
        f"📡 **ВХОДЯЩИЙ СИГНАЛ: DISPATCH**\n"
        f"──────────────────────────\n"
        f"👤 **Подозреваемый:** `{username}`\n"
        f"🌐 **IP-Адрес:** `{ip}`\n"
        f"📄 **Обвинение:** {reason}\n"
        f"──────────────────────────\n"
        f"✅ **Данные зафиксированы.**"
    )

    embed = discord.Embed(
        title="📂 ПЕРЕДАЧА ДАННЫХ",
        description=desc,
        color=0x2f3136
    )
    
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1022/1022484.png")
    
    await interaction.response.send_message(embed=embed, delete_after=15)




#vanish
@bot.tree.command(name="vanish", description="Перейти в режим невидимости")
@app_commands.describe(username="Ник игрока, которого нужно скрыть (оставьте пустым для себя)")
async def vanish(interaction: discord.Interaction, username: str = None):
    # Проверка прав
    allowed_roles = ["admin", "stadmin", "curator", "owner", "stmoderator", "media+"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    if username:
        desc = (
            f"👤 Администратор **{interaction.user.display_name}** перевел игрока **{username}** в режим **Vanish**.\n\n"
            f"✨ *Его присутствие в игре теперь скрыто.*"
        )
    else:
        desc = (
            f"👤 Вы активировали режим **Vanish**.\n\n"
            f"✨ *Ваше присутствие в игре теперь скрыто.*\n"
            f"🕵️‍♂️ *Вы вышли из поля зрения игроков.*"
        )

    embed = discord.Embed(
        description=desc,
        color=discord.Color.from_rgb(200, 200, 200)
    )


    await interaction.response.send_message(embed=embed, delete_after=15)



#unvanish
@bot.tree.command(name="unvanish", description="Выйти из режима невидимости")
@app_commands.describe(username="Ник игрока, которого нужно проявить (оставьте пустым для себя)")
async def unvanish(interaction: discord.Interaction, username: str = None):
    allowed_roles = ["admin", "stadmin", "curator", "owner", "stmoderator", "media+"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    if username:
        desc = (
            f"👁️ Администратор **{interaction.user.display_name}** вывел игрока **{username}** из режима **Vanish**.\n\n"
            f"📢 *Пользователь снова виден всем игрокам.*"
        )
    else:
        desc = (
            f"👁️ Вы вышли из режима **Vanish**.\n\n"
            f"📢 *Ваше присутствие в игре снова отображается.*\n"
            f"👋 *Игроки могут вас видеть.*"
        )

    embed = discord.Embed(
        description=desc,
        color=discord.Color.blue() 
    )

    await interaction.response.send_message(embed=embed, delete_after=15)


#cash
@bot.tree.command(name="cash", description="Управление балансом игрока")
@app_commands.describe(
    type="Выберите действие: выдать или забрать",
    username="Ник игрока",
    amount="Количество валюты"
)
@app_commands.choices(type=[
    app_commands.Choice(name="Выдать (give)", value="give"),
    app_commands.Choice(name="Забрать (take)", value="take")
])
async def cash(
    interaction: discord.Interaction, 
    type: app_commands.Choice[str], 
    username: str, 
    amount: int
):
    allowed_roles = ["admin", "stadmin", "curator", "media+","owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    if type.value == 'give':
        desc = f"💰 Отлично! Игрок **{username}** получил **{amount}** единиц баланса! 🎉"
        color = discord.Color.green()
    else:
        desc = f"⚠️ Внимание! Игрок **{username}** лишился **{amount}** единиц баланса! 😢"
        color = discord.Color.red()

    embed = discord.Embed(description=desc, color=color)
    
    await interaction.response.send_message(embed=embed, delete_after=15)


#bal
@bot.tree.command(name="bal", description="Управление специальной валютой игрока")
@app_commands.describe(
    type="Выберите действие",
    username="Ник игрока",
    currency="Выберите валюту",
    amount="Количество"
)
@app_commands.choices(type=[
    app_commands.Choice(name="Выдать (give)", value="give"),
    app_commands.Choice(name="Забрать (take)", value="take")
], currency=[
    app_commands.Choice(name="Dodicoin", value="Dodicoin"),
    app_commands.Choice(name="Лунные Листья", value="Лунные Листья"),
    app_commands.Choice(name="Очки Зеркала", value="Очки Зеркала")
])
async def bal(
    interaction: discord.Interaction, 
    type: app_commands.Choice[str], 
    username: str, 
    currency: app_commands.Choice[str], 
    amount: int
):
    allowed_roles = ["admin", "stadmin", "curator", "media+","owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    cur_name = currency.value
    
    if type.value == 'give':
        desc = f"🎉 Ура! Игрок **{username}** получил **{amount}** {cur_name}! 💎"
        color = discord.Color.gold()
    else:
        desc = f"⚠️ Внимание! Игрок **{username}** лишился **{amount}** {cur_name}! 😢"
        color = discord.Color.red()

    embed = discord.Embed(description=desc, color=color)
    
    await interaction.response.send_message(embed=embed, delete_after=15)



#secretpass
@bot.tree.command(name="secretpass", description="Управление Secret Pass+")
@app_commands.describe(
    action="Выберите действие: выдать или забрать",
    username="Ник игрока",
    season="Номер сезона"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Выдать (give)", value="give"),
    app_commands.Choice(name="Забрать (remove)", value="remove")
])
async def secretpass(
    interaction: discord.Interaction, 
    action: app_commands.Choice[str], 
    username: str, 
    season: str
):
    allowed_roles = ["admin", "stadmin", "curator", "media+", "owner"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    if action.value == 'give':
        desc = f"🎟 Пользователь **{username}** получил **Secret Pass+ Season {season}**!"
        color = discord.Color.purple() 
    else:
        desc = f"🎟 У пользователя **{username}** был забран **Secret Pass+ Season {season}**."
        color = discord.Color.greyple()

    embed = discord.Embed(description=desc, color=color)
    
    await interaction.response.send_message(embed=embed, delete_after=15)


# skin
@bot.tree.command(name="skin", description="Управление скинами через 4-значные ID")
@app_commands.describe(
    action="Выберите: выдать или забрать",
    username="Ник игрока",
    skin_id="Введите 4-значный ID скина"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Выдать (give)", value="give"),
    app_commands.Choice(name="Забрать (remove)", value="remove")
])
async def skin(
    interaction: discord.Interaction, 
    action: app_commands.Choice[str], 
    username: str, 
    skin_id: int
):
    # Проверка прав
    allowed_roles = ["admin", "stadmin", "curator", "owner", "media+"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    # Словарь скинов с 4-значными ID
    skins_dict = {
        # Хэллоуин и Мистика (1000+)
        1001: "Тыквенный Король", 1002: "Призрачный Охотник", 1003: "Костяной Воин", 1004: "Вампир",
        1005: "Чёрный Колдун", 1006: "Тень Леса", 1007: "Проклятый Мечник", 1008: "Лорд Преисподней",
        1009: "Хранитель Мира Теней", 1010: "Туманное Облако",
        
        # Духи и Природа (2000+)
        2001: "Дух Ветра", 2002: "Пещерный Элементаль", 2003: "Светлячок", 2004: "Природный Ассасин",
        2005: "Странник Мхов", 2006: "Зелёный Маг", 2007: "Лесной Охотник", 2008: "Владыка Рощи",
        2009: "Дух Джунглей", 2010: "Иследователь Джунглей", 2011: "Хранитель Листопада",
        
        # Животные и Оборотни (3000+)
        3001: "Юмористический Пудель", 3002: "Злой Пудель-Соперник", 3003: "Альфа Волк Лидер",
        3004: "Фреди Пудель-Оборотень", 3005: "Мистический оборотень", 3006: "Пустынный Лев",
        3007: "Огненный Лев",
        
        # Зима и Праздники (4000+)
        4001: "Таяние зимы", 4002: "Праздничный Фреди", 4003: "Новогодняя елка", 4004: "Пряничный Воин",
        4005: "Снежный Голем Санты", 4006: "Снежный Стражник(type 1)", 4007: "Эльф Мастерской", 
        4008: "Снежный Король", 4009: "Ледяной Страж", 4010: "Снежный Дух", 4011: "Страж Льда", 
        4012: "Снежный Страж(type 2)",
        
        # Люди и Стиль (5000+)
        5001: "Фреди Человек", 5002: "Городской Стиль", 5003: "Фейерверк Человек", 5004: "Путешественник заката",
        5005: "Звезда крикета", 5006: "Звезда Крикета:Элитная Лига", 5007: "Ученик Кубошколы",
        
        # Легендарные и Редкие (9000+)
        9001: "Лунный Защитник", 9002: "Звёздный Странник", 9003: "Песчаный Фантом", 9004: "Небесный Хранитель",
        9005: "Защитник миров", 9006: "Повелитель Нижнего Мира", 9007: "Глубинный Страж", 9008: "Победитель 2025",
        9009: "Юбилейный Защитник", 9010: "Пепельный Скиталец", 9011: "Новолунный Воитель", 9012: "Пробуждающийся Воитель"
    }

    skin_name = skins_dict.get(skin_id)

    if not skin_name:
        await interaction.response.send_message(f"❌ Скин с ID `{skin_id}` не найден в базе данных!", ephemeral=True)
        return

    if action.value == 'give':
        desc = f"👕 Игрок **{username}** получил скин **{skin_name}**!\n🆔 ID: `{skin_id}`"
        color = discord.Color.green()
    else:
        desc = f"🗑️ У игрока **{username}** отозван скин **{skin_name}**.\n🆔 ID: `{skin_id}`"
        color = discord.Color.red()

    embed = discord.Embed(description=desc, color=color)
    embed.set_footer(text="Skin System • Secret World")
    
    await interaction.response.send_message(embed=embed, delete_after=15)



# title
@bot.tree.command(name="title", description="Управление титулами игроков через 4-значные ID")
@app_commands.describe(
    action="Выберите: выдать или забрать",
    username="Ник игрока",
    title_id="Введите 4-значный ID титула"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Выдать (give)", value="give"),
    app_commands.Choice(name="Забрать (remove)", value="remove")
])
async def title(
    interaction: discord.Interaction, 
    action: app_commands.Choice[str], 
    username: str, 
    title_id: int
):
    allowed_roles = ["admin", "stadmin", "curator", "owner", "media+"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    # Словарь титулов с 4-значными ID
    titles_dict = {
        # Зима и Санта (11xx)
        1101: "Секретная миссия санта",
        1102: "Путь спасителя санты",
        1103: "Хранитель Зимней Тайны",

        # Природа и Стихии (22xx)
        2201: "Покоритель Весны",
        2202: "Зов Весны",
        2203: "Хранитель Океана",
        2204: "Охотник за закатами",
        2205: "Покоритель Джунглей",
        2206: "Шёпот Леса",
        2207: "Хранитель Тишины",

        # История и События (33xx)
        3301: "Хранители Руин",
        3302: "Глашатай Перемен",
        3303: "Чемпион 2025",
        3304: "Предсказатель",
        3305: "Легенда Крикета",

        # Редкие и Статус (44xx)
        4401: "Ветеран Секрета",
        4402: "Blockmaster",
        4403: "Пепельный",
        4404: "Тень Новолуния"
    }

    title_name = titles_dict.get(title_id)

    if not title_name:
        await interaction.response.send_message(f"❌ Титул с ID `{title_id}` не найден!", ephemeral=True)
        return

    if action.value == 'give':
        desc = f"🏷️ Игрок **{username}** получил новый титул: **{title_name}**!\n🆔 ID: `{title_id}`"
        color = discord.Color.gold()
    else:
        desc = f"🗑️ У игрока **{username}** был удален титул **{title_name}**.\n🆔 ID: `{title_id}`"
        color = discord.Color.dark_red()

    embed = discord.Embed(description=desc, color=color)
    embed.set_author(name="Title System", icon_url="https://cdn-icons-png.flaticon.com/512/1066/1066371.png")
    
    await interaction.response.send_message(embed=embed, delete_after=15)



# cloak
@bot.tree.command(name="cloak", description="Управление плащами игроков")
@app_commands.describe(
    action="Выберите: выдать или забрать",
    username="Ник игрока",
    cloak_id="Введите 4-значный ID плаща"
)
@app_commands.choices(action=[
    app_commands.Choice(name="Выдать (give)", value="give"),
    app_commands.Choice(name="Забрать (remove)", value="remove")
])
async def cloak(
    interaction: discord.Interaction, 
    action: app_commands.Choice[str], 
    username: str, 
    cloak_id: int
):
    allowed_roles = ["admin", "stadmin", "curator", "owner", "media+"]
    user_roles = [role.name.lower() for role in interaction.user.roles]
    if not any(target in user_roles for target in allowed_roles):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    cloaks_dict = {
        7701: "Чемпион",
        7702: "Тень Предсказателя",
        7703: "Разработчик Secret World",
        7704: "Shadow Wanderer",
        7705: "Плащ Первого Года",
        7706: "Падающие Пиксели",
        7707: "Пепельный Обрывок",
        7708: "Дыхание Дриады",
        7709: "Северная Тень",
        7710: "Ледяной Сигнал",
        7711: "Лунный Щит",
        7712: "Первые Ростки"
    }

    cloak_name = cloaks_dict.get(cloak_id)

    if not cloak_name:
        await interaction.response.send_message(f"❌ Плащ с ID `{cloak_id}` не найден!", ephemeral=True)
        return

    if action.value == 'give':
        desc = f"🧥 Игрок **{username}** надел плащ: **{cloak_name}**!\n🆔 ID: `{cloak_id}`"
        color = discord.Color.blue()
    else:
        desc = f"🗑️ У игрока **{username}** снят плащ **{cloak_name}**.\n🆔 ID: `{cloak_id}`"
        color = discord.Color.dark_grey()

    embed = discord.Embed(description=desc, color=color)
    embed.set_footer(text="Cloak System • Secret World")
    
    await interaction.response.send_message(embed=embed, delete_after=15)











#logs
@bot.event
async def on_interaction(interaction: discord.Interaction):
    # Логируем только слэш-команды
    if interaction.type == discord.InteractionType.application_command:
        
        # 1. Проверка ID канала (берем из конфига)
        log_channel = bot.get_channel(config.LOG_CHANNEL_ID)
        
        # Если бот не нашел канал через bot.get_channel, пробуем через fetch
        if not log_channel:
            try:
                log_channel = await bot.fetch_channel(config.LOG_CHANNEL_ID)
            except:
                print(f"❌ ОШИБКА: Не удалось найти канал логов с ID {config.LOG_CHANNEL_ID}")
                return

        # 2. Собираем аргументы (улучшенный парсер)
        args_list = []
        
        def parse_options(options):
            for opt in options:
                if 'value' in opt:
                    args_list.append(f"**{opt['name']}:** `{opt['value']}`")
                if 'options' in opt: # Если есть подкоманды
                    parse_options(opt['options'])

        if "options" in interaction.data:
            parse_options(interaction.data["options"])

        args_text = "\n".join(args_list) if args_list else "*Нет аргументов*"

        # 3. Создаем Embed
        embed = discord.Embed(
            title="🛠 Выполнена команда",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="Кто:", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
        embed.add_field(name="Команда:", value=f"**/{interaction.command.name}**", inline=True)
        embed.add_field(name="Параметры:", value=args_text, inline=False)
        
        try:
            await log_channel.send(embed=embed)
            print(f"✅ Лог команды /{interaction.command.name} отправлен.")
        except Exception as e:
            print(f"❌ ОШИБКА при отправке лога: {e}")
#синхронизация команд
@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')
    try:
        bot.tree.copy_global_to(guild=MY_GUILD)
        await bot.tree.sync(guild=MY_GUILD)
        print('Команды синхронизированы и готовы к работе.')
    except Exception as e:
        print(f'Ошибка: {e}')

#запуск бота
if __name__ == "__main__":
    keep_alive() 
    bot.run(config.TOKEN)
