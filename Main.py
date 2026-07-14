import os
import telebot
from telebot import types
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone

# API Token (use @botfather to get your API Token)
# SECURE PRACTICE FOR GITHUB: Loaded securely from environment variables.
API_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'your_bot_token_here') 

# Admin IDs (use @userinfobot to find your Telegram ID)
# SECURE PRACTICE: Input actual numeric IDs here (e.g., [123456789]) or set them via environments.
ADMIN_IDS = [int(admin_id) for admin_id in os.environ.get('ADMIN_IDS', '123456789').split(',')] if os.environ.get('ADMIN_IDS') else [123456789]  

bot = telebot.TeleBot(API_TOKEN)
DB_NAME = 'game_bet.db'

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ⏰ Timezone Helper: Calculates target local time independent of the host server location.
# To shift the bot's standard operating time to another timezone, adjust timedelta hours/minutes below.
def get_timezone_now():
    target_tz = timezone(timedelta(hours=3, minutes=30))  # Default set to UTC+3:30
    return datetime.now(target_tz).replace(tzinfo=None)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        balance INTEGER DEFAULT 1500,
                        last_bet_time TEXT,
                        total_bets_count INTEGER DEFAULT 0,
                        total_profit INTEGER DEFAULT 0)''')
    
    # Matches table
    cursor.execute('''CREATE TABLE IF NOT EXISTS matches (
                        match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        team1 TEXT,
                        team2 TEXT,
                        odds_1 REAL,
                        odds_X REAL,
                        odds_2 REAL,
                        start_time TEXT,
                        status TEXT DEFAULT 'upcoming',
                        result TEXT)''')
    
    # Bets table
    cursor.execute('''CREATE TABLE IF NOT EXISTS bets (
                        bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        match_id INTEGER,
                        prediction TEXT,
                        amount INTEGER,
                        exact_score TEXT DEFAULT '-',
                        scorers TEXT DEFAULT '-',
                        timestamp TEXT,
                        win_base INTEGER DEFAULT 0,
                        win_exact INTEGER DEFAULT 0,
                        win_scorer INTEGER DEFAULT 0,
                        UNIQUE(user_id, match_id))''')
    
    # 🏦 Loans table
    cursor.execute('''CREATE TABLE IF NOT EXISTS loans (
                        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        amount_given INTEGER DEFAULT 1000,
                        amount_due INTEGER DEFAULT 1250,
                        amount_paid INTEGER DEFAULT 0,
                        taken_at TEXT,
                        status TEXT DEFAULT 'active')''')
    
    # 🛡 DB Migrations layer for pre-existing databases (safely appends columns)
    try:
        cursor.execute("ALTER TABLE bets ADD COLUMN win_base INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE bets ADD COLUMN win_exact INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    try:
        cursor.execute("ALTER TABLE bets ADD COLUMN win_scorer INTEGER DEFAULT 0")
    except sqlite3.OperationalError: pass
    
    conn.commit()
    conn.close()

init_db()

def register_user(user_id, username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if not cursor.fetchone():
        now_str = get_timezone_now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO users (user_id, username, balance, last_bet_time) VALUES (?, ?, ?, ?)",
                       (user_id, username, 1500, now_str))
        conn.commit()
    else:
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()
    conn.close()

def main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("Help 📜", "Rules ⚖️")
    markup.row("Matches 📅", "Leaderboard 🏆")
    markup.row("About Bot ℹ️", "Wallet 💰")
    return markup

# --- General Commands ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    register_user(message.from_user.id, message.from_user.username)
    welcome_text = "Hello! Welcome to the Game Betting Bot! ⚽️\n\nThe button menu is now active. You can also view the full list of commands using /help."
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())
    send_help(message)
    
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🎮 <b>Full Bot Commands Guide</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🚀 <b>Registration & Getting Started:</b>\n"
        "🔹 Receive 1500 starting gift Tokens\n"
        "➡️ /start\n\n"
        "💰 <b>Finance & Account Info:</b>\n"
        "🔹 View current wallet balance\n"
        "➡️ /wallet\n\n"
        "📊 <b>Performance & Stats:</b>\n"
        "🔹 Wins, losses, and total profit of yourself or others (tag/reply)\n"
        "➡️ /stats @username\n\n"
        "💸 <b>Transfer Funds:</b>\n"
        "🔹 Transfer Tokens to others using username, tag, or reply\n"
        "➡️ <code>/transfer username 400</code>\n\n"
        "⚽️ <b>View Tournament Matches:</b>\n"
        "🔹 Upcoming matches and betting odds (paginated)\n"
        "➡️ /matches\n\n"
        "🗄 <b>Match Archive:</b>\n"
        "🔹 Full match history of all tournament games\n"
        "➡️ /all_matches\n\n"
        "📋 <b>My Bets:</b>\n"
        "🔹 History, status, and profits of your own bets (paginated)\n"
        "➡️ /my_bets\n\n"
        "🔍 <b>Check Competitors:</b>\n"
        "🔹 View active and past bets of another user via tag or reply\n"
        "➡️ /bets @username\n\n"
        "👥 <b>Group Radar:</b>\n"
        "🔹 View the latest bets placed by other members in the group\n"
        "➡️ /all_bets\n\n"
        "🏆 <b>Top Scorers & Awards:</b>\n"
        "🔹 Standings of Ballon d'Or and Golden Boot contenders\n"
        "➡️ /awards\n\n"
        "🥇 <b>Leaderboard:</b>\n"
        "🔹 Rankings of top tournament contenders based on total assets (paginated)\n"
        "➡️ /leaderboard\n\n"
        "📜 <b>Game Rules:</b>\n"
        "🔹 Tournament guide, rules, and economy system\n"
        "➡️ /rule\n\n"
        "✍️ <b>Bet Management Commands:</b>\n"
        "🔸 Place a new bet on matches:\n"
        "➡️ <code>/bet match_id 1 500</code>\n\n"
        "🔸 Edit a placed bet (before match starts):\n"
        "➡️ <code>/edit_bet match_id 1 500</code>\n\n"
        "🔸 Cancel a bet and refund funds (before match starts):\n"
        "➡️ <code>/cancel_bet match_id</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏦 <b>Bank & Loan System:</b>\n"
        "💵 <code>/get_loan</code> ──> Get an instant loan (1000 Tokens)\n"
        "💳 <code>/pay_loan [amount]</code> ──> Pay off loan installments or settle in full\n"
        "📈 <code>/loan_status</code> ──> View outstanding debt, receipt time, and loan details\n"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")

@bot.message_handler(commands=['rule'])
def send_rule(message):
    rule_text = (
        "⚖️ <b>Game Rules & Economy System</b>\n\n"
        "1️⃣ Starting Capital & Goal\n"
        "Every player starts with 1500 Tokens. The final winner is the player with the highest balance at the end of the tournament.\n\n"
        "2️⃣ Bet Limits\n"
        "You can only place one bet per match. Placing two concurrent bets on a single match is not allowed.\n\n"
        "3️⃣ Minimum Bet\n"
        "The minimum amount to place a bet on any match is 150 Tokens.\n\n"
        "4️⃣ Inactivity Fine\n"
        "If 96 hours pass since your last activity, the bot will fine you 250 Tokens.\n\n"
        "5️⃣ Single Message Rule\n"
        "Your bet must be sent strictly in a single, accurate message. Edited messages are not processed for registering new bets.\n\n"
        "6️⃣ Time Window\n"
        "You can place bets from 24 hours before a match up until the exact start time. Betting locks as soon as the match begins.\n\n"
        "7️⃣ Escrow System\n"
        "The bet amount is temporarily deducted and locked from your wallet so that your total active bets do not exceed your total assets.\n\n"
        "8️⃣ Loan and Transfer System\n"
        "If you run out of funds, you can receive transfers from other players. Transfers are supported via ID, reply, and username tag.\n\n"
        "9️⃣ Special Awards\n"
        "The Golden Boot award goes to the user with the most correct bets, and the Ballon d'Or is awarded for the highest net profit of the tournament.\n\n"
        "🔟 Optional Bonuses\n"
        "In addition to predicting the winner, you can predict the exact score for a 25% profit bonus, and named scorers for a 10% profit bonus per correct scorer.\n\n"
        "🏦 <b>Loan System Rules & Regulations:</b>\n\n"
        "1. Every user is allowed to take a loan <b>only 2 times</b> in total.\n"
        "2. Taking a loan adds <b>1000 Tokens</b> to your balance, but you must repay <b>1250 Tokens</b>.\n"
        "3. You cannot have 2 active loans simultaneously; the first loan must be fully settled before you can take the second.\n"
        "4. <b>Repayment deadline is 5 days.</b> During these 5 days, you can repay your debt at any time in installments or as a lump sum.\n"
        "5. The system will not allow you to pay more than your outstanding debt.\n"
        "6. ⚠️ <b>CRITICAL:</b> If not settled manually within 5 days, the system will automatically deduct the remaining debt from your balance (even if it makes your balance negative).\n\n"
        "📢 <b>Breaking News Rule</b>\n"
        "Users placing a heavy bet of 1000 Tokens or more on a single match will trigger an automated public announcement with banter in the group!"
    )
    bot.send_message(message.chat.id, rule_text, parse_mode="HTML")

def send_about(message):
    about_text = (
        "ℹ️ <b>About the Game Betting Bot</b>\n\n"
        "This bot fully automates the management of your real or simulated football matches.\n"
        "Calculation of odds, scorer reward bonuses, and exact score settlements are all processed programmatically."
    )
    bot.send_message(message.chat.id, about_text, parse_mode="HTML")

@bot.message_handler(commands=['helpadmin'])
def send_help_admin(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    admin_text = (
        "👑 <b>Admin Management Commands</b>\n\n"
        "Register a new match in the tournament system:\n"
        "<code>/add_match team1 team2 2.1 3.5 2.8 2026-06-15 22:30</code>\n\n"
        "Settle a match and credit profits including scorer and exact score bonuses:\n"
        "<code>/settle_match match_id 1 2-1 messi</code>\n\n"
        "Recalculate/Revise a previously settled match result dynamically:\n"
        "<code>/resettle_match match_id X 1-1 -</code>\n\n"
        "Completely remove a match and auto-refund staked capital tokens:\n"
        "<code>/delete_match match_id</code>\n\n"
        "Adjust or manipulate specific user balances:\n"
        "<code>/admin give/take user_id amount</code>\n\n"
        "Gift tokens to all registered users simultaneously:\n"
        "<code>/giveall amount</code>"
    )
    bot.send_message(message.chat.id, admin_text, parse_mode="HTML")

# --- Pagination Views Logic Helpers ---

def send_matches_page(chat_id, page=1, message_id=None):
    items_per_page = 5
    offset = (page - 1) * items_per_page
    conn = get_db()
    cursor = conn.cursor()
    
    matches = cursor.execute("SELECT * FROM matches WHERE status = 'upcoming' ORDER BY match_id DESC LIMIT ? OFFSET ?", (items_per_page, offset)).fetchall()
    total_items = cursor.execute("SELECT COUNT(*) FROM matches WHERE status = 'upcoming'").fetchone()[0]
    conn.close()
    
    if not matches and page == 1:
        msg_none = "📅 <b>No upcoming matches are currently registered.</b>"
        if message_id:
            bot.edit_message_text(msg_none, chat_id, message_id, parse_mode="HTML")
        else:
            bot.send_message(chat_id, msg_none, parse_mode="HTML")
        return
        
    text = f"📅 <b>Upcoming Matches and Odds (Page {page}):</b>\n\n"
    for m in matches:
        text += (f"⚽️ <b>Match ID: {m['match_id']}</b>\n"
                 f"1️⃣ <b>{m['team1']}</b> ── 🔹 Odds: {m['odds_1']}\n"
                 f"❌ <b>Draw (X)</b> ── 🔹 Odds: {m['odds_X']}\n"
                 f"2️⃣ <b>{m['team2']}</b> ── 🔹 Odds: {m['odds_2']}\n"
                 f"⏰ Start Time: {m['start_time']}\n"
                 f"───────────────────\n")
                 
    markup = types.InlineKeyboardMarkup()
    buttons = []
    if page > 1:
        buttons.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"matches:{page-1}"))
    if total_items > offset + items_per_page:
        buttons.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"matches:{page+1}"))
    if buttons:
        markup.add(*buttons)
        
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        except Exception: pass
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

def send_my_bets_page(chat_id, user_id, page=1, message_id=None):
    items_per_page = 5
    offset = (page - 1) * items_per_page
    conn = get_db()
    cursor = conn.cursor()
    
    bets = cursor.execute("""
        SELECT b.*, m.team1, m.team2, m.status, m.result 
        FROM bets b 
        JOIN matches m ON b.match_id = m.match_id 
        WHERE b.user_id = ? 
        ORDER BY b.bet_id DESC LIMIT ? OFFSET ?
    """, (user_id, items_per_page, offset)).fetchall()
    
    total_items = cursor.execute("SELECT COUNT(*) FROM bets WHERE user_id = ?", (user_id,)).fetchone()[0]
    conn.close()
    
    if not bets and page == 1:
        msg_none = "📋 <b>No bets have been recorded yet.</b>"
        if message_id:
            bot.edit_message_text(msg_none, chat_id, message_id, parse_mode="HTML")
        else:
            bot.send_message(chat_id, msg_none, parse_mode="HTML")
        return
        
    text = f"📋 <b>Betting History File (Page {page}):</b>\n\n"
    for b in bets:
        text += (f"⚔️ <b>{b['team1']} - {b['team2']}</b>\n"
                 f"💰 Bet Amount: {b['amount']} Tokens | Prediction: [{b['prediction']}]\n"
                 f"🎯 Exact Score: {b['exact_score']} | ⚽️ Scorers: {b['scorers']}\n")
        if b['status'] == 'upcoming':
            text += "⏳ Status: Pending Match\n"
        elif b['status'] == 'ongoing':
            text += "🏃‍♂️ Status: In Progress\n"
        else:
            total_win = b['win_base'] + b['win_exact'] + b['win_scorer']
            if total_win > 0:
                text += f"✅ Status: Won (+{total_win} Tokens)\n"
            else:
                text += "❌ Status: Lost\n"
        text += "───────────────────\n"
        
    markup = types.InlineKeyboardMarkup()
    buttons = []
    if page > 1:
        buttons.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"mybets:{page-1}"))
    if total_items > offset + items_per_page:
        buttons.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"mybets:{page+1}"))
    if buttons:
        markup.add(*buttons)
        
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        except Exception: pass
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

def send_leaderboard_page(chat_id, page=1, message_id=None):
    items_per_page = 10
    offset = (page - 1) * items_per_page
    conn = get_db()
    cursor = conn.cursor()
    
    users = cursor.execute("SELECT * FROM users ORDER BY balance DESC LIMIT ? OFFSET ?", (items_per_page, offset)).fetchall()
    total_items = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    
    if not users and page == 1:
        msg_none = "🏆 <b>Leaderboard data is currently empty.</b>"
        if message_id:
            bot.edit_message_text(msg_none, chat_id, message_id, parse_mode="HTML")
        else:
            bot.send_message(chat_id, msg_none, parse_mode="HTML")
        return
        
    text = f"🏆 <b>Tournament Leaderboard Rankings (Page {page}):</b>\n\n"
    for idx, u in enumerate(users, start=offset + 1):
        username_str = f"@{u['username']}" if u['username'] else f"User {u['user_id']}"
        text += f"{idx}. <b>{username_str}</b> ── 💰 {u['balance']} Tokens\n"
    text += "\n───────────────────\n"
        
    markup = types.InlineKeyboardMarkup()
    buttons = []
    if page > 1:
        buttons.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"leaderboard:{page-1}"))
    if total_items > offset + items_per_page:
        buttons.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"leaderboard:{page+1}"))
    if buttons:
        markup.add(*buttons)
        
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup, parse_mode="HTML")
        except Exception: pass
    else:
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        data = call.data.split(':')
        action = data[0]
        page = int(data[1])
        
        if action == "matches":
            send_matches_page(call.message.chat.id, page=page, message_id=call.message.message_id)
        elif action == "mybets":
            send_my_bets_page(call.message.chat.id, call.from_user.id, page=page, message_id=call.message.message_id)
        elif action == "leaderboard":
            send_leaderboard_page(call.message.chat.id, page=page, message_id=call.message.message_id)
            
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Error in callback query handler: {e}")

# --- Wallet & Transfer Sub-Modules ---

@bot.message_handler(commands=['wallet'])
def show_wallet(message):
    register_user(message.from_user.id, message.from_user.username)
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
    conn.close()
    
    text = (f"💰 <b>Your Wallet Portfolio Status</b>\n\n"
            f"👤 User: @{user['username'] if user['username'] else message.from_user.id}\n"
            f"💵 Net Available Balance: <b>{user['balance']} Tokens</b>")
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['transfer'])
def transfer_money(message):
    args = message.text.split()
    if len(args) < 3 and not message.reply_to_message:
        return bot.reply_to(message, "🔧 <b>Usage Framework:</b>\n<code>/transfer [username/tag/ID] [amount]</code>\nOr via replying to a user's text message: <code>/transfer [amount]</code>", parse_mode="HTML")
    
    conn = get_db()
    cursor = conn.cursor()
    
    sender_id = message.from_user.id
    register_user(sender_id, message.from_user.username)
    sender = cursor.execute("SELECT * FROM users WHERE user_id = ?", (sender_id,)).fetchone()
    
    try:
        if message.reply_to_message:
            if message.reply_to_message.from_user.is_bot:
                conn.close()
                return bot.reply_to(message, "❌ Transfer operations toward bots are strictly prohibited.")
            amount = int(args[1])
            target_id = message.reply_to_message.from_user.id
            target_username = message.reply_to_message.from_user.username
        else:
            target_input = args[1].replace('@', '')
            amount = int(args[2])
            
            if target_input.isdigit():
                target_id = int(target_input)
                target_user = cursor.execute("SELECT * FROM users WHERE user_id = ?", (target_id,)).fetchone()
            else:
                target_user = cursor.execute("SELECT * FROM users WHERE username = ?", (target_input,)).fetchone()
                
            if not target_user:
                conn.close()
                return bot.reply_to(message, "❌ The specified target recipient user does not exist inside our system records.")
            target_id = target_user['user_id']
            target_username = target_user['username']
            
        if amount <= 0:
            conn.close()
            return bot.reply_to(message, "❌ Transfer values must stay strictly above 0.")
            
        if sender['balance'] < amount:
            conn.close()
            return bot.reply_to(message, "❌ Action failed. Insufficient funds inside your wallet container.")
            
        if sender_id == target_id:
            conn.close()
            return bot.reply_to(message, "❌ Loop error! You cannot perform transfer routines to your own account.")
            
        register_user(target_id, target_username)
        
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
        conn.commit()
        
        bot.reply_to(message, f"✅ Successfully wired <b>{amount} Tokens</b> to target recipient accounts.", parse_mode="HTML")
        try:
            bot.send_message(target_id, f"💰 You received a wallet package containing <b>{amount} Tokens</b> from @{sender['username'] if sender['username'] else sender_id}!", parse_mode="HTML")
        except Exception: pass
    except ValueError:
        bot.reply_to(message, "❌ Parsing mismatch error. Ensure token parameters are formatted as integers.")
    finally:
        conn.close()

# --- Core Betting Placement Engines ---

@bot.message_handler(commands=['bet'])
def place_bet_command(message):
    register_user(message.from_user.id, message.from_user.username)
    args = message.text.split()
    if len(args) < 4:
        return bot.reply_to(message, "🔧 <b>Usage Framework Architecture:</b>\n<code>/bet [match_id] [1/X/2] [amount] [exact_score optional: 2-1] [scorers optional: messi,villa]</code>", parse_mode="HTML")
        
    try:
        match_id = int(args[1])
        prediction = args[2].upper()
        amount = int(args[3])
        exact_score = args[4] if len(args) > 4 else "-"
        scorers = args[5] if len(args) > 5 else "-"
        
        if prediction not in ['1', 'X', '2']:
            return bot.reply_to(message, "❌ Outcome configurations must map strictly to `1`, `X`, or `2` values.")
            
        if amount < 150:
            return bot.reply_to(message, "❌ Threshold block. Minimum active bet allowed is 150 Tokens.")
            
        conn = get_db()
        cursor = conn.cursor()
        
        match = cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if not match:
            conn.close()
            return bot.reply_to(message, "❌ Validation error. The requested Match ID does not exist.")
            
        if match['status'] != 'upcoming':
            conn.close()
            return bot.reply_to(message, "❌ Operational denial. The targeted match setup is already locked/running/settled.")
            
        user = cursor.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
        if user['balance'] < amount:
            conn.close()
            return bot.reply_to(message, "❌ Execution denied. Insufficient tokens available in wallet.")
            
        existing_bet = cursor.execute("SELECT * FROM bets WHERE user_id = ? AND match_id = ?", (message.from_user.id, match_id)).fetchone()
        if existing_bet:
            conn.close()
            return bot.reply_to(message, "❌ Constraint collision. You already have a bet logged for this game. Use `/edit_bet` instead.")
            
        now_str = get_timezone_now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO bets (user_id, match_id, prediction, amount, exact_score, scorers, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (message.from_user.id, match_id, prediction, amount, exact_score, scorers, now_str))
        cursor.execute("UPDATE users SET balance = balance - ?, last_bet_time = ?, total_bets_count = total_bets_count + 1 WHERE user_id = ?",
                       (amount, now_str, message.from_user.id))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✅ Stake of <b>{amount} Tokens</b> successfully locked for Match ID: {match_id}!", parse_mode="HTML")
        
        if amount >= 1000:
            group_msg = (f"📢 <b>🔥 HEAVY BET ANNOUNCEMENT! 🔥</b>\n\n"
                         f"👤 High Roller @{user['username'] if user['username'] else message.from_user.id} just committed a massive stake of <b>{amount} Tokens</b> on <b>{match['team1']} vs {match['team2']}</b>!\n"
                         f"🔮 Prediction Vector: [{prediction}] | Let the public banter begin! 🗣🔊")
            bot.send_message(message.chat.id, group_msg, parse_mode="HTML")
            
    except ValueError:
        bot.reply_to(message, "❌ Mismatch error. Verify Match ID and Stake variables are formatted as integers.")

@bot.message_handler(commands=['edit_bet'])
def edit_bet_command(message):
    args = message.text.split()
    if len(args) < 4:
        return bot.reply_to(message, "🔧 <b>Usage Framework:</b>\n<code>/edit_bet [match_id] [1/X/2] [new_amount]</code>", parse_mode="HTML")
    try:
        match_id = int(args[1])
        prediction = args[2].upper()
        amount = int(args[3])
        
        if prediction not in ['1', 'X', '2']:
            return bot.reply_to(message, "❌ Predictions must be `1`, `X`, or `2`.")
        if amount < 150:
            return bot.reply_to(message, "❌ Minimum stake requirement is 150 Tokens.")
            
        conn = get_db()
        cursor = conn.cursor()
        
        old_bet = cursor.execute("SELECT * FROM bets WHERE user_id = ? AND match_id = ?", (message.from_user.id, match_id)).fetchone()
        if not old_bet:
            conn.close()
            return bot.reply_to(message, "❌ You have no active stake recorded for this match entity.")
            
        match = cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if match['status'] != 'upcoming':
            conn.close()
            return bot.reply_to(message, "❌ Betting vectors are already locked for this match.")
            
        user = cursor.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,)).fetchone()
        
        if (user['balance'] + old_bet['amount']) < amount:
            conn.close()
            return bot.reply_to(message, "❌ Mismatch. Insufficient net balance assets to apply modifications.")
            
        balance_diff = old_bet['amount'] - amount
        now_str = get_timezone_now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute("UPDATE bets SET prediction = ?, amount = ?, timestamp = ? WHERE user_id = ? AND match_id = ?",
                       (prediction, amount, now_str, message.from_user.id, match_id))
        cursor.execute("UPDATE users SET balance = balance + ?, last_bet_time = ? WHERE user_id = ?",
                       (balance_diff, now_str, message.from_user.id))
        conn.commit()
        conn.close()
        bot.reply_to(message, "✅ Stake modifications successfully updated within database matrices.")
    except ValueError:
        bot.reply_to(message, "❌ Formatting mismatch observed on incoming parameters.")

@bot.message_handler(commands=['cancel_bet'])
def cancel_bet_command(message):
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "🔧 <b>Usage:</b>\n<code>/cancel_bet [match_id]</code>", parse_mode="HTML")
    try:
        match_id = int(args[1])
        conn = get_db()
        cursor = conn.cursor()
        
        old_bet = cursor.execute("SELECT * FROM bets WHERE user_id = ? AND match_id = ?", (message.from_user.id, match_id)).fetchone()
        if not old_bet:
            conn.close()
            return bot.reply_to(message, "❌ No bet records found mapping your profile to this match index.")
            
        match = cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if match['status'] != 'upcoming':
            conn.close()
            return bot.reply_to(message, "❌ Cancellation lock enforcement. Match window has closed.")
            
        cursor.execute("DELETE FROM bets WHERE user_id = ? AND match_id = ?", (message.from_user.id, match_id))
        cursor.execute("UPDATE users SET balance = balance + ?, total_bets_count = max(0, total_bets_count - 1) WHERE user_id = ?", (old_bet['amount'], message.from_user.id))
        conn.commit()
        conn.close()
        bot.reply_to(message, "✅ Bet voided successfully. Staked capital fully restored to your active balance container.")
    except ValueError:
        bot.reply_to(message, "❌ Invalid Match ID integer sequence format.")

# --- Banking & System Loan Mechanisms ---

@bot.message_handler(commands=['get_loan'])
def get_loan_command(message):
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username)
    
    conn = get_db()
    cursor = conn.cursor()
    
    loans_count = cursor.execute("SELECT COUNT(*) FROM loans WHERE user_id = ?", (user_id,)).fetchone()[0]
    if loans_count >= 2:
        conn.close()
        return bot.reply_to(message, "❌ Lifecycle constraint triggered! You can only invoke the system loan module 2 times across eternity.")
        
    active_loan = cursor.execute("SELECT * FROM loans WHERE user_id = ? AND status = 'active'", (user_id,)).fetchone()
    if active_loan:
        conn.close()
        return bot.reply_to(message, "❌ Outstanding debt detected. Settle active open contracts first via `/pay_loan`.")
        
    now_str = get_timezone_now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO loans (user_id, amount_given, amount_due, amount_paid, taken_at, status) VALUES (?, 1000, 1250, 0, ?, 'active')", (user_id, now_str))
    cursor.execute("UPDATE users SET balance = balance + 1000 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    bot.reply_to(message, "💵 <b>System Loan Approved!</b>\n\n1000 Tokens added to your profile assets. A repayment calculation of 1250 Tokens must be fulfilled within 5 days. Track status with `/loan_status`.", parse_mode="HTML")

@bot.message_handler(commands=['pay_loan'])
def pay_loan_command(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "🔧 <b>Usage Structure:</b>\n<code>/pay_loan [amount]</code>", parse_mode="HTML")
        
    try:
        pay_amount = int(args[1])
        if pay_amount <= 0:
            return bot.reply_to(message, "❌ Transaction values must exceed 0 numerical parameters.")
            
        conn = get_db()
        cursor = conn.cursor()
        
        loan = cursor.execute("SELECT * FROM loans WHERE user_id = ? AND status = 'active'", (user_id,)).fetchone()
        if not loan:
            conn.close()
            return bot.reply_to(message, "🟢 Clean report. You have no active unpaid liabilities currently matching your ID.")
            
        user = cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if user['balance'] < pay_amount:
            conn.close()
            return bot.reply_to(message, "❌ Allocation denied. Your current assets cannot clear this payment bracket size.")
            
        remaining_debt = loan['amount_due'] - loan['amount_paid']
        if pay_amount > remaining_debt:
            conn.close()
            return bot.reply_to(message, f"❌ Overflow error! Your outstanding obligation caps precisely at {remaining_debt} Tokens. Excess deposits are locked.")
            
        new_paid = loan['amount_paid'] + pay_amount
        new_status = 'paid' if new_paid >= loan['amount_due'] else 'active'
        
        cursor.execute("UPDATE loans SET amount_paid = ?, status = ? WHERE loan_id = ?", (new_paid, new_status, loan['loan_id']))
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (pay_amount, user_id))
        conn.commit()
        conn.close()
        
        if new_status == 'paid':
            bot.reply_to(message, "🎉 <b>Liability Closed!</b>\n\nYou successfully settled the final installment. Debt records cleared.")
        else:
            bot.reply_to(message, f"✅ Payment accepted. Outstanding balance reduced. Remaining liability: <b>{loan['amount_due'] - new_paid} Tokens</b>.")
            
    except ValueError:
        bot.reply_to(message, "❌ Numerical matching mismatch. Input digits only.")

@bot.message_handler(commands=['loan_status'])
def loan_status_command(message):
    user_id = message.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    loan = cursor.execute("SELECT * FROM loans WHERE user_id = ? AND status = 'active'", (user_id,)).fetchone()
    conn.close()
    
    if loan:
        remaining = loan['amount_due'] - loan['amount_paid']
        text = (f"📈 <b>Active Open Liability File</b>\n\n"
                f"💵 Disbursed Principal: 1000 Tokens\n"
                f"💳 Target Maturity Obligation: 1250 Tokens\n"
                f"💰 Total Amortized Payments: {loan['amount_paid']} Tokens\n"
                f"🚨 Current Outstanding Debt: <b>{remaining} Tokens</b>\n"
                f"⏰ Timestamp of Origination: {loan['taken_at']}\n\n"
                f"_Notice: Failure to resolve manually within 5 days triggers automated escrow enforcement extraction calculation routines._")
        bot.reply_to(message, text, parse_mode="Markdown")
    else:
        bot.reply_to(message, "🟢 Clean statement. No outstanding unpaid loan balances linked to this channel.")

# --- Admin Core Management Systems ---

@bot.message_handler(commands=['add_match'])
def add_match_command(message):
    if message.from_user.id not in ADMIN_IDS:
        return bot.reply_to(message, "❌ Unauthorized administrative sector access denied.")
    args = message.text.split()
    if len(args) < 8:
        return bot.reply_to(message, "🔧 <b>Usage Framework:</b>\n<code>/add_match [team1] [team2] [odds_1] [odds_X] [odds_2] [YYYY-MM-DD] [HH:MM]</code>", parse_mode="HTML")
    try:
        team1 = args[1]
        team2 = args[2]
        odds_1 = float(args[3])
        odds_X = float(args[4])
        odds_2 = float(args[5])
        start_time = f"{args[6]} {args[7]}"
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO matches (team1, team2, odds_1, odds_X, odds_2, start_time, status) VALUES (?, ?, ?, ?, ?, ?, 'upcoming')",
                       (team1, team2, odds_1, odds_X, odds_2, start_time))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Match matrix: <b>{team1} vs {team2}</b> successfully deployed into upcoming schedules.", parse_mode="HTML")
    except ValueError:
        bot.reply_to(message, "❌ Parameter format issue. Verify odds are floats and timing follows explicit syntax.")

@bot.message_handler(commands=['settle_match'])
def settle_match_command(message):
    if message.from_user.id not in ADMIN_IDS:
        return bot.reply_to(message, "❌ Unauthorized.")
    args = message.text.split()
    if len(args) < 4:
        return bot.reply_to(message, "🔧 <b>Usage Framework:</b>\n<code>/settle_match [match_id] [1/X/2] [A-B] [scorer1,scorer2... or -]</code>", parse_mode="HTML")
        
    try:
        match_id = int(args[1])
        result = args[2].upper()
        actual_score = args[3]
        actual_scorers_text = args[4].lower() if len(args) > 4 else "-"
        actual_scorers = [s.strip() for s in actual_scorers_text.split(",") if s.strip() and s.strip() != "-"]
        
        if result not in ['1', 'X', '2']:
            return bot.reply_to(message, "❌ Outcome maps strictly to choices `1`, `X`, or `2`.")
            
        conn = get_db()
        cursor = conn.cursor()
        
        match = cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if not match or match['status'] == 'settled':
            conn.close()
            return bot.reply_to(message, "❌ Targeted index does not point to an active un-settled match.")
            
        bets = cursor.execute("SELECT * FROM bets WHERE match_id = ?", (match_id,)).fetchall()
        
        for bet in bets:
            user_id = bet['user_id']
            win_base = 0
            win_exact = 0
            win_scorer = 0
            
            if bet['prediction'] == result:
                odds = match[f"odds_{result}"]
                base_winnings = int(bet['amount'] * odds)
                win_base = base_winnings - bet['amount']
                
                # Exact Score Module (25% bonus profit calculation)
                if str(bet['exact_score']).strip() == str(actual_score).strip():
                    win_exact = int(win_base * 0.25)
                    
                # Scorer Allocation Module (Pro-rata model: 10% profit reward per correct item matching)
                if bet['scorers'] != "-" and actual_scorers:
                    user_scorers = [s.strip().lower() for s in bet['scorers'].split(",") if s.strip()]
                    matched_scorers = [scorer for scorer in set(user_scorers) if scorer in actual_scorers]
                    win_scorer = len(matched_scorers) * int(win_base * 0.10)
                    
                total_payout = bet['amount'] + win_base + win_exact + win_scorer
                net_profit = win_base + win_exact + win_scorer
                
                cursor.execute("UPDATE users SET balance = balance + ?, total_profit = total_profit + ? WHERE user_id = ?", (total_payout, net_profit, user_id))
            else:
                net_profit = -bet['amount']
                cursor.execute("UPDATE users SET total_profit = total_profit + ? WHERE user_id = ?", (net_profit, user_id))
                
            cursor.execute("UPDATE bets SET win_base = ?, win_exact = ?, win_scorer = ? WHERE bet_id = ?", (win_base, win_exact, win_scorer, bet['bet_id']))
            
            try:
                total_win = win_base + win_exact + win_scorer
                if total_win > 0:
                    msg = (f"🎉 <b>Match Settled! You Won!</b>\n\n"
                           f"⚔️ {match['team1']} - {match['team2']} ({actual_score})\n"
                           f"💰 Base Profit yield: {win_base} Tokens\n"
                           f"🎯 Exact Score Premium: {win_exact} Tokens\n"
                           f"⚽️ Scorers Premium: {win_scorer} Tokens\n"
                           f"💵 Distributed Return: {bet['amount'] + total_win} Tokens")
                else:
                    msg = (f"❌ <b>Match Settled Result. Better luck next time!</b>\n\n"
                           f"⚔️ {match['team1']} - {match['team2']} ({actual_score})\n"
                           f"💸 Liquidated Amount: {bet['amount']} Tokens")
                bot.send_message(user_id, msg, parse_mode="HTML")
            except Exception: pass
                
        cursor.execute("UPDATE matches SET status = 'settled', result = ? WHERE match_id = ?", (f"{actual_score} ({result})", match_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"🏁 Distribution executed. Match ID {match_id} successfully closed and archived.")
    except ValueError:
        bot.reply_to(message, "❌ Processing fault inside argument variables.")

@bot.message_handler(commands=['resettle_match'])
def resettle_match_command(message):
    if message.from_user.id not in ADMIN_IDS:
        return bot.reply_to(message, "❌ Unauthorized.")
    args = message.text.split()
    if len(args) < 4:
        return bot.reply_to(message, "🔧 <b>Usage Framework:</b>\n<code>/resettle_match [match_id] [1/X/2] [A-B] [scorers or -]</code>", parse_mode="HTML")
        
    try:
        match_id = int(args[1])
        new_result = args[2].upper()
        actual_score = args[3]
        actual_scorers_text = args[4].lower() if len(args) > 4 else "-"
        actual_scorers = [s.strip() for s in actual_scorers_text.split(",") if s.strip() and s.strip() != "-"]
        
        if new_result not in ['1', 'X', '2']:
            return bot.reply_to(message, "❌ Results must strictly map to `1`, `X`, or `2` values.")
            
        conn = get_db()
        cursor = conn.cursor()
        
        match = cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if not match or match['status'] != 'settled':
            conn.close()
            return bot.reply_to(message, "❌ targeted target index must match a finished/settled profile.")
            
        bets = cursor.execute("SELECT * FROM bets WHERE match_id = ?", (match_id,)).fetchall()
        
        for bet in bets:
            user_id = bet['user_id']
            
            # 1. Rollback old settlement parameters safely
            old_total_win = bet['win_base'] + bet['win_exact'] + bet['win_scorer']
            old_payout = bet['amount'] + old_total_win if old_total_win > 0 else 0
            old_net_profit = old_total_win if old_total_win > 0 else -bet['amount']
            
            cursor.execute("UPDATE users SET balance = balance - ?, total_profit = total_profit - ? WHERE user_id = ?", (old_payout, old_net_profit, user_id))
            
            # 2. Recalculate with corrected parameters (Identical Pro-Rata Scorer Calculation logic applied)
            new_win_base = 0
            new_win_exact = 0
            new_win_scorer = 0
            
            if bet['prediction'] == new_result:
                odds = match[f"odds_{new_result}"]
                new_base_winnings = int(bet['amount'] * odds)
                new_win_base = new_base_winnings - bet['amount']
                
                # Exact Score Premium Check
                if str(bet['exact_score']).strip() == str(actual_score).strip():
                    new_win_exact = int(new_win_base * 0.25)
                    
                # Fixed Pro-Rata Scorer matching (Identical to settle_match)
                if bet['scorers'] != "-" and actual_scorers:
                    user_scorers = [s.strip().lower() for s in bet['scorers'].split(",") if s.strip()]
                    matched_scorers = [scorer for scorer in set(user_scorers) if scorer in actual_scorers]
                    new_win_scorer = len(matched_scorers) * int(new_win_base * 0.10)
                    
                new_total_payout = bet['amount'] + new_win_base + new_win_exact + new_win_scorer
                new_net_profit = new_win_base + new_win_exact + new_win_scorer
                
                cursor.execute("UPDATE users SET balance = balance + ?, total_profit = total_profit + ? WHERE user_id = ?", (new_total_payout, new_net_profit, user_id))
            else:
                new_net_profit = -bet['amount']
                cursor.execute("UPDATE users SET total_profit = total_profit + ? WHERE user_id = ?", (new_net_profit, user_id))
                
            cursor.execute("UPDATE bets SET win_base = ?, win_exact = ?, win_scorer = ? WHERE bet_id = ?", (new_win_base, new_win_exact, new_win_scorer, bet['bet_id']))
            
            try:
                new_total_win = new_win_base + new_win_exact + new_win_scorer
                if new_total_win > 0:
                    msg = (f"🔄 <b>Match ID {match_id} Recalculated & Revised!</b>\n\n"
                           f"🎉 Ledger update: Your stake is now processed as a Winner!\n"
                           f"💰 Base Profit yield: {new_win_base} Tokens\n"
                           f"🎯 Exact Score Premium: {new_win_exact} Tokens\n"
                           f"⚽️ Scorers Premium: {new_win_scorer} Tokens\n"
                           f"💵 Distributed Return: {bet['amount'] + new_total_win} Tokens")
                else:
                    msg = (f"🔄 <b>Match ID {match_id} Recalculated & Revised!</b>\n\n"
                           f"❌ Ledger update: Your prediction evaluates as a Loss.\n"
                           f"💸 Liquidated Amount: {bet['amount']} Tokens")
                bot.send_message(user_id, msg, parse_mode="HTML")
            except Exception: pass
                
        cursor.execute("UPDATE matches SET result = ? WHERE match_id = ?", (f"{actual_score} ({new_result})", match_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Revision complete. Balances and histories updated cleanly for Match ID {match_id}!")
    except ValueError:
        bot.reply_to(message, "❌ Parameter error encountered on incoming values.")

@bot.message_handler(commands=['delete_match'])
def delete_match_command(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Usage syntax error. Use /delete_match [match_id]")
    try:
        match_id = int(args[1])
        conn = get_db()
        cursor = conn.cursor()
        
        match = cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
        if not match:
            conn.close()
            return bot.reply_to(message, "❌ Target Match ID index location empty.")
            
        bets = cursor.execute("SELECT * FROM bets WHERE match_id = ?", (match_id,)).fetchall()
        for bet in bets:
            if match['status'] != 'settled':
                cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (bet['amount'], bet['user_id']))
            else:
                total_win = bet['win_base'] + bet['win_exact'] + bet['win_scorer']
                payout = bet['amount'] + total_win if total_win > 0 else 0
                net_profit = total_win if total_win > 0 else -bet['amount']
                cursor.execute("UPDATE users SET balance = balance - ? + ?, total_profit = total_profit - ? WHERE user_id = ?", (payout, bet['amount'], net_profit, bet['user_id']))
                
            try:
                bot.send_message(bet['user_id'], f"🚨 <b>Match Void Alert!</b>\n\nMatch ID {match_id} has been dropped by administration. Your baseline stake of {bet['amount']} Tokens has been refunded safely.")
            except Exception: pass
                
        cursor.execute("DELETE FROM bets WHERE match_id = ?", (match_id,))
        cursor.execute("DELETE FROM matches WHERE match_id = ?", (match_id,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Match ID {match_id} scrubbed from records. Stakes restored to players.")
    except ValueError:
        bot.reply_to(message, "❌ Match ID conversion failure.")

@bot.message_handler(commands=['admin'])
def admin_give_take(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 4:
        return bot.reply_to(message, "Usage syntax error. Use /admin [give/take] [user_id] [amount]")
    action = args[1].lower()
    try:
        target_id = int(args[2])
        amount = int(args[3])
        conn = get_db()
        cursor = conn.cursor()
        if action == 'give':
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
            bot.reply_to(message, f"✅ Balance credited. Added {amount} Tokens to User ID: {target_id}")
        elif action == 'take':
            cursor.execute("UPDATE users SET balance = max(0, balance - ?) WHERE user_id = ?", (amount, target_id))
            bot.reply_to(message, f"✅ Balance debited. Extracted {amount} Tokens from User ID: {target_id}")
        conn.commit()
        conn.close()
    except ValueError:
        bot.reply_to(message, "❌ Mathematical conversion parameter mismatch.")

@bot.message_handler(commands=['giveall'])
def give_money_to_all(message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.text.split()
    if len(args) < 2:
        return bot.reply_to(message, "Usage syntax error. Use /giveall [amount]")
    try:
        amount = int(args[1])
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ?", (amount,))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"✅ Global drop completed. Deposited {amount} Tokens to all database participant accounts.")
    except ValueError:
        bot.reply_to(message, "❌ Non-numerical argument encountered.")

# --- Public Informational Matrix Links ---

@bot.message_handler(commands=['all_matches'])
def show_all_matches(message):
    conn = get_db()
    matches = conn.execute("SELECT * FROM matches ORDER BY match_id DESC").fetchall()
    conn.close()
    if not matches:
        return bot.reply_to(message, "🗄 <b>Match archive register is empty.</b>", parse_mode="HTML")
    text = "🗄 <b>Complete Tournament Match History Logs:</b>\n\n"
    for m in matches:
        if m['status'] == 'upcoming': status_str = "⏳ Pending Match Window"
        elif m['status'] == 'ongoing': status_str = "🏃‍♂️ In Progress"
        else: status_str = f"🏁 Finished ({m['result']})"
        text += (f"🔹 <b>Match ID: {m['match_id']}</b> | {m['team1']} vs {m['team2']}\n"
                 f"📊 Pricing Configurations: [{m['odds_1']} / {m['odds_X']} / {m['odds_2']}]\n"
                 f"🏁 Status: {status_str}\n"
                 f"───────────────────\n")
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['stats'])
def show_user_stats(message):
    args = message.text.split()
    target_id = None
    conn = get_db()
    cursor = conn.cursor()
    
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        display_name = f"@{message.reply_to_message.from_user.username}" if message.reply_to_message.from_user.username else f"User {target_id}"
    elif len(args) > 1:
        input_val = args[1].replace('@', '')
        if input_val.isdigit(): target_id = int(input_val)
        else:
            u = cursor.execute("SELECT * FROM users WHERE username = ?", (input_val,)).fetchone()
            if u: target_id = u['user_id']
        display_name = args[1]
    else:
        target_id = message.from_user.id
        display_name = f"@{message.from_user.username}" if message.from_user.username else f"User {target_id}"
        
    user_row = cursor.execute("SELECT * FROM users WHERE user_id = ?", (target_id,)).fetchone() if target_id else None
    if not user_row:
        conn.close()
        return bot.reply_to(message, "❌ Target ledger profile could not be found.")
        
    correct_bets = cursor.execute("SELECT COUNT(*) FROM bets b JOIN matches m ON b.match_id = m.match_id WHERE b.user_id = ? AND (b.win_base > 0)", (target_id,)).fetchone()[0]
    total_completed = cursor.execute("SELECT COUNT(*) FROM bets b JOIN matches m ON b.match_id = m.match_id WHERE b.user_id = ? AND m.status = 'settled'", (target_id,)).fetchone()[0]
    wrong_bets = total_completed - correct_bets
    conn.close()
    
    stats_text = (f"📊 <b>Performance Analytics for {display_name}</b>\n\n"
                  f"💰 <b>Current Assets Wallet:</b> {user_row['balance']} Tokens\n"
                  f"📈 <b>Net Accumulation Yield:</b> {user_row['total_profit']} Tokens\n"
                  f"📝 <b>Total Tracked Bets Placed:</b> {user_row['total_bets_count']}\n"
                  f"✅ <b>Successful Outcomes Evaluated:</b> {correct_bets}\n"
                  f"❌ <b>Unsuccessful Outcomes Evaluated:</b> {wrong_bets}")
    bot.reply_to(message, stats_text, parse_mode="HTML")

@bot.message_handler(commands=['my_bets'])
def my_bets_cmd(message):
    send_my_bets_page(message.chat.id, message.from_user.id, page=1)

@bot.message_handler(commands=['bets'])
def view_other_user_bets(message):
    args = message.text.split()
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif len(args) > 1:
        input_val = args[1].replace('@', '')
        conn = get_db()
        if input_val.isdigit(): target_id = int(input_val)
        else:
            u = conn.execute("SELECT * FROM users WHERE username = ?", (input_val,)).fetchone()
            if u: target_id = u['user_id']
        conn.close()
        
    if not target_id:
        return bot.reply_to(message, "Syntax pattern issue. Use: /bets [@username/ID] or reply directly to target user message threads.")
    send_my_bets_page(message.chat.id, target_id, page=1)

@bot.message_handler(commands=['all_bets'])
def view_all_bets_radar(message):
    conn = get_db()
    bets = conn.execute("""
        SELECT b.*, u.username, m.team1, m.team2 
        FROM bets b 
        JOIN users u ON b.user_id = u.user_id 
        JOIN matches m ON b.match_id = m.match_id 
        ORDER BY b.bet_id DESC LIMIT 10
    """).fetchall()
    conn.close()
    
    if not bets:
        return bot.reply_to(message, "👥 <b>Global transaction system feeds are currently empty.</b>", parse_mode="HTML")
        
    text = "👥 <b>Global Betting Feed Radar (Last 10 entries):</b>\n\n"
    for b in bets:
        user_name = f"@{b['username']}" if b['username'] else f"User {b['user_id']}"
        text += f"👤 {user_name} dropped {b['amount']} Tokens onto match {b['team1']}-{b['team2']} -> prediction vector [{b['prediction']}]\n"
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['awards'])
def view_awards(message):
    conn = get_db()
    cursor = conn.cursor()
    ballon_dor = cursor.execute("SELECT username, user_id, total_profit FROM users ORDER BY total_profit DESC LIMIT 3").fetchall()
    
    golden_boot = cursor.execute("""
        SELECT u.username, u.user_id, COUNT(b.bet_id) as correct_count 
        FROM users u 
        JOIN bets b ON u.user_id = b.user_id 
        WHERE b.win_base > 0 
        GROUP BY u.user_id 
        ORDER BY correct_count DESC LIMIT 3
    """).fetchall()
    conn.close()
    
    text = "🏆 <b>Tournament Prestigious Awards Standings</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "✨ <b>Ballon d'Or Race Tracker (Highest Net Gains Profit):</b>\n"
    for idx, u in enumerate(ballon_dor, start=1):
        uname = f"@{u['username']}" if u['username'] else f"User {u['user_id']}"
        text += f"{idx}️⃣ {uname} ── 📈 {u['total_profit']} Net Profits\n"
        
    text += "\n✨ <b>Golden Boot Race Tracker (Highest Correct Count):</b>\n"
    if golden_boot:
        for idx, u in enumerate(golden_boot, start=1):
            uname = f"@{u['username']}" if u['username'] else f"User {u['user_id']}"
            text += f"{idx}️⃣ {uname} ── ✅ {u['correct_count']} Correct Bets\n"
    else:
        text += "No records verified inside the criteria parameters yet.\n"
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=['leaderboard'])
def leaderboard_cmd(message):
    send_leaderboard_page(message.chat.id, page=1)

@bot.message_handler(func=lambda message: message.text in ["Help 📜", "Rules ⚖️", "Matches 📅", "Leaderboard 🏆", "About Bot ℹ️", "Wallet 💰"])
def handle_text_menu_buttons(message):
    if message.text == "Help 📜": send_help(message)
    elif message.text == "Rules ⚖️": send_rule(message)
    elif message.text == "Matches 📅": send_matches_page(message.chat.id, page=1)
    elif message.text == "Leaderboard 🏆": send_leaderboard_page(message.chat.id, page=1)
    elif message.text == "About Bot ℹ️": send_about(message)
    elif message.text == "Wallet 💰": show_wallet(message)

# --- Interactive Smart Betting Wizard (Inline Query Handling Matrix) ---

@bot.inline_handler(func=lambda query: True)
def handle_inline_bet_wizard(query):
    text = query.query.strip()
    if text.lower().startswith('bet'):
        args = text[3:].strip().split()
    else:
        args = text.split()
        
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    results = []
    
    try:
        # Step 1: Browse active options
        if len(args) == 0:
            matches = cursor.execute("SELECT * FROM matches WHERE status = 'upcoming' ORDER BY match_id DESC").fetchall()
            if not matches:
                item = types.InlineQueryResultArticle(
                    id="no_matches", title="📅 No active match schedules loaded",
                    description="There are currently no upcoming open match channels open for staking.",
                    input_message_content=types.InputTextMessageContent(message_text="No open slots.")
                )
                results.append(item)
            else:
                for m in matches:
                    desc = f"1: {m['odds_1']} | X: {m['odds_X']} | 2: {m['odds_2']} | Locks: {m['start_time']}"
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(text="🎯 Select Match Node", switch_inline_query_current_chat=f"bet {m['match_id']} "))
                    
                    item = types.InlineQueryResultArticle(
                        id=f"match_{m['match_id']}",
                        title=f"⚽️ {m['team1']} vs {m['team2']}",
                        description=desc,
                        input_message_content=types.InputTextMessageContent(message_text=f"Target Match Selected: {m['match_id']}"),
                        reply_markup=markup
                    )
                    results.append(item)
                    
        # Step 2: Prediction selection vector setup
        elif len(args) == 1:
            match_id = args[0]
            m = cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
            if m:
                predictions = [('1', f"Win {m['team1']}"), ('X', "Draw Balance (X)"), ('2', f"Win {m['team2']}")]
                for pred_code, pred_label in predictions:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(text=f"✅ Lock {pred_label}", switch_inline_query_current_chat=f"bet {match_id} {pred_code} "))
                    
                    item = types.InlineQueryResultArticle(
                        id=f"pred_{match_id}_{pred_code}",
                        title=f"🔮 Configuration vector: {pred_label}",
                        description=f"Event: {m['team1']}-{m['team2']} | Rate Odds: {m[f'odds_{pred_code}']}",
                        input_message_content=types.InputTextMessageContent(message_text=f"Vector Locked: {pred_code}"),
                        reply_markup=markup
                    )
                    results.append(item)
                    
        # Step 3: Stake selection options configuration
        elif len(args) == 2:
            match_id = args[0]
            prediction = args[1].upper()
            m = cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
            if m and prediction in ['1', 'X', '2']:
                pred_text = m['team1'] if prediction == '1' else (m['team2'] if prediction == '2' else "Draw")
                suggested_amounts = [150, 500, 1000]
                for amt in suggested_amounts:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton(text=f"💵 {amt} Tokens", switch_inline_query_current_chat=f"bet {match_id} {prediction} {amt} "))
                    
                    extra_text = " 🔥 (Heavy Bet Announcement Flagged!)" if amt >= 1000 else ""
                    item = types.InlineQueryResultArticle(
                        id=f"amt_{amt}",
                        title=f"💰 Deposit Tier: {amt} Tokens{extra_text}",
                        description=f"Fixture: {m['team1']}-{m['team2']} | Path: {pred_text}",
                        input_message_content=types.InputTextMessageContent(message_text=f"Stake configuration marked at: {amt}"),
                        reply_markup=markup
                    )
                    results.append(item)
                    
                results.append(types.InlineQueryResultArticle(
                    id="amt_manual", title="✍️ Custom allocation field",
                    description="Append an extra blank space and input custom values directly manually (e.g., 350)",
                    input_message_content=types.InputTextMessageContent(message_text="Manual override payload pending input data...")
                ))
                
        # Step 4: Final verification generation structure
        elif len(args) >= 3:
            match_id = args[0]
            prediction = args[1].upper()
            amount_str = args[2]
            exact_score = args[3] if len(args) > 3 else "-"
            scorers = args[4] if len(args) > 4 else "-"
            
            m = cursor.execute("SELECT * FROM matches WHERE match_id = ?", (match_id,)).fetchone()
            if m and amount_str.isdigit():
                amount = int(amount_str)
                command_text = f"/bet {match_id} {prediction} {amount} {exact_score} {scorers}"
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton(text="🚀 EXECUTE TRANSACTION DISPATCH NOW", switch_inline_query_current_chat=f"bet {match_id} {prediction} {amount} "))
                
                item = types.InlineQueryResultArticle(
                    id="confirm_bet",
                    title="📝 Click this container to finalize and paste text configuration payload into chat context",
                    description=f"Resultant macro payload: {command_text}",
                    input_message_content=types.InputTextMessageContent(message_text=command_text)
                )
                results.append(item)
                
        bot.answer_inline_query(query.id, results, cache_time=1)
    except Exception as e:
        print(f"Error in inline_handler block module: {e}")
    finally:
        # 🔒 CRITICAL ANTI-LEAK ESCROW PROTECTION ENGINE COMPLIANCE LAYER:
        # Connection matrix is guaranteed execution closure here regardless of routing exceptions.
        conn.close()

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.chat.type in ['group', 'supergroup'] and f"@{bot.get_me().username}" in message.text:
        bot.reply_to(message, "Syntax mismatch observed. Invoke /start or review active instructions via /help module configurations.")

# --- Asynchronous Scheduled Escrow Background Thread Workers ---

def inactivity_checker():
    """Implements automated inactivity checking fines for users exceeding timeline windows."""
    while True:
        try:
            conn = get_db()
            cursor = conn.cursor()
            users = cursor.execute("SELECT * FROM users").fetchall()
            now = get_timezone_now()
            for user in users:
                if user['last_bet_time']:
                    last_bet = datetime.strptime(user['last_bet_time'], '%Y-%m-%d %H:%M:%S')
                    if now - last_bet >= timedelta(hours=96):
                        new_balance = max(0, user['balance'] - 250)
                        now_str = now.strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("UPDATE users SET balance = ?, last_bet_time = ? WHERE user_id = ?", (new_balance, now_str, user['user_id']))
                        conn.commit()
                        actual_fine = user['balance'] - new_balance
                        if actual_fine > 0:
                            try:
                                bot.send_message(user['user_id'], f"⚠️ 96 hours of complete tournament betting inactivity observed. Automated escrow fine of {actual_fine} Tokens extracted.")
                            except Exception: pass
            conn.close()
        except Exception as e:
            print(f"Error in inactivity evaluation loops: {e}")
        time.sleep(3600)  # Evaluation routine loops every hour.

def loan_checker():
    """Performs automated checking scans across loans to extract maturity obligations upon day 5 thresholds."""
    while True:
        try:
            conn = get_db()
            cursor = conn.cursor()
            active_loans = cursor.execute("SELECT * FROM loans WHERE status = 'active'").fetchall()
            now = get_timezone_now()
            for loan in active_loans:
                taken_at = datetime.strptime(loan['taken_at'], '%Y-%m-%d %H:%M:%S')
                if now - taken_at >= timedelta(days=5):
                    remaining_debt = loan['amount_due'] - loan['amount_paid']
                    user_id = loan['user_id']
                    
                    cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (remaining_debt, user_id))
                    cursor.execute("UPDATE loans SET status = 'defaulted', amount_paid = amount_due WHERE loan_id = ?", (loan['loan_id'],))
                    
                    try:
                        msg = (f"🚨 <b>Automated Escrow Enforcement Recovery Notification</b>\n\n"
                               f"⚠️ Your 5-day maturity window threshold has been crossed.\n"
                               f"💸 The remaining settlement liability of <b>{remaining_debt} Tokens</b> was automatically pulled from your account balances.")
                        bot.send_message(user_id, msg, parse_mode="HTML")
                    except Exception: pass
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error in loan escrow resolution sweeps thread: {e}")
        time.sleep(60)  # Scans database rows thoroughly every 60 seconds.

if __name__ == '__main__':
    print("🤖 Bot is running and listening for messages...")
    
    # Run structural daemon background monitoring systems
    threading.Thread(target=inactivity_checker, daemon=True).start()
    threading.Thread(target=loan_checker, daemon=True).start()
    
    bot.infinity_polling()