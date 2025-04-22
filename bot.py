import telebot
import re
import requests
import time
import os
import json
import traceback
import logging
import psutil
import threading
from datetime import datetime
import pytz
from functools import wraps
from flask import Flask, jsonify
from dotenv import load_dotenv
from telebot.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from functions import (insertUser, track_exists, addBalance, cutBalance, getData,
                       addRefCount, isExists, setWelcomeStaus, setReferredStatus, updateUser, 
                       ban_user, unban_user, get_all_users, is_banned, get_banned_users, 
                       get_top_users, get_user_count, get_active_users, get_total_orders, 
                       get_total_deposits, get_top_referrer, get_user_orders_stats, cleanup_previous_messages) # Import your functions from functions.py

if not os.path.exists('Account'):
    os.makedirs('Account')

# Load environment variables from .env file
load_dotenv()

# Add at the top (with other global variables)
user_last_bot_message = {}  # { user_id: bot_message_id }
user_last_user_message = {}  # { user_id: user_message_id }

# =============== Bot Configuration =============== #
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
SmmPanelApi = os.getenv("SMM_PANEL_API_KEY")
SmmPanelApiUrl = os.getenv("SMM_PANEL_API_URL")
# Simple admin IDs loading (comma-separated in .env)
# Replace the single admin line with:
admin_user_ids = [int(id.strip()) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id.strip()]

bot = telebot.TeleBot(bot_token)

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
button6 = KeyboardButton("🏆 Leaderboard")
button7 = KeyboardButton("📜 Help")
button8 = KeyboardButton("🛠 Admin Panel")

main_markup.add(button1, button2)
main_markup.add(button3, button4)
main_markup.add(button5, button6)
main_markup.add(button7)
main_markup.add(button8)

# Admin keyboard markup
admin_markup = ReplyKeyboardMarkup(resize_keyboard=True)
admin_markup.row("➕ Add Coins", "➖ Remove Coins")
admin_markup.row("📌 Pin Message", "📤 Broadcast")
admin_markup.row("🔒 Ban User", "✅ Unban User")
admin_markup.row("📋 List Banned", "👤 User Info")  # New
admin_markup.row("🖥 Server Status", "📤 Export Data")  # New
admin_markup.row("📦 Order Manager", "📊 Analytics")  # New
admin_markup.row("🔧 Maintenance")
admin_markup.row("🔙 Main Menu")
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
    KeyboardButton("👀 Order Views"),
    KeyboardButton("❤️ Order Likes")
)
tiktok_services_markup.row(
    KeyboardButton("👥 Order Followers"),
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

#==================================== MongoDB Integration =======================#
# Replace the existing add_order function in bot.py with this:
def add_order(user_id, order_data):
    """Add a new order to user's history using MongoDB"""
    try:
        # Ensure the order_data has required fields
        order_data['user_id'] = str(user_id)
        if 'timestamp' not in order_data:
            order_data['timestamp'] = time.time()
        if 'status' not in order_data:
            order_data['status'] = 'pending'
        
        # Add to MongoDB
        from functions import add_order as mongo_add_order
        return mongo_add_order(user_id, order_data)
    except Exception as e:
        print(f"Error adding order to MongoDB: {e}")
        return False
#==================================== Channel Membership Check =======================#
#================================== Force Join Method =======================================#
required_channels = ["SmmBoosterz", "Megahubbots", "Freenethubz", "Freenethubchannel", "smmserviceslogs"]  # Channel usernames without "@"
payment_channel = "@smmserviceslogs"  # Channel for payment notifications

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
            "🚨 *Tᴏ Uꜱᴇ Tʜɪꜱ Bᴏᴛ, Yᴏᴜ Mᴜꜱᴛ Jᴏɪɴ Tʜᴇ RᴇQᴜɪʀᴇᴅ Cʜᴀɴɴᴇʟꜱ Fɪʀꜱᴛ!* 🚨\ɴ\ɴ"
          "Cʟɪᴄᴋ Tʜᴇ Bᴜᴛᴛᴏɴꜱ Bᴇʟᴏᴡ Tᴏ Jᴏɪɴ, Tʜᴇɴ Pʀᴇꜱꜱ *'✅ I Joined'*. ",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("MAIN CHANNEL", url="https://t.me/SmmBoosterz")],
                [InlineKeyboardButton("BOTS UPDATE", url="https://t.me/Megahubbots")],
                [InlineKeyboardButton("PROMOTER CHANNEL", url="https://t.me/Freenethubz")],
                [InlineKeyboardButton("BACKUP CHANNEL", url="https://t.me/Freenethubchannel")],
                [InlineKeyboardButton("LOGS CHANNEL", url="https://t.me/smmserviceslogs")],
                [InlineKeyboardButton("WHASTAPP CHANNEL", url="https://whatsapp.com/channel/0029VaDnY2y0rGiPV41aSX0l")],
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
            text="✅ 𝐘𝐨𝐮 𝐚𝐫𝐞 𝐯𝐞𝐫𝐢𝐟𝐢𝐞𝐝! 𝐘𝐨𝐮 𝐜𝐚𝐧 𝐧𝐨𝐰 𝐮𝐬𝐞 𝐭𝐡𝐞 𝐛𝐨𝐭. 𝐂𝐥𝐢𝐜𝐤 /start 𝐚𝐠𝐚𝐢𝐧"
        )
        send_welcome(call.message)  # Restart the welcome process
    else:
        bot.answer_callback_query(
            callback_query_id=call.id,
            text="❌ Y̶o̶u̶ ̶h̶a̶v̶e̶n̶'̶t̶ ̶j̶o̶i̶n̶e̶d̶ ̶a̶l̶l̶ ̶t̶h̶e̶ ̶r̶e̶q̶u̶i̶r̶e̶d̶ ̶c̶h̶a̶n̶n̶e̶l̶s̶ ̶y̶e̶t̶!",
            show_alert=True
        )
#==============================================#
#========================= utility function to check bans =================#
# Enhanced check_ban decorator to include maintenance check
def check_ban(func):
    @wraps(func)
    def wrapped(message, *args, **kwargs):
        user_id = str(message.from_user.id)
        
        # Check maintenance mode
        if maintenance_mode and user_id not in map(str, admin_user_ids):
            bot.reply_to(message, maintenance_message)
            return
            
        # Check ban status
        if is_banned(user_id):
            bot.reply_to(message, "⛔ ❝𝐘𝐨𝐮 𝐡𝐚𝐯𝐞 𝐛𝐞𝐞𝐧 𝐛𝐚𝐧𝐧𝐞𝐝 𝐟𝐫𝐨𝐦 𝐮𝐬𝐢𝐧𝐠 𝐭𝐡𝐢𝐬 𝐛𝐨𝐭❞.")
            return
            
        return func(message, *args, **kwargs)
    return wrapped
#================== Send Orders Button ============================#
@bot.message_handler(func=lambda message: message.text == "📤 Send Orders")
@check_ban
def send_orders_menu(message):
    """Handle the main Send Orders menu"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    # Update last activity and username
    data = getData(user_id)
    data['last_activity'] = time.time()
    data['username'] = message.from_user.username
    updateUser(user_id, data)

    # Check if the user has joined all required channels
    if not check_membership_and_prompt(user_id, message):
        return  # Stop execution until the user joins

    # If the user is a member, show the Send Orders menu
    sent_msg = bot.reply_to(message, "📤 Sᴇʟᴇᴄᴛ Pʟᴀᴛꜰᴏʀᴍ Tᴏ Sᴇɴᴅ Oʀᴅᴇʀꜱ:", reply_markup=send_orders_markup)
    user_last_bot_message[user_id] = sent_msg.message_id


def set_bot_commands():
    """Set bot commands for the Telegram bot"""
    commands = [
        BotCommand('start', 'Restart the bot')
        # Removed 'addcoins' and 'removecoins' from global commands
    ]
    try:
        bot.set_my_commands(commands)
        print("Bot commands set successfully")
    except Exception as e:
        print(f"Error setting bot commands: {e}")

# Debugging print statement for updateUser function
print(updateUser)
  
#======================= Start Command =======================#
@bot.message_handler(commands=['start'])
@check_ban
def send_welcome(message):
    """Handle the /start command and welcome the user"""
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    ref_by = message.text.split()[1] if len(message.text.split()) > 1 and message.text.split()[1].isdigit() else None

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    # Check channel membership
    if not check_membership_and_prompt(user_id, message):
        return

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
        addBalance(user_id, welcome_bonus)
        setWelcomeStaus(user_id)

    # Referral bonus logic
    data = getData(user_id)
    if data['ref_by'] != "none" and data['referred'] == 0:
        bot.send_message(data['ref_by'], f"You referred {first_name} +{ref_bonus}")
        addBalance(data['ref_by'], ref_bonus)
        setReferredStatus(user_id)

    # Send welcome image with caption
    welcome_image_url = "https://t.me/smmserviceslogs/20"  # Replace with your image URL
    welcome_caption = f"""
🎉 <b>Welcome {first_name} !</b> 🎉

🆔 <b>User ID:</b> <code>{user_id}</code>
👤 <b>Username:</b> {username}

Wɪᴛʜ Oᴜʀ Bᴏᴛ, Yᴏᴜ Cᴀɴ Bᴏᴏꜱᴛ Yᴏᴜʀ Sᴏᴄɪᴀʟ Mᴇᴅɪᴀ Aᴄᴄᴏᴜɴᴛꜱ & Pᴏꜱᴛꜱ Wɪᴛʜ Jᴜꜱᴛ A Fᴇᴡ Sɪᴍᴘʟᴇ Sᴛᴇᴘꜱ!

👇 <b>Cʜᴏᴏꜱᴇ Aɴ Oᴘᴛɪᴏɴ Bᴇʟᴏᴡ Tᴏ Gᴇᴛ Sᴛᴀʀᴛᴇᴅ:</b>
"""

    try:
        # Send photo with caption
        sent_msg = bot.send_photo(
            chat_id=user_id,
            photo=welcome_image_url,
            caption=welcome_caption,
            parse_mode='HTML',
            reply_markup=main_markup
        )
        user_last_bot_message[user_id] = sent_msg.message_id

        # Send welcome bonus message separately if applicable
        if userData['welcome_bonus'] == 0:
            sent_msg = bot.send_message(
                user_id,
                f"🎁 <b>Yᴏᴜ Rᴇᴄᴇɪᴠᴇᴅ +{welcome_bonus} Cᴏɪɴꜱ Wᴇʟᴄᴏᴍᴇ Bᴏɴᴜꜱ!</b>",
                parse_mode='HTML'
            )
            user_last_bot_message[user_id] = sent_msg.message_id

    except Exception as e:
        print(f"Error sending welcome message: {e}")
        # Fallback to text message if image fails
        sent_msg = bot.send_message(
            user_id,
            welcome_caption,
            parse_mode='HTML',
            reply_markup=main_markup
        )
        user_last_bot_message[user_id] = sent_msg.message_id
#====================== My Account =====================#
@bot.message_handler(func=lambda message: message.text == "👤 My Account")
def my_account(message):
    user_id = str(message.chat.id)
    data = getData(user_id)
    
    if not data:
        bot.reply_to(message, "❌ Account not found. Please /start again.")
        return
    
    # Update last activity and username
    data['last_activity'] = time.time()
    data['username'] = message.from_user.username
    updateUser(user_id, data)
    
    # Get current time and date
    from datetime import datetime
    now = datetime.now()
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%Y-%m-%d")
    
    # Get user profile photos
    photos = bot.get_user_profile_photos(message.from_user.id, limit=1)
    
    # Format the message
    caption = f"""
<b><u>𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁</u></b>

🆔 Uꜱᴇʀ Iᴅ: <code>`{user_id}`</code>
👤 Uꜱᴇʀɴᴀᴍᴇ: @{message.from_user.username if message.from_user.username else "N/A"}
🗣 Iɴᴠɪᴛᴇᴅ Uꜱᴇʀꜱ: {data.get('total_refs', 0)}
⏰ Tɪᴍᴇ: {current_time}
📅 Dᴀᴛᴇ: {current_date}

🪙 Bᴀʟᴀɴᴄᴇ: <code>{data['balance']}</code> Cᴏɪɴꜱ
"""
    
    if photos.photos:
        # User has profile photo - get the largest available size
        photo_file_id = photos.photos[0][-1].file_id
        try:
            bot.send_photo(
                chat_id=user_id,
                photo=photo_file_id,
                caption=caption,
                parse_mode='HTML'
            )
            return
        except Exception as e:
            print(f"Error sending profile photo: {e}")
    
    # Fallback if no profile photo or error
    bot.send_message(
        chat_id=user_id,
        text=caption,
        parse_mode='HTML'
    )

#======================= Invite Friends =======================#
@bot.message_handler(func=lambda message: message.text == "🗣 Invite Friends")
@check_ban
def invite_friends(message):
    user_id = str(message.chat.id)
    bot_username = bot.get_me().username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    data = getData(user_id)
    
    if not data:
        bot.reply_to(message, "❌ Account not found. Please /start again.")
        return
        
    total_refs = data['total_refs']
    
    # Enhanced referral message
    referral_message = f"""
📢 <b>𝗜𝗻𝘃𝗶𝘁𝗲 𝗙𝗿𝗶𝗲𝗻𝗱𝘀 &amp; 𝗘𝗮𝗿𝗻 𝗙𝗿𝗲𝗲 𝗖𝗼𝗶𝗻𝘀!</b>  

🔗 <b>Yᴏᴜʀ Rᴇꜰᴇʀʀᴀʟ Lɪɴᴋ:</b>  
<code>{referral_link}</code>  

💎 <b>𝙃𝙤𝙬 𝙞𝙩 𝙒𝙤𝙧𝙠𝙨:</b>  
1️⃣ Sʜᴀʀᴇ ʏᴏᴜʀ ᴜɴɪQᴜᴇ ʟɪɴᴋ ᴡɪᴛʜ ꜰʀɪᴇɴᴅꜱ  
2️⃣ Wʜᴇɴ ᴛʜᴇʏ ᴊᴏɪɴ ᴜꜱɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ, <b>Bᴏᴛʜ ᴏꜰ ʏᴏᴜ ɢᴇᴛ {ref_bonus} ᴄᴏɪɴꜱ</b> ɪɴꜱᴛᴀɴᴛʟʏ!  
3️⃣ Eᴀʀɴ ᴜɴʟɪᴍɪᴛᴇᴅ ᴄᴏɪɴꜱ - <b>Nᴏ ʟɪᴍɪᴛꜱ ᴏɴ ʀᴇꜰᴇʀʀᴀʟꜱ!</b>  

🏆 <b>Bᴏɴᴜꜱ:</b> Tᴏᴘ ʀᴇꜰᴇʀʀᴇʀꜱ ɢᴇᴛ ꜱᴘᴇᴄɪᴀʟ ʀᴇᴡᴀʀᴅꜱ!  

💰 <b>Wʜʏ Wᴀɪᴛ?</b> Sᴛᴀʀᴛ ɪɴᴠɪᴛɪɴɢ ɴᴏᴡ ᴀɴᴅ ʙᴏᴏꜱᴛ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ ꜰᴏʀ ꜰʀᴇᴇ!  

📌 <b>Pʀᴏ Tɪᴘ:</b> Sʜᴀʀᴇ ʏᴏᴜʀ ʟɪɴᴋ ɪɴ ɢʀᴏᴜᴘꜱ/ᴄʜᴀᴛꜱ ᴡʜᴇʀᴇ ᴘᴇᴏᴘʟᴇ ɴᴇᴇᴅ ꜱᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ ɢʀᴏᴡᴛʜ!

📊 <b>Yᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ʀᴇꜰᴇʀʀᴀʟꜱ:</b> {total_refs}
"""
    
    bot.reply_to(
        message,
        referral_message,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

@bot.message_handler(func=lambda message: message.text == "📜 Help")
def help_command(message):
    user_id = message.chat.id
    msg = f"""
<b>FʀᴇQᴜᴇɴᴛʟʏ Aꜱᴋᴇᴅ Qᴜᴇꜱᴛɪᴏɴꜱ</b>

<b>• Aʀᴇ ᴛʜᴇ ᴠɪᴇᴡꜱ ʀᴇᴀʟ?</b>
Nᴏ, ᴛʜᴇ ᴠɪᴇᴡꜱ ᴀʀᴇ ꜱɪᴍᴜʟᴀᴛᴇᴅ ᴀɴᴅ ɴᴏᴛ ꜰʀᴏᴍ ʀᴇᴀʟ ᴜꜱᴇʀꜱ.

<b>• Wʜᴀᴛ'ꜱ ᴛʜᴇ ᴀᴠᴇʀᴀɢᴇ ꜱᴇʀᴠɪᴄᴇ ꜱᴘᴇᴇᴅ?</b>
Dᴇʟɪᴠᴇʀʏ ꜱᴘᴇᴇᴅ ᴠᴀʀɪᴇꜱ ʙᴀꜱᴇᴅ ᴏɴ ɴᴇᴛᴡᴏʀᴋ ᴄᴏɴᴅɪᴛɪᴏɴꜱ ᴀɴᴅ ᴏʀᴅᴇʀ ᴠᴏʟᴜᴍᴇ, ʙᴜᴛ ᴡᴇ ᴇɴꜱᴜʀᴇ ꜰᴀꜱᴛ ᴅᴇʟɪᴠᴇʀʏ.

<b>• Hᴏᴡ ᴛᴏ ɪɴᴄʀᴇᴀꜱᴇ ʏᴏᴜʀ ᴄᴏɪɴꜱ?</b>
1️⃣ Iɴᴠɪᴛᴇ ꜰʀɪᴇɴᴅꜱ - Eᴀʀɴ {ref_bonus} ᴄᴏɪɴꜱ ᴘᴇʀ ʀᴇꜰᴇʀʀᴀʟ
2️⃣ Bᴜʏ ᴄᴏɪɴ ᴘᴀᴄᴋᴀɢᴇꜱ - Aᴄᴄᴇᴘᴛᴇᴅ ᴘᴀʏᴍᴇɴᴛꜱ:
   • Mᴏʙɪʟᴇ Mᴏɴᴇʏ
   • Cʀʏᴘᴛᴏᴄᴜʀʀᴇɴᴄɪᴇꜱ (BTC, USDT, ᴇᴛᴄ.)
   • WᴇʙMᴏɴᴇʏ & Pᴇʀꜰᴇᴄᴛ Mᴏɴᴇʏ

<b>• Cᴀɴ I ᴛʀᴀɴꜱꜰᴇʀ ᴍʏ ʙᴀʟᴀɴᴄᴇ?</b>
Yᴇꜱ! Fᴏʀ ʙᴀʟᴀɴᴄᴇꜱ ᴏᴠᴇʀ 10,000 ᴄᴏɪɴꜱ, ᴄᴏɴᴛᴀᴄᴛ ꜱᴜᴘᴘᴏʀᴛ.
"""

    # Create inline button for support
    markup = InlineKeyboardMarkup()
    support_button = InlineKeyboardButton("🆘 Contact Support", url="https://t.me/SocialBoosterAdmin")
    markup.add(support_button)

    bot.reply_to(
        message, 
        msg,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "💳 Pricing")
def pricing_command(message):
    user_id = message.chat.id
    msg = f"""<b><u>💎 Pricing 💎</u></b>

<i> Cʜᴏᴏꜱᴇ Oɴᴇ Oꜰ Tʜᴇ Cᴏɪɴꜱ Pᴀᴄᴋᴀɢᴇꜱ Aɴᴅ Pᴀʏ Iᴛꜱ Cᴏꜱᴛ Vɪᴀ Pʀᴏᴠɪᴅᴇᴅ Pᴀʏᴍᴇɴᴛ Mᴇᴛʜᴏᴅꜱ.</i>

<b><u>📜 𝐏𝐚𝐜𝐤𝐚𝐠𝐞𝐬:</u></b>
<b>➊ 📦 10K coins – $1.00
➋ 📦 30K coins – $2.50
➌ 📦 50K coins – $4.00
➍ 📦 100K coins – $7.00
➎ 📦 150K coins – $10.00
➏ 📦 300K coins – $15.00 </b>

<b>💡NOTE: 𝘙𝘦𝘮𝘦𝘮𝘣𝘦𝘳 𝘵𝘰 𝘴𝘦𝘯𝘥 𝘺𝘰𝘶𝘳 𝘈𝘤𝘤𝘰𝘶𝘯𝘵 𝘐𝘋 𝘵𝘰 𝘳𝘦𝘤𝘦𝘪𝘷𝘦 𝘤𝘰𝘪𝘯𝘴</b>
<b>🆔 Your id:</b> <code>{user_id}</code>
"""

    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton("💲 PayPal", url="https://t.me/SocialBoosterAdmin")
    button2 = InlineKeyboardButton("💳 Mobile Money",
                                   url="https://t.me/SocialBoosterAdmin")
    button6 = InlineKeyboardButton("💳 Webmoney", url="https://t.me/SocialBoosterAdmin")
    button3 = InlineKeyboardButton("💎 Bitcoin, Litecoin, USDT...",
                                   url="https://t.me/SocialBoosterAdmin")
    button4 = InlineKeyboardButton("💸 Paytm", url="https://t.me/SocialBoosterAdmin")
    button5 = InlineKeyboardButton("💰 Paytm", url="https://t.me/SocialBoosterAdmin")

    markup.add(button1)
    markup.add(button2, button6)
    markup.add(button3)
    markup.add(button4, button5)

    bot.reply_to(message, msg, parse_mode="html", reply_markup=markup)

#======================= Order Statistics =======================#
@bot.message_handler(func=lambda message: message.text == "📊 Order Statistics")
@check_ban
def show_order_stats(message):
    """Show comprehensive order statistics for the user"""
    user_id = str(message.from_user.id)
    
    try:
        # Get basic stats
        stats = get_user_orders_stats(user_id)
        
        # Get recent orders (last 5)
        recent_orders = []
        try:
            from functions import orders_collection
            recent_orders = list(orders_collection.find(
                {"user_id": user_id},
                {"service": 1, "quantity": 1, "status": 1, "timestamp": 1, "_id": 0}
            ).sort("timestamp", -1).limit(5))
        except Exception as e:
            print(f"Error getting recent orders: {e}")
        
        # Format the message with stylish text
        msg = f"""📊 <b>𝗬𝗼𝘂𝗿 𝗢𝗿𝗱𝗲𝗿 𝗦𝘁𝗮𝘁𝗶𝘀𝘁𝗶𝗰𝘀</b>
        
🔄 <b>Tᴏᴛᴀʟ Oʀᴅᴇʀꜱ:</b> {stats['total']}
✅ <b>Cᴏᴍᴘʟᴇᴛᴇᴅ:</b> {stats['completed']}
⏳ <b>Pᴇɴᴅɪɴɢ:</b> {stats['pending']}
❌ <b>Fᴀɪʟᴇᴅ:</b> {stats['failed']}

