import sqlite3
import logging
from datetime import date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- কনফিগারেশন ---
TOKEN = '8798367985:AAG3DY0ZON6PrIzCpM5FmQoPhDL6VCcvaRk'
ADMIN_ID = 8545037231  
GROUP_ID = -1003992993085 
GROUP_LINK = "https://t.me/+39SP_t2J2LNiNWU1" 
ADMIN_CONTACT = "https://t.me/leo20608" 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- ডেটাবেস ফাংশন ---
def init_db():
    conn = sqlite3.connect('bot_manager.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 user_id INTEGER PRIMARY KEY, 
                 credits INTEGER DEFAULT 5, 
                 last_refill DATE,
                 is_vip INTEGER DEFAULT 0,
                 vip_expiry DATE,
                 referred_by INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS videos (v_code TEXT PRIMARY KEY, file_id TEXT, image_id TEXT)''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN vip_expiry DATE")
    except: pass
    conn.commit()
    conn.close()

def get_user_data(user_id):
    today = date.today()
    conn = sqlite3.connect('bot_manager.db'); c = conn.cursor()
    c.execute("SELECT credits, last_refill, is_vip, vip_expiry FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        credits, last_refill, is_vip, vip_expiry = row
        if is_vip == 1 and vip_expiry:
            expiry_date = date.fromisoformat(vip_expiry)
            if today > expiry_date:
                is_vip = 0
                c.execute("UPDATE users SET is_vip = 0, vip_expiry = NULL WHERE user_id = ?", (user_id,))
                conn.commit()
        if str(last_refill) != str(today) and is_vip == 0:
            c.execute("UPDATE users SET credits = 5, last_refill = ? WHERE user_id = ?", (str(today), user_id))
            conn.commit()
            credits = 5
        conn.close()
        return (credits, str(today), is_vip, vip_expiry)
    return None

# --- অ্যাডমিন কমান্ড সমূহ ---
async def make_vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_id = int(context.args[0].replace("/", ""))
        days = int(context.args[1].replace("/", ""))
        expiry_date = date.today() + timedelta(days=days)
        conn = sqlite3.connect('bot_manager.db'); c = conn.cursor()
        c.execute("UPDATE users SET is_vip = 1, vip_expiry = ? WHERE user_id = ?", (str(expiry_date), target_id))
        conn.commit(); conn.close()
        duration = f"{days} দিনের জন্য" if days < 5000 else "লাইফটাইম"
        await update.message.reply_text(f"👑 আইডি <code>{target_id}</code> এখন <b>{duration}</b> VIP!", parse_mode='HTML')
    except:
        await update.message.reply_text("❌ নিয়ম: `/makevip /আইডি /দিন` (যেমন: /makevip /123 /30)")

async def add_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        raw_args = context.args
        target_id = int(raw_args[0].replace("/", ""))
        amount = int(raw_args[1].replace("/", ""))
        conn = sqlite3.connect('bot_manager.db'); c = conn.cursor()
        c.execute("UPDATE users SET credits = credits + ? WHERE user_id = ?", (amount, target_id))
        conn.commit(); conn.close()
        await update.message.reply_text(f"✅ আইডি <code>{target_id}</code> আপডেট হয়েছে।", parse_mode='HTML')
    except: pass

# --- স্টার্ট মেসেজ (নতুন বাটন ফরম্যাট সহ) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today_str = str(date.today())
    conn = sqlite3.connect('bot_manager.db'); c = conn.cursor()
    
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not c.fetchone():
        ref_id = None
        if context.args:
            try:
                ref_id = int(context.args[0])
                if ref_id != user_id:
                    c.execute("UPDATE users SET credits = credits + 2 WHERE user_id=?", (ref_id,))
                    await context.bot.send_message(chat_id=ref_id, text="🎁 অভিনন্দন! আপনার রেফারেল লিঙ্কের মাধ্যমে একজন যুক্ত হয়েছে। **+২ ক্রেডিট** অটোমেটিক যোগ হয়েছে।", parse_mode='HTML')
            except: pass
        c.execute("INSERT INTO users (user_id, credits, last_refill, is_vip) VALUES (?, 5, ?, 0)", (user_id, today_str))
        conn.commit()

    data = get_user_data(user_id)
    conn.close()
    ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start={user_id}"
    
    keyboard = [
        [InlineKeyboardButton("💎 Buy VIP Group (20,000+ Videos)", url=ADMIN_CONTACT)],
        [InlineKeyboardButton("👑 VIP Membership (1 Day - Lifetime)", url=ADMIN_CONTACT)]
    ]

    msg = (f"👋 **স্বাগতম আমাদের বিনোদন জোনে!**\n\n"
           f"📺 আমাদের সকল ভিডিও আপনি পেয়ে যাবেন নিচে দেওয়া মেইন গ্রুপে।\n\n"
           f"✨ আপনার জন্য প্রতিদিন **৫টি ফ্রি ক্রেডিট** বরাদ্দ করা হয়েছে। প্রতি ২৪ ঘণ্টা পর পর এগুলো অটোমেটিক রিনিউ হয়ে যাবে।\n\n"
           f"🎬 **ভিডিও কীভাবে দেখবেন?**\n"
           f"মেইন গ্রুপে গিয়ে ভিডিওর নিচে থাকা **Watch Now** বাটনে ক্লিক করলেই ভিডিওটি এখানে চলে আসবে।\n\n"
           f"🎁 **আরো ক্রেডিট দরকার?**\n"
           f"৫টির বেশি ভিডিও দেখতে চাইলে বন্ধুদের রেফার করুন। প্রতিটি সফল রেফারের জন্য আপনি পাবেন **২ ক্রেডিট** বোনাস।\n\n"
           f"👑 **ভিআইপি মেম্বারশিপ:**\n"
           f"আপনারা চাইলে আপনাদের নিজের ইচ্ছামতো মেম্বারশিপ কিনে নিতে পারেন। ভিআইপি হয়ে গেলে আপনি **আনলিমিটেড ভিডিও** দেখতে পারবেন কোনো লিমিট ছাড়াই এবং কোনো ঝামেলা ছাড়াই।\n\n"
           f"💰 **আপনার ব্যালেন্স:** <b>{'আনলিমিটেড (VIP)' if data[2] == 1 else str(data[0]) + ' ক্রেডিট'}</b> 💎\n"
           f"🆔 **আপনার আইডি:** <code>{user_id}</code>\n"
           f"{'📅 <b>মেয়াদ শেষ:</b> <code>' + str(data[3]) + '</code>' if data[2] == 1 and data[3] else ''}\n\n"
           f"🔗 **আপনার রেফারেল লিঙ্ক:**\n<code>{ref_link}</code>\n\n"
           f"👇👇 **ভিডিও পেতে সবার আগে নিচের গ্রুপে জয়েন করুন** 👇👇\n"
           f"{GROUP_LINK}")
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML', disable_web_page_preview=False)

# --- ভিডিও হ্যান্ডলার ---
async def handle_video_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; user_id = query.from_user.id; v_code = query.data
    data = get_user_data(user_id)
    if data and (data[2] == 1 or data[0] > 0):
        conn = sqlite3.connect('bot_manager.db'); c = conn.cursor()
        if data[2] == 0:
            c.execute("UPDATE users SET credits = credits - 1 WHERE user_id = ?", (user_id,))
        c.execute("SELECT file_id FROM videos WHERE v_code=?", (v_code,))
        video = c.fetchone()
        conn.commit(); conn.close()
        if video:
            await query.answer("ভিডিও পাঠানো হচ্ছে...")
            await context.bot.send_video(chat_id=user_id, video=video[0], caption="🎬 উপভোগ করুন!")
    else:
        await query.answer("❌ আপনার ক্রেডিট শেষ! ভিআইপি মেম্বারশিপ নিন।", show_alert=True)

# --- মিডিয়া সেভ ও পোস্ট (অ্যাডমিন) ---
async def save_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    conn = sqlite3.connect('bot_manager.db'); c = conn.cursor()
    if update.message.video:
        file_id = update.message.video.file_id
        c.execute("SELECT COUNT(*) FROM videos")
        v_code = f"v{c.fetchone()[0] + 1}"
        c.execute("INSERT INTO videos (v_code, file_id) VALUES (?, ?)", (v_code, file_id))
        conn.commit()
        await update.message.reply_text(f"✅ ভিডিও সেভ! কোড: /{v_code}")
    elif update.message.photo:
        image_id = update.message.photo[-1].file_id
        c.execute("SELECT v_code FROM videos WHERE image_id IS NULL ORDER BY v_code DESC LIMIT 1")
        row = c.fetchone()
        if row:
            c.execute("UPDATE videos SET image_id = ? WHERE v_code = ?", (image_id, row[0]))
            conn.commit()
            await update.message.reply_text(f"🖼️ থাম্বনেইল সেট! কোড: /{row[0]}")
    conn.close()

async def post_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        v_code = context.args[0].replace("/", "")
        v_name = " ".join(context.args[1:])
        conn = sqlite3.connect('bot_manager.db'); c = conn.cursor()
        c.execute("SELECT image_id FROM videos WHERE v_code=?", (v_code,))
        res = c.fetchone(); conn.close()
        keyboard = [[InlineKeyboardButton(f"📺 Watch Now", callback_data=v_code)]]
        await context.bot.send_photo(chat_id=GROUP_ID, photo=res[0], caption=f"🎬 **{v_name}**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    except: pass

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", post_cmd))
    app.add_handler(CommandHandler("add", add_credits))
    app.add_handler(CommandHandler("makevip", make_vip))
    app.add_handler(MessageHandler(filters.VIDEO | filters.PHOTO, save_media))
    app.add_handler(CallbackQueryHandler(handle_video_request))
    app.run_polling()
