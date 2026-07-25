import telebot
import sqlite3
import time
import os
import shutil

DB_PATH = "/data/hybrid_bot.db"

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# ================= SECURE SETTINGS =================

TOKEN = os.getenv('BOT_TOKEN', '8629212279:AAF7rgLbU7SLYG64Mli2hupmGZENxbmNg24')  

# ================= OWNER / DEVELOPERS =================

OWNER_ID = 6641244885

DEVELOPERS = [
    OWNER_ID,        # Owner
    # 123456789,     # Future Developer
]

BOT_USERNAME = 'ShadowNetflix_bot' 



# CHANNEL & GROUP DETAILS

CHANNEL_USERNAME = '@Shadow_cipher0'

CHANNEL_URL = 'https://t.me/Shadow_cipher0'

GROUP_USERNAME = '@Shadow_cipher00'

GROUP_URL = 'https://t.me/Shadow_cipher00'

# ================= BOT INITIALIZATION =================

bot = telebot.TeleBot(TOKEN)

admin_states = {}


# ================= DEVELOPER SYSTEM =================

developer_states = {}
developer_points = {}
def is_developer(user_id):
    return user_id in DEVELOPERS

def deny_access(message):
    bot.reply_to(
        message,
        "❌ You are not authorized to use Developer Commands."
    )

def dev_only(func):
    def wrapper(message):
        if not is_developer(message.from_user.id):
            return deny_access(message)
        return func(message)
    return wrapper


# ================= DATABASE SETUP =================

def init_db():

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  first_name TEXT,
                  pending_referrer INTEGER)''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN bonus_points INTEGER DEFAULT 0")
    except:
        pass

    try:
        c.execute("ALTER TABLE users ADD COLUMN last_daily_claim INTEGER DEFAULT 0")
    except:
        pass




    c.execute('''CREATE TABLE IF NOT EXISTS referrals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  referrer_id INTEGER,
                  referred_user_id INTEGER UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS stock 

                 (id INTEGER PRIMARY KEY AUTOINCREMENT, item_type TEXT, item_value TEXT, is_used INTEGER DEFAULT 0)''')

    c.execute('''CREATE TABLE IF NOT EXISTS giveaway_participants
                 (user_id INTEGER PRIMARY KEY)''')

    c.execute('''CREATE TABLE IF NOT EXISTS giveaway_referrals
                 (user_id INTEGER PRIMARY KEY,
                  referral_count INTEGER DEFAULT 0)''')

    conn.commit()

    conn.close()



init_db()



def db_query(query, params=(), fetch=False, fetchall=False):

    conn = sqlite3.connect(DB_PATH)

    c = conn.cursor()

    try:

        c.execute(query, params)

        if fetch: result = c.fetchone()

        elif fetchall: result = c.fetchall()

        else:

            conn.commit()

            result = True

    except Exception as e:

        print(f"DB Error: {e}")

        result = None

    finally:

        conn.close()

    return result



# ================= SUBSCRIPTION CHECKER =================

def is_subscribed(user_id):

    if user_id == OWNER_ID:

        return True

    try:

        for _ in range(2):

            m1 = bot.get_chat_member(CHANNEL_USERNAME, user_id)

            m2 = bot.get_chat_member(GROUP_USERNAME, user_id)

            valid = ['member', 'administrator', 'creator']

            if m1.status in valid and m2.status in valid:

                return True

            time.sleep(0.5)

        return False

    except Exception as e: 

        print(f"Telegram API Connection Alert: {e}")

        return False



# ================= ANTI-BYPASS REFERRED POINTS =================

def get_user_points(user_id):

    referred_users = db_query(
        "SELECT referred_user_id FROM referrals WHERE referrer_id=?",
        (user_id,),
        fetchall=True
    )

    valid_ref_count = 0

    if referred_users:
        for ref in referred_users:
            if is_subscribed(ref[0]):
                valid_ref_count += 1

    referral_points = valid_ref_count * 5

    bonus = db_query(
        "SELECT bonus_points FROM users WHERE user_id=?",
        (user_id,),
        fetch=True
    )

    bonus_points = bonus[0] if bonus else 0

    return referral_points + bonus_points


# ================= MAIN MENU =================

@bot.message_handler(commands=['start'])