<b>Rᴇᴄᴇɴᴛ Oʀᴅᴇʀꜱ:</b>"""
        
        if recent_orders:
            for i, order in enumerate(recent_orders, 1):
                timestamp = datetime.fromtimestamp(order.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M')
                msg += f"\n{i}. {order.get('service', 'N/A')} - {order.get('quantity', '?')} (Sᴛᴀᴛᴜꜱ: {order.get('status', 'ᴜɴᴋɴᴏᴡɴ')}) @ {timestamp}"
        else:
            msg += "\nNᴏ ʀᴇᴄᴇɴᴛ ᴏʀᴅᴇʀꜱ ꜰᴏᴜɴᴅ"
            
        msg += "\n\n<i>Nᴏᴛᴇ: Sᴛᴀᴛᴜꜱ ᴜᴘᴅᴀᴛᴇꜱ ᴍᴀʏ ᴛᴀᴋᴇ ꜱᴏᴍᴇ ᴛɪᴍᴇ ᴛᴏ ʀᴇꜰʟᴇᴄᴛ</i>"
        
        bot.reply_to(message, msg, parse_mode='HTML')
        
    except Exception as e:
        print(f"Error showing order stats: {e}")
        bot.reply_to(message, "❌ Cᴏᴜʟᴅ ɴᴏᴛ ʀᴇᴛʀɪᴇᴠᴇ ᴏʀᴅᴇʀ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ. Pʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")
      
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
            "name": "Post Views",
            "quality": "Super Fast",
            "min": 1000,
            "max": 100000,
            "price": 200,
            "unit": "1k views",
            "service_id": "10576",  # Your SMM panel service ID for views
            "link_hint": "Telegram post link"
        },
        "❤️ Order Reactions": {
            "name": "Positive Reactions",
            "quality": "No Refil",
            "min": 50,
            "max": 1000,
            "price": 1500,
            "unit": "1k reactions",
            "service_id": "12209",  # Replace with actual service ID
            "link_hint": "Telegram post link"
            
        },
        "👥 Order Members": {
            "name": "Members [Mixed]",
            "quality": "Refill 90 Days",
            "min": 500,
            "max": 10000,
            "price": 10000,
            "unit": "1k members",
            "service_id": "18578", # Replace with actual service ID
            "link_hint": "Telegram channel link"  # Replace with actual service ID
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
    
📌 Mɪɴɪᴍᴜᴍ: {service['min']}
📌 Mᴀxɪᴍᴜᴍ: {service['max']}
💰 Pʀɪᴄᴇ: {service['price']} coins/{service['unit']}
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}


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
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ ᴛᴏ Tᴇʟᴇɢʀᴀᴍ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=telegram_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Mɪɴɪᴍᴜᴍ Oʀᴅᴇʀ ɪꜱ {service['min']}", reply_markup=telegram_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Mᴀxɪᴍᴜᴍ Oʀᴅᴇʀ ɪꜱ {service['max']}", reply_markup=telegram_services_markup)
            return
            
        # Calculate cost
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Iɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ. Yᴏᴜ ɴᴇᴇᴅ {cost} ᴄᴏɪɴꜱ.", reply_markup=telegram_services_markup)
            return
            
        # Ask for link
        cancel_back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_back_markup.row(
            KeyboardButton("✘ Cancel")
        )
        
        bot.reply_to(message, "🔗 Pʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ Tᴇʟᴇɢʀᴀᴍ Pᴏꜱᴛ Lɪɴᴋ:", reply_markup=cancel_back_markup)
        bot.register_next_step_handler(
            message, 
            process_telegram_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Pʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ", reply_markup=telegram_services_markup)

def process_telegram_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    # Validate link format (basic check)
    if not re.match(r'^https?://t\.me/', link):
        bot.reply_to(message, "❌ Iɴᴠᴀʟɪᴅ Tᴇʟᴇɢʀᴀᴍ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ", reply_markup=telegram_services_markup)
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
        print(f"SMM Panel Response: {result}")  # Debug print
        
        if result and result.get('order'):
            # Deduct balance
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            # Prepare complete order data
            order_data = {
                'service': service['name'],
                'service_type': 'telegram',
                'service_id': service['service_id'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'order_id': str(result['order']),
                'status': 'pending',
                'timestamp': time.time(),
                'username': message.from_user.username or str(message.from_user.id)
            }
            
            # Add to order history
            add_order(str(message.from_user.id), order_data)
            
            # Stylish confirmation message
            bot.reply_to(
                message,
                f"""✅ <b>{service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
                
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
😊 <b>⚠️𝗪𝗮𝗿𝗻𝗶𝗴: ᴅᴏ ɴᴏᴛ ꜱᴇɴᴅ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏʀᴅᴇʀ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ᴇʟꜱᴇ ʏᴏᴜ ᴍɪɢʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!</b>
😊 <b>Tʜᴀɴᴋꜱ Fᴏʀ Oʀᴅᴇʀɪɴɢ!</b>""",
                reply_markup=main_markup,
                disable_web_page_preview=True,
                parse_mode='HTML'
            )
            
            # Update orders count
            user_id = str(message.from_user.id)
            data = getData(user_id)
            if 'orders_count' not in data:
                data['orders_count'] = 0
            data['orders_count'] += 1
            updateUser(user_id, data)
            
            # Stylish notification to payment channel
            try:
                bot.send_message(
                    payment_channel,
                    f"""📢 <b>Nᴇᴡ Tᴇʟᴇɢʀᴀᴍ Oʀᴅᴇʀ</b>
                    
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name} (@{message.from_user.username or 'N/A'})
🆔 <b>ID:</b> {message.from_user.id}
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>Pʀᴏᴄᴇꜱꜱɪɴɢ...</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}""",
                    disable_web_page_preview=True,
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Fᴀɪʟᴇᴅ ᴛᴏ ꜱᴇɴᴅ ᴛᴏ ᴘᴀʏᴍᴇɴᴛ ᴄʜᴀɴɴᴇʟ: {e}")
            
        else:
            error_msg = result.get('error', 'Uɴᴋɴᴏᴡɴ ᴇʀʀᴏʀ ꜰʀᴏᴍ SMM ᴘᴀɴᴇʟ')
            raise Exception(error_msg)
            
    except requests.Timeout:
        bot.reply_to(
            message,
            "⚠️ Tʜᴇ ᴏʀᴅᴇʀ ɪꜱ ᴛᴀᴋɪɴɢ ʟᴏɴɢᴇʀ ᴛʜᴀɴ ᴇxᴘᴇᴄᴛᴇᴅ. Pʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ ᴀɴᴅ ᴏʀᴅᴇʀ ꜱᴛᴀᴛᴜꜱ ʟᴀᴛᴇʀ.",
            reply_markup=main_markup
        )
    except Exception as e:
        print(f"Eʀʀᴏʀ ꜱᴜʙᴍɪᴛᴛɪɴɢ {service['name']} ᴏʀᴅᴇʀ: {str(e)}")
        if 'result' not in locals() or not result.get('order'):
            bot.reply_to(
                message,
                f"❌ Fᴀɪʟᴇᴅ ᴛᴏ ꜱᴜʙᴍɪᴛ {service['name']} ᴏʀᴅᴇʀ. Pʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
                reply_markup=main_markup
            )
        else:
            bot.reply_to(
                message,
                f"⚠️ Oʀᴅᴇʀ ᴡᴀꜱ ꜱᴜʙᴍɪᴛᴛᴇᴅ (ID: {result['order']}) ʙᴜᴛ ᴛʜᴇʀᴇ ᴡᴀꜱ ᴀɴ ɪꜱꜱᴜᴇ ᴡɪᴛʜ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴꜱ.",
                reply_markup=main_markup
            )
#========================= Telegram Orders End =========================#

#========================= Order for Tiktok =========================#
#======================= Send Orders for Tiktok =======================#
@bot.message_handler(func=lambda message: message.text == "🎵 Order TikTok")
def order_tiktok_menu(message):
    """Show Telegram service options"""
    # Clean previous messages
    cleanup_previous_messages(message.from_user.id)
    user_last_user_message[message.from_user.id] = message.message_id
    
    sent_msg = bot.reply_to(message, "🎵 TikTok Services:", reply_markup=tiktok_services_markup)
    user_last_bot_message[message.from_user.id] = sent_msg.message_id

@bot.message_handler(func=lambda message: message.text in ["👀 Order Views", "❤️ Order Likes", "👥 Order Followers"])
def handle_tiktok_order(message):
    """Handle TikTok service selection"""
    user_id = str(message.from_user.id)
    
    # Clean previous messages
    cleanup_previous_messages(message.from_user.id)
    user_last_user_message[message.from_user.id] = message.message_id
    
    # TikTok service configurations
    services = {
        "👀 Order Views": {
            "name": "TikTok Views",
            "quality": "Fast Speed",
            "link_hint": "Tiktok Post Link",
            "min": 500,
            "max": 100000,
            "price": 200,
            "unit": "1k views",
            "service_id": "17566"
        },
        "❤️ Order Likes": {
            "name": "TikTok Likes",
            "quality": "Real & Active",
            "link_hint": "Tiktok Post Link",
            "min": 100,
            "max": 10000,
            "price": 1500,
            "unit": "1k likes",
            "service_id": "17335"
        },
        "👥 Order Followers": {
            "name": "TikTok Followers",
            "quality": "High Quality",
            "link_hint": "Tiktok Profile Link",
            "min": 100,
            "max": 10000,
            "price": 15000,
            "unit": "1k followers",
            "service_id": "18383"
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
    
📌 Mɪɴɪᴍᴜᴍ: {service['min']}
📌 Mᴀxɪᴍᴜᴍ: {service['max']}
💰 Pʀɪᴄᴇ: {service['price']} coins/{service['unit']}
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}

Enter quantity:"""
    
    sent_msg = bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    user_last_bot_message[message.from_user.id] = sent_msg.message_id
    
    bot.register_next_step_handler(
        message, 
        process_tiktok_quantity, 
        service
    )

