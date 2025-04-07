import telebot
import re
import requests
import time
import os
import json
import traceback
import logging
from telebot.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from functions import (insertUser, track_exists, addBalance, cutBalance, getData,
                       addRefCount, isExists, setWelcomeStaus, setReferredStatus, updateUser, 
                       ban_user, unban_user, get_all_users, is_banned, get_banned_users, 
                       get_top_users, get_user_count, get_active_users, get_total_orders, 
                       get_total_deposits, get_top_referrer, is_valid_tiktok_link,  get_user_orders_stats) # Import your functions from functions.py

if not os.path.exists('Account'):
    os.makedirs('Account')

bot_token = "7668069068:AAGKv0jZjb2hhGPdjKzLOYFpA3kOtGzY8h0"
SmmPanelApi = "76dfaf950208ee730acd16f3e836a60977bcb48eeb231dacbed122aa82f96087"
SmmPanelApiUrl = "https://shakergainske.com/api/v2"
bot = telebot.TeleBot(bot_token)
admin_user_id = 5962658076
welcome_bonus = 100
ref_bonus = 50
min_view = 1000
max_view = 30000

# Main keyboard markup
main_markup = ReplyKeyboardMarkup(resize_keyboard=True)
button1 = KeyboardButton("📤 Send Orders")  # Changed from "👁‍🗨 Order View"
button2 = KeyboardButton("👤 My Account")
button3 = KeyboardButton("💳 Pricing")
button4 = KeyboardButton("📊 Order Statistics")
button5 = KeyboardButton("🗣 Invite Friends")
button6 = KeyboardButton("📜 Help")
button7 = KeyboardButton("🛠 Admin Panel")

main_markup.add(button1, button2)
main_markup.add(button3, button4)
main_markup.add(button5, button6)
main_markup.add(button7)

# Admin keyboard markup
admin_markup = ReplyKeyboardMarkup(resize_keyboard=True)
admin_markup.row(
    KeyboardButton("➕ Add Coins"),
    KeyboardButton("➖ Remove Coins")
)
admin_markup.row(
    KeyboardButton("📊 Analytics"),
    KeyboardButton("📢 Broadcast")
)
admin_markup.row(
    KeyboardButton("⛔ Ban User"),
    KeyboardButton("✅ Unban User")
)
admin_markup.row(
    KeyboardButton("📋 List Banned"),
    KeyboardButton("🏆 Leaderboard")
)
admin_markup.add(KeyboardButton("🔙 Main Menu"))
#======================= Send Orders main menu =======================#
send_orders_markup = ReplyKeyboardMarkup(resize_keyboard=True)
send_orders_markup.row(
    KeyboardButton("📱 Order Telegram"),
    KeyboardButton("🎵 Order TikTok"),
    KeyboardButton("")
)

send_orders_markup.row(
    KeyboardButton("📸 Order Instagram"),
    KeyboardButton("▶️ Order YouTube"),
)

send_orders_markup.row(
    KeyboardButton("📘 Order Facebook"),
    KeyboardButton("💬 Order WhatsApp")
)
send_orders_markup.add(KeyboardButton("🔙 Main Menu"))

# Telegram services menu
telegram_services_markup = ReplyKeyboardMarkup(resize_keyboard=True)
telegram_services_markup.row(
    KeyboardButton("👀 Order Views"),
    KeyboardButton("❤️ Order Reactions")
)
telegram_services_markup.row(
    KeyboardButton("👥 Order Members"),
)
telegram_services_markup.row(
    KeyboardButton("↩️ Go Back")
)

# TikTok services menu (placeholder for now)
tiktok_services_markup = ReplyKeyboardMarkup(resize_keyboard=True)
tiktok_services_markup.row(
    KeyboardButton("👀 TikTok Views"),
    KeyboardButton("❤️ TikTok Likes")
)
tiktok_services_markup.row(
    KeyboardButton("👥 TikTok Followers"),
)
tiktok_services_markup.row(
    KeyboardButton("↩️ Go Back")
)

# Instagram services menu
instagram_services_markup = ReplyKeyboardMarkup(resize_keyboard=True)
instagram_services_markup.row(
    KeyboardButton("🎥 Insta Vid Views"),
    KeyboardButton("❤️ Insta Likes")
)
instagram_services_markup.row(
    KeyboardButton("👥 Insta Followers"),
)
instagram_services_markup.row(
    KeyboardButton("↩️ Go Back")
)

# YouTube services menu
youtube_services_markup = ReplyKeyboardMarkup(resize_keyboard=True)
youtube_services_markup.row(
    KeyboardButton("▶️ YT Views"),
    KeyboardButton("👍 YT Likes")
)
youtube_services_markup.row(
    KeyboardButton("👥 YT Subscribers"),
)
youtube_services_markup.row(
    KeyboardButton("↩️ Go Back")
)

# Facebook services menu
facebook_services_markup = ReplyKeyboardMarkup(resize_keyboard=True)
facebook_services_markup.row(
    KeyboardButton("👤 Profile Followers"),
    KeyboardButton("📄 Page Followers")
)
facebook_services_markup.row(
    KeyboardButton("🎥 Video/Reel Views"),
    KeyboardButton("❤️ Post Likes")
)
facebook_services_markup.add(KeyboardButton("↩️ Go Back"))

# WhatsApp services menu
whatsapp_services_markup = ReplyKeyboardMarkup(resize_keyboard=True)
whatsapp_services_markup.row(
    KeyboardButton("👥 Channel Members"),
)
whatsapp_services_markup.row(
    KeyboardButton("😀 Channel EmojiReaction")
)
whatsapp_services_markup.add(KeyboardButton("↩️ Go Back"))

############################ END OF NEW FEATURES #############################
def add_order(user_id, order_data):
    """Add a new order to user's history"""
    try:
        filepath = os.path.join('Account', f'{user_id}.json')
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if 'orders' not in data:
                data['orders'] = []
            
            # Add timestamp and status if not provided
            if 'timestamp' not in order_data:
                order_data['timestamp'] = time.time()
            if 'status' not in order_data:
                order_data['status'] = 'pending'
            
            data['orders'].append(order_data)
            
            with open(filepath, 'w') as f:
                json.dump(data, f)
            return True
        return False
    except Exception as e:
        print(f"Error adding order: {e}")
        return False
#========== Channels =================#
required_channels = ["Megahubbots"] #"Freeairtimehub", #"Freenethubchannel"]  # Channel usernames without "@"
payment_channel = "@Reactionchanneltest"  # Corrected from a list to a string

def is_user_member(user_id):
    """Check if a user is a member of all required channels."""
    for channel in required_channels:
        try:
            chat_member = bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                return False  # User is NOT a member
        except Exception as e:
            print(f"Error checking channel membership for {channel}: {e}")
            return False  # Assume not a member if an error occurs
    return True  # User is a member of all channels


def check_membership_and_prompt(user_id, message):
    """Check if the user is a member of all required channels and prompt them to join if not."""
    if not is_user_member(user_id):
        bot.reply_to(
            message,
            "🚨 *To use this bot, you must join the required channels first!* 🚨\n\n"
            "Click the buttons below to join, then press *'✅ I Joined'*. ",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("MAIN CHANNEL", url="https://t.me/Megahubbots")],
                [InlineKeyboardButton("✅ I Joined", callback_data="verify_membership")]
            ])
        )
        return False  # User is not a member
    return True  # User is a member