def start_menu(message):

    user_id = message.from_user.id

    first_name = message.from_user.first_name

    

    parts = message.text.split()

    referrer_id = None

    if len(parts) > 1:

        try:

            referrer_id = int(parts[1])

            if referrer_id == user_id: referrer_id = None

        except: pass



    user = db_query("SELECT * FROM users WHERE user_id=?", (user_id,), fetch=True)

    if not user:

        db_query("INSERT INTO users (user_id, first_name, pending_referrer) VALUES (?, ?, ?)", (user_id, first_name, referrer_id))

    else:

        if not is_subscribed(user_id) and referrer_id:

            db_query("UPDATE users SET pending_referrer=? WHERE user_id=?", (referrer_id, user_id))



    if not is_subscribed(user_id):

        markup = InlineKeyboardMarkup()

        markup.add(InlineKeyboardButton("📢 Join Official Channel", url=CHANNEL_URL))

        markup.add(InlineKeyboardButton("💬 Join Official Group", url=GROUP_URL))

        markup.add(InlineKeyboardButton("✅ I Have Joined Both", callback_data="check_sub"))

        

        text = (
            f"👋 Hello {first_name}!\n\n"
            "🛑 **ACCESS DENIED**\n\n"
            "To use this bot and claim premium rewards, you must join **both** our Official Channel and Group.\n\n"
            "👇 Click the buttons below to join, then click 'I Have Joined Both' to verify."
        )

        bot.send_message(
            user_id,
            text,
            parse_mode="Markdown",
            reply_markup=markup
        )

        return



    show_main_dashboard(user_id, first_name)