def process_tiktok_quantity(message, service):
    """Process the quantity input for TikTok orders"""
    # Clean previous messages first
    cleanup_previous_messages(message.from_user.id)
    user_last_user_message[message.from_user.id] = message.message_id
    
    if message.text == "✘ Cancel":
        sent_msg = bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    elif message.text == "↩️ Go Back":
        sent_msg = bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ ᴛᴏ TɪᴋTᴏᴋ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=tiktok_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            sent_msg = bot.reply_to(message, f"❌ Mɪɴɪᴍᴜᴍ Oʀᴅᴇʀ ɪꜱ {service['min']}", reply_markup=tiktok_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
        if quantity > service['max']:
            sent_msg = bot.reply_to(message, f"❌ Mᴀxɪᴍᴜᴍ Oʀᴅᴇʀ ɪꜱ {service['max']}", reply_markup=tiktok_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        # Calculate cost
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            sent_msg = bot.reply_to(message, f"❌ Iɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ Bᴀʟᴀɴᴄᴇ. Yᴏᴜ ɴᴇᴇᴅ {cost} ᴄᴏɪɴꜱ.", reply_markup=tiktok_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        # Ask for link
        cancel_back_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_back_markup.row(KeyboardButton("✘ Cancel"))
        
        sent_msg = bot.reply_to(message, "🔗 Pʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ TɪᴋTᴏᴋ Pᴏꜱᴛ Lɪɴᴋ:", reply_markup=cancel_back_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        
        bot.register_next_step_handler(
            message, 
            process_telegram_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        sent_msg = bot.reply_to(message, "❌ Pʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ", reply_markup=tiktok_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

def process_tiktok_link(message, service, quantity, cost):
    # Clean previous messages
    cleanup_previous_messages(message.from_user.id)
    user_last_user_message[message.from_user.id] = message.message_id
    
    if message.text == "✘ Cancel":
        sent_msg = bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    link = message.text.strip()
    
    # Validate link format (basic check)
    if not  re.match(r'^https?://(www\.)?tiktok\.com/', link):
        sent_msg = bot.reply_to(message, "❌ Iɴᴠᴀʟɪᴅ TɪᴋTᴏᴋ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ", reply_markup=tiktok_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
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
        print(f"SMM Panel Response: {result}")
        
        if result and result.get('order'):
            # Deduct balance
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            # Prepare complete order data
            order_data = {
                'service': service['name'],
                'service_type': 'telegram',
                'service_id': service['service_id'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'order_id': str(result['order']),
                'status': 'pending',
                'timestamp': time.time(),
                'username': message.from_user.username or str(message.from_user.id)
            }
            
            # Add to order history
            add_order(str(message.from_user.id), order_data)
            
            # Create "Check Order Status" button
            check_status_markup = InlineKeyboardMarkup()
            check_status_button = InlineKeyboardButton(
                text="Check Order Status",
                url=payment_channel
            )
            check_status_markup.add(check_status_button)
            
            # Stylish confirmation message
            sent_msg = bot.reply_to(
                message,
                f"""✅ <b>{service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
                
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
😊 <b>⚠️𝗪𝗮𝗿𝗻𝗶𝗻𝗴: ᴅᴏ ɴᴏᴛ ꜱᴇɴᴅ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏʀᴅᴇʀ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ᴇʟꜱᴇ ʏᴏᴜ ᴍɪɢʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!</b>
😊 <b>Tʜᴀɴᴋꜱ Fᴏʀ Oʀᴅᴇʀɪɴɢ!</b>""",
                reply_markup=check_status_markup,
                disable_web_page_preview=True,
                parse_mode='HTML'
            )
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            
            # Update orders count
            user_id = str(message.from_user.id)
            data = getData(user_id)
            if 'orders_count' not in data:
                data['orders_count'] = 0
            data['orders_count'] += 1
            updateUser(user_id, data)
            
            # Stylish notification to payment channel
            try:
                bot.send_message(
                    payment_channel,
                    f"""📢 <b>Nᴇᴡ TɪᴋTᴏᴋ Oʀᴅᴇʀ</b>
                    
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name} (@{message.from_user.username or 'N/A'})
🆔 <b>ID:</b> {message.from_user.id}
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>Pʀᴏᴄᴇꜱꜱɪɴɢ...</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}""",
                    disable_web_page_preview=True,
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Fᴀɪʟᴇᴅ ᴛᴏ ꜱᴇɴᴅ ᴛᴏ ᴘᴀʏᴍᴇɴᴛ ᴄʜᴀɴɴᴇʟ: {e}")
            
        else:
            error_msg = result.get('error', 'Uɴᴋɴᴏᴡɴ ᴇʀʀᴏʀ ꜰʀᴏᴍ SMM ᴘᴀɴᴇʟ')
            raise Exception(error_msg)
            
    except requests.Timeout:
        sent_msg = bot.reply_to(
            message,
            "⚠️ Tʜᴇ ᴏʀᴅᴇʀ ɪꜱ ᴛᴀᴋɪɴɢ ʟᴏɴɢᴇʀ ᴛʜᴀɴ ᴇxᴘᴇᴄᴛᴇᴅ. Pʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ ᴀɴᴅ ᴏʀᴅᴇʀ ꜱᴛᴀᴛᴜꜱ ʟᴀᴛᴇʀ.",
            reply_markup=main_markup
        )
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
    except Exception as e:
        print(f"Eʀʀᴏʀ ꜱᴜʙᴍɪᴛᴛɪɴɢ {service['name']} ᴏʀᴅᴇʀ: {str(e)}")
        if 'result' not in locals() or not result.get('order'):
            sent_msg = bot.reply_to(
                message,
                f"❌ Fᴀɪʟᴇᴅ ᴛᴏ ꜱᴜʙᴍɪᴛ {service['name']} ᴏʀᴅᴇʀ. Pʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
                reply_markup=main_markup
            )
        else:
            sent_msg = bot.reply_to(
                message,
                f"⚠️ Oʀᴅᴇʀ ᴡᴀꜱ ꜱᴜʙᴍɪᴛᴛᴇᴅ (ID: {result['order']}) ʙᴜᴛ ᴛʜᴇʀᴇ ᴡᴀꜱ ᴀɴ ɪꜱꜱᴜᴇ ᴡɪᴛʜ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴꜱ.",
                reply_markup=main_markup
            )
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
    
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

        # Clean previous messages
    cleanup_previous_messages(message.from_user.id)
    user_last_user_message[message.from_user.id] = message.message_id
    
  # TikTok service configurations
    services = {
        "🎥 Insta Vid Views": {
            "name": "Instagram Video Views",
            "quality": "Real Accounts",
            "min": 1000,
            "max": 100000,
            "price": 300,
            "unit": "1k views",
            "service_id": "17316",
            "link_hint": "Instagram video link"
        },
        "❤️ Insta Likes": {
            "name": "Instagram Likes",
            "quality": "Power Quality",
            "min": 500,
            "max": 10000,
            "price": 1000,
            "unit": "1k likes",
            "service_id": "17375",
            "link_hint": "Instagram post link"
        },
        "👥 Insta Followers": {
            "name": "Instagram Followers",
            "quality": "Old Accounts With Posts",
            "min": 500,
            "max": 10000,
            "price": 13000,
            "unit": "1k followers",
            "service_id": "18968",
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
    
📌 Mɪɴɪᴍᴜᴍ: {service['min']}
📌 Mᴀxɪᴍᴜᴍ: {service['max']}
💰 Pʀɪᴄᴇ: {service['price']} coins/{service['unit']}
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}

Enter quantity:"""
    
    sent_msg=bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    user_last_bot_message[message.from_user.id] = sent_msg.message_id

    bot.register_next_step_handler(
        message, 
        process_instagram_quantity, 
        service
    )

def process_instagram_quantity(message, service):
    """Process Instagram order quantity"""
        # Clean previous messages first
    cleanup_previous_messages(message.from_user.id)
    user_last_user_message[message.from_user.id] = message.message_id

    if message.text == "✘ Cancel":
        sent_msg=bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    elif message.text == "↩️ Go Back":
        sent_msg=bot.reply_to(message, "Returning to Instagram services...", reply_markup=instagram_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            sent_msg=bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=instagram_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
        if quantity > service['max']:
            sent_msg=bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=instagram_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            sent_msg=bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=instagram_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        sent_msg=bot.reply_to(message, f"🔗 Please send the {service['link_hint']}:", reply_markup=cancel_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        
        bot.register_next_step_handler(
            message, 
            process_instagram_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        sent_msg=bot.reply_to(message, "❌ Pʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ", reply_markup=instagram_services_markup)

def process_instagram_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        sent_msg=bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    link = message.text.strip()
    
    if not re.match(r'^https?://(www\.)?instagram\.com/', link):
        sent_msg=bot.reply_to(message, "❌ Iɴᴠᴀʟɪᴅ instagram ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ", reply_markup=instagram_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
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
        
        if result and result.get('order'):
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            order_data = {
                'service': service['name'],
                'service_type': 'instagram',
                'service_id': service['service_id'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'order_id': str(result['order']),
                'status': 'pending',
                'timestamp': time.time(),
                'username': message.from_user.username or str(message.from_user.id)
            }
            add_order(str(message.from_user.id), order_data)
            
            # Update user stats
            user_id = str(message.from_user.id)
            data = getData(user_id)
            data['orders_count'] = data.get('orders_count', 0) + 1
            updateUser(user_id, data)
            
            bot.reply_to(
                message,
                f"""✅ {service['name']}  Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
                
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
😊 <b>⚠️𝗪𝗮𝗿𝗻𝗶𝗴: ᴅᴏ ɴᴏᴛ ꜱᴇɴᴅ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏʀᴅᴇʀ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ᴇʟꜱᴇ ʏᴏᴜ ᴍɪɢʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!</b>
😊 <b>Tʜᴀɴᴋꜱ Fᴏʀ Oʀᴅᴇʀɪɴɢ!</b>""",
                reply_markup=main_markup,
                disable_web_page_preview=True
            )
            
            try:
                bot.send_message(
                    payment_channel,
                    f"""📢 New Instagram Order:
                    
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name} (@{message.from_user.username or 'N/A'})
🆔 <b>ID:</b> {message.from_user.id}
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>Pʀᴏᴄᴇꜱꜱɪɴɢ...</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}""",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send to payment channel: {e}")
                
        else:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
    except requests.Timeout:
        sent_msg=bot.reply_to(
            message,
            "⚠️  Tʜᴇ ᴏʀᴅᴇʀ ɪꜱ ᴛᴀᴋɪɴɢ ʟᴏɴɢᴇʀ ᴛʜᴀɴ ᴇxᴘᴇᴄᴛᴇᴅ. Pʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ ᴀɴᴅ ᴏʀᴅᴇʀ ꜱᴛᴀᴛᴜꜱ ʟᴀᴛᴇʀ.",
            reply_markup=main_markup
        )
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

    except Exception as e:
        print(f"Eʀʀᴏʀ ꜱᴜʙᴍɪᴛᴛɪɴɢ {service['name']} ᴏʀᴅᴇʀ: {str(e)}")
        if 'result' not in locals() or not result.get('order'):
            sent_msg=bot.reply_to(
                message,
                f"❌ Fᴀɪʟᴇᴅ ᴛᴏ ꜱᴜʙᴍɪᴛ {service['name']} ᴏʀᴅᴇʀ. Pʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.",
                reply_markup=main_markup
            )
            
        else:
            sent_msg=bot.reply_to(
                message,
                f"⚠️ Oʀᴅᴇʀ ᴡᴀꜱ ꜱᴜʙᴍɪᴛᴛᴇᴅ (ID: {result['order']}) ʙᴜᴛ ᴛʜᴇʀᴇ ᴡᴀꜱ ᴀɴ ɪꜱꜱᴜᴇ ᴡɪᴛʜ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴꜱ.",
                reply_markup=main_markup
            )
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
#======================== End of Instagram Orders ===========================#

#======================== Send Orders for Youtube =====================#
@bot.message_handler(func=lambda message: message.text == "▶️ Order YouTube")
def order_youtube_menu(message):
    """Show YouTube service options"""
        # Clean previous messages
    cleanup_previous_messages(message.from_user.id)
    user_last_user_message[message.from_user.id] = message.message_id

    sent_msg=bot.reply_to(message, "▶️ YouTube Services:", reply_markup=youtube_services_markup)
    user_last_bot_message[message.from_user.id] = sent_msg.message_id

@bot.message_handler(func=lambda message: message.text in ["▶️ YT Views", "👍 YT Likes", "👥 YT Subscribers"])
def handle_youtube_order(message):
    """Handle YouTube service selection"""
    user_id = str(message.from_user.id)
    
    services = {
        "▶️ YT Views": {
            "name": "YouTube Views",
            "quality": "100% Real",
            "min": 40000,
            "max": 1000000,
            "price": 7000,
            "unit": "1k views",
            "service_id": "11272",
            "link_hint": "YouTube video link"
        },
        "👍 YT Likes": {
            "name": "YouTube Likes [Real]",
            "quality": "No Refill",
            "min": 500,
            "max": 10000,
            "price": 2000,
            "unit": "1k likes",
            "service_id": "18144",
            "link_hint": "YouTube video link"
        },
        "👥 YT Subscribers": {
            "name": "YouTube Subscribers [Cheapest]",
            "quality": "Refill 30 days",
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
    
📌 Mɪɴɪᴍᴜᴍ: {service['min']}
📌 Mᴀxɪᴍᴜᴍ: {service['max']}
💰 Pʀɪᴄᴇ: {service['price']} coins/{service['unit']}
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}

Enter quantity:"""
    
    sent_msg=bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    user_last_bot_message[message.from_user.id] = sent_msg.message_id

    bot.register_next_step_handler(
        message, 
        process_youtube_quantity, 
        service
    )

def process_youtube_quantity(message, service):
    """Process YouTube order quantity"""
    if message.text == "✘ Cancel":
        sent_msg=bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    elif message.text == "↩️ Go Back":
        sent_msg=bot.reply_to(message, "Returning to YouTube services...", reply_markup=youtube_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            sent_msg=bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=youtube_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
        if quantity > service['max']:
            sent_msg=bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=youtube_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            sent_msg=bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=youtube_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        sent_msg=bot.reply_to(message, f"🔗 Please send the {service['link_hint']}:", reply_markup=cancel_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

        bot.register_next_step_handler(
            message, 
            process_youtube_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        sent_msg=bot.reply_to(message, "❌ Please enter a valid number", reply_markup=youtube_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

def process_youtube_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        sent_msg=bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    link = message.text.strip()
    
    if not re.match(r'^https?://(www\.)?youtube\.com/', link):
        sent_msg=bot.reply_to(message, "❌ Invalid YouTube link format", reply_markup=youtube_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
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
        
        if result and result.get('order'):
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            order_data = {
                'service': service['name'],
                'service_type': 'youtube',
                'service_id': service['service_id'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'order_id': str(result['order']),
                'status': 'pending',
                'timestamp': time.time(),
                'username': message.from_user.username or str(message.from_user.id)
            }
            add_order(str(message.from_user.id), order_data)
            
            # Update user stats
            user_id = str(message.from_user.id)
            data = getData(user_id)
            data['orders_count'] = data.get('orders_count', 0) + 1
            updateUser(user_id, data)
            
            bot.reply_to(
                message,
                f"""✅ {service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
                
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
😊 <b>⚠️𝗪𝗮𝗿𝗻𝗶𝗴: ᴅᴏ ɴᴏᴛ ꜱᴇɴᴅ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏʀᴅᴇʀ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ᴇʟꜱᴇ ʏᴏᴜ ᴍɪɢʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!</b>
😊 <b>Tʜᴀɴᴋꜱ Fᴏʀ Oʀᴅᴇʀɪɴɢ!</b>""",
                reply_markup=main_markup,
                disable_web_page_preview=True
            )
            
            try:
                bot.send_message(
                    payment_channel,
                    f"""📢 New Youtube Order:
                    
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name} (@{message.from_user.username or 'N/A'})
🆔 <b>ID:</b> {message.from_user.id}
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>Pʀᴏᴄᴇꜱꜱɪɴɢ...</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}""",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send to payment channel: {e}")
                
        else:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
    except requests.Timeout:
        sent_msg=bot.reply_to(
            message,
            "⚠️ The order is taking longer than expected. Please check your balance and order status later.",
            reply_markup=main_markup
        )
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

    except Exception as e:
        print(f"Error submitting {service['name']} order: {str(e)}")
        if 'result' not in locals() or not result.get('order'):
            sent_msg=bot.reply_to(
                message,
                f"❌ Failed to submit {service['name']} order. Please try again later.",
                reply_markup=main_markup
            )
        else:
            sent_msg=bot.reply_to(
                message,
                f"⚠️ Order was submitted (ID: {result['order']}) but there was an issue with notifications.",
                reply_markup=main_markup
            )
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
#======================== End of Youtube Orders =====================#

#======================== Send Orders for Facebook =====================#
@bot.message_handler(func=lambda message: message.text == "📘 Order Facebook")
def order_facebook_menu(message):
    """Show Facebook service options"""
            # Clean previous messages
    cleanup_previous_messages(message.from_user.id)
    user_last_user_message[message.from_user.id] = message.message_id

    sent_msg=bot.reply_to(message, "📘 Facebook Services:", reply_markup=facebook_services_markup)
    user_last_bot_message[message.from_user.id] = sent_msg.message_id

@bot.message_handler(func=lambda message: message.text in ["👤 Profile Followers", "📄 Page Followers", "🎥 Video/Reel Views", "❤️ Post Likes"])
def handle_facebook_order(message):
    """Handle Facebook service selection"""
    user_id = str(message.from_user.id)
    
    services = {
        "👤 Profile Followers": {
            "name": "FB Profile Followers",
            "quality": "High Quality",
            "min": 500,
            "max": 100000,
            "price": 10000,
            "unit": "1k followers",
            "service_id": "18977",
            "link_hint": "Facebook profile link"
        },
        "📄 Page Followers": {
            "name": "FB Page Followers",
            "quality": "Refill 30 Days",
            "min": 500,
            "max": 10000,
            "price": 6000,
            "unit": "1k followers",
            "service_id": "18984",
            "link_hint": "Facebook page link"
        },
        "🎥 Video/Reel Views": {
            "name": "FB Video/Reel Views",
            "quality": "Non Drop",
            "min": 500,
            "max": 10000,
            "price": 500,
            "unit": "1k views",
            "service_id": "17859",
            "link_hint": "Facebook video/reel link"
        },
        "❤️ Post Likes": {
            "name": "FB Post Likes",
            "quality": "No Refill",
            "min": 100,
            "max": 10000,
            "price": 5000,
            "unit": "1k likes",
            "service_id": "18990",
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
    
📌 Mɪɴɪᴍᴜᴍ: {service['min']}
📌 Mᴀxɪᴍᴜᴍ: {service['max']}
💰 Pʀɪᴄᴇ: {service['price']} coins/{service['unit']}
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}

Enter quantity:"""
    
    sent_msg=bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    user_last_bot_message[message.from_user.id] = sent_msg.message_id

    bot.register_next_step_handler(
        message, 
        process_facebook_quantity, 
        service
    )

def process_facebook_quantity(message, service):
    """Process Facebook order quantity"""
    if message.text == "✘ Cancel":
        sent_msg=bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    elif message.text == "↩️ Go Back":
        sent_msg=bot.reply_to(message, "Returning to Facebook services...", reply_markup=facebook_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            sent_msg=bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=facebook_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
        if quantity > service['max']:
            sent_msg=bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=facebook_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            sent_msg=bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=facebook_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        sent_msg=bot.reply_to(message, f"🔗 Please send the {service['link_hint']}:", reply_markup=cancel_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

        bot.register_next_step_handler(
            message, 
            process_facebook_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        sent_msg=bot.reply_to(message, "❌ Please enter a valid number", reply_markup=facebook_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

def process_facebook_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        sent_msg=bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    link = message.text.strip()
    
    if not re.match(r'^https?://(www\.)?facebook\.com/', link):
        sent_msg=bot.reply_to(message, "❌ Invalid Facebook link format", reply_markup=facebook_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
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
        
        if result and result.get('order'):
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            order_data = {
                'service': service['name'],
                'service_type': 'facebook',
                'service_id': service['service_id'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'order_id': str(result['order']),
                'status': 'pending',
                'timestamp': time.time(),
                'username': message.from_user.username or str(message.from_user.id)
            }
            add_order(str(message.from_user.id), order_data)
            
            # Update user stats
            user_id = str(message.from_user.id)
            data = getData(user_id)
            data['orders_count'] = data.get('orders_count', 0) + 1
            updateUser(user_id, data)
            
            bot.reply_to(
                message,
                f"""✅ {service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
                
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
😊 <b>⚠️𝗪𝗮𝗿𝗻𝗶𝗴: ᴅᴏ ɴᴏᴛ ꜱᴇɴᴅ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏʀᴅᴇʀ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ᴇʟꜱᴇ ʏᴏᴜ ᴍɪɢʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!</b>
😊 <b>Tʜᴀɴᴋꜱ Fᴏʀ Oʀᴅᴇʀɪɴɢ!</b>""",
                reply_markup=main_markup,
                disable_web_page_preview=True
            )
            
            try:
                bot.send_message(
                    payment_channel,
                    f"""📢 New Facebook Order:
                    
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name} (@{message.from_user.username or 'N/A'})
🆔 <b>ID:</b> {message.from_user.id}
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>Pʀᴏᴄᴇꜱꜱɪɴɢ...</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}""",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send to payment channel: {e}")
                
        else:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
    except requests.Timeout:
        sent_msg=bot.reply_to(
            message,
            "⚠️ The order is taking longer than expected. Please check your balance and order status later.",
            reply_markup=main_markup
        )
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

    except Exception as e:
        print(f"Error submitting {service['name']} order: {str(e)}")
        if 'result' not in locals() or not result.get('order'):
            sent_msg=bot.reply_to(
                message,
                f"❌ Failed to submit {service['name']} order. Please try again later.",
                reply_markup=main_markup
            )
        else:
            sent_msg=bot.reply_to(
                message,
                f"⚠️ Order was submitted (ID: {result['order']}) but there was an issue with notifications.",
                reply_markup=main_markup
            )
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
#======================== End of Facebook Orders =====================# 

#======================== Send Orders for Whastapp =====================#
@bot.message_handler(func=lambda message: message.text == "💬 Order WhatsApp")
def order_whatsapp_menu(message):
    """Show WhatsApp service options"""
                # Clean previous messages
    cleanup_previous_messages(message.from_user.id)
    user_last_user_message[message.from_user.id] = message.message_id

    sent_msg=bot.reply_to(message, "💬 WhatsApp Services:", reply_markup=whatsapp_services_markup)
    user_last_bot_message[message.from_user.id] = sent_msg.message_id

@bot.message_handler(func=lambda message: message.text in ["👥 Channel Members", "😀 Channel EmojiReaction"])
def handle_whatsapp_order(message):
    """Handle WhatsApp service selection"""
    user_id = str(message.from_user.id)
    
    services = {
        "👥 Channel Members": {
            "name": "WhatsApp Channel Members",
            "quality": "EU Users",
            "min": 100,
            "max": 40000,
            "price": 16000,
            "unit": "1k members",
            "service_id": "18848",
            "link_hint": "WhatsApp channel invite link"
        },
        "😀 Channel EmojiReaction": {
            "name": "WhatsApp Channel EmojiReaction",
            "quality": "Mixed",
            "min": 100,
            "max": 10000,
            "price": 3000,
            "unit": "1k reactions",
            "service_id": "18846",
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
    
📌 Mɪɴɪᴍᴜᴍ: {service['min']}
📌 Mᴀxɪᴍᴜᴍ: {service['max']}
💰 Pʀɪᴄᴇ: {service['price']} coins/{service['unit']}
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}

Enter quantity:"""
    
    sent_msg=bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    user_last_bot_message[message.from_user.id] = sent_msg.message_id

    bot.register_next_step_handler(
        message, 
        process_whatsapp_quantity, 
        service
    )

def process_whatsapp_quantity(message, service):
    """Process WhatsApp order quantity"""
    if message.text == "✘ Cancel":
        sent_msg=bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    elif message.text == "↩️ Go Back":
        sent_msg=bot.reply_to(message, "Returning to WhatsApp services...", reply_markup=whatsapp_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            sent_msg=bot.reply_to(message, f"❌ Minimum order is {service['min']}", reply_markup=whatsapp_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
        if quantity > service['max']:
            sent_msg=bot.reply_to(message, f"❌ Maximum order is {service['max']}", reply_markup=whatsapp_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            sent_msg=bot.reply_to(message, f"❌ Insufficient balance. You need {cost} coins.", reply_markup=whatsapp_services_markup)
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        sent_msg=bot.reply_to(message, f"🔗 Please send the {service['link_hint']}:", reply_markup=cancel_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id


        bot.register_next_step_handler(
            message, 
            process_whatsapp_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        sent_msg=bot.reply_to(message, "❌ Please enter a valid number", reply_markup=whatsapp_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

def process_whatsapp_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        sent_msg=bot.reply_to(message, "❌ Order cancelled.", reply_markup=main_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
    link = message.text.strip()
    
    if not re.match(r'^https?://(chat\.whatsapp\.com|wa\.me)/', link):
        sent_msg=bot.reply_to(message, "❌ Invalid WhatsApp link format", reply_markup=whatsapp_services_markup)
        user_last_bot_message[message.from_user.id] = sent_msg.message_id
        return
    
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
        
        if result and result.get('order'):
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            order_data = {
                'service': service['name'],
                'service_type': 'whatsapp',
                'service_id': service['service_id'],
                'quantity': quantity,
                'cost': cost,
                'link': link,
                'order_id': str(result['order']),
                'status': 'pending',
                'timestamp': time.time(),
                'username': message.from_user.username or str(message.from_user.id)
            }
            add_order(str(message.from_user.id), order_data)
            
            # Update user stats
            user_id = str(message.from_user.id)
            data = getData(user_id)
            data['orders_count'] = data.get('orders_count', 0) + 1
            updateUser(user_id, data)
            
            bot.reply_to(
                message,
                f"""✅ {service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
                
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
😊 <b>⚠️𝗪𝗮𝗿𝗻𝗶𝗴: ᴅᴏ ɴᴏᴛ ꜱᴇɴᴅ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏʀᴅᴇʀ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ᴇʟꜱᴇ ʏᴏᴜ ᴍɪɢʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!</b>
😊 <b>Tʜᴀɴᴋꜱ Fᴏʀ Oʀᴅᴇʀɪɴɢ!</b>""",
                reply_markup=main_markup,
                disable_web_page_preview=True
            )
            
            try:
                bot.send_message(
                    payment_channel,
                    f"""📢 New Whastapp Order:
                    
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name} (@{message.from_user.username or 'N/A'})
🆔 <b>ID:</b> {message.from_user.id}
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>Pʀᴏᴄᴇꜱꜱɪɴɢ...</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}""",
                    disable_web_page_preview=True
                )
            except Exception as e:
                print(f"Failed to send to payment channel: {e}")
                
        else:
            error_msg = result.get('error', 'Unknown error from SMM panel')
            raise Exception(error_msg)
            
    except requests.Timeout:
        sent_msg=bot.reply_to(
            message,
            "⚠️ The order is taking longer than expected. Please check your balance and order status later.",
            reply_markup=main_markup
        )
        user_last_bot_message[message.from_user.id] = sent_msg.message_id

    except Exception as e:
        print(f"Error submitting {service['name']} order: {str(e)}")
        if 'result' not in locals() or not result.get('order'):
            sent_msg=bot.reply_to(
                message,
                f"❌ Failed to submit {service['name']} order. Please try again later.",
                reply_markup=main_markup
            )
        else:
            sent_msg=bot.reply_to(
                message,
                f"⚠️ Order was submitted (ID: {result['order']}) but there was an issue with notifications.",
                reply_markup=main_markup
            )
            user_last_bot_message[message.from_user.id] = sent_msg.message_id
#======================== End of Whastapp Orders =====================#

#=================== The back button handler =========================================
@bot.message_handler(func=lambda message: message.text in ["↩️ Go Back", "✘ Cancel"])
def handle_back_buttons(message):
    """Handle all back/cancel buttons"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    if message.text == "↩️ Go Back":
        # Determine where to go back based on context
        if message.text in ["👀 Order Views", "❤️ Order Reactions", "👥 Order Members"]:
            sent_msg = bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Tᴇʟᴇɢʀᴀᴍ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=telegram_services_markup)
        elif message.text in ["👀 Order TikTok Views", "❤️ Order Likes", "👥 Order Followers"]:
            sent_msg = bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Tɪᴋᴛᴏᴋ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=tiktok_services_markup)
        elif message.text in ["🎥 Insta Vid Views", "❤️ Insta Likes", "👥 Insta Followers"]:
            sent_msg = bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Iɴꜱᴛᴀɢʀᴀᴍ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=instagram_services_markup)
        elif message.text in ["▶️ YT Views", "👍 YT Likes", "👥 YT Subscribers"]:
            sent_msg = bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Yᴏᴜᴛᴜʙᴇ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=youtube_services_markup)
        elif message.text in ["👤 Profile Followers", "📄 Page Followers", "🎥 Video/Reel Views", "❤️ Post Likes"]:
            sent_msg = bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Fᴀᴄᴇʙᴏᴏᴋ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=facebook_services_markup)
        elif message.text in ["👥 Channel Members", "😀 Channel EmojiReaction"]:
            sent_msg = bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Wʜᴀꜱᴛᴀᴘᴘ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=whatsapp_services_markup)
        else:
            # Default back to Send Orders menu
            sent_msg = bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Oʀᴅᴇʀ Oᴘᴛɪᴏɴꜱ...", reply_markup=send_orders_markup)
    else:
        # Cancel goes straight to main menu
        sent_msg = bot.reply_to(message, "Oᴘᴇʀᴀᴛɪᴏɴ Cᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)

    # Store the bot's last message ID
    user_last_bot_message[user_id] = sent_msg.message_id

# ================= ADMIN COMMANDS ================== #
@bot.message_handler(commands=['addcoins', 'removecoins'])
def handle_admin_commands(message):
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    if user_id not in admin_user_ids:
        sent_msg = bot.reply_to(message, "❌ Y̶o̶u̶ ̶a̶r̶e̶ ̶n̶o̶t̶ ̶a̶u̶t̶h̶o̶r̶i̶z̶e̶d̶ ̶t̶o̶ ̶u̶s̶e̶ ̶t̶h̶i̶s̶ ̶c̶o̶m̶m̶a̶n̶d̶.")
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    try:
        args = message.text.split()
        if len(args) != 3:
            sent_msg = bot.reply_to(message, f"⚠️ Usage: {args[0]} <user_id> <amount>")
            user_last_bot_message[user_id] = sent_msg.message_id
            return

        user_id = args[1]
        try:
            amount = float(args[2])
        except ValueError:
            sent_msg = bot.reply_to(message, "⚠️ Aᴍᴏᴜɴᴛ Mᴜꜱᴛ Bᴇ ᴀ Nᴜᴍʙᴇʀ")
            user_last_bot_message[user_id] = sent_msg.message_id
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
                sent_msg = bot.reply_to(message, f"✅ Added {amount} coins to user {user_id}")
                user_last_bot_message[user_id] = sent_msg.message_id
                try:
                    bot.send_message(user_id, f"📢 Aᴅᴍɪɴ Aᴅᴅᴇᴅ {amount} Cᴏɪɴꜱ Tᴏ Yᴏᴜʀ Aᴄᴄᴏᴜɴᴛ!")
                except:
                    pass
            else:
                sent_msg = bot.reply_to(message, "❌ Failed to add coins")
                user_last_bot_message[user_id] = sent_msg.message_id

        elif args[0] == '/removecoins':
            if cutBalance(user_id, amount):
                sent_msg = bot.reply_to(message, f"✅ Removed {amount} coins from user {user_id}")
                user_last_bot_message[user_id] = sent_msg.message_id
                try:
                    bot.send_message(user_id, f"📢 Aᴅᴍɪɴ Rᴇᴍᴏᴠᴇᴅ {amount} Cᴏɪɴꜱ Fʀᴏᴍ Yᴏᴜʀ Aᴄᴄᴏᴜɴᴛ!")
                except:
                    pass
            else:
                sent_msg = bot.reply_to(message, "❌ Failed to remove coins (insufficient balance or user doesn't exist)")
                user_last_bot_message[user_id] = sent_msg.message_id

    except Exception as e:
        sent_msg = bot.reply_to(message, f"⚠️ Error: {str(e)}")
        user_last_bot_message[user_id] = sent_msg.message_id
        print(f"Admin command error: {traceback.format_exc()}")


@bot.message_handler(func=lambda message: message.text == "🛠 Admin Panel")
def admin_panel(message):
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    if user_id not in admin_user_ids:
        sent_msg = bot.reply_to(message, "❌ Y̶o̶u̶ ̶a̶r̶e̶ ̶n̶o̶t̶ ̶a̶u̶t̶h̶o̶r̶i̶z̶e̶d̶ ̶t̶o̶ ̶a̶c̶c̶e̶s̶s̶ ̶t̶h̶i̶s̶ ̶p̶a̶n̶e̶l̶.")
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    sent_msg = bot.reply_to(message, "🛠 Welcome to Admin Panel:", reply_markup=admin_markup)
    user_last_bot_message[user_id] = sent_msg.message_id

#========== New Commands ==============#
# Admin Stats Command
@bot.message_handler(func=lambda m: m.text == "📊 Analytics" and m.from_user.id in admin_user_ids)
def show_analytics(message):
    """Show comprehensive bot analytics"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    try:
        total_users = get_user_count()
        active_users = get_active_users(7)
        total_orders = get_total_orders()
        total_deposits = get_total_deposits()
        top_referrer = get_top_referrer()
        
        # Format top referrer display
        if top_referrer['user_id']:
            username = f"@{top_referrer['username']}" if top_referrer['username'] else f"User {top_referrer['user_id']}"
            referrer_display = f"{username} ({top_referrer['count']} invites)"
        else:
            referrer_display = "No referrals yet"
        
        msg = f"""📊 <b>Bot Analytics</b>
        
👤 <b>Tᴏᴛᴀʟ Uꜱᴇʀꜱ:</b> {total_users}
🔥 <b>Aᴄᴛɪᴠᴇ Uꜱᴇʀꜱ (7 Days):</b> {active_users}
🚀 <b>Tᴏᴛᴀʟ Oʀᴅᴇʀꜱ Pʀᴏᴄᴇꜱꜱᴇᴅ:</b> {total_orders}
💰 <b>Tᴏᴛᴀʟ Dᴇᴘᴏꜱɪᴛꜱ:</b> {total_deposits:.2f} coins
🎯 <b>Tᴏᴘ Rᴇꜰᴇʀʀᴇʀ:</b> {referrer_display}"""
        
        sent_msg = bot.reply_to(message, msg, parse_mode='HTML')
        user_last_bot_message[user_id] = sent_msg.message_id
    except Exception as e:
        print(f"Error showing analytics: {e}")
        sent_msg = bot.reply_to(message, "❌ Failed to load analytics. Please try again later.")
        user_last_bot_message[user_id] = sent_msg.message_id

# =========================== Broadcast Command ================= #
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and m.from_user.id in admin_user_ids)
def broadcast_start(message):
    """Start normal broadcast process (unpinned)"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    msg = bot.reply_to(message, "📢 Eɴᴛᴇʀ Tʜᴇ Mᴇꜱꜱᴀɢᴇ Yᴏᴜ Wᴀɴᴛ Tᴏ Bʀᴏᴀᴅᴄᴀꜱᴛ Tᴏ Aʟʟ Uꜱᴇʀꜱ (ᴛʜɪꜱ ᴡᴏɴ'ᴛ ʙᴇ ᴘɪɴɴᴇᴅ):")
    user_last_bot_message[user_id] = msg.message_id
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    """Process and send the broadcast message (unpinned)"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    if message.text == "✘ Cancel":
        sent_msg = bot.reply_to(message, "❌ Broadcast cancelled.", reply_markup=admin_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    users = get_all_users()
    success = 0
    failed = 0

    sent_msg = bot.reply_to(message, f"⏳ Sᴇɴᴅɪɴɢ Bʀᴏᴀᴅᴄᴀꜱᴛ Tᴏ {len(users)} users...")
    user_last_bot_message[user_id] = sent_msg.message_id

    for user_id in users:
        try:
            if message.content_type == 'text':
                bot.send_message(user_id, message.text, parse_mode="Markdown")
            elif message.content_type == 'photo':
                bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'document':
                bot.send_document(user_id, message.document.file_id, caption=message.caption)
            success += 1
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")
            failed += 1
        time.sleep(0.1)  # Rate limiting

    sent_msg = bot.reply_to(message, f"""✅ Broadcast Complete:
    
📤 Sent: {success}
❌ Failed: {failed}""", reply_markup=admin_markup)
    user_last_bot_message[user_id] = sent_msg.message_id

#====================== Ban User Command ================================#
@bot.message_handler(func=lambda m: m.text == "🔒 Ban User" and m.from_user.id in admin_user_ids)
def ban_user_start(message):
    """Start ban user process"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    msg = bot.reply_to(message, "Eɴᴛᴇʀ Uꜱᴇʀ Iᴅ Tᴏ Bᴀɴ:")
    user_last_bot_message[user_id] = msg.message_id
    bot.register_next_step_handler(msg, process_ban_user)

def process_ban_user(message):
    """Ban a user"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    if message.text == "✘ Cancel":
        sent_msg = bot.reply_to(message, "❌ Ban cancelled.", reply_markup=admin_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    target_user_id = message.text.strip()

    if not target_user_id.isdigit():
        sent_msg = bot.reply_to(message, "❌ Invalid user ID. Must be numeric.", reply_markup=admin_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    if is_banned(target_user_id):
        sent_msg = bot.reply_to(message, "⚠️ User is already banned.", reply_markup=admin_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    ban_user(target_user_id)

    # Send notification to banned user
    try:
        appeal_markup = InlineKeyboardMarkup()
        appeal_markup.add(InlineKeyboardButton("📩 Send Appeal", url="https://t.me/SocialHubBoosterHelper"))

        bot.send_message(
            target_user_id,
            f"⛔ 𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 𝙗𝙚𝙚𝙣 𝙗𝙖𝙣𝙣𝙚𝙙 𝙛𝙧𝙤𝙢 𝙪𝙨𝙞𝙣𝙜 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩.\n\n"
            f"𝙄𝙛 𝙮𝙤𝙪 𝙗𝙚𝙡𝙞𝙚𝙫𝙚 𝙩𝙝𝙞𝙨 𝙬𝙖𝙨 𝙖 𝙢𝙞𝙨𝙩𝙖𝙠𝙚, 𝙮𝙤𝙪 𝙘𝙖𝙣 𝙖𝙥𝙥𝙚𝙖𝙡 𝙮𝙤𝙪𝙧 𝙗𝙖𝙣:",
            reply_markup=appeal_markup
        )
    except Exception as e:
        print(f"Could not notify banned user: {e}")

    sent_msg = bot.reply_to(message, f"✅ User {target_user_id} has been banned.", reply_markup=admin_markup)
    user_last_bot_message[user_id] = sent_msg.message_id

#================================= Unban User Command =============================================#
@bot.message_handler(func=lambda m: m.text == "✅ Unban User" and m.from_user.id in admin_user_ids)
def unban_user_start(message):
    """Start unban user process"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    msg = bot.reply_to(message, "Eɴᴛᴇʀ Uꜱᴇʀ Iᴅ Tᴏ Uɴʙᴀɴ:")
    user_last_bot_message[user_id] = msg.message_id
    bot.register_next_step_handler(msg, process_unban_user)

def process_unban_user(message):
    """Unban a user"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    if message.text == "✘ Cancel":
        sent_msg = bot.reply_to(message, "❌ Unban cancelled.", reply_markup=admin_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    target_user_id = message.text.strip()

    if not target_user_id.isdigit():
        sent_msg = bot.reply_to(message, "❌ Invalid user ID. Must be numeric.", reply_markup=admin_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    if not is_banned(target_user_id):
        sent_msg = bot.reply_to(message, "⚠️ User is not currently banned.", reply_markup=admin_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    unban_user(target_user_id)

    # Notify unbanned user
    try:
        bot.send_message(target_user_id, "✅ 𝗬𝗼𝘂𝗿 𝗯𝗮𝗻 𝗵𝗮𝘀 𝗯𝗲𝗲𝗻 𝗹𝗶𝗳𝘁𝗲𝗱. 𝗬𝗼𝘂 𝗰𝗮𝗻 𝗻𝗼𝘄 𝘂𝘀𝗲 𝘁𝗵𝗲 𝗯𝗼𝘁 𝗮𝗴𝗮𝗶𝗻.")
    except Exception as e:
        print(f"Could not notify unbanned user: {e}")

    sent_msg = bot.reply_to(message, f"✅ User {target_user_id} has been unbanned.", reply_markup=admin_markup)
    user_last_bot_message[user_id] = sent_msg.message_id

@bot.message_handler(func=lambda m: m.text == "📋 List Banned" and m.from_user.id in admin_user_ids)
def list_banned(message):
    """Show list of banned users"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    banned_users = get_banned_users()

    if not banned_users:
        sent_msg = bot.reply_to(message, "ℹ️ 𝗡𝗼 𝘂𝘀𝗲𝗿𝘀 𝗮𝗿𝗲 𝗰𝘂𝗿𝗿𝗲𝗻𝘁𝗹𝘆 𝗯𝗮𝗻𝗻𝗲𝗱.", reply_markup=admin_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    msg = "⛔ Banned Users:\n\n" + "\n".join(banned_users)
    sent_msg = bot.reply_to(message, msg, reply_markup=admin_markup)
    user_last_bot_message[user_id] = sent_msg.message_id

#==================== Leaderboard Command ==========================#
@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def show_leaderboard(message):
    """Show top 10 users by orders"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    top_users = get_top_users(10)
    
    if not top_users:
        sent_msg = bot.reply_to(message, "🏆 𝙉𝙤 𝙤𝙧𝙙𝙚𝙧 𝙙𝙖𝙩𝙖 𝙖𝙫𝙖𝙞𝙡𝙖𝙗𝙡𝙚 𝙮𝙚𝙩.", reply_markup=main_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return
    
    leaderboard = ["🏆 𝗧𝗼𝗽 𝗨𝘀𝗲𝗿𝘀 𝗯𝘆 𝗢𝗿𝗱𝗲𝗿𝘀:"]
    for i, (user_id, count) in enumerate(top_users, 1):
        try:
            user = bot.get_chat(user_id)
            name = user.first_name or f"User {user_id}"
            leaderboard.append(f"{i}. {name}: {count} orders")
        except:
            leaderboard.append(f"{i}. User {user_id}: {count} orders")
    
    sent_msg = bot.reply_to(message, "\n".join(leaderboard), reply_markup=main_markup)
    user_last_bot_message[user_id] = sent_msg.message_id

#======================= Function to Pin Annoucement Messages ====================#
@bot.message_handler(func=lambda m: m.text == "📌 Pin Message" and m.from_user.id in admin_user_ids)
def pin_message_start(message):
    """Start pin message process"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    msg = bot.reply_to(
        message,
        "📌 Sᴇɴᴅ Tʜᴇ Mᴇꜱꜱᴀɢᴇ Yᴏᴜ Wᴀɴᴛ Tᴏ Pɪɴ Iɴ Aʟʟ Uꜱᴇʀ Cʜᴀᴛꜱ:\n"
        "(ᴛʜɪꜱ ᴡɪʟʟ ᴘɪɴ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ᴀᴛ ᴛʜᴇ ᴛᴏᴘ ᴏꜰ ᴇᴀᴄʜ ᴜꜱᴇʀ'ꜱ ᴄʜᴀᴛ ᴡɪᴛʜ ᴛʜᴇ ʙᴏᴛ)\n\n"
        "Tʏᴘᴇ 'Cancel' Tᴏ Aʙᴏʀᴛ."
    )
    user_last_bot_message[user_id] = msg.message_id
    bot.register_next_step_handler(msg, process_pin_message)

def process_pin_message(message):
    """Process and send the pinned message to all users"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    if message.text == "Cancel":
        sent_msg = bot.reply_to(message, "❌ Pɪɴ Cᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=admin_markup)
        user_last_bot_message[user_id] = sent_msg.message_id
        return

    users = get_all_users()
    success = 0
    failed = 0

    sent_msg = bot.reply_to(message, "⏳ Sᴛᴀʀᴛɪɴɢ Tᴏ Pɪɴ Mᴇꜱꜱᴀɢᴇꜱ Iɴ Uꜱᴇʀ Cʜᴀᴛꜱ...", reply_markup=admin_markup)
    user_last_bot_message[user_id] = sent_msg.message_id

    for user_id in users:
        try:
            # Send and pin the message based on content type
            if message.content_type == 'text':
                sent_msg = bot.send_message(user_id, message.text, parse_mode="Markdown")
            elif message.content_type == 'photo':
                sent_msg = bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'document':
                sent_msg = bot.send_document(user_id, message.document.file_id, caption=message.caption)

            # Pin the message in the user's chat
            bot.pin_chat_message(user_id, sent_msg.message_id)
            success += 1
        except Exception as e:
            print(f"Failed to pin message for {user_id}: {e}")
            failed += 1
        time.sleep(0.1)  # Rate limiting

    sent_msg = bot.reply_to(
        message,
        f"📌 𝗣𝗶𝗻𝗻𝗶𝗻𝗴 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲:\n"
        f"✅ Successfully pinned in {success} chats\n"
        f"❌ Failed in {failed} chats",
        reply_markup=admin_markup
    )
    user_last_bot_message[user_id] = sent_msg.message_id


#================= Check User Info by ID ===================================#
@bot.message_handler(func=lambda m: m.text == "👤 User Info" and m.from_user.id in admin_user_ids)
def user_info_start(message):
    """Start user info process"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    msg = bot.reply_to(message, "Enter user ID or username (@username):")
    user_last_bot_message[user_id] = msg.message_id
    bot.register_next_step_handler(msg, process_user_info)

def process_user_info(message):
    """Process user info query"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    query = message.text.strip()
    try:
        if query.startswith('@'):
            user = bot.get_chat(query)
            target_user_id = user.id
        else:
            target_user_id = int(query)
            user = bot.get_chat(target_user_id)
        
        user_data = getData(target_user_id) or {}
        
        info = f"""
🔍 <b>𝗨𝘀𝗲𝗿 𝗜𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻</b>:
🆔 Iᴅ: <code>{target_user_id}</code>
👤 Nᴀᴍᴇ: {user.first_name} {user.last_name or ''}
📛 Uꜱᴇʀɴᴀᴍᴇ: @{user.username if user.username else 'N/A'}
💰 Bᴀʟᴀɴᴄᴇ: {user_data.get('balance', 0)}
📊 Oʀᴅᴇʀꜱ: {user_data.get('orders_count', 0)}
👥 Rᴇꜰᴇʀʀᴀʟꜱ: {user_data.get('total_refs', 0)}
🔨 Sᴛᴀᴛᴜꜱ: {"BANNED ⛔" if is_banned(target_user_id) else "ACTIVE ✅"}
        """
        sent_msg = bot.reply_to(message, info, parse_mode="HTML")
        user_last_bot_message[user_id] = sent_msg.message_id
    except ValueError:
        sent_msg = bot.reply_to(message, "❌ Invalid user ID. Must be numeric.")
        user_last_bot_message[user_id] = sent_msg.message_id
    except Exception as e:
        sent_msg = bot.reply_to(message, f"❌ Error: {str(e)}")
        user_last_bot_message[user_id] = sent_msg.message_id

#============================== Server Status Command ===============================#
@bot.message_handler(func=lambda m: m.text == "🖥 Server Status" and m.from_user.id in admin_user_ids)
def server_status(message):

    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    try:
        import psutil, platform
        from datetime import datetime
        from functions import db
        
        # System info
        uname = platform.uname()
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        # Memory info
        mem = psutil.virtual_memory()
        
        # Disk info
        disk = psutil.disk_usage('/')
        
        # MongoDB stats
        mongo_stats = db.command("dbstats")
        
        status = f"""
🖥 <b>𝙎𝙮𝙨𝙩𝙚𝙢 𝙎𝙩𝙖𝙩𝙪𝙨</b>
━━━━━━━━━━━━━━
💻 <b>Sʏꜱᴛᴇᴍ</b>: {uname.system} {uname.release}
⏱ <b>Uᴘᴛɪᴍᴇ</b>: {datetime.now() - boot_time}
━━━━━━━━━━━━━━━━━━━━━━━━
🧠 <b>Cᴘᴜ</b>: {psutil.cpu_percent()}% usage
💾 <b>Mᴇᴍᴏʀʏ</b>: {mem.used/1024/1024:.1f}MB / {mem.total/1024/1024:.1f}MB
🗄 <b>Dɪꜱᴋ</b>: {disk.used/1024/1024:.1f}MB / {disk.total/1024/1024:.1f}MB
━━━━━━━━━━━━━━━━━━━━━━━━
📊 <b>𝙈𝙤𝙣𝙜𝙤𝘿𝘽 𝙎𝙩𝙖𝙩𝙨</b>
📦 Dᴀᴛᴀ ꜱɪᴢᴇ: {mongo_stats['dataSize']/1024/1024:.1f}MB
🗃 Sᴛᴏʀᴀɢᴇ: {mongo_stats['storageSize']/1024/1024:.1f}MB
📂 Cᴏʟʟᴇᴄᴛɪᴏɴꜱ: {mongo_stats['collections']}
━━━━━━━━━━━━━━━━━━━━━━━━
        """
        sent_msg=bot.reply_to(message, status, parse_mode="HTML")
    except Exception as e:
        sent_msg=bot.reply_to(message, f"❌ Error getting status: {str(e)}")
        user_last_bot_message[user_id] = sent_msg.message_id

#========================== Export User Data (CSV) =================#
@bot.message_handler(func=lambda m: m.text == "📤 Export Data" and m.from_user.id in admin_user_ids)
def export_data(message):

    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    try:
        from functions import users_collection
        import csv
        from io import StringIO
        
        users = users_collection.find({})
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Username', 'Balance', 'Join Date', 'Referrals', 'Status'])
        
        # Write data
        for user in users:
            writer.writerow([
                user.get('user_id', ''),
                f"@{user.get('username', '')}" if user.get('username') else '',
                user.get('balance', 0),
                user.get('join_date', ''),
                user.get('total_refs', 0),
                'BANNED' if user.get('banned', False) else 'ACTIVE'
            ])
        
        # Send file
        output.seek(0)
        sent_msg=bot.send_document(
            message.chat.id,
            ('users_export.csv', output.getvalue()),
            caption="📊 Uꜱᴇʀ Dᴀᴛᴀ Exᴘᴏʀᴛ"
        )
    except Exception as e:
        sent_msg=bot.reply_to(message, f"❌ Export failed: {str(e)}")
        user_last_bot_message[user_id] = sent_msg.message_id

#======================= Maintenance Mode command ==================================#

# Add this at the top with other global variables
maintenance_mode = False
maintenance_message = "🚧 𝙏𝙝𝙚 𝙗𝙤𝙩 𝙞𝙨 𝙘𝙪𝙧𝙧𝙚𝙣𝙩𝙡𝙮 𝙪𝙣𝙙𝙚𝙧 𝙢𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚. 𝙋𝙡𝙚𝙖𝙨𝙚 𝙩𝙧𝙮 𝙖𝙜𝙖𝙞𝙣 𝙡𝙖𝙩𝙚𝙧."

# Maintenance toggle command
@bot.message_handler(func=lambda m: m.text == "🔧 Maintenance" and m.from_user.id in admin_user_ids)
def toggle_maintenance(message):
    """Toggle maintenance mode"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    global maintenance_mode, maintenance_message

    if maintenance_mode:
        maintenance_mode = False
        sent_msg = bot.reply_to(message, "✅ 𝙈𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚 𝙢𝙤𝙙𝙚 𝘿𝙄𝙎𝘼𝘽𝙇𝙀𝘿")
        user_last_bot_message[user_id] = sent_msg.message_id
    else:
        msg = bot.reply_to(message, "✍️ Eɴᴛᴇʀ Mᴀɪɴᴛᴇɴᴀɴᴄᴇ Mᴇꜱꜱᴀɢᴇ Tᴏ Sᴇɴᴅ Tᴏ Uꜱᴇʀꜱ:")
        user_last_bot_message[user_id] = msg.message_id
        bot.register_next_step_handler(msg, set_maintenance_message)

def set_maintenance_message(message):
    """Set maintenance message and enable maintenance mode"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    global maintenance_mode, maintenance_message
    maintenance_message = message.text
    maintenance_mode = True

    # Send maintenance message to all users
    users = get_all_users()
    sent = 0
    for user_id in users:
        try:
            bot.send_message(user_id, f"⚠️ 𝙈𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚 𝙉𝙤𝙩𝙞𝙘𝙚:\n{maintenance_message}")
            sent += 1
            time.sleep(0.1)
        except Exception as e:
            print(f"Failed to send maintenance message to {user_id}: {e}")
            continue

    sent_msg = bot.reply_to(message, f"🔧 𝙈𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚 𝙢𝙤𝙙𝙚 𝙀𝙉𝘼𝘽𝙇𝙀𝘿\nMessage sent to {sent} users")
    user_last_bot_message[user_id] = sent_msg.message_id

def auto_disable_maintenance():
    """Automatically disable maintenance mode after 1 hour"""
    global maintenance_mode
    time.sleep(3600)  # 1 hour
    maintenance_mode = False

# Start auto-disable thread in set_maintenance_message
threading.Thread(target=auto_disable_maintenance).start()

#============================ Order Management Commands =============================#
@bot.message_handler(func=lambda m: m.text == "📦 Order Manager" and m.from_user.id in admin_user_ids)
def check_order_start(message):
    """Start order check process"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    msg = bot.reply_to(message, "Enter Order ID:")
    user_last_bot_message[user_id] = msg.message_id
    bot.register_next_step_handler(msg, process_check_order)

def process_check_order(message):
    """Process order check"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    order_id = message.text.strip()
    try:
        from functions import orders_collection
        order = orders_collection.find_one({"order_id": order_id})
        
        if order:
            status_time = datetime.fromtimestamp(order.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M')
            status = f"""
📦 <b>Order #{order_id}</b>
━━━━━━━━━━━━━━
👤 Uꜱᴇʀ: {order.get('username', 'N/A')} (<code>{order.get('user_id', 'N/A')}</code>)
🛒 Sᴇʀᴠɪᴄᴇ: {order.get('service', 'N/A')}
🔗 Lɪɴᴋ: {order.get('link', 'N/A')}
📊 Qᴜᴀɴᴛɪᴛʏ: {order.get('quantity', 'N/A')}
💰 Cᴏꜱᴛ: {order.get('cost', 'N/A')}
🔄 Sᴛᴀᴛᴜꜱ: {order.get('status', 'N/A')}
⏱ Dᴀᴛᴇ: {status_time}
            """
            sent_msg = bot.reply_to(message, status, parse_mode="HTML", disable_web_page_preview=True)
            user_last_bot_message[user_id] = sent_msg.message_id
        else:
            sent_msg = bot.reply_to(message, "❌ Order not found")
            user_last_bot_message[user_id] = sent_msg.message_id
    except Exception as e:
        sent_msg = bot.reply_to(message, f"❌ Error: {str(e)}")
        user_last_bot_message[user_id] = sent_msg.message_id


#========================== Add this handler for the /policy command =================#
@bot.message_handler(commands=['policy'])
def policy_command(message):
    """Show the bot's usage policy"""
    user_id = message.from_user.id

    # Clean previous messages
    cleanup_previous_messages(user_id)
    user_last_user_message[user_id] = message.message_id

    policy_text = """
📜 𝘽𝙤𝙩 𝙐𝙨𝙖𝙜𝙚 𝙋𝙤𝙡𝙞𝙘𝙮 📜

1. **Prohibited Content**: Do not use this bot to promote illegal content, spam, or harassment.

2. **Fair Use**: Abuse of the bot's services may result in account suspension.

3. **Refunds**: All purchases are final. No refunds will be issued for completed orders.

4. **Privacy**: We respect your privacy. Your data will not be shared with third parties.

5. **Compliance**: Users must comply with all Telegram Terms of Service.

Violations of these policies may result in permanent bans.
"""
    sent_msg = bot.reply_to(message, policy_text, parse_mode="Markdown")
    user_last_bot_message[user_id] = sent_msg.message_id


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
def get_formatted_datetime():
    """Get current datetime in East Africa Time (EAT) timezone"""
    tz = pytz.timezone('Africa/Nairobi')  # Nairobi is in EAT timezone
    now = datetime.now(tz)
    return {
        'date': now.strftime('%Y-%m-%d'),
        'time': now.strftime('%I:%M:%S %p'),
        'timezone': now.strftime('%Z')  # This will show 'EAT'
    }

def send_startup_message(is_restart=False):
    """Send bot status message to logs channel"""
    try:
        dt = get_formatted_datetime()
        status = "Rᴇsᴛᴀʀᴛᴇᴅ" if is_restart else "Sᴛᴀʀᴛᴇᴅ"
        
        message = f"""
🚀 <b>Bᴏᴛ {status}</b> !

📅 Dᴀᴛᴇ : {dt['date']}
⏰ Tɪᴍᴇ : {dt['time']}
🌐 Tɪᴍᴇᴢᴏɴᴇ : {dt['timezone']}
🛠️ Bᴜɪʟᴅ Sᴛᴀᴛᴜs: v2 [ Sᴛᴀʙʟᴇ ]
"""
        bot.send_message(
            chat_id=payment_channel,  # Or your specific logs channel ID
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending startup message: {e}")
      
# ==================== FLASK INTEGRATION ==================== #

# Create enhanced Flask app
web_app = Flask(__name__)
start_time = time.time()  # Track bot start time

@web_app.route('/')
def home():
    return jsonify({
        "status": "running",
        "bot": bot.get_me().username,
        "uptime_seconds": time.time() - start_time,
        "admin_count": len(admin_user_ids),
        "version": "1.0"
    }), 200

@web_app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "memory_usage": f"{psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.2f} MB"
    }), 200

@web_app.route('/ping')
def ping():
    """Endpoint for keep-alive pings"""
    return "pong", 200

# ==================== KEEP-ALIVE SYSTEM ==================== #
def keep_alive():
    """Pings the server periodically to prevent shutdown"""
    while True:
        try:
            # Ping our own health endpoint
            requests.get(f'http://localhost:{os.getenv("PORT", "10000")}/ping', timeout=5)
            # Optionally ping external services
            requests.get('https://www.google.com', timeout=5)
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
        time.sleep(120)  # Ping every 5 minutes

# ==================== BOT POLLING ==================== #
def run_bot():
    set_bot_commands()
    print("Bot is running...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            error_msg = f"Bot polling failed: {str(e)[:200]}"
            print(error_msg)
            
            # Send alert to all admins
            for admin_id in admin_user_ids:
                try:
                    bot.send_message(
                        admin_id,
                        f"⚠️ <b>Bot Error Notification</b> ⚠️\n\n"
                        f"🔧 <code>{error_msg}</code>\n\n"
                        f"🔄 Bot is automatically restarting...",
                        parse_mode='HTML'
                    )
                except Exception as admin_error:
                    print(f"Failed to notify admin {admin_id}: {admin_error}")
            
            time.sleep(10)  # Wait before restarting
            send_startup_message(is_restart=True)

# ==================== MAIN EXECUTION ==================== #
if __name__ == '__main__':
    import threading
    
    # Start keep-alive thread
    keep_alive_thread = threading.Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Start Flask web server in main thread
    web_app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', '10000')),
        debug=False,
        use_reloader=False,
        threaded=True  # Enable multi-threading for better performance
    )