@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def verify_membership(call):
    user_id = call.from_user.id

    if is_user_member(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✅ You are verified! You can now use the bot."
        )
        send_welcome(call.message)  # Restart the welcome process
    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text="❌ You haven't joined all the required channels yet!",
            show_alert=True
        )
#==============================================#

############################ END OF NEW FEATURES #############################
#======================= Channel Membership Check =======================#
#========== Channels =================#
required_channels = ["Megahubbots"] #"Freeairtimehub", #"Freenethubchannel"]  # Channel usernames without "@"
payment_channel = "@Reactionchanneltest"  # Corrected from a list to a string

def is_user_member(user_id):
    """Check if a user is a member of all required channels."""
    for channel in required_channels:
        try:
            chat_member = bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                return False  # User is NOT a member
        except Exception as e:
            print(f"Error checking channel membership for {channel}: {e}")
            return False  # Assume not a member if an error occurs
    return True  # User is a member of all channels


def check_membership_and_prompt(user_id, message):
    """Check if the user is a member of all required channels and prompt them to join if not."""
    if not is_user_member(user_id):
        bot.reply_to(
            message,
            "🚨 *To use this bot, you must join the required channels first!* 🚨\n\n"
            "Click the buttons below to join, then press *'✅ I Joined'*. ",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("MAIN CHANNEL", url="https://t.me/Megahubbots")],
                [InlineKeyboardButton("✅ I Joined", callback_data="verify_membership")]
            ])
        )
        return False  # User is not a member
    return True  # User is a member

@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def verify_membership(call):
    user_id = call.from_user.id

    if is_user_member(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✅ You are verified! You can now use the bot."
        )
        send_welcome(call.message)  # Restart the welcome process
    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text="❌ You haven't joined all the required channels yet!",
            show_alert=True
        )
#==============================================#
#==============================================#
@bot.message_handler(func=lambda message: message.text == "📤 Send Orders")
def send_orders_menu(message):
    user_id = message.from_user.id

    # Update last activity and username
    data = getData(user_id)
    data['last_activity'] = time.time()
    data['username'] = message.from_user.username
    updateUser(user_id, data)

    # Check if the user has joined all required channels
    if not check_membership_and_prompt(user_id, message):
        return  # Stop execution until the user joins
    
    # If the user is a member, show the Send Orders menu
    """Handle the main Send Orders menu"""
    bot.reply_to(message, "📤 Select platform to send orders:", reply_markup=send_orders_markup)


def set_bot_commands():
    commands = [
        BotCommand('start', 'Restart the bot')
        # Removed 'addcoins' and 'removecoins' from global commands
    ]
    try:
        bot.set_my_commands(commands)
        print("Bot commands set successfully")
    except Exception as e:
        print(f"Error setting bot commands: {e}")
# imports the updateUser function from functions.py
print(updateUser) 

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    ref_by = message.text.split()[1] if len(message.text.split()) > 1 and message.text.split()[1].isdigit() else None

   # Check if the user has joined all required channels
    if not check_membership_and_prompt(user_id, message):
        return  # Stop execution until the user joins

    # Referral system logic
    if ref_by and int(ref_by) != int(user_id) and track_exists(ref_by):
        if not isExists(user_id):
            initial_data = {
                "user_id": user_id,
                "balance": "0.00",
                "ref_by": ref_by,
                "referred": 0,
                "welcome_bonus": 0,
                "total_refs": 0,
            }
            insertUser(user_id, initial_data)
            addRefCount(ref_by)

    if not isExists(user_id):
        initial_data = {
            "user_id": user_id,
            "balance": "0.00",
            "ref_by": "none",
            "referred": 0,
            "welcome_bonus": 0,
            "total_refs": 0,
        }
        insertUser(user_id, initial_data)

    # Welcome bonus logic
    userData = getData(user_id)
    if userData['welcome_bonus'] == 0:
        bot.send_message(user_id, f"+{welcome_bonus} coins as welcome bonus.")
        addBalance(user_id, welcome_bonus)
        setWelcomeStaus(user_id)

    # Referral bonus logic
    data = getData(user_id)
    if data['ref_by'] != "none" and data['referred'] == 0:
        bot.send_message(data['ref_by'], f"You referred {first_name} +{ref_bonus}")
        addBalance(data['ref_by'], ref_bonus)
        setReferredStatus(user_id)

    # Send the main menu
    bot.reply_to(
        message,
        """With view booster bot there's just a few steps to increase the views of your Telegram posts.

👇🏻 To continue choose an item""",
        reply_markup=main_markup
    )

#====================== My Account =====================#
@bot.message_handler(func=lambda message: message.text == "👤 My Account")
def my_account(message):
    user_id = str(message.chat.id)
    bot_username = bot.get_me().username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    data = getData(user_id)
    
    if not data:
        bot.reply_to(message, "❌ Account not found. Please /start again.")
        return
    
    # Update last activity and username
    data = getData(user_id)
    data['last_activity'] = time.time()
    data['username'] = message.from_user.username
    updateUser(user_id, data)
        
    total_refs = data['total_refs']
    balance = data['balance']
    msg = f"""<b><u>My Account</u></b>

🆔 User id: {user_id}
👤 Username: @{message.chat.username}
🗣 Invited users: {total_refs}
🔗 Referral link: {referral_link}

👁‍🗨 Balance: <code>{balance}</code> Views"""
    bot.reply_to(message, msg, parse_mode='html')

@bot.message_handler(func=lambda message: message.text == "🗣 Invite Friends")
def invite_friends(message):
    user_id = str(message.chat.id)
    bot_username = bot.get_me().username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    data = getData(user_id)
    
    if not data:
        bot.reply_to(message, "❌ Account not found. Please /start again.")
        return
        
    total_refs = data['total_refs']
    bot.reply_to(
        message,
        f"<b>Referral link:</b> {referral_link}\n\n<b><u>Share it with friends and get {ref_bonus} coins for each referral</u></b>",
        parse_mode='html'
    )

@bot.message_handler(func=lambda message: message.text == "📜 Help")
def help_command(message):
    user_id = message.chat.id
    msg = f"""<b><u>❓ Frequently Asked questions</u></b>

<b><u>•Are the views real?</u></b>
No, the views are completely fake and no real observations are made.

<b><u>•What is the minimum and maximum views order for a single post?</u></b>
The minimum and maximum views order for a post is {min_view} and {max_view} views, respectively.

<b><u>•Is it possible to register a channel and view automatically?</u></b>
Yes, first set the bot as your channel admin and then register your channel in the bot and specify the amount of views. As soon as a post is published on your channel, the view starts automatically.

<b><u>•What is the average speed of views?</u></b>
Estimating views speed is difficult because the speed can vary depending on the network status and the amount of orders, but on average 40 to 80 views per minute is possible for one post.

<b><u>•How to increase your credit?</u></b>
1- Invite your friends to Bot, for each invitation, {ref_bonus} free views will be added to your account and {welcome_bonus} to your invited user.
2- Buy one of the views packages. We accept PayPal, Paytm, WebMoney, Perfect Money, Payeer, Bitcoin, Tether and other Cryptocurrencies.

<b><u>•Is it possible to transfer balance to other users?</u></b>
Yes, if your balance is more than 10k and you want to transfer all of them, you can send a request to support.

🆘 In case you have any problem, contact @KsCoder"""

    bot.reply_to(message, msg, parse_mode="html")

@bot.message_handler(func=lambda message: message.text == "💳 Pricing")
def pricing_command(message):
    user_id = message.chat.id
    msg = f"""<b><u>💎 Pricing 💎</u></b>

<i>👉 Choose one of the views packages and pay its cost via provided payment methods.</i>

<b><u>📜 Packages:</u></b>
<b>➊ 📦 75K views for 5$ (0.07$ per K)
➋ 📦 170K views for 10$ (0.06$ per K)
➌ 📦 400K views for 20$ (0.05$ per K)
➍ 📦 750K views for 30$ (0.04$ per K)
➎ 📦 1700K views for 50$ (0.03$ per K)
➏ 📦 5000K views for 100$ (0.02$ per K) </b>

💰 Pay with Bitcoin, USDT, BSC, BUSD,  ... 👉🏻 @KsCoder

💳️ Pay with Paypal, Paytm, WebMoney, Perfect Money, Payeer ... 👉🏻 @KsCoder

<b><u>🎁 Bonus:</u></b>
Cryptocurrency: 10%
Payeer and Perfect Money: 5%
Other methods: 0%

<b>🆔 Your id:</b> <code>{user_id}</code>
"""

    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton("💲 PayPal", url="https://t.me/KsCoder")
    button2 = InlineKeyboardButton("💳 Perfect Money",
                                   url="https://t.me/KsCoder")
    button6 = InlineKeyboardButton("💳 Webmoney", url="https://t.me/KsCoder")
    button3 = InlineKeyboardButton("💎 Bitcoin, Litecoin, USDT...",
                                   url="https://t.me/KsCoder")
    button4 = InlineKeyboardButton("💸 Paytm", url="https://t.me/KsCoder")
    button5 = InlineKeyboardButton("💰 Paytm", url="https://t.me/KsCoder")

    markup.add(button1)
    markup.add(button2, button6)
    markup.add(button3)
    markup.add(button4, button5)

    bot.reply_to(message, msg, parse_mode="html", reply_markup=markup)

#======================= Order Statistics =======================#
@bot.message_handler(func=lambda message: message.text == "📊 Order Statistics")
def show_order_stats(message):
    """Show order statistics for the user"""
    user_id = str(message.from_user.id)
    stats = get_user_orders_stats(user_id)
    
    msg = f"""📊 <b>Your Order Statistics</b>
    
🔄 <b>Total Orders Placed:</b> {stats['total']}
✅ <b>Completed Orders:</b> {stats['completed']}
⏳ <b>Pending Orders:</b> {stats['pending']}
❌ <b>Failed Orders:</b> {stats['failed']}
    
<i>Note: Status updates may take some time to reflect</i>"""
    
    bot.reply_to(message, msg, parse_mode='HTML')
#======================= Send Orders for Telegram =======================#
#======================= Send Orders for Telegram =======================#
@bot.message_handler(func=lambda message: message.text == "📱 Order Telegram")
def order_telegram_menu(message):
    """Show Telegram service options"""
    bot.reply_to(message, "📱 Telegram Services:", reply_markup=telegram_services_markup)

@bot.message_handler(func=lambda message: message.text in ["👀 Order Views", "❤️ Order Reactions", "👥 Order Members"])
def handle_telegram_order(message):
    """Handle Telegram service selection"""
    user_id = str(message.from_user.id)
    
    # Store service details in a dictionary
    services = {
        "👀 Order Views": {
            "name": "Views",
            "min": 1000,
            "max": 1000000,
            "price": 200,
            "unit": "1k views",
            "service_id": "10576"  # Your SMM panel service ID for views
        },
        "❤️ Order Reactions": {
            "name": "Reactions",
            "min": 10,
            "max": 4000,
            "price": 1000,
            "unit": "1k reactions",
            "service_id": "10617"  # Replace with actual service ID
        },
        "👥 Order Members": {
            "name": "Members",
            "min": 500,
            "max": 10000,
            "price": 7000,
            "unit": "1k members",
            "service_id": "000000"  # Replace with actual service ID
        }
    }
    
    service = services[message.text]
    
    # Create cancel markup
    cancel_back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_back_markup.row(
    KeyboardButton("✘ Cancel"),
    KeyboardButton("↩️ Go Back")
)
    
    # Store service data in user session (you may need a session system)
    # Here we'll just pass it through the register_next_step_handler
    
    msg = f"""📊 Order {service['name']}:
    
📌 Min: {service['min']}
📌 Max: {service['max']}
💰 Price: {service['price']} coins/{service['unit']}

Enter quantity:"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_telegram_quantity, 
        service
    )

def process_telegram_quantity(message, service):
    """Process the quantity input for Telegram orders"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Returning to Telegram services...", reply_markup=telegram_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=telegram_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=telegram_services_markup)
            return
            
        # Calculate cost
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=telegram_services_markup)
            return
            
        # Ask for link
        cancel_back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_back_markup.row(
        KeyboardButton("✘ Cancel"),
        
)
        
        bot.reply_to(message, "🔗 Please send the Telegram post/channel link:", reply_markup=cancel_back_markup)
        bot.register_next_step_handler(
            message, 
            process_telegram_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Please enter a valid number", reply_markup=telegram_services_markup)

def process_telegram_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    # Validate link format (basic check)
    if not re.match(r'^https?://t\.me/', link):
        bot.reply_to(message, "❌ Invalid Telegram link format", reply_markup=telegram_services_markup)
        return
    
    # Submit to SMM panel
    try:
        response = requests.post(
            SmmPanelApiUrl,
            data={
                'key': SmmPanelApi,
                'action': 'add',
                'service': service['service_id'],
                'link': link,
                'quantity': quantity
            },
            timeout=30
        )
        result = response.json()
        
        if result and 'order' in result:
            # Deduct balance
            cutBalance(str(message.from_user.id), cost)

             # Create order record
            order_data = {
                'order_id': result['order'],
                'service': service['name'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'status': 'pending',  # Initial status
                'timestamp': time.time()
            }
            add_order(str(message.from_user.id), order_data)
            
            # Send confirmation to user
            bot.reply_to(
                message,
                f"""✅ {service['name']} Order Submitted!
                
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                reply_markup=main_markup,
                disable_web_page_preview=True
            )

            # After successful order submission
            user_id = str(message.from_user.id)
            data = getData(user_id)
            if 'orders_count' not in data:
                data['orders_count'] = 0
            data['orders_count'] += 1
            updateUser(user_id, data)
            
            try:
                # Send notification to channel
                bot.send_message(
                    payment_channel,
                    f"""📢 New {service['name']} Order:
                    
👤 User: {message.from_user.first_name} (@{message.from_user.username})
🆔 ID: {message.from_user.id}
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send to channel: {e}")
                # You might want to notify admin here
            
        else:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
    except requests.Timeout:
        bot.reply_to(
            message,
            "⚠️ The order is taking longer than expected. Please check your balance and order status later.",
            reply_markup=main_markup
        )
    except Exception as e:
        print(f"Error submitting {service['name']} order: {str(e)}")
        bot.reply_to(
            message,
            f"❌ Failed to submit {service['name']} order. Please try again later.",
            reply_markup=main_markup
        )

#========================= Telegram Orders End =========================#

#========================= Order for Tiktok =========================#
@bot.message_handler(func=lambda message: message.text == "🎵 Order TikTok")
def order_tiktok_menu(message):
    """Show TikTok service options"""
    bot.reply_to(message, "🎵 TikTok Services:", reply_markup=tiktok_services_markup)


@bot.message_handler(func=lambda message: message.text in ["👀 TikTok Views", "❤️ TikTok Likes", "👥 TikTok Followers"])
def handle_tiktok_order(message):
    """Handle TikTok service selection"""
    user_id = str(message.from_user.id)
    
    # TikTok service configurations
    services = {
        "👀 TikTok Views": {
            "name": "TikTok Views [FastSpeed]",
            "min": 100,
            "max": 100000,
            "price": 13,
            "unit": "1k views",
            "service_id": "18165"
        },
        "❤️ TikTok Likes": {
            "name": "TikTok Likes [Real&Active]",
            "min": 10,
            "max": 10000,
            "price": 600,
            "unit": "1k likes",
            "service_id": "18151"
        },
        "👥 TikTok Followers": {
            "name": "TikTok Followers [Real&Active]",
            "min": 100,
            "max": 10000,
            "price": 12000,
            "unit": "1k followers",
            "service_id": "17239"
        }
    }
    
    service = services[message.text]
    
    # Create cancel markup
    cancel_back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_back_markup.row(
    KeyboardButton("✘ Cancel"),
    KeyboardButton("↩️ Go Back")
)
    
    msg = f"""📊 Order {service['name']}:
    
📌 Min: {service['min']}
📌 Max: {service['max']}
💰 Price: {service['price']} coins/{service['unit']}

Enter quantity:"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_tiktok_quantity, 
        service
    )

def process_tiktok_quantity(message, service):
    """Process the quantity input for TikTok orders"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Returning to TikTok services...", reply_markup=tiktok_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=tiktok_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=tiktok_services_markup)
            return
            
        # Calculate cost (price is per 1k, so divide quantity by 1000)
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=tiktok_services_markup)
            return
            
        # Ask for TikTok link
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, "🔗 Please send the TikTok video/profile link:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_tiktok_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Please enter a valid number", reply_markup=tiktok_services_markup)

def process_tiktok_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    # Clean the link by removing tracking parameters
    clean_link = link.split('?')[0]
    
    if not is_valid_tiktok_link(clean_link):
        error_msg = """❌ Invalid TikTok link format. Please use one of these formats:
        
- https://vm.tiktok.com/ZMBxjuyy7/
- https://www.tiktok.com/@username/video/123456789
- https://tiktok.com/t/ZMBxjuyy7/"""
        
        bot.reply_to(message, error_msg, reply_markup=tiktok_services_markup)
        return
    
    try:
        # Submit to SMM panel with cleaned link
        response = requests.post(
            SmmPanelApiUrl,
            data={
                'key': SmmPanelApi,
                'action': 'add',
                'service': service['service_id'],
                'link': clean_link,
                'quantity': quantity
            },
            timeout=30
        )
        
        if not response.ok:
            raise Exception(f"API returned {response.status_code}")
            
        result = response.json()
        
        if not result or 'order' not in result:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
        # Deduct balance
        cutBalance(str(message.from_user.id), cost)

        # Create order record
        order_data = {
            'order_id': result['order'],
            'service': service['name'],
            'quantity': quantity,
            'cost': cost,
            'link': clean_link,
            'status': 'pending',
            'timestamp': time.time()
        }
        add_order(str(message.from_user.id), order_data)
        
        # Send confirmation to user
        bot.reply_to(
            message,
            f"""✅ {service['name']} Order Submitted!
            
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {clean_link}
🆔 Order ID: {result['order']}""",
            reply_markup=main_markup,
            disable_web_page_preview=True
        )

        # Send notification to channel
        try:
            bot.send_message(
                payment_channel,
                f"""📢 New {service['name']} Order:
                
👤 User: {message.from_user.first_name} (@{message.from_user.username})
🆔 ID: {message.from_user.id}
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {clean_link}
🆔 Order ID: {result['order']}""",
                disable_web_page_preview=True
            )
        except Exception as e:
            print(f"Failed to send to channel: {e}")
            bot.send_message(
                admin_user_id,
                f"⚠️ Failed to post to {payment_channel}:\nOrder ID: {result['order']}\nError: {e}"
            )
            
    except requests.Timeout:
        bot.reply_to(
            message,
            "⚠️ The order is taking longer than expected. Please check your balance and order status later.",
            reply_markup=main_markup
        )
    except Exception as e:
        print(f"Error submitting TikTok order: {str(e)}")
        bot.reply_to(
            message,
            f"❌ Failed to submit order: {str(e)}\nPlease try again later.",
            reply_markup=main_markup
        )
        # Notify admin
        bot.send_message(
            admin_user_id,
            f"⚠️ Failed TikTok order:\nUser: {message.from_user.id}\nLink: {clean_link}\nError: {e}"
        )
#======================== End of TikTok Orders ========================#

#======================== Send Orders for Instagram =====================#
@bot.message_handler(func=lambda message: message.text == "📸 Order Instagram")
def order_instagram_menu(message):
    """Show Instagram service options"""
    bot.reply_to(message, "📸 Instagram Services:", reply_markup=instagram_services_markup)

@bot.message_handler(func=lambda message: message.text in ["🎥 Insta Vid Views", "❤️ Insta Likes", "👥 Insta Followers"])
def handle_instagram_order(message):
    """Handle Instagram service selection"""
    user_id = str(message.from_user.id)
    
    services = {
        "🎥 Insta Vid Views": {
            "name": "Instagram Video Views [InstantSpeed]",
            "min": 100,
            "max": 100000,
            "price": 53,
            "unit": "1k views",
            "service_id": "17350",
            "link_hint": "Instagram video link"
        },
        "❤️ Insta Likes": {
            "name": "Instagram Likes [PowerQuality]",
            "min": 500,
            "max": 10000,
            "price": 1000,
            "unit": "1k likes",
            "service_id": "9578",
            "link_hint": "Instagram post link"
        },
        "👥 Insta Followers": {
            "name": "Instagram Followers [OldAccountsWithPosts]",
            "min": 500,
            "max": 10000,
            "price": 13000,
            "unit": "1k followers",
            "service_id": "18808",
            "link_hint": "Instagram profile link"
        }
    }
    
    service = services[message.text]
    
    cancel_back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_back_markup.row(
        KeyboardButton("✘ Cancel"),
        KeyboardButton("↩️ Go Back")
    )
    
    msg = f"""📊 Order {service['name']}:
    
📌 Min: {service['min']}
📌 Max: {service['max']}
💰 Price: {service['price']} coins/{service['unit']}

Enter quantity:"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_instagram_quantity, 
        service
    )

def process_instagram_quantity(message, service):
    """Process Instagram order quantity"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Returning to Instagram services...", reply_markup=instagram_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=instagram_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=instagram_services_markup)
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=instagram_services_markup)
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, f"🔗 Please send the {service['link_hint']}:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_instagram_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Please enter a valid number", reply_markup=instagram_services_markup)

def process_instagram_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    # Basic Instagram link validation
    if not re.match(r'^https?://(www\.)?instagram\.com/', link):
        bot.reply_to(message, "❌ Invalid Instagram link format", reply_markup=instagram_services_markup)
        return
    
    # Submit to SMM panel
    try:
        response = requests.post(
            SmmPanelApiUrl,
            data={
                'key': SmmPanelApi,
                'action': 'add',
                'service': service['service_id'],
                'link': link,
                'quantity': quantity
            },
            timeout=30
        )
        result = response.json()
        
        if result and 'order' in result:
            # Deduct balance
            cutBalance(str(message.from_user.id), cost)

             # Create order record
            order_data = {
                'order_id': result['order'],
                'service': service['name'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'status': 'pending',  # Initial status
                'timestamp': time.time()
            }
            add_order(str(message.from_user.id), order_data)
            
            # Send confirmation to user
            bot.reply_to(
                message,
                f"""✅ {service['name']} Order Submitted!
                
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                reply_markup=main_markup,
                disable_web_page_preview=True
            )

            # After successful order submission
            user_id = str(message.from_user.id)
            data = getData(user_id)
            if 'orders_count' not in data:
                data['orders_count'] = 0
            data['orders_count'] += 1
            updateUser(user_id, data)
            
            try:
                # Send notification to channel
                bot.send_message(
                    payment_channel,
                    f"""📢 New {service['name']} Order:
                    
👤 User: {message.from_user.first_name} (@{message.from_user.username})
🆔 ID: {message.from_user.id}
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send to channel: {e}")
                # You might want to notify admin here
            
        else:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
    except requests.Timeout:
        bot.reply_to(
            message,
            "⚠️ The order is taking longer than expected. Please check your balance and order status later.",
            reply_markup=main_markup
        )
    except Exception as e:
        print(f"Error submitting {service['name']} order: {str(e)}")
        bot.reply_to(
            message,
            f"❌ Failed to submit {service['name']} order. Please try again later.",
            reply_markup=main_markup
        )
#======================== End of Instagram Orders ===========================#

#======================== Send Orders for Youtube =====================#
@bot.message_handler(func=lambda message: message.text == "▶️ Order YouTube")
def order_youtube_menu(message):
    """Show YouTube service options"""
    bot.reply_to(message, "▶️ YouTube Services:", reply_markup=youtube_services_markup)

@bot.message_handler(func=lambda message: message.text in ["▶️ YT Views", "👍 YT Likes", "👥 YT Subscribers"])
def handle_youtube_order(message):
    """Handle YouTube service selection"""
    user_id = str(message.from_user.id)
    
    services = {
        "▶️ YT Views": {
            "name": "YouTube Views [100% Real]",
            "min": 15000,
            "max": 1000000,
            "price": 6000,
            "unit": "1k views",
            "service_id": "17460",
            "link_hint": "YouTube video link"
        },
        "👍 YT Likes": {
            "name": "YouTube Likes [Real]",
            "min": 500,
            "max": 10000,
            "price": 2000,
            "unit": "1k likes",
            "service_id": "181446",
            "link_hint": "YouTube video link"
        },
        "👥 YT Subscribers": {
            "name": "YouTube Subscribers [Cheapest]",
            "min": 500,
            "max": 10000,
            "price": 12000,
            "unit": "1k subscribers",
            "service_id": "16912",
            "link_hint": "YouTube channel link"
        }
    }
    
    service = services[message.text]
    
    cancel_back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_back_markup.row(
        KeyboardButton("✘ Cancel"),
        KeyboardButton("↩️ Go Back")
    )
    
    msg = f"""📊 Order {service['name']}:
    
📌 Min: {service['min']}
📌 Max: {service['max']}
💰 Price: {service['price']} coins/{service['unit']}

Enter quantity:"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_youtube_quantity, 
        service
    )

def process_youtube_quantity(message, service):
    """Process YouTube order quantity"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Returning to YouTube services...", reply_markup=youtube_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=youtube_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=youtube_services_markup)
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=youtube_services_markup)
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, f"🔗 Please send the {service['link_hint']}:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_youtube_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Please enter a valid number", reply_markup=youtube_services_markup)

def process_youtube_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    # Basic YouTube link validation
    if not re.match(r'^https?://(www\.)?youtube\.com/', link):
        bot.reply_to(message, "❌ Invalid YouTube link format", reply_markup=youtube_services_markup)
        return
    
    # Submit to SMM panel
    try:
        response = requests.post(
            SmmPanelApiUrl,
            data={
                'key': SmmPanelApi,
                'action': 'add',
                'service': service['service_id'],
                'link': link,
                'quantity': quantity
            },
            timeout=30
        )
        result = response.json()
        
        if result and 'order' in result:
            # Deduct balance
            cutBalance(str(message.from_user.id), cost)

             # Create order record
            order_data = {
                'order_id': result['order'],
                'service': service['name'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'status': 'pending',  # Initial status
                'timestamp': time.time()
            }
            add_order(str(message.from_user.id), order_data)
            
            # Send confirmation to user
            bot.reply_to(
                message,
                f"""✅ {service['name']} Order Submitted!
                
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                reply_markup=main_markup,
                disable_web_page_preview=True
            )

            # After successful order submission
            user_id = str(message.from_user.id)
            data = getData(user_id)
            if 'orders_count' not in data:
                data['orders_count'] = 0
            data['orders_count'] += 1
            updateUser(user_id, data)
            
            try:
                # Send notification to channel
                bot.send_message(
                    payment_channel,
                    f"""📢 New {service['name']} Order:
                    
👤 User: {message.from_user.first_name} (@{message.from_user.username})
🆔 ID: {message.from_user.id}
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send to channel: {e}")
                # You might want to notify admin here
            
        else:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
    except requests.Timeout:
        bot.reply_to(
            message,
            "⚠️ The order is taking longer than expected. Please check your balance and order status later.",
            reply_markup=main_markup
        )
    except Exception as e:
        print(f"Error submitting {service['name']} order: {str(e)}")
        bot.reply_to(
            message,
            f"❌ Failed to submit {service['name']} order. Please try again later.",
            reply_markup=main_markup
        )
#======================== End of Youtube Orders =====================#

#======================== Send Orders for Facebook =====================#
@bot.message_handler(func=lambda message: message.text == "📘 Order Facebook")
def order_facebook_menu(message):
    """Show Facebook service options"""
    bot.reply_to(message, "📘 Facebook Services:", reply_markup=facebook_services_markup)

@bot.message_handler(func=lambda message: message.text in ["👤 Profile Followers", "📄 Page Followers", "🎥 Video/Reel Views", "❤️ Post Likes"])
def handle_facebook_order(message):
    """Handle Facebook service selection"""
    user_id = str(message.from_user.id)
    
    services = {
        "👤 Profile Followers": {
            "name": "Facebook Profile Followers [HighQuality]",
            "min": 500,
            "max": 100000,
            "price": 10000,
            "unit": "1k followers",
            "service_id": "17332",
            "link_hint": "Facebook profile link"
        },
        "📄 Page Followers": {
            "name": "Facebook Page Followers [NonDrop]",
            "min": 500,
            "max": 10000,
            "price": 10000,
            "unit": "1k followers",
            "service_id": "17759",
            "link_hint": "Facebook page link"
        },
        "🎥 Video/Reel Views": {
            "name": "Facebook Video/Reel Views [NonDrop]",
            "min": 500,
            "max": 10000,
            "price": 500,
            "unit": "1k views",
            "service_id": "17766",
            "link_hint": "Facebook video/reel link"
        },
        "❤️ Post Likes": {
            "name": "Facebook Post Likes [NoRefill]",
            "min": 100,
            "max": 10000,
            "price": 5000,
            "unit": "1k likes",
            "service_id": "18860",
            "link_hint": "Facebook post link"
        }
    }
    
    service = services[message.text]
    
    cancel_back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_back_markup.row(
        KeyboardButton("✘ Cancel"),
        KeyboardButton("↩️ Go Back")
    )
    
    msg = f"""📊 Order {service['name']}:
    
📌 Min: {service['min']}
📌 Max: {service['max']}
💰 Price: {service['price']} coins/{service['unit']}

Enter quantity:"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_facebook_quantity, 
        service
    )

def process_facebook_quantity(message, service):
    """Process Facebook order quantity"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Returning to Facebook services...", reply_markup=facebook_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=facebook_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=facebook_services_markup)
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=facebook_services_markup)
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, f"🔗 Please send the {service['link_hint']}:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_facebook_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Please enter a valid number", reply_markup=facebook_services_markup)

def process_facebook_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    # Basic Facebook link validation
    if not re.match(r'^https?://(www\.)?facebook\.com/', link):
        bot.reply_to(message, "❌ Invalid Facebook link format", reply_markup=facebook_services_markup)
        return
    
    # Submit to SMM panel
    try:
        response = requests.post(
            SmmPanelApiUrl,
            data={
                'key': SmmPanelApi,
                'action': 'add',
                'service': service['service_id'],
                'link': link,
                'quantity': quantity
            },
            timeout=30
        )
        result = response.json()
        
        if result and 'order' in result:
            # Deduct balance
            cutBalance(str(message.from_user.id), cost)

             # Create order record
            order_data = {
                'order_id': result['order'],
                'service': service['name'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'status': 'pending',  # Initial status
                'timestamp': time.time()
            }
            add_order(str(message.from_user.id), order_data)
            
            # Send confirmation to user
            bot.reply_to(
                message,
                f"""✅ {service['name']} Order Submitted!
                
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                reply_markup=main_markup,
                disable_web_page_preview=True
            )

            # After successful order submission
            user_id = str(message.from_user.id)
            data = getData(user_id)
            if 'orders_count' not in data:
                data['orders_count'] = 0
            data['orders_count'] += 1
            updateUser(user_id, data)
            
            try:
                # Send notification to channel
                bot.send_message(
                    payment_channel,
                    f"""📢 New {service['name']} Order:
                    
👤 User: {message.from_user.first_name} (@{message.from_user.username})
🆔 ID: {message.from_user.id}
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send to channel: {e}")
                # You might want to notify admin here
            
        else:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
    except requests.Timeout:
        bot.reply_to(
            message,
            "⚠️ The order is taking longer than expected. Please check your balance and order status later.",
            reply_markup=main_markup
        )
    except Exception as e:
        print(f"Error submitting {service['name']} order: {str(e)}")
        bot.reply_to(
            message,
            f"❌ Failed to submit {service['name']} order. Please try again later.",
            reply_markup=main_markup
        )
#======================== End of Facebook Orders =====================#

#======================== Send Orders for Whastapp =====================#
@bot.message_handler(func=lambda message: message.text == "💬 Order WhatsApp")
def order_whatsapp_menu(message):
    """Show WhatsApp service options"""
    bot.reply_to(message, "💬 WhatsApp Services:", reply_markup=whatsapp_services_markup)

@bot.message_handler(func=lambda message: message.text in ["👥 Channel Members", "😀 Channel EmojiReaction"])
def handle_whatsapp_order(message):
    """Handle WhatsApp service selection"""
    user_id = str(message.from_user.id)
    
    services = {
        "👥 Channel Members": {
            "name": "WhatsApp Channel Members [EU Users]",
            "min": 500,
            "max": 40000,
            "price": 16000,
            "unit": "1k members",
            "service_id": "18855",
            "link_hint": "WhatsApp channel invite link"
        },
        "😀 Channel EmojiReaction": {
            "name": "WhatsApp Channel EmojiReaction [Mixed]",
            "min": 500,
            "max": 10000,
            "price": 3000,
            "unit": "1k reactions",
            "service_id": "18832",
            "link_hint": "WhatsApp channel message link"
        }
    }
    
    service = services[message.text]
    
    cancel_back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_back_markup.row(
        KeyboardButton("✘ Cancel"),
        KeyboardButton("↩️ Go Back")
    )
    
    msg = f"""📊 Order {service['name']}:
    
📌 Min: {service['min']}
📌 Max: {service['max']}
💰 Price: {service['price']} coins/{service['unit']}

Enter quantity:"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_whatsapp_quantity, 
        service
    )

def process_whatsapp_quantity(message, service):
    """Process WhatsApp order quantity"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Returning to WhatsApp services...", reply_markup=whatsapp_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=whatsapp_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=whatsapp_services_markup)
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=whatsapp_services_markup)
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, f"🔗 Please send the {service['link_hint']}:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_whatsapp_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Please enter a valid number", reply_markup=whatsapp_services_markup)

def process_whatsapp_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    # Basic WhatsApp link validation
    if not re.match(r'^https?://(chat\.whatsapp\.com|wa\.me)/', link):
        bot.reply_to(message, "❌ Invalid WhatsApp link format", reply_markup=whatsapp_services_markup)
        return
    
    # Submit to SMM panel
    try:
        response = requests.post(
            SmmPanelApiUrl,
            data={
                'key': SmmPanelApi,
                'action': 'add',
                'service': service['service_id'],
                'link': link,
                'quantity': quantity
            },
            timeout=30
        )
        result = response.json()
        
        if result and 'order' in result:
            # Deduct balance
            cutBalance(str(message.from_user.id), cost)

             # Create order record
            order_data = {
                'order_id': result['order'],
                'service': service['name'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'status': 'pending',  # Initial status
                'timestamp': time.time()
            }
            add_order(str(message.from_user.id), order_data)
            
            # Send confirmation to user
            bot.reply_to(
                message,
                f"""✅ {service['name']} Order Submitted!
                
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                reply_markup=main_markup,
                disable_web_page_preview=True
            )

            # After successful order submission
            user_id = str(message.from_user.id)
            data = getData(user_id)
            if 'orders_count' not in data:
                data['orders_count'] = 0
            data['orders_count'] += 1
            updateUser(user_id, data)
            
            try:
                # Send notification to channel
                bot.send_message(
                    payment_channel,
                    f"""📢 New {service['name']} Order:
                    
👤 User: {message.from_user.first_name} (@{message.from_user.username})
🆔 ID: {message.from_user.id}
📦 Service: {service['name']}
🔢 Quantity: {quantity}
💰 Cost: {cost} coins
📎 Link: {link}
🆔 Order ID: {result['order']}""",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send to channel: {e}")
                # You might want to notify admin here
            
        else:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
    except requests.Timeout:
        bot.reply_to(
            message,
            "⚠️ The order is taking longer than expected. Please check your balance and order status later.",
            reply_markup=main_markup
        )
    except Exception as e:
        print(f"Error submitting {service['name']} order: {str(e)}")
        bot.reply_to(
            message,
            f"❌ Failed to submit {service['name']} order. Please try again later.",
            reply_markup=main_markup
        )
#======================== End of Whastapp Orders =====================#

#=================== The back button handler =========================================
@bot.message_handler(func=lambda message: message.text in ["↩️ Go Back", "✘ Cancel"])
def handle_back_buttons(message):
    """Handle all back/cancel buttons"""
    if message.text == "↩️ Go Back":
        # Determine where to go back based on context
        if message.text in ["👀 Order Views", "❤️ Order Reactions", "👥 Order Members"]:
            bot.reply_to(message, "Returning to Telegram services...", reply_markup=telegram_services_markup)
        elif message.text in ["👀 Order TikTok Views", "❤️ Order Likes", "👥 Order Followers"]:
            bot.reply_to(message, "Returning to TikTok services...", reply_markup=tiktok_services_markup)
        elif message.text in ["🎥 Insta Vid Views", "❤️ Insta Likes", "👥 Insta Followers"]:
            bot.reply_to(message, "Returning to Instagram services...", reply_markup=instagram_services_markup)
        elif message.text in ["▶️ YT Views", "👍 YT Likes", "👥 YT Subscribers"]:
            bot.reply_to(message, "Returning to YouTube services...", reply_markup=youtube_services_markup)
        elif message.text in ["👤 Profile Followers", "📄 Page Followers", "🎥 Video/Reel Views", "❤️ Post Likes"]:
            bot.reply_to(message, "Returning to Facebook services...", reply_markup=facebook_services_markup)
        elif message.text in ["👥 Channel Members", "😀 Channel EmojiReaction"]:
            bot.reply_to(message, "Returning to WhatsApp services...", reply_markup=whatsapp_services_markup)
        else:
            # Default back to Send Orders menu
            bot.reply_to(message, "Returning to order options...", reply_markup=send_orders_markup)
    else:
        # Cancel goes straight to main menu
        bot.reply_to(message, "Operation cancelled.", reply_markup=main_markup)



@bot.message_handler(commands=['addcoins'])
def add_coins(message):
    if message.from_user.id != admin_user_id:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, "⚠️ Usage: /addcoins <user_id> <amount>")
            return

        user_id = args[1]  # Keep as string to match file naming
        try:
            amount = float(args[2])
        except ValueError:
            bot.reply_to(message, "⚠️ Amount must be a number")
            return

        # Ensure the user exists
        if not isExists(user_id):
            initial_data = {
                "user_id": user_id,
                "balance": "0.00",  # Note the string format
                "ref_by": "none",
                "referred": 0,
                "welcome_bonus": 0,
                "total_refs": 0,
            }
            insertUser(user_id, initial_data)

        if addBalance(user_id, amount):
            bot.reply_to(message, f"✅ Successfully added {amount} coins to user {user_id}.")
            # Send confirmation to the user if possible
            try:
                bot.send_message(user_id, f"📢 Admin has added {amount} coins to your account!")
            except:
                pass
        else:
            bot.reply_to(message, f"❌ Failed to add coins to user {user_id}.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")

@bot.message_handler(commands=['removecoins'])
def remove_coins(message):
    print(f"\nDEBUG: Received removecoins command: {message.text}")  # Log the command
    
    if message.from_user.id != admin_user_id:
        error_msg = "❌ You are not authorized to use this command."
        print(f"DEBUG: Unauthorized access attempt by {message.from_user.id}")
        bot.reply_to(message, error_msg)
        return

    try:
        args = message.text.split()
        if len(args) != 3:
            error_msg = "⚠️ Usage: /removecoins <user_id> <amount>"
            print(f"DEBUG: Invalid arguments: {args}")
            bot.reply_to(message, error_msg)
            return

        user_id = args[1]
        try:
            amount = float(args[2])
            print(f"DEBUG: Parsed user_id: {user_id}, amount: {amount}")
        except ValueError:
            error_msg = "⚠️ Amount must be a number"
            print(f"DEBUG: Invalid amount format: {args[2]}")
            bot.reply_to(message, error_msg)
            return

        # Check if user exists
        user_exists = isExists(user_id)
        print(f"DEBUG: User {user_id} exists: {user_exists}")
        
        if not user_exists:
            bot.reply_to(message, f"❌ User {user_id} does not exist.")
            return

        # Get current balance for debugging
        user_data = getData(user_id)
        current_balance = float(user_data['balance'])
        print(f"DEBUG: Current balance: {current_balance}, Amount to remove: {amount}")

        if cutBalance(user_id, amount):
            success_msg = f"✅ Successfully removed {amount} coins from user {user_id}."
            print(f"DEBUG: {success_msg}")
            bot.reply_to(message, success_msg)
            
            # Verify the new balance
            updated_data = getData(user_id)
            print(f"DEBUG: New balance: {updated_data['balance']}")
        else:
            error_msg = f"❌ Failed to remove coins. User {user_id} may have insufficient balance."
            print(f"DEBUG: {error_msg}")
            bot.reply_to(message, error_msg)
            
    except Exception as e:
        error_msg = f"⚠️ Error: {str(e)}"
        print(f"DEBUG: Exception occurred: {error_msg}")
        print(f"Full traceback:\n{traceback.format_exc()}")  # Add this at top of file: import traceback
        bot.reply_to(message, error_msg)


# ================= ADMIN COMMANDS ================== #
@bot.message_handler(commands=['addcoins', 'removecoins'])
def handle_admin_commands(message):
    if message.from_user.id != admin_user_id:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message, f"⚠️ Usage: {args[0]} <user_id> <amount>")
            return
            
        user_id = args[1]
        try:
            amount = float(args[2])
        except ValueError:
            bot.reply_to(message, "⚠️ Amount must be a number")
            return
            
        if args[0] == '/addcoins':
            if not isExists(user_id):
                initial_data = {
                    "user_id": user_id,
                    "balance": "0.00",
                    "ref_by": "none",
                    "referred": 0,
                    "welcome_bonus": 0,
                    "total_refs": 0,
                }
                insertUser(user_id, initial_data)
                
            if addBalance(user_id, amount):
                bot.reply_to(message, f"✅ Added {amount} coins to user {user_id}")
                try:
                    bot.send_message(user_id, f"📢 Admin added {amount} coins to your account!")
                except:
                    pass
            else:
                bot.reply_to(message, "❌ Failed to add coins")
                
        elif args[0] == '/removecoins':
            if cutBalance(user_id, amount):
                bot.reply_to(message, f"✅ Removed {amount} coins from user {user_id}")
                try:
                    bot.send_message(user_id, f"📢 Admin removed {amount} coins from your account!")
                except:
                    pass
            else:
                bot.reply_to(message, "❌ Failed to remove coins (insufficient balance or user doesn't exist)")
                
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {str(e)}")
        print(f"Admin command error: {traceback.format_exc()}")

@bot.message_handler(func=lambda message: message.text == "🛠 Admin Panel")
def admin_panel(message):
    if message.from_user.id != admin_user_id:
        bot.reply_to(message, "❌ You are not authorized to access this panel.")
        return
    
    bot.reply_to(message, "🛠 Admin Panel:", reply_markup=admin_markup)

@bot.message_handler(func=lambda message: message.text in ["➕ Add Coins", "➖ Remove Coins"] and message.from_user.id == admin_user_id)
def admin_actions(message):
    """Guide admin to use addcoins or removecoins commands"""
    if "Add" in message.text:
        bot.reply_to(message, "Send: /addcoins <user_id> <amount>")
    elif "Remove" in message.text:
        bot.reply_to(message, "Send: /removecoins <user_id> <amount>")

@bot.message_handler(func=lambda message: message.text == "🔙 Main Menu")
def back_to_main(message):
    bot.reply_to(message, "Returning to main menu...", reply_markup=main_markup)

#========== New Commands ==============#
# Admin Stats Command
@bot.message_handler(func=lambda m: m.text == "📊 Analytics" and m.from_user.id == admin_user_id)
def show_analytics(message):
    """Show comprehensive bot analytics"""
    total_users = get_user_count()
    active_users = get_active_users(7)
    total_orders = get_total_orders()
    total_deposits = get_total_deposits()
    top_referrer = get_top_referrer()
    
    # Format top referrer display
    if top_referrer['username']:
        referrer_display = f"@{top_referrer['username']} ({top_referrer['count']} invites)"
    elif top_referrer['user_id']:
        referrer_display = f"User {top_referrer['user_id']} ({top_referrer['count']} invites)"
    else:
        referrer_display = "No referrals yet"
    
    msg = f"""📊 <b>Bot Analytics</b>
    
👤 <b>Total Users:</b> {total_users}
🔥 <b>Active Users (7 Days):</b> {active_users}
🚀 <b>Orders Processed:</b> {total_orders}
💰 <b>Total Deposits:</b> {total_deposits:.2f} coins
🎯 <b>Top Referrer:</b> {referrer_display}"""
    
    bot.reply_to(message, msg, parse_mode='HTML')

# Broadcast Command
@bot.message_handler(func=lambda m: m.text == "📢 Broadcast" and m.from_user.id == admin_user_id)
def broadcast_start(message):
    """Start broadcast process"""
    msg = bot.reply_to(message, "📢 Enter the message you want to broadcast to all users:")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    """Send message to all users"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Broadcast cancelled.", reply_markup=admin_markup)
        return
    
    users = get_all_users()
    success = 0
    failed = 0
    
    bot.reply_to(message, f"⏳ Sending broadcast to {len(users)} users...")
    
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 Announcement:\n\n{message.text}")
            success += 1
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")
            failed += 1
        time.sleep(0.1)  # Rate limiting
    
    bot.reply_to(message, f"""✅ Broadcast Complete:
    
📤 Sent: {success}
❌ Failed: {failed}""", reply_markup=admin_markup)

# Ban User Command
@bot.message_handler(func=lambda m: m.text == "⛔ Ban User" and m.from_user.id == admin_user_id)
def ban_user_start(message):
    """Start ban user process"""
    msg = bot.reply_to(message, "Enter user ID to ban:")
    bot.register_next_step_handler(msg, process_ban_user)

def process_ban_user(message):
    """Ban a user"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Ban cancelled.", reply_markup=admin_markup)
        return
    
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.reply_to(message, "❌ Invalid user ID. Must be numeric.", reply_markup=admin_markup)
        return
    
    if is_banned(user_id):
        bot.reply_to(message, "⚠️ User is already banned.", reply_markup=admin_markup)
        return
    
    ban_user(user_id)
    
    # Send notification to banned user
    try:
        appeal_markup = InlineKeyboardMarkup()
        appeal_markup.add(InlineKeyboardButton("📩 Send Appeal", url="https://t.me/Silando"))
        
        bot.send_message(
            user_id,
            f"⛔ You have been banned from using this bot.\n\n"
            f"If you believe this was a mistake, you can appeal your ban:",
            reply_markup=appeal_markup
        )
    except Exception as e:
        print(f"Could not notify banned user: {e}")
    
    bot.reply_to(message, f"✅ User {user_id} has been banned.", reply_markup=admin_markup)

# Unban User Command
@bot.message_handler(func=lambda m: m.text == "✅ Unban User" and m.from_user.id == admin_user_id)
def unban_user_start(message):
    """Start unban user process"""
    msg = bot.reply_to(message, "Enter user ID to unban:")
    bot.register_next_step_handler(msg, process_unban_user)

def process_unban_user(message):
    """Unban a user"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Unban cancelled.", reply_markup=admin_markup)
        return
    
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.reply_to(message, "❌ Invalid user ID. Must be numeric.", reply_markup=admin_markup)
        return
    
    if not is_banned(user_id):
        bot.reply_to(message, "⚠️ User is not currently banned.", reply_markup=admin_markup)
        return
    
    unban_user(user_id)
    
    # Notify unbanned user
    try:
        bot.send_message(user_id, "✅ Your ban has been lifted. You can now use the bot again.")
    except Exception as e:
        print(f"Could not notify unbanned user: {e}")
    
    bot.reply_to(message, f"✅ User {user_id} has been unbanned.", reply_markup=admin_markup)

# List Banned Command
@bot.message_handler(func=lambda m: m.text == "📋 List Banned" and m.from_user.id == admin_user_id)
def list_banned(message):
    """Show list of banned users"""
    banned_users = get_banned_users()
    
    if not banned_users:
        bot.reply_to(message, "ℹ️ No users are currently banned.", reply_markup=admin_markup)
        return
    
    msg = "⛔ Banned Users:\n\n" + "\n".join(banned_users)
    bot.reply_to(message, msg, reply_markup=admin_markup)

#==================== Leaderboard Command ==========================#
@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def show_leaderboard(message):
    """Show top 10 users by orders"""
    top_users = get_top_users(10)
    
    if not top_users:
        bot.reply_to(message, "🏆 No order data available yet.", reply_markup=main_markup)
        return
    
    leaderboard = ["🏆 Top Users by Orders:"]
    for i, (user_id, count) in enumerate(top_users, 1):
        try:
            user = bot.get_chat(user_id)
            name = user.first_name or f"User {user_id}"
            leaderboard.append(f"{i}. {name}: {count} orders")
        except:
            leaderboard.append(f"{i}. User {user_id}: {count} orders")
    
    bot.reply_to(message, "\n".join(leaderboard), reply_markup=main_markup)

#======================= Function to periodically check order status ====================#
def check_pending_orders():
    """Periodically check and update status of pending orders"""
    account_folder = 'Account'
    if not os.path.exists(account_folder):
        return
    
    for filename in os.listdir(account_folder):
        if filename.endswith('.json'):
            user_id = filename.split('.')[0]
            filepath = os.path.join(account_folder, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                if 'orders' in data:
                    updated = False
                    for order in data['orders']:
                        if order.get('status') == 'pending':
                            # Check with your SMM API for status
                            try:
                                response = requests.post(
                                    SmmPanelApiUrl,
                                    data={
                                        'key': SmmPanelApi,
                                        'action': 'status',
                                        'order': order['order_id']
                                    },
                                    timeout=10
                                )
                                result = response.json()
                                
                                if result and 'status' in result:
                                    new_status = result['status'].lower()
                                    if new_status in ['completed', 'partial', 'processing', 'failed']:
                                        if new_status != order['status']:
                                            order['status'] = new_status
                                            updated = True
                            except:
                                continue
                    
                    if updated:
                        with open(filepath, 'w') as f:
                            json.dump(data, f)
            except:
                continue

# Run this periodically (e.g., every hour)
def order_status_checker():
    while True:
        check_pending_orders()
        time.sleep(3600)  # Check every hour

# Start the checker thread when bot starts
import threading
checker_thread = threading.Thread(target=order_status_checker)
checker_thread.daemon = True
checker_thread.start()



#======================== Logging Setup =====================#
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='bot.log'
)
logger = logging.getLogger(__name__)

print(f"Account folder exists: {os.path.exists('Account')}")
print(f"Files in Account: {os.listdir('Account')}")

print(f"Can write to Account: {os.access('Account', os.W_OK)}")

#======================== Set Bot Commands =====================#
if __name__ == '__main__':
    set_bot_commands()
    print("Bot is Ready to Hustle...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Bot polling failed: {e}")
            time.sleep(10)