def show_main_dashboard(user_id, first_name):

    points = get_user_points(user_id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎬 Netflix (30 Points)", callback_data="redeem_netflix"))
    markup.add(InlineKeyboardButton("🍿 Prime Video (30 Points)", callback_data="redeem_prime"))
    markup.add(InlineKeyboardButton("🎵 Spotify Premium (30 Points)", callback_data="redeem_spotify"))
    markup.add(InlineKeyboardButton("🎁 Join Giveaway", callback_data="join_giveaway"))
    markup.add(InlineKeyboardButton("🔄 Refresh Points", callback_data="refresh_dash"))
    markup.add(InlineKeyboardButton("🎁 Daily Reward (+2 Points)", callback_data="daily_reward"))

    text = (
        f"👋 **Welcome, {first_name}!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 **Your Balance:** `{points}` Points\n"
        f"👥 **Referral Value:** 5 Points per friend\n"
        "🎯 **Redeem Target:** 30 Points per account\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 **Your Referral Link:**\n`{ref_link}`\n\n"
        "⚠️ *Note: If your friends leave the channel or group, your points will be automatically deducted! (Anti-Cheat Active)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "👇 **Select an item to redeem:**"
    )

    bot.send_message(
        user_id,
        text,
        parse_mode="Markdown",
        reply_markup=markup
    )


# ================= DEVELOPER PANEL =================

@bot.message_handler(commands=['dev'])
@dev_only
def developer_panel(message):

    text = (
    "👨‍💻 Developer Panel\n\n"
    "Available Commands:\n\n"
    "👥 /users\n"
    "➕ /addpoints\n"
    "➖ /removepoints\n"
    "👤 /resetuser\n"
    "🎁 /testredeem\n"
    "🔗 /testreferral\n"
    "📦 /addstock\n"
    "📊 /stats\n"
    "ℹ️ /userinfo\n"
    "💰 /userpoints\n"
    "💾 /backupdb\n"
)

    bot.send_message(message.chat.id, text)
    # ================= ADD POINTS =================

@bot.message_handler(commands=['addpoints'])
@dev_only
def add_points(message):
    msg = bot.reply_to(
        message,
        "👤 Send:\n\n<user_id> <points>\n\nExample:\n6641244885 30"
    )
    bot.register_next_step_handler(msg, process_add_points)


def process_add_points(message):
    try:
        user_id, points = message.text.split()
        user_id = int(user_id)
        points = int(points)

        user = db_query(
            "SELECT bonus_points FROM users WHERE user_id=?",
            (user_id,),
            fetch=True
        )

        if not user:
            return bot.reply_to(message, "❌ User not found.")

        db_query(
            "UPDATE users SET bonus_points = bonus_points + ? WHERE user_id=?",
            (points, user_id)
        )

        bot.reply_to(
            message,
            f"✅ {points} points added successfully."
        )

        try:
            bot.send_message(
                user_id,
                f"🎉 Admin added {points} bonus points.\n\nCurrent Points: {get_user_points(user_id)}"
            )
        except:
            pass

    except:
        bot.reply_to(message, "❌ Invalid format.")

# ================= REMOVE POINTS =================

@bot.message_handler(commands=['removepoints'])
@dev_only
def remove_points(message):
    msg = bot.reply_to(
        message,
        "👤 Send:\n\n<user_id> <points>\n\nExample:\n6641244885 10"
    )
    bot.register_next_step_handler(msg, process_remove_points)


def process_remove_points(message):
    try:
        user_id, points = message.text.split()
        user_id = int(user_id)
        points = int(points)

        user = db_query(
            "SELECT bonus_points FROM users WHERE user_id=?",
            (user_id,),
            fetch=True
        )

        if not user:
            return bot.reply_to(message, "❌ User not found.")

        current_bonus = user[0]

        if current_bonus <= 0:
            return bot.reply_to(message, "⚠️ User has no bonus points.")

        remove = min(points, current_bonus)

        db_query(
            "UPDATE users SET bonus_points = bonus_points - ? WHERE user_id=?",
            (remove, user_id)
        )

        bot.reply_to(
            message,
            f"✅ {remove} points removed successfully."
        )

        try:
            bot.send_message(
                user_id,
                f"⚠️ Admin removed {remove} bonus points.\n\nCurrent Points: {get_user_points(user_id)}"
            )
        except:
            pass

    except:
        bot.reply_to(message, "❌ Invalid format.")

# ================= USER POINTS =================

@bot.message_handler(commands=['userpoints'])
@dev_only
def user_points(message):
    msg = bot.reply_to(
        message,
        "👤 Send User ID\n\nExample:\n6641244885"
    )
    bot.register_next_step_handler(msg, process_user_points)


def process_user_points(message):
    try:
        user_id = int(message.text.strip())

        user = db_query(
            "SELECT bonus_points FROM users WHERE user_id=?",
            (user_id,),
            fetch=True
        )

        if not user:
            return bot.reply_to(message, "❌ User not found.")

        bonus_points = user[0]

        referral_count = db_query(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id=?",
            (user_id,),
            fetch=True
        )[0]

        referral_points = referral_count * 5
        total_points = get_user_points(user_id)

        text = (
            "💰 USER POINTS\n\n"
            f"🆔 User ID: `{user_id}`\n"
            f"👥 Referral Points: {referral_points}\n"
            f"🎁 Bonus Points: {bonus_points}\n"
            f"⭐ Total Points: {total_points}"
        )

        bot.reply_to(message, text, parse_mode="Markdown")

    except:
        bot.reply_to(message, "❌ Invalid User ID.")

# ================= USER INFO =================

@bot.message_handler(commands=['userinfo'])
@dev_only
def user_info(message):
    msg = bot.reply_to(
        message,
        "👤 Send User ID\n\nExample:\n6641244885"
    )
    bot.register_next_step_handler(msg, process_user_info)


def process_user_info(message):
    try:
        user_id = int(message.text.strip())

        user = db_query(
            "SELECT first_name, bonus_points FROM users WHERE user_id=?",
            (user_id,),
            fetch=True
        )

        if not user:
            return bot.reply_to(message, "❌ User not found.")

        ref_count = db_query(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id=?",
            (user_id,),
            fetch=True
        )[0]

        total_points = get_user_points(user_id)

        text = (
            "👤 USER INFORMATION\n\n"
            f"🆔 User ID: `{user_id}`\n"
            f"📝 Name: {user[0]}\n"
            f"💰 Bonus Points: {user[1]}\n"
            f"⭐ Total Points: {total_points}\n"
            f"👥 Referrals: {ref_count}"
        )

        bot.reply_to(message, text, parse_mode="Markdown")

    except:
        bot.reply_to(message, "❌ Invalid User ID.")

# ================= RESET USER =================

@bot.message_handler(commands=['resetuser'])
@dev_only
def reset_user(message):
    msg = bot.reply_to(
        message,
        "👤 Send User ID\n\nExample:\n7883903202"
    )
    bot.register_next_step_handler(msg, process_reset_user)


def process_reset_user(message):
    try:
        user_id = int(message.text.strip())

        db_query(
            "DELETE FROM referrals WHERE referred_user_id=? OR referrer_id=?",
            (user_id, user_id)
        )

        db_query(
            "DELETE FROM giveaway_referrals WHERE user_id=?",
            (user_id,)
        )

        db_query(
            "DELETE FROM giveaway_participants WHERE user_id=?",
            (user_id,)
        )

        db_query(
            "DELETE FROM users WHERE user_id=?",
            (user_id,)
        )

        bot.reply_to(
            message,
            f"✅ User {user_id} has been completely reset.\n\n"
            "Now they can join again using a referral link."
        )

    except:
        bot.reply_to(message, "❌ Invalid User ID.")

# ================= USERS LIST =================

@bot.message_handler(commands=['users'])
@dev_only
def users_list(message):

    users = db_query(
        "SELECT user_id, first_name FROM users ORDER BY rowid DESC",
        fetchall=True
    )

    if not users:
        return bot.reply_to(message, "❌ No users found.")

    markup = InlineKeyboardMarkup(row_width=1)

    for uid, name in users:
        markup.add(
            InlineKeyboardButton(
                f"👤 {name} ({uid})",
                callback_data=f"userinfo_{uid}"
            )
        )

    bot.send_message(
        message.chat.id,
        "👥 Registered Users\n\nSelect a user:",
        reply_markup=markup
    )

# ================= ADMIN CONTROL PANEL =================

@bot.message_handler(commands=['admin'])

def send_admin_panel(message):

    if message.from_user.id != OWNER_ID: return

    show_admin_panel(message.chat.id)



def show_admin_panel(chat_id):

    net_stock = db_query("SELECT COUNT(*) FROM stock WHERE item_type='netflix' AND is_used=0", fetch=True)[0]

    prime_stock = db_query("SELECT COUNT(*) FROM stock WHERE item_type='prime' AND is_used=0", fetch=True)[0]

    spot_stock = db_query("SELECT COUNT(*) FROM stock WHERE item_type='spotify' AND is_used=0", fetch=True)[0]

    total_users = db_query("SELECT COUNT(*) FROM users", fetch=True)[0]

    

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(

        InlineKeyboardButton("➕ Add Netflix", callback_data="admin_add_netflix"),

        InlineKeyboardButton("🗑 Clear Netflix", callback_data="admin_clear_netflix"),

        InlineKeyboardButton("➕ Add Prime", callback_data="admin_add_prime"),

        InlineKeyboardButton("🗑 Clear Prime", callback_data="admin_clear_prime"),

        InlineKeyboardButton("➕ Add Spotify", callback_data="admin_add_spotify"),

        InlineKeyboardButton("🗑 Clear Spotify", callback_data="admin_clear_spotify")

    )

    markup.add(

        InlineKeyboardButton("🎁 Reset Giveaway", callback_data="admin_reset_giveaway"),

        InlineKeyboardButton("📢 Giveaway Broadcast", callback_data="admin_giveaway_broadcast")

    )

    markup.add(
    InlineKeyboardButton("👥 View Participants", callback_data="admin_participants")
   
    )
    
    markup.add(InlineKeyboardButton("📢 Custom Broadcast Message", callback_data="admin_broadcast"))

    markup.add(InlineKeyboardButton("🏆 Leaderboard Stats", callback_data="admin_stats"))

    

    text = (

        "👑 **ADMIN CONTROL DASHBOARD** 👑\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"

        f"👥 **Total Joined Users:** `{total_users}` Users\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"

        f"🎬 **Netflix Stock:** `{net_stock}` Accounts\n"

        f"🍿 **Prime Video Stock:** `{prime_stock}` Accounts\n"

        f"🎵 **Spotify Stock:** `{spot_stock}` Codes/Links\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━\n"

        "👇 **Niche diye gaye buttons se direct manage karein:**"

    )

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)



# ================= CALLBACK & ACTION HANDLERS =================

@bot.callback_query_handler(func=lambda call: True)

def handle_clicks(call):

    user_id = call.from_user.id

    first_name = call.from_user.first_name

   

    if call.data.startswith("userinfo_"):

        target_id = int(call.data.split("_")[1])

        user = db_query(
            "SELECT first_name, bonus_points FROM users WHERE user_id=?",
            (target_id,),
            fetch=True
        )

        if not user:
            bot.answer_callback_query(call.id, "❌ User not found.")
            return

        ref_count = db_query(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id=?",
            (target_id,),
            fetch=True
        )[0]

        total_points = get_user_points(target_id)

        text = (
            "👤 USER INFORMATION\n\n"
            f"🆔 User ID: `{target_id}`\n"
            f"📝 Name: {user[0]}\n"
            f"💰 Bonus Points: {user[1]}\n"
            f"⭐ Total Points: {total_points}\n"
            f"👥 Referrals: {ref_count}"
        )

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )

        return

    # 👇 YE LINE PAHLE SE HAI, ISKO MAT HATANA
    if call.data == "check_sub":    


        if is_subscribed(user_id):

            try: bot.delete_message(call.message.chat.id, call.message.message_id)

            except: pass

            

            user_data = db_query("SELECT pending_referrer FROM users WHERE user_id=?", (user_id,), fetch=True)

            if user_data and user_data[0]:

                referrer_id = user_data[0]

                try:

                    db_query("INSERT INTO referrals (referrer_id, referred_user_id) VALUES (?, ?)", (referrer_id, user_id))
                    db_query("""
INSERT INTO giveaway_referrals (user_id, referral_count)
VALUES (?, 1)
ON CONFLICT(user_id)
DO UPDATE SET referral_count = referral_count + 1
""", (referrer_id,))

                    bot.send_message(referrer_id, "🎉 **New Refer Point Added!**\nSomeone joined genuinely using your link (+5 Points).", parse_mode="Markdown")

                except: pass

                db_query("UPDATE users SET pending_referrer = NULL WHERE user_id=?", (user_id,))

            show_main_dashboard(user_id, first_name)

        else: 

            bot.answer_callback_query(call.id, "⚠️ You must join BOTH the channel and the group first!", show_alert=True)



    elif call.data == "refresh_dash":

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        show_main_dashboard(user_id, first_name)

    elif call.data == "daily_reward":

        now = int(time.time())

        data = db_query(
            "SELECT last_daily_claim FROM users WHERE user_id=?",
            (user_id,),
            fetch=True
        )

        last_claim = data[0] if data else 0

        if now - last_claim < 86400:
            remaining = 86400 - (now - last_claim)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60

            bot.answer_callback_query(
                call.id,
                f"⏳ You already claimed today's reward.\n\nTry again in {hours}h {minutes}m.",
                show_alert=True
            )
            return

        db_query(
            "UPDATE users SET bonus_points = bonus_points + 2, last_daily_claim=? WHERE user_id=?",
            (now, user_id)
        )

        bot.answer_callback_query(
            call.id,
            "🎉 Daily Reward Claimed!\n\n+2 Bonus Points Added.",
            show_alert=True
        )

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        show_main_dashboard(user_id, first_name)
        
    elif call.data == "join_giveaway":

        if not is_subscribed(user_id):
            return bot.answer_callback_query(
                call.id,
                "⚠️ Join channel and group first!",
                show_alert=True
                
            )
            
        already = db_query(
            "SELECT 1 FROM giveaway_participants WHERE user_id=?",
            (user_id,),
            fetch=True
        )

        if already:
            return bot.answer_callback_query(
                call.id,
                "✅ You are already in the giveaway!",
                show_alert=True
            )
        data = db_query(
            "SELECT referral_count FROM giveaway_referrals WHERE user_id=?",
            (user_id,),
            fetch=True
        )

        if not data or data[0] < 1:
            return bot.answer_callback_query(
                call.id,
                "❌ You must complete 1 valid referral before joining this giveaway!",
                show_alert=True
            )

        try:
            db_query(
                "INSERT INTO giveaway_participants (user_id) VALUES (?)",
                (user_id,)
            )

            db_query(
                "UPDATE giveaway_referrals SET referral_count = 0 WHERE user_id=?",
                (user_id,)
            )

            bot.answer_callback_query(
                call.id,
                "🎉 Successfully joined the giveaway!",
                show_alert=True
            )

        except:
            bot.answer_callback_query(
                call.id,
                "✅ You are already in the giveaway!",
                show_alert=True
            )



    elif call.data.startswith("redeem_"):

        if not is_subscribed(user_id):

            bot.answer_callback_query(call.id, "⚠️ Access Denied! You left the group/channel.", show_alert=True)

            return

            

        item_type = call.data.replace("redeem_", "")

        points = get_user_points(user_id)

        

        if points < 30:

            bot.answer_callback_query(call.id, f"⚠️ You need 30 points to redeem! (Current: {points})", show_alert=True)

            return

            

        stock_data = db_query("SELECT id, item_value FROM stock WHERE item_type=? AND is_used=0 LIMIT 1", (item_type,), fetch=True)

        if stock_data:

            item_id, item_val = stock_data

            db_query("UPDATE stock SET is_used=1 WHERE id=?", (item_id,))

            

            referred_users = db_query("SELECT referred_user_id FROM referrals WHERE referrer_id=? LIMIT 5", (user_id,), fetchall=True)

            for ref in referred_users:

                db_query("DELETE FROM referrals WHERE referred_user_id=?", (ref[0],))

                

            bot.send_message(user_id, f"🎉 **REDEEM SUCCESSFUL!** 🎉\n\n🎁 **Your {item_type.capitalize()} Reward:**\n`{item_val}`\n\nThank you for inviting real members! ❤️", parse_mode="Markdown")

            bot.answer_callback_query(call.id, "Reward Claimed!", show_alert=True)

        else:

            bot.answer_callback_query(call.id, f"⚠️ {item_type.capitalize()} is currently out of stock! Admin will restock soon.", show_alert=True)



    elif call.data.startswith("admin_"):

        if user_id != OWNER_ID: return

        action = call.data.replace("admin_", "")

        

        if action.startswith("add_"):

            item_type = action.replace("add_", "")

            admin_states[user_id] = f"upload_{item_type}"

            msg = bot.send_message(user_id, f"📥 **Send Stock Data:**\nFormat for {item_type.capitalize()}:\nSend text data (e.g. `email:pass` or `code`). Type `/cancel` to abort.")

            bot.register_next_step_handler(msg, process_stock_upload)

            

        elif action.startswith("clear_"):

            item_type = action.replace("clear_", "")

            db_query("DELETE FROM stock WHERE item_type=? AND is_used=0", (item_type,))

            bot.answer_callback_query(call.id, f"🗑️ Unused {item_type.capitalize()} stock cleared!", show_alert=True)

            try: bot.delete_message(call.message.chat.id, call.message.message_id)

            except: pass

            show_admin_panel(user_id)

            

        elif action == "reset_giveaway":

            db_query("DELETE FROM giveaway_participants")
            db_query("DELETE FROM giveaway_referrals")

            bot.answer_callback_query(call.id, "✅ Giveaway list reset! Fresh start.", show_alert=True)

            try: bot.delete_message(call.message.chat.id, call.message.message_id)

            except: pass

            show_admin_panel(user_id)

            

        elif action == "giveaway_broadcast":

            admin_states[user_id] = "giveaway_broadcasting"

            msg = bot.send_message(user_id, "📢 **GIVEAWAY BROADCAST MODE**\nSend content for giveaway participants. Type `/cancel` to abort.")

            bot.register_next_step_handler(msg, process_giveaway_broadcast)

            

        elif action == "broadcast":

            admin_states[user_id] = "broadcasting"

            msg = bot.send_message(
                user_id,
                "📢 **BROADCAST MODE**\nSend any text, photo, video or message you want to blast to all users. Type `/cancel` to abort."
            )

            bot.register_next_step_handler(msg, process_broadcast)

        elif action == "participants":

            participants = db_query("""
                SELECT giveaway_participants.user_id, users.first_name
                FROM giveaway_participants
                LEFT JOIN users
                ON giveaway_participants.user_id = users.user_id
                ORDER BY giveaway_participants.rowid DESC
            """, fetchall=True)

            if not participants:
                return bot.send_message(user_id, "❌ No giveaway participants yet.")

            text = "🎉 **GIVEAWAY PARTICIPANTS**\n"
            text += "━━━━━━━━━━━━━━━━━━━━━━\n\n"

            for i, (uid, name) in enumerate(participants, 1):
                text += f"{i}. 👤 {name or 'Unknown'}\n🆔 `{uid}`\n\n"

            text += f"━━━━━━━━━━━━━━━━━━━━━━\n👥 Total Participants: {len(participants)}"

            bot.send_message(user_id, text, parse_mode="Markdown")

        elif action == "stats":

            users_list = db_query(
                "SELECT user_id, first_name FROM users",
                fetchall=True
            )

            leaderboard = []

            for u in users_list:

                pts = get_user_points(u[0])

                ref_count = db_query(
                    "SELECT COUNT(*) FROM referrals WHERE referrer_id=?",
                    (u[0],),
                    fetch=True
                )[0]

                if pts > 0:
                    leaderboard.append((u[1], pts, ref_count))

            leaderboard.sort(key=lambda x: x[1], reverse=True)
            leaderboard = leaderboard[:10]

            text = "🏆 **TOP 10 LEADERBOARD** 🏆\n━━━━━━━━━━━━━━━━━━━━━━━━\n"

            if leaderboard:

                for i, (name, pts, ref_count) in enumerate(leaderboard, 1):
                    text += f"{i}. {name} — **{pts} Points** ({ref_count} Invites)\n"

            else:
                text += "No points recorded yet."

            bot.send_message(user_id, text, parse_mode="Markdown")



# ================= ADMIN INPUT STEPS =================

def process_stock_upload(message):

    user_id = message.from_user.id

    if message.text == '/cancel':

        if user_id in admin_states: del admin_states[user_id]

        return bot.reply_to(message, "❌ Upload cancelled.")

        

    if user_id not in admin_states or not admin_states[user_id].startswith("upload_"):

        return

        

    item_type = admin_states[user_id].replace("upload_", "")

    item_val = message.text.strip() if message.text else ""

    

    if not item_val:

        return bot.reply_to(message, "⚠️ Invalid input.")

        

    if db_query("INSERT INTO stock (item_type, item_value) VALUES (?, ?)", (item_type, item_val)):

        bot.reply_to(message, f"✅ Successfully uploaded to **{item_type.capitalize()}** stock!")

    else:

        bot.reply_to(message, "❌ Database error.")

        

    if user_id in admin_states: del admin_states[user_id]

    show_admin_panel(user_id)



def process_giveaway_broadcast(message):

    user_id = message.from_user.id

    if message.text == '/cancel':

        if user_id in admin_states: del admin_states[user_id]

        return bot.reply_to(message, "❌ Broadcast cancelled.")

        

    participants = db_query("SELECT user_id FROM giveaway_participants", fetchall=True)

    if not participants: 

        if user_id in admin_states: del admin_states[user_id]

        return bot.reply_to(message, "⚠️ Giveaway list khali hai!")

        

    bot.reply_to(message, f"⏳ Broadcasting to {len(participants)} giveaway participants...")

    success, fail = 0, 0

    

    for user in participants:

        try:

            bot.copy_message(chat_id=user[0], from_chat_id=message.chat.id, message_id=message.message_id)

            success += 1

            time.sleep(0.05)

        except Exception: 

            fail += 1

            

    bot.send_message(OWNER_ID, f"✅ **GIVEAWAY BROADCAST COMPLETE!**\nDelivered: `{success}`\nFailed/Blocked: `{fail}`")

    if user_id in admin_states: del admin_states[user_id]

    show_admin_panel(user_id)



def process_broadcast(message):

    user_id = message.from_user.id

    if message.text == '/cancel':

        if user_id in admin_states: del admin_states[user_id]

        return bot.reply_to(message, "❌ Broadcast cancelled.")

        

    users = db_query("SELECT user_id FROM users", fetchall=True)

    if not users: 

        if user_id in admin_states: del admin_states[user_id]

        return bot.reply_to(message, "⚠️ No users found in database.")

        

    bot.reply_to(message, f"⏳ Broadcasting to {len(users)} users. Please wait...")

    success, fail = 0, 0

    

    for user in users:

        try:

            bot.copy_message(chat_id=user[0], from_chat_id=message.chat.id, message_id=message.message_id)

            success += 1

            time.sleep(0.05)

        except Exception: 

            fail += 1

            

    bot.send_message(OWNER_ID, f"✅ **BROADCAST COMPLETE!**\nDelivered: `{success}`\nFailed/Blocked: `{fail}`")

    if user_id in admin_states: del admin_states[user_id]

    show_admin_panel(user_id)

# ================= DATABASE BACKUP =================

@bot.message_handler(commands=['backupdb'])
@dev_only
def backup_database(message):

    user_id = message.from_user.id

    try:
        backup_file = "/data/hybrid_bot_backup.db"

        shutil.copy(DB_PATH, backup_file)

        with open(backup_file, "rb") as db:
            bot.send_document(
                user_id,
                db,
                caption="✅ Database Backup"
            )

    except Exception as e:
        bot.reply_to(
            message,
            f"❌ Backup Failed!\n\n{e}"
        )

print("🔥 SHADOW FREE REWARDS BOT IS RUNNING ON RAILWAY! 🔥")

bot.infinity_polling(timeout=20, long_polling_timeout=20)
