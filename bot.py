import json
import random
import string

from telegram import *
from telegram.ext import *

from config import *

# ---------- database ----------

def load_users():
    with open("data.json") as f:
        return json.load(f)

def save_users(data):
    with open("data.json","w") as f:
        json.dump(data,f)

def load_videos():
    with open("videos.json") as f:
        return json.load(f)

def save_videos(v):
    with open("videos.json","w") as f:
        json.dump(v,f)

def load_redeem():
    with open("redeem.json") as f:
        return json.load(f)

def save_redeem(r):
    with open("redeem.json","w") as f:
        json.dump(r,f)

# ---------- keyboard ----------

def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["💰 Balance","🎥 Get Video"],
            ["👥 Refer","📊 My Refer"]
        ],
        resize_keyboard=True
    )

# ---------- force join ----------

async def force_join(user_id,bot):

    for ch in FORCE_CHANNELS:

        try:
            member = await bot.get_chat_member(ch,user_id)

            if member.status in ["left","kicked"]:
                return False

        except:
            return False

    return True

# ---------- start ----------

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    uid = str(user.id)

    users = load_users()

    if uid not in users:

        users[uid] = {
            "coins":0,
            "refers":[],
            "used_videos":[]
        }

        save_users(users)

        await context.bot.send_message(
            OWNER_ID,
            f"New User\n{user.first_name}\n{uid}"
        )

        if context.args:

            ref = context.args[0]

            if ref in users and ref != uid:

                users[ref]["coins"] += 10
                users[ref]["refers"].append(uid)

                save_users(users)

                await context.bot.send_message(
                    ref,
                    "🎉 New Referral\n10 coins added"
                )

    if not await force_join(update.effective_user.id,context.bot):

        btn = [
            [InlineKeyboardButton("Join Channel 1",url=f"https://t.me/{FORCE_CHANNELS[0][1:]}")],
            [InlineKeyboardButton("Join Channel 2",url=f"https://t.me/{FORCE_CHANNELS[1][1:]}")]
        ]

        await update.message.reply_text(
            "Join both channels first",
            reply_markup=InlineKeyboardMarkup(btn)
        )

        return

    await update.message.reply_text(
        "Welcome",
        reply_markup=main_keyboard()
    )

# ---------- balance ----------

async def balance(update,context):

    users = load_users()

    uid = str(update.effective_user.id)

    coins = users[uid]["coins"]

    await update.message.reply_text(
        f"Coins : {coins}"
    )

# ---------- refer ----------

async def refer(update,context):

    uid = update.effective_user.id

    link = f"https://t.me/{context.bot.username}?start={uid}"

    await update.message.reply_text(
        f"Your Refer Link\n{link}\n\n10 coins per refer"
    )

# ---------- my refer ----------

async def myrefer(update,context):

    users = load_users()

    uid = str(update.effective_user.id)

    r = len(users[uid]["refers"])

    await update.message.reply_text(
        f"Total Refer : {r}"
    )

# ---------- get video ----------

async def getvideo(update,context):

    users = load_users()
    vids = load_videos()

    uid = str(update.effective_user.id)

    if users[uid]["coins"] < 1:

        await update.message.reply_text(
            "Not enough coins"
        )
        return

    available = [
        v for v in vids
        if v not in users[uid]["used_videos"]
    ]

    if not available:

        await update.message.reply_text(
            "No new videos"
        )
        return

    vid = random.choice(available)

    await update.message.reply_video(vid)

    users[uid]["coins"] -= 1
    users[uid]["used_videos"].append(vid)

    save_users(users)

# ---------- upload ----------

upload_mode = {}

async def upload(update,context):

    if update.effective_user.id != OWNER_ID:
        return

    upload_mode[update.effective_user.id] = True

    await update.message.reply_text(
        "Send your videos"
    )

async def save_video(update,context):

    if update.effective_user.id not in upload_mode:
        return

    vids = load_videos()

    file_id = update.message.video.file_id

    vids.append(file_id)

    save_videos(vids)

# ---------- stats ----------

async def stats(update,context):

    if update.effective_user.id != OWNER_ID:
        return

    users = load_users()

    await update.message.reply_text(
        f"Total Users : {len(users)}"
    )

# ---------- broadcast ----------

async def broadcast(update,context):

    if update.effective_user.id != OWNER_ID:
        return

    text = update.message.text.replace("/broadcast ","")

    users = load_users()

    for uid in users:

        try:
            await context.bot.send_message(uid,text)
        except:
            pass

# ---------- create redeem ----------

async def createredeem(update,context):

    if update.effective_user.id != OWNER_ID:
        return

    coins = int(context.args[0])

    code = ''.join(
        random.choice(string.ascii_uppercase+string.digits)
        for _ in range(8)
    )

    r = load_redeem()

    r[code] = {
        "coins":coins,
        "used":[]
    }

    save_redeem(r)

    await update.message.reply_text(
        f"Code : {code}\nCoins : {coins}"
    )

# ---------- redeem ----------

async def redeemcode(update,context):

    code = context.args[0]

    r = load_redeem()

    users = load_users()

    if code not in r:

        await update.message.reply_text(
            "Invalid code"
        )
        return

    uid = str(update.effective_user.id)

    if uid in r[code]["used"]:

        await update.message.reply_text(
            "Already used"
        )
        return

    coins = r[code]["coins"]

    users[uid]["coins"] += coins

    r[code]["used"].append(uid)

    save_users(users)
    save_redeem(r)

    await update.message.reply_text(
        f"{coins} coins added"
    )

# ---------- handlers ----------

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("upload",upload))
app.add_handler(CommandHandler("stats",stats))
app.add_handler(CommandHandler("broadcast",broadcast))
app.add_handler(CommandHandler("createredeem",createredeem))
app.add_handler(CommandHandler("redeem",redeemcode))

app.add_handler(MessageHandler(filters.VIDEO,save_video))

app.add_handler(MessageHandler(filters.TEXT & filters.Regex("💰 Balance"),balance))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("🎥 Get Video"),getvideo))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("👥 Refer"),refer))
app.add_handler(MessageHandler(filters.TEXT & filters.Regex("📊 My Refer"),myrefer))

app.run_polling()