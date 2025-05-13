import telebot
import re
import requests
import time
import os
import traceback
import logging
import psutil
import threading
from threading import Thread
import datetime
from datetime import datetime
import pytz
from functools import wraps
from flask import Flask, jsonify
from dotenv import load_dotenv
import logging
from telebot import types
from logging.handlers import RotatingFileHandler
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from telebot.types import ForceReply, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from functions import (insertUser, track_exists, addBalance, cutBalance, getData,
                       addRefCount, isExists, setWelcomeStaus, setReferredStatus, updateUser, 
                       ban_user, unban_user, get_all_users, is_banned, get_banned_users, 
                       get_top_users, get_user_count, get_active_users, get_total_orders, 
                       get_total_deposits, get_top_referrer, get_user_orders_stats, get_new_users,
                       get_completed_orders, get_all_users, save_pinned_message, get_all_pinned_messages,
                         clear_all_pinned_messages, orders_collection, get_confirmed_spent, get_pending_spent) # Import your functions from functions.py



# Load environment variables from .env file
load_dotenv()

# =============== Bot Configuration =============== #
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
SmmPanelApi = os.getenv("SMM_PANEL_API_KEY")
SmmPanelApiUrl = os.getenv("SMM_PANEL_API_URL")
# Simple admin IDs loading (comma-separated in .env)
# Replace the single admin line with:
admin_user_ids = [int(id.strip()) for id in os.getenv("ADMIN_USER_IDS", "").split(",") if id.strip()]

bot = telebot.TeleBot(bot_token)


welcome_bonus = 60
ref_bonus = 50

# Main keyboard markup
main_markup = ReplyKeyboardMarkup(resize_keyboard=True)
button1 = KeyboardButton("🛒 Buy Services")  # Changed from "👁‍🗨 Order View"
button2 = KeyboardButton("👤 My Account")
button3 = KeyboardButton("💳 Pricing")
button4 = KeyboardButton("📊 Order Stats")
button5 = KeyboardButton("🗣 Invite")
button6 = KeyboardButton("🏆 Leaderboard")
button7 = KeyboardButton("📜 Help")

main_markup.add(button1, button2)
main_markup.add(button3, button4)
main_markup.add(button5, button6)
main_markup.add(button7)

# Admin keyboard markup
admin_markup = ReplyKeyboardMarkup(resize_keyboard=True)
admin_markup.row("➕ Add Coins", "➖ Remove Coins")
admin_markup.row("📌 Pin Message", "📍 Unpin")
admin_markup.row("🔒 Ban User", "✅ Unban User")
admin_markup.row("📋 List Banned", "👤 User Info")  # New
admin_markup.row("🖥 Server Status", "📤 Export Data")  # New
admin_markup.row("📦 Order Manager", "📊 Analytics")  # New
admin_markup.row("🔧 Maintenance", "📤 Broadcast")
admin_markup.row("📦 Batch Coins")
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
    KeyboardButton("👀 Post Views"),
    KeyboardButton("❤️ Post Reactions")
)
telegram_services_markup.row(
    KeyboardButton("👥 Channel Members"),
)
telegram_services_markup.row(
    KeyboardButton("↩️ Go Back")
)

# TikTok services menu (placeholder for now)
tiktok_services_markup = ReplyKeyboardMarkup(resize_keyboard=True)
tiktok_services_markup.row(
    KeyboardButton("👀 Tiktok Views"),
    KeyboardButton("❤️ Tiktok Likes")
)
tiktok_services_markup.row(
    KeyboardButton("👥 Tiktok Followers"),
)
tiktok_services_markup.row(
    KeyboardButton("↩️ Go Back")
)

# Instagram services menu
instagram_services_markup = ReplyKeyboardMarkup(resize_keyboard=True)
instagram_services_markup.row(
    KeyboardButton("🎥 Video Views"),
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
    KeyboardButton("👥 Channel Subscribers"),
)
whatsapp_services_markup.row(
    KeyboardButton("😀 Post EmojiReaction")
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
#================================== Force Join Method =======================================#
required_channels = ["smmserviceslogs"]  # Channel usernames without "@"
payment_channel = "@smmserviceslogs"  # Channel for payment notifications

def is_user_member(user_id):
    """Check if a user is a member of all required channels."""
    for channel in required_channels:
        try:
            chat_member = bot.get_chat_member(chat_id=f"@{channel}", user_id=user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"Error checking channel membership for {channel}: {e}")
            # If there's an error checking, assume user is not member
            return False
    return True

def check_membership_and_prompt(user_id, message):
    """Check if the user is a member of all required channels and prompt them to join if not."""
    if not is_user_member(user_id):
        # First, check if this is a callback query or regular message
        if hasattr(message, 'message_id'):
            chat_id = message.chat.id
            reply_to_message_id = message.message_id
        else:
            chat_id = message.chat.id
            reply_to_message_id = None
        
        # Send the join message
        bot.send_message(
            chat_id=chat_id,
            reply_to_message_id=reply_to_message_id,
            text="""
<blockquote>
*🚀 Wᴇʟᴄᴏᴍᴇ Tᴏ Sᴍᴍʜᴜʙ Bᴏᴏꜱᴛᴇʀ Bᴏᴛ ! 🚀*

🚨 *Tᴏ Uꜱᴇ Tʜɪꜱ Bᴏᴛ, Yᴏᴜ Mᴜꜱᴛ Jᴏɪɴ Tʜᴇ RᴇQᴜɪʀᴇᴅ Cʜᴀɴɴᴇʟꜱ Fɪʀꜱᴛ!* 🚨

📊 *Cᴏᴍᴘʟᴇᴛᴇ Tʜᴇꜱᴇ Sᴛᴇᴘꜱ Tᴏ Uɴʟᴏᴄᴋ:*
▫️ Jᴏɪɴ Aʟʟ Cʜᴀɴɴᴇʟꜱ Bᴇʟᴏᴡ
▫️ Cʟɪᴄᴋ *'✅ VERIFY MEMBERSHIP'* Bᴜᴛᴛᴏɴ
▫️ Wᴀɪᴛ Fᴏʀ Vᴇʀɪғɪᴄᴀᴛɪᴏɴ


🔐 *Vᴇʀɪғɪᴄᴀᴛɪᴏɴ Sᴛᴀᴛᴜꜱ:* 𝘕𝘰𝘵 𝘝𝘦𝘳𝘪𝘧𝘪𝘦𝘥
━━━━━━━━━━━━━━━━━━━━
</blockquote>""",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
              #  [InlineKeyboardButton("📢 MAIN CHANNEL", url="https://t.me/SmmBoosterz")],
              #  [InlineKeyboardButton("🤖 BOTS UPDATE", url="https://t.me/Megahubbots")],
               # [InlineKeyboardButton("💎 PROMOTER CHANNEL", url="https://t.me/Freenethubz")],
               # [InlineKeyboardButton("🔰 BACKUP CHANNEL", url="https://t.me/Freenethubchannel")],
                [InlineKeyboardButton("📝 LOGS CHANNEL", url="https://t.me/smmserviceslogs")],
               # [InlineKeyboardButton("📱 WHATSAPP CHANNEL", url="https://whatsapp.com/channel/0029VaDnY2y0rGiPV41aSX0l")],
                [InlineKeyboardButton("✨ ✅ VERIFY MEMBERSHIP", callback_data="verify_membership")],
                [InlineKeyboardButton("❓ Why Join These Channels?", callback_data="why_join_info")]
            ])
        )
        return False
    return True

@bot.callback_query_handler(func=lambda call: call.data == "why_join_info")
def handle_why_join(call):
    """Send the privileges info when user clicks 'Why Join?' button"""
    perks_text = """
<blockquote>
🛡️ *𝙋𝙧𝙞𝙫𝙞𝙡𝙚𝙜𝙚𝙨 𝙮𝙤𝙪'𝙡𝙡 𝙜𝙚𝙩:*
✓ Fᴜʟʟ Bᴏᴛ Aᴄᴄᴇꜱꜱ  
✓ Exᴄʟᴜꜱɪᴠᴇ Oғғᴇʀꜱ  
✓ Pʀᴇᴍɪᴜᴍ Sᴜᴘᴘᴏʀᴛ  
✓ Rᴇɢᴜʟᴀʀ Uᴘᴅᴀᴛᴇꜱ
━━━━━━━━━━━━━━━━━━━━
</blockquote>
"""
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, perks_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "verify_membership")
def verify_membership(call):
    user_id = call.from_user.id
    
    if is_user_member(user_id):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_welcome(call.message)
        except Exception as e:
            print(f"Error in verify_membership: {e}")
            bot.answer_callback_query(
                call.id,
                text="✅ Hᴇʏ! Yᴏᴜ ᴀʀᴇ ᴠᴇʀɪꜰɪᴇᴅ! Yᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ. Cʟɪᴄᴋ /start ᴀɢᴀɪɴ.",
                show_alert=True
            )
    else:
        bot.answer_callback_query(
            call.id,
            text="❌ Yᴏᴜ ʜᴀᴠᴇɴ'ᴛ ᴊᴏɪɴᴇᴅ ᴀʟʟ ᴛʜᴇ ʀᴇQᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟꜱ ʏᴇᴛ!",
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
            bot.reply_to(message, "⛔ ❝Yᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ʙᴀɴɴᴇᴅ ꜰʀᴏᴍ ᴜꜱɪɴɢ ᴛʜɪꜱ ʙᴏᴛ❞.")
            return
            
        return func(message, *args, **kwargs)
    return wrapped
#================== Send Orders Button ============================#
@bot.message_handler(func=lambda message: message.text == "🛒 Buy Services")
@check_ban
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
    bot.reply_to(message, "📤 Sᴇʟᴇᴄᴛ Pʟᴀᴛꜰᴏʀᴍ Tᴏ Sᴇɴᴅ Oʀᴅᴇʀꜱ:", reply_markup=send_orders_markup)


def set_bot_commands():
    commands = [
        BotCommand('start', 'Restart the bot'),
        BotCommand('policy', 'View usage policy'),
    ]
    
    # Admin-only commands
    admin_commands = [
        BotCommand('adminpanel', 'Access admin controls'),
    ]
    
    try:
        # Set basic commands for all users
        bot.set_my_commands(commands)
        
        # Set admin commands specifically for admin users
        for admin_id in admin_user_ids:
            try:
                bot.set_chat_menu_button(
                    chat_id=admin_id,
                    menu_button=types.MenuButtonCommands()
                )
                bot.set_my_commands(admin_commands + commands, scope=types.BotCommandScopeChat(admin_id))
            except Exception as e:
                print(f"Error setting admin commands for {admin_id}: {e}")
        
        print("Bot commands set successfully")
    except Exception as e:
        print(f"Error setting bot commands: {e}")
  
#======================= Start Command =======================#
@bot.message_handler(commands=['start']) 
@check_ban
def send_welcome(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    ref_by = message.text.split()[1] if len(message.text.split()) > 1 and message.text.split()[1].isdigit() else None

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

    # Professional Referral bonus logic
    data = getData(user_id)
    if data['ref_by'] != "none" and data['referred'] == 0:
        referrer_data = getData(data['ref_by'])
        referral_message = f"""
<blockquote>
🎉 <b>Rᴇꜰᴇʀʀᴀʟ Rᴇᴡᴀʀᴅ Nᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ</b> 🎉

Wᴇ'ʀᴇ ᴘʟᴇᴀꜱᴇᴅ ᴛᴏ ɪɴꜰᴏʀᴍ ʏᴏᴜ ᴛʜᴀᴛ ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ <b>{first_name}</b> ʜᴀꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴊᴏɪɴᴇᴅ ᴜꜱɪɴɢ ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ.

💰 <b>Rᴇᴡᴀʀᴅ Cʀᴇᴅɪᴛᴇᴅ:</b> +{ref_bonus} ᴄᴏɪɴꜱ
📈 <b>Yᴏᴜʀ Tᴏᴛᴀʟ Rᴇꜰᴇʀʀᴀʟꜱ:</b> {int(referrer_data.get('total_refs', 0)) + 1}
💎 <b>Cᴜʀʀᴇɴᴛ Bᴀʟᴀɴᴄᴇ:</b> {float(referrer_data.get('balance', 0)) + float(ref_bonus):.2f} ᴄᴏɪɴꜱ

Kᴇᴇᴘ ꜱʜᴀʀɪɴɢ ʏᴏᴜʀ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ ᴛᴏ ᴇᴀʀɴ ᴍᴏʀᴇ ʀᴇᴡᴀʀᴅꜱ!
Yᴏᴜʀ ᴜɴɪQᴜᴇ ʟɪɴᴋ: https://t.me/{bot.get_me().username}?start={data['ref_by']}

Tʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ʜᴇʟᴘɪɴɢ ɢʀᴏᴡ ᴏᴜʀ ᴄᴏᴍᴍᴜɴɪᴛʏ!
</blockquote>
"""
        bot.send_message(
            data['ref_by'], 
            referral_message,
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        addBalance(data['ref_by'], ref_bonus)
        setReferredStatus(user_id)

    # Send welcome image with caption
    welcome_image_url = "https://t.me/smmserviceslogs/20"  # Replace with your image URL
    welcome_caption = f"""
<blockquote>
🎉 <b>Wᴇʟᴄᴏᴍᴇ {first_name}!</b> 🎉

👤 <b>Uꜱᴇʀɴᴀᴍᴇ:</b> {username}

Wɪᴛʜ ᴏᴜʀ ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ ʙᴏᴏꜱᴛ ʏᴏᴜʀ ꜱᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ ᴀᴄᴄᴏᴜɴᴛꜱ & ᴘᴏꜱᴛꜱ ᴡɪᴛʜ ᴊᴜꜱᴛ ᴀ ꜰᴇᴡ ꜱɪᴍᴘʟᴇ ꜱᴛᴇᴘꜱ!

👇 <b>Cʜᴏᴏꜱᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ɢᴇᴛ ꜱᴛᴀʀᴛᴇᴅ:</b>
</blockquote>
"""

    try:
        # Send photo with caption
        bot.send_photo(
            chat_id=user_id,
            photo=welcome_image_url,
            caption=welcome_caption,
            parse_mode='HTML',
            reply_markup=main_markup
        )

        # Send welcome bonus message separately if applicable
        if userData['welcome_bonus'] == 0:
            bot.send_message(
                user_id,
                f"🎁 <b>You received +{welcome_bonus} coins welcome bonus!</b>",
                parse_mode='HTML'
            )

        # ✅ ADDITION: Check for pending orders and notify the user
        stats = get_user_orders_stats(user_id)
        if stats['pending'] > 0:
            bot.send_message(
                user_id,
                f"⏳ You have {stats['pending']} pending orders",
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("View Orders", callback_data="order_history")
                )
            )

    except Exception as e:
        print(f"Error in send_welcome: {e}")

#====================== My Account =====================#
@bot.message_handler(func=lambda message: message.text == "👤 My Account")
def my_account(message):
    user_id = str(message.chat.id)
    data = getData(user_id)
    
    confirmed_spent = get_confirmed_spent(user_id)
    pending_spent = get_pending_spent(user_id)


    if not data:
        bot.reply_to(message, "❌ Account not found. Please /start again.")
        return
    
    # Update last activity and username
    data['last_activity'] = time.time()
    data['username'] = message.from_user.username
    updateUser(user_id, data)
    
    # Get current time and date
    now = datetime.now()
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%Y-%m-%d")
    
    # Get user profile photos
    photos = bot.get_user_profile_photos(message.from_user.id, limit=1)
    
    # Format the message
    caption = f"""
<blockquote>
<b><u>𝗠𝘆 𝗔𝗰𝗰𝗼𝘂𝗻𝘁</u></b>

🆔 Uꜱᴇʀ Iᴅ: <code>{user_id}</code>
👤 Uꜱᴇʀɴᴀᴍᴇ: @{message.from_user.username if message.from_user.username else "N/A"}
🗣 Iɴᴠɪᴛᴇᴅ Uꜱᴇʀꜱ: {data.get('total_refs', 0)}
⏰ Tɪᴍᴇ: {current_time}
📅 Dᴀᴛᴇ: {current_date}

🪙 Bᴀʟᴀɴᴄᴇ: <code>{data['balance']}</code> Cᴏɪɴꜱ
💸 Cᴏɴꜰɪʀᴍᴇᴅ Sᴘᴇɴᴛ: <code>{confirmed_spent:.2f}</code> Cᴏɪɴꜱ
⏳ Pᴇɴᴅɪɴɢ Sᴘᴇɴᴅɪɴɢ: <code>{pending_spent:.2f}</code> Cᴏɪɴꜱ
</blockquote>
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
@bot.message_handler(func=lambda message: message.text == "🗣 Invite")
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
<blockquote>
💎 <b>𝙃𝙤𝙬 𝙞𝙩 𝙒𝙤𝙧𝙠𝙨:</b>  
1️⃣ Sʜᴀʀᴇ ʏᴏᴜʀ ᴜɴɪQᴜᴇ ʟɪɴᴋ ᴡɪᴛʜ ꜰʀɪᴇɴᴅꜱ  
2️⃣ Wʜᴇɴ ᴛʜᴇʏ ᴊᴏɪɴ ᴜꜱɪɴɢ ʏᴏᴜʀ ʟɪɴᴋ, <b>Bᴏᴛʜ ᴏꜰ ʏᴏᴜ ɢᴇᴛ {ref_bonus} ᴄᴏɪɴꜱ</b> ɪɴꜱᴛᴀɴᴛʟʏ!  
3️⃣ Eᴀʀɴ ᴜɴʟɪᴍɪᴛᴇᴅ ᴄᴏɪɴꜱ - <b>Nᴏ ʟɪᴍɪᴛꜱ ᴏɴ ʀᴇꜰᴇʀʀᴀʟꜱ!</b>  

🏆 <b>Bᴏɴᴜꜱ:</b> Tᴏᴘ ʀᴇꜰᴇʀʀᴇʀꜱ ɢᴇᴛ ꜱᴘᴇᴄɪᴀʟ ʀᴇᴡᴀʀᴅꜱ!  

💰 <b>Wʜʏ Wᴀɪᴛ?</b> Sᴛᴀʀᴛ ɪɴᴠɪᴛɪɴɢ ɴᴏᴡ ᴀɴᴅ ʙᴏᴏꜱᴛ ʏᴏᴜʀ ʙᴀʟᴀɴᴄᴇ ꜰᴏʀ ꜰʀᴇᴇ!  

📌 <b>Pʀᴏ Tɪᴘ:</b> Sʜᴀʀᴇ ʏᴏᴜʀ ʟɪɴᴋ ɪɴ ɢʀᴏᴜᴘꜱ/ᴄʜᴀᴛꜱ ᴡʜᴇʀᴇ ᴘᴇᴏᴘʟᴇ ɴᴇᴇᴅ ꜱᴏᴄɪᴀʟ ᴍᴇᴅɪᴀ ɢʀᴏᴡᴛʜ!

📊 <b>Yᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ʀᴇꜰᴇʀʀᴀʟꜱ:</b> {total_refs}
</blockquote>
"""
    
    bot.reply_to(
        message,
        referral_message,
        parse_mode='HTML',
        disable_web_page_preview=True
    )

#======================= Help =======================#
@bot.message_handler(func=lambda message: message.text == "📜 Help")
def help_command(message):
    user_id = message.chat.id
    msg = f"""
<blockquote>
<b>FʀᴇQᴜᴇɴᴛʟʏ Aꜱᴋᴇᴅ Qᴜᴇꜱᴛɪᴏɴꜱ</b>

<b>• Aʀᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇꜱ ʀᴇᴀʟ?</b>
ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇꜱ ᴀʀᴇ ʀᴀɴᴅᴏᴍʟʏ ꜱᴇʟᴇᴄᴛᴇᴅ ꜰʀᴏᴍ ᴏᴜʀ ᴘᴀɴᴇʟ ʙᴜᴛ ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴏɴʟʏ ʀᴇᴀʟ ᴏɴᴇꜱ ᴏɴʟʏ, ꜰᴇᴇʟ ꜰʀᴇᴇ ᴛᴏ ᴄᴏɴᴛᴀᴄᴛ ᴜꜱ ꜰᴏʀ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ.

<b>• Wʜᴀᴛ'ꜱ ᴛʜᴇ ᴀᴠᴇʀᴀɢᴇ ꜱᴇʀᴠɪᴄᴇ ꜱᴘᴇᴇᴅ?</b>
Dᴇʟɪᴠᴇʀʏ ꜱᴘᴇᴇᴅ ᴠᴀʀɪᴇꜱ ʙᴀꜱᴇᴅ ᴏɴ ɴᴇᴛᴡᴏʀᴋ ᴄᴏɴᴅɪᴛɪᴏɴꜱ ᴀɴᴅ ᴏʀᴅᴇʀ ᴠᴏʟᴜᴍᴇ, ʙᴜᴛ ᴡᴇ ᴇɴꜱᴜʀᴇ ꜰᴀꜱᴛ ᴅᴇʟɪᴠᴇʀʏ.

<b>• Hᴏᴡ ᴛᴏ ɪɴᴄʀᴇᴀꜱᴇ ʏᴏᴜʀ ᴄᴏɪɴꜱ?</b>
1️⃣ Iɴᴠɪᴛᴇ ꜰʀɪᴇɴᴅꜱ - Eᴀʀɴ {ref_bonus} ᴄᴏɪɴꜱ ᴘᴇʀ ʀᴇꜰᴇʀʀᴀʟ
2️⃣ Bᴜʏ ᴄᴏɪɴ ᴘᴀᴄᴋᴀɢᴇꜱ - Aᴄᴄᴇᴘᴛᴇᴅ ᴘᴀʏᴍᴇɴᴛꜱ:
   • Mᴏʙɪʟᴇ Mᴏɴᴇʏ
   • Cʀʏᴘᴛᴏᴄᴜʀʀᴇɴᴄɪᴇꜱ (BTC, USDT, ᴇᴛᴄ.)
   • WᴇʙMᴏɴᴇʏ & Pᴇʀꜰᴇᴄᴛ Mᴏɴᴇʏ
   
<b>• Bᴜɢꜱ Rᴇᴘᴏʀᴛ Rᴇᴡᴀʀᴅ:</b>
Wᴇ ʀᴇᴡᴀʀᴅ ᴏᴜʀ Uꜱᴇʀꜱ Fʀᴇᴇ 100 ᴄᴏɪɴꜱ ꜰᴏʀ ᴇᴀᴄʜ Bᴜɢ ᴏʀ Eʀʀᴏʀ ᴛʜᴇʏ Rᴇᴘᴏʀᴛ ᴛᴏ Uꜱ. Jᴜꜱᴛ ᴄʟɪᴄᴋ ᴛʜᴇ Bᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.

<b>• Cᴀɴ I ᴛʀᴀɴꜱꜰᴇʀ ᴍʏ ʙᴀʟᴀɴᴄᴇ?</b>
Yᴇꜱ! Fᴏʀ ʙᴀʟᴀɴᴄᴇꜱ ᴏᴠᴇʀ 10,000 ᴄᴏɪɴꜱ, ᴄᴏɴᴛᴀᴄᴛ ꜱᴜᴘᴘᴏʀᴛ.
</blockquote>
"""

    # Create inline button for support
    markup = InlineKeyboardMarkup()
    support_button = InlineKeyboardButton("🆘 Contact Support", url="https://t.me/SocialHubBoosterTMbot")
    markup.add(support_button)

    bot.reply_to(
        message, 
        msg,
        parse_mode="HTML",
        reply_markup=markup
    )

#======================== Pricing Command =======================#
@bot.message_handler(func=lambda message: message.text == "💳 Pricing")
def pricing_command(message):
    user_id = message.chat.id
    msg = f"""<b><u>💎 Pricing 💎</u></b>

<i> Cʜᴏᴏꜱᴇ Oɴᴇ Oꜰ Tʜᴇ Cᴏɪɴꜱ Pᴀᴄᴋᴀɢᴇꜱ Aɴᴅ Pᴀʏ Iᴛꜱ Cᴏꜱᴛ Vɪᴀ Pʀᴏᴠɪᴅᴇᴅ Pᴀʏᴍᴇɴᴛ Mᴇᴛʜᴏᴅꜱ.</i>
<blockquote>
<b><u>📜 𝐏𝐚𝐜𝐤𝐚𝐠𝐞𝐬:</u></b>
<b>➊ 📦 10K coins – $1.00
➋ 📦 30K coins – $2.50
➌ 📦 50K coins – $4.00
➍ 📦 100K coins – $7.00
➎ 📦 150K coins – $10.00
➏ 📦 300K coins – $15.00 </b>
</blockquote>
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
# ============================= Enhanced Order Statistics with Auto-Clean ============================= #
@bot.message_handler(func=lambda message: message.text == "📊 Order Stats")
@check_ban
def show_order_stats(message):
    """Show performance overview only. Hide completed/failed orders immediately."""
    user_id = str(message.from_user.id)

    try:
        stats = get_user_orders_stats(user_id)

        # Immediately hide completed and failed orders
        orders_collection.update_many(
            {
                "user_id": user_id,
                "status": {"$in": ["completed", "Completed", "failed", "Failed"]},
                "hidden": {"$ne": True}
            },
            {"$set": {"hidden": True}}
        )

        completion_rate = (stats['completed'] / stats['total']) * 100 if stats['total'] > 0 else 0

        msg = f"""
📦 <b>Yᴏᴜʀ SMM Oʀᴅᴇʀ Pᴏʀᴛꜰᴏʟɪᴏ</b>
━━━━━━━━━━━━━━━━━━━━

📊 <b>Pᴇʀꜰᴏʀᴍᴀɴᴄᴇ Oᴠᴇʀᴠɪᴇᴡ</b>
├ 🔄 Tᴏᴛᴀʟ Oʀᴅᴇʀꜱ: <code>{stats['total']}</code>
├ ✅ Cᴏᴍᴘʟᴇᴛɪᴏɴ Rᴀᴛᴇ: <code>{completion_rate:.1f}%</code>
├ ⏳ Pᴇɴᴅɪɴɢ: <code>{stats['pending']}</code>
└ ❌ Fᴀɪʟᴇᴅ: <code>{stats['failed']}</code>

📌 <b>NOTE:</b> Iꜰ ʏᴏᴜ ʜᴀᴠᴇ ᴀ Fᴀɪʟᴇᴅ Oʀᴅᴇʀ ᴀɴᴅ ʏᴏᴜʀ Cᴏɪɴꜱ ᴡᴇʀᴇ Dᴇᴅᴜᴄᴛᴇᴅ, 
Vɪꜱɪᴛ ᴛʜᴇ @smmserviceslogs ᴀɴᴅ ɢᴇᴛ ʏᴏᴜʀ Oʀᴅᴇʀ Iᴅ. 
Tʜᴇɴ ꜱᴇɴᴅ ɪᴛ ᴛᴏ ᴛʜᴇ Aᴅᴍɪɴ ꜰᴏʀ Aꜱꜱɪꜱᴛᴀɴᴄᴇ @SocialHubBoosterTMbot.
"""

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("📜 Check Orders", callback_data="order_history")
        )

        if hasattr(message, 'is_callback'):
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=msg,
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            sent_msg = bot.send_message(
                message.chat.id,
                msg,
                parse_mode='HTML',
                reply_markup=markup
            )
            threading.Thread(target=delete_after_delay, args=(message.chat.id, sent_msg.message_id, 120)).start()

    except Exception as e:
        print(f"Order stats error: {e}")
        bot.reply_to(message,
            "⚠️ <b>Oʀᴅᴇʀ Sᴛᴀᴛɪꜱᴛɪᴄꜱ Uɴᴀᴠᴀɪʟᴀʙʟᴇ</b>\n\n"
            "ᴡWᴇ ᴄᴏᴜʟᴅɴ'ᴛ ʀᴇᴛʀɪᴇᴠᴇ ʏᴏᴜʀ Oʀᴅᴇʀ Dᴀᴛᴀ ᴀᴛ ᴛʜɪꜱ ᴛɪᴍᴇ\n"
            "Pʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ",
            parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == "order_history")
def show_recent_orders(call):
    """Show pending orders from the last 24h only"""
    user_id = str(call.from_user.id)

    try:
        recent_orders = list(orders_collection.find(
            {
                "user_id": user_id,
                "status": {"$in": ["pending", "processing"]},
                "hidden": {"$ne": True}
            },
            {"service": 1, "quantity": 1, "status": 1, "timestamp": 1, "_id": 0}
        ).sort("timestamp", -1))

        msg = "🕒 <b>Pᴇɴᴅɪɴɢ Oʀᴅᴇʀꜱ (Lᴀꜱᴛ 24ʜ)</b>\n"

        if recent_orders:
            for i, order in enumerate(recent_orders, 1):
                time_ago = format_timespan(time.time() - order.get('timestamp', time.time()))
                msg += f"\n{i}. ⏳ {order.get('service', 'N/A')[:15]}... x{order.get('quantity', '?')} (<i>{time_ago} ᴀɢᴏ</i>)"
        else:
            msg += "\n└ 🌟 Nᴏ ᴘᴇɴᴅɪɴɢ ᴏʀᴅᴇʀꜱ ꜰᴏᴜɴᴅ"

        msg += "\n\n📌 <i>Oɴʟʏ ᴘᴇɴᴅɪɴɢ ᴏʀᴅᴇʀꜱ ᴀʀᴇ ꜱʜᴏᴡɴ ʜᴇʀᴇ</i>"

        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🔙 Back to Overview", callback_data="show_order_stats")
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=msg,
            parse_mode='HTML',
            reply_markup=markup
        )
    except Exception as e:
        print(f"Recent orders error: {e}")
        bot.answer_callback_query(call.id, "❌ Failed to load pending orders")

@bot.callback_query_handler(func=lambda call: call.data == "show_order_stats")
@check_ban
def callback_show_order_stats(call):
    """Back to stats page from order list"""
    try:
        from types import SimpleNamespace
        message = SimpleNamespace()
        message.chat = call.message.chat
        message.message_id = call.message.message_id
        message.from_user = call.from_user
        message.is_callback = True
        show_order_stats(message)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Callback show_order_stats error: {e}")
        bot.answer_callback_query(call.id, "⚠️ Failed to go back", show_alert=True)
      
def delete_after_delay(chat_id, message_id, delay):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f"Could not delete message: {e}")

def format_timespan(seconds):
    intervals = (
        ('days', 86400),
        ('hours', 3600),
        ('minutes', 60),
        ('seconds', 1)
    )
    result = []
    for name, count in intervals:
        value = int(seconds // count)
        if value:
            seconds -= value * count
            result.append(f"{value} {name}")
    return ', '.join(result[:2])


#======================= Send Orders for Telegram =======================#
@bot.message_handler(func=lambda message: message.text == "📱 Order Telegram")
def order_telegram_menu(message):
    """Show Telegram service options"""
    bot.reply_to(message, "📱 Telegram Services:", reply_markup=telegram_services_markup)

@bot.message_handler(func=lambda message: message.text in ["👀 Post Views", "❤️ Post Reactions", "👥 Channel Members"])
def handle_telegram_order(message):
    """Handle Telegram service selection"""
    user_id = str(message.from_user.id)
    
    # Store service details in a dictionary
    services = {
        "👀 Post Views": {
            "name": "Post Views",
            "quality": "Super Fast",
            "min": 1000,
            "max": 100000,
            "price": 100,
            "unit": "1k views",
            "service_id": "10576",  # Your SMM panel service ID for views
            "link_hint": "Telegram post link"
        },
        "❤️ Post Reactions": {
            "name": "Positive Reactions",
            "quality": "No Refil",
            "min": 100,
            "max": 1000,
            "price": 989,
            "unit": "1k reactions",
            "service_id": "12209",  # Replace with actual service ID
            "link_hint": "Telegram post link"
            
        },
        "👥 Channel Members": {
            "name": "Members [Mixed]",
            "quality": "Refill 90 Days",
            "min": 500,
            "max": 10000,
            "price": 9560,
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
    
    msg = f"""⭐️ ｢{service['name']} Dᴇᴛᴀɪʟꜱ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📌 Oʀᴅᴇʀ ID: {service['service_id']}
━━━━━━━━━━━━━━━━━━━━━━━
📉 Mɪɴɪᴍᴜᴍ: {service['min']}
📈 Mᴀxɪᴍᴜᴍ: {service['max']}
━━━━━━━━━━━━━━━━━━━━━━━
💰 Pʀɪᴄᴇ: {service['price']} ᴄᴏɪɴꜱ / {service['unit']}
━━━━━━━━━━━━━━━━━━━━━━━
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
━━━━━━━━━━━━━━━━━━━━━━━
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 Eɴᴛᴇʀ Qᴜᴀɴᴛɪᴛʏ: 
━━━━━━━━━━━━━━━━━━━━━━━"""
    
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
            
            # Generate notification image
            try:
                user_img = get_profile_photo(message.from_user.id)
                bot_img = get_profile_photo(bot.get_me().id)
                image_path = generate_notification_image(
                    user_img,
                    bot_img,
                    message.from_user.first_name,
                    bot.get_me().first_name,
                    service['name']
                )
                
                if image_path:
                    # Create buttons
                    markup = InlineKeyboardMarkup()
                    markup.row(
                        InlineKeyboardButton("🔗 View Order Link", url=link),
                        InlineKeyboardButton("🤖 Visit Bot", url=f"https://t.me/{bot.get_me().username}")
                    )
                    
                    # Stylish notification to payment channel
                    caption = f"""⭐️ ｢ɴᴇᴡ ᴏʀᴅᴇʀ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
➠ 🕵🏻‍♂️ Uꜱᴇʀɴᴀᴍᴇ: @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Uꜱᴇʀ Iᴅ: {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 📦 Sᴇʀᴠɪᴄᴇ: {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 💰 Cᴏꜱᴛ: {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Oʀᴅᴇʀ Iᴅ: <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
➠ ⚡ Sᴛᴀᴛᴜꜱ: <code>{result.get('status', 'pending').capitalize()}</code>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━"""
                    
                    with open(image_path, 'rb') as photo:
                        bot.send_photo(
                            payment_channel,
                            photo,
                            caption=caption,
                            parse_mode='HTML',
                            reply_markup=markup
                        )
                    
                    # Clean up
                    os.remove(image_path)
                    
            except Exception as e:
                print(f"Error generating notification image: {e}")
                # Fallback to text message if image generation fails
                bot.send_message(
                    payment_channel,
f"""⭐️ ｢Nᴇᴡ {service['name'].upper()} Oʀᴅᴇʀ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name}
━━━━━━━━━━━━━━━━━━━━━━━
🕵🏻‍♂️ <b>Uꜱᴇʀɴᴀᴍᴇ:</b> @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>Uꜱᴇʀ Iᴅ:</b> {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>{result.get('status', 'pending').capitalize()}</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━""",
                    disable_web_page_preview=True,
                    parse_mode='HTML'
                )

            # Create "Check Order Status" button for user
            markup = InlineKeyboardMarkup()
            check_status_button = InlineKeyboardButton(
                text="📊 Check Order Status",
                url=f"https://t.me/{payment_channel.lstrip('@')}"
            )
            markup.add(check_status_button)
            
            # Stylish confirmation message
            bot.reply_to(
                message,
f"""✅ <b>{service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
━━━━━━━━━━━━━━━━━━━━━━━
😊 <b>Tʜᴀɴᴋꜱ ꜰᴏʀ ᴏʀᴅᴇʀɪɴɢ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
⚠️ <b>𝙒𝙖𝙧𝙣𝙞𝙣𝙜:</b> Dᴏ ɴᴏᴛ ꜱᴇɴᴅ ᴛʜᴇ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏɴᴇ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ʏᴏᴜ ᴍɪɡʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!""",
                reply_markup=markup,
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
@bot.message_handler(func=lambda message: message.text == "🎵 Order TikTok")
def order_tiktok_menu(message):
    """Show TikTok service options"""
    bot.reply_to(message, "🎵 TikTok Services:", reply_markup=tiktok_services_markup)


@bot.message_handler(func=lambda message: message.text in ["👀 Tiktok Views", "❤️ Tiktok Likes", "👥 Tiktok Followers"])
def handle_tiktok_order(message):
    """Handle TikTok service selection"""
    user_id = str(message.from_user.id)
    
    # TikTok service configurations
    services = {
        "👀 Tiktok Views": {
            "name": "TikTok Views",
            "quality": "Fast Speed",
            "link_hint": "Tiktok Post Link",
            "min": 1000,
            "max": 100000,
            "price": 14,
            "unit": "1k views",
            "service_id": "18454"
        },
        "❤️ Tiktok Likes": {
            "name": "TikTok Likes",
            "quality": "Real & Active",
            "link_hint": "Tiktok Post Link",
            "min": 100,
            "max": 10000,
            "price": 1164,
            "unit": "1k likes",
            "service_id": "17335"
        },
        "👥 Tiktok Followers": {
            "name": "TikTok Followers",
            "quality": "High Quality",
            "link_hint": "Tiktok Profile Link",
            "min": 100,
            "max": 10000,
            "price": 16943,
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
    
    msg = f"""⭐️ ｢{service['name']} Dᴇᴛᴀɪʟꜱ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📌 Oʀᴅᴇʀ ID: {service['service_id']}
━━━━━━━━━━━━━━━━━━━━━━━
📉 Mɪɴɪᴍᴜᴍ: {service['min']}
📈 Mᴀxɪᴍᴜᴍ: {service['max']}
━━━━━━━━━━━━━━━━━━━━━━━
💰 Pʀɪᴄᴇ: {service['price']} ᴄᴏɪɴꜱ / {service['unit']}
━━━━━━━━━━━━━━━━━━━━━━━
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
━━━━━━━━━━━━━━━━━━━━━━━
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 Eɴᴛᴇʀ Qᴜᴀɴᴛɪᴛʏ: 
━━━━━━━━━━━━━━━━━━━━━━━"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_tiktok_quantity, 
        service
    )

def process_tiktok_quantity(message, service):
    """Process the quantity input for TikTok orders"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ ᴛᴏ TɪᴋTᴏᴋ ꜱᴇʀᴠɪᴄᴇꜱ...", reply_markup=tiktok_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Mɪɴɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['min']}", reply_markup=tiktok_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Mᴀxɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['max']}", reply_markup=tiktok_services_markup)
            return
            
        # Calculate cost (price is per 1k, so divide quantity by 1000)
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Iɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ. Yᴏᴜ ɴᴇᴇᴅ {cost} ᴄᴏɪɴꜱ.", reply_markup=tiktok_services_markup)
            return
            
        # Ask for TikTok link
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, "🔗 Pʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ TɪᴋTᴏᴋ ᴠɪᴅᴇᴏ ʟɪɴᴋ:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_tiktok_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Pʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ", reply_markup=tiktok_services_markup)

def process_tiktok_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    # Validate TikTok link format
    if not re.match(r'^https?://(www\.)?(tiktok\.com|vm\.tiktok\.com)/', link):
        bot.reply_to(message, "❌ Iɴᴠᴀʟɪᴅ TɪᴋTᴏᴋ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ", reply_markup=tiktok_services_markup)
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
        print(f"SMM Panel Response: {result}")  # Debug print
        
        if result and result.get('order'):
            # Deduct balance
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            # Prepare complete order data
            order_data = {
                'service': service['name'],
                'service_type': 'tiktok',
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
            
            # Generate notification image
            try:
                user_img = get_profile_photo(message.from_user.id)
                bot_img = get_profile_photo(bot.get_me().id)
                image_path = generate_notification_image(
                    user_img,
                    bot_img,
                    message.from_user.first_name,
                    bot.get_me().first_name,
                    service['name']
                )
                
                if image_path:
                    # Create buttons
                    markup = InlineKeyboardMarkup()
                    markup.row(
                        InlineKeyboardButton("🔗 View Order Link", url=link),
                        InlineKeyboardButton("🤖 Visit Bot", url=f"https://t.me/{bot.get_me().username}")
                    )
                    
                    # Stylish notification to payment channel
                    caption = f"""⭐️ ｢ɴᴇᴡ ᴏʀᴅᴇʀ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
➠ 🕵🏻‍♂️ Uꜱᴇʀɴᴀᴍᴇ: @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Uꜱᴇʀ Iᴅ: {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 📦 Sᴇʀᴠɪᴄᴇ: {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 💰 Cᴏꜱᴛ: {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Oʀᴅᴇʀ Iᴅ: <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
➠ ⚡ Sᴛᴀᴛᴜꜱ: <code>{result.get('status', 'pending').capitalize()}</code>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━"""
                    
                    with open(image_path, 'rb') as photo:
                        bot.send_photo(
                            payment_channel,
                            photo,
                            caption=caption,
                            parse_mode='HTML',
                            reply_markup=markup
                        )
                    
                    # Clean up
                    os.remove(image_path)
                    
            except Exception as e:
                print(f"Error generating notification image: {e}")
                # Fallback to text message if image generation fails
                bot.send_message(
                    payment_channel,
f"""⭐️ ｢Nᴇᴡ {service['name'].upper()} Oʀᴅᴇʀ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name}
━━━━━━━━━━━━━━━━━━━━━━━
🕵🏻‍♂️ <b>Uꜱᴇʀɴᴀᴍᴇ:</b> @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>Uꜱᴇʀ Iᴅ:</b> {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>{result.get('status', 'pending').capitalize()}</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━""",
                    disable_web_page_preview=True,
                    parse_mode='HTML'
                )

            # Create "Check Order Status" button for user
            markup = InlineKeyboardMarkup()
            check_status_button = InlineKeyboardButton(
                text="📊 Check Order Status",
                url=f"https://t.me/{payment_channel.lstrip('@')}"
            )
            markup.add(check_status_button)
            
            # Stylish confirmation message
            bot.reply_to(
                message,
f"""✅ <b>{service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
━━━━━━━━━━━━━━━━━━━━━━━
😊 <b>Tʜᴀɴᴋꜱ ꜰᴏʀ ᴏʀᴅᴇʀɪɴɢ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
⚠️ <b>𝙒𝙖𝙧𝙣𝙞𝙣𝙜:</b> Dᴏ ɴᴏᴛ ꜱᴇɴᴅ ᴛʜᴇ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏɴᴇ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ʏᴏᴜ ᴍɪɡʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!""",
                reply_markup=markup,
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
    
#======================== End of TikTok Orders ========================#

#======================== Send Orders for Instagram =====================#
@bot.message_handler(func=lambda message: message.text == "📸 Order Instagram")
def order_instagram_menu(message):
    """Show Instagram service options"""
    bot.reply_to(message, "📸 Instagram Services:", reply_markup=instagram_services_markup)

@bot.message_handler(func=lambda message: message.text in ["🎥 Video Views", "❤️ Insta Likes", "👥 Insta Followers"])
def handle_instagram_order(message):
    """Handle Instagram service selection"""
    user_id = str(message.from_user.id)
    
    services = {
        "🎥 Video Views": {
            "name": "Instagram Video Views",
            "quality": "Real Accounts",
            "min": 1000,
            "max": 100000,
            "price": 72,
            "unit": "1k views",
            "service_id": "17316",
            "link_hint": "Instagram video link"
        },
        "❤️ Insta Likes": {
            "name": "Instagram Likes",
            "quality": "Power Quality",
            "min": 100,
            "max": 10000,
            "price": 225,
            "unit": "1k likes",
            "service_id": "17375",
            "link_hint": "Instagram post link"
        },
        "👥 Insta Followers": {
            "name": "Instagram Followers",
            "quality": "Old Accounts With Posts",
            "min": 100,
            "max": 10000,
            "price": 12353,
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
    
    msg = f"""⭐️ ｢{service['name']} Dᴇᴛᴀɪʟꜱ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📌 Oʀᴅᴇʀ ID: {service['service_id']}
━━━━━━━━━━━━━━━━━━━━━━━
📉 Mɪɴɪᴍᴜᴍ: {service['min']}
📈 Mᴀxɪᴍᴜᴍ: {service['max']}
━━━━━━━━━━━━━━━━━━━━━━━
💰 Pʀɪᴄᴇ: {service['price']} ᴄᴏɪɴꜱ / {service['unit']}
━━━━━━━━━━━━━━━━━━━━━━━
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
━━━━━━━━━━━━━━━━━━━━━━━
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 Eɴᴛᴇʀ Qᴜᴀɴᴛɪᴛʏ: 
━━━━━━━━━━━━━━━━━━━━━━━"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_instagram_quantity, 
        service
    )

def process_instagram_quantity(message, service):
    """Process Instagram order quantity"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ ᴛᴏ Iɴꜱᴛᴀɢʀᴀᴍ ꜱᴇʀᴠɪᴄᴇꜱ...", reply_markup=instagram_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Mɪɴɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['min']}", reply_markup=instagram_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Mᴀxɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['max']}", reply_markup=instagram_services_markup)
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Iɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ. Yᴏᴜ ɴᴇᴇᴅ {cost} ᴄᴏɪɴꜱ.", reply_markup=instagram_services_markup)
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, f"🔗 Pʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ {service['link_hint']}:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_instagram_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Pʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ", reply_markup=instagram_services_markup)

def process_instagram_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    # Validate Instagram link format
    if not re.match(r'^https?://(www\.)?instagram\.com/[\w./-]+', link):
        bot.reply_to(message, "❌ Iɴᴠᴀʟɪᴅ Iɴꜱᴛᴀɢʀᴀᴍ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ", reply_markup=instagram_services_markup)
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
        print(f"SMM Panel Response: {result}")  # Debug print
        
        if result and result.get('order'):
            # Deduct balance
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            # Prepare complete order data
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
            
            # Add to order history
            add_order(str(message.from_user.id), order_data)
            
            # Generate notification image
            try:
                user_img = get_profile_photo(message.from_user.id)
                bot_img = get_profile_photo(bot.get_me().id)
                image_path = generate_notification_image(
                    user_img,
                    bot_img,
                    message.from_user.first_name,
                    bot.get_me().first_name,
                    service['name']
                )
                
                if image_path:
                    # Create buttons
                    markup = InlineKeyboardMarkup()
                    markup.row(
                        InlineKeyboardButton("🔗 View Order Link", url=link),
                        InlineKeyboardButton("🤖 Visit Bot", url=f"https://t.me/{bot.get_me().username}")
                    )
                    
                    # Stylish notification to payment channel
                    caption = f"""⭐️ ｢ɴᴇᴡ ᴏʀᴅᴇʀ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
➠ 🕵🏻‍♂️ Uꜱᴇʀɴᴀᴍᴇ: @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Uꜱᴇʀ Iᴅ: {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 📦 Sᴇʀᴠɪᴄᴇ: {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 💰 Cᴏꜱᴛ: {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Oʀᴅᴇʀ Iᴅ: <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
➠ ⚡ Sᴛᴀᴛᴜꜱ: <code>{result.get('status', 'pending').capitalize()}</code>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━"""
                    
                    with open(image_path, 'rb') as photo:
                        bot.send_photo(
                            payment_channel,
                            photo,
                            caption=caption,
                            parse_mode='HTML',
                            reply_markup=markup
                        )
                    
                    # Clean up
                    os.remove(image_path)
                    
            except Exception as e:
                print(f"Error generating notification image: {e}")
                # Fallback to text message if image generation fails
                bot.send_message(
                    payment_channel,
f"""⭐️ ｢Nᴇᴡ {service['name'].upper()} Oʀᴅᴇʀ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name}
━━━━━━━━━━━━━━━━━━━━━━━
🕵🏻‍♂️ <b>Uꜱᴇʀɴᴀᴍᴇ:</b> @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>Uꜱᴇʀ Iᴅ:</b> {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>{result.get('status', 'pending').capitalize()}</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━""",
                    disable_web_page_preview=True,
                    parse_mode='HTML'
                )

            # Create "Check Order Status" button for user
            markup = InlineKeyboardMarkup()
            check_status_button = InlineKeyboardButton(
                text="📊 Check Order Status",
                url=f"https://t.me/{payment_channel.lstrip('@')}"
            )
            markup.add(check_status_button)
            
            # Stylish confirmation message
            bot.reply_to(
                message,
f"""✅ <b>{service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
━━━━━━━━━━━━━━━━━━━━━━━
😊 <b>Tʜᴀɴᴋꜱ ꜰᴏʀ ᴏʀᴅᴇʀɪɴɢ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
⚠️ <b>𝙒𝙖𝙧𝙣𝙞𝙣𝙜:</b> Dᴏ ɴᴏᴛ ꜱᴇɴᴅ ᴛʜᴇ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏɴᴇ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ʏᴏᴜ ᴍɪɡʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!""",
                reply_markup=markup,
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
            "name": "YouTube Views",
            "quality": "100% Real",
            "min": 40000,
            "max": 1000000,
            "price": 7713,
            "unit": "1k views",
            "service_id": "11272",
            "link_hint": "YouTube video link"
        },
        "👍 YT Likes": {
            "name": "YouTube Likes [Real]",
            "quality": "No Refill",
            "min": 100,
            "max": 10000,
            "price": 1607,
            "unit": "1k likes",
            "service_id": "18144",
            "link_hint": "YouTube video link"
        },
        "👥 YT Subscribers": {
            "name": "YouTube Subscribers [Cheapest]",
            "quality": "Refill 30 days",
            "min": 100,
            "max": 10000,
            "price": 11078,
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
    
    msg = f"""⭐️ ｢{service['name']} Dᴇᴛᴀɪʟꜱ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📌 Oʀᴅᴇʀ ID: {service['service_id']}
━━━━━━━━━━━━━━━━━━━━━━━
📉 Mɪɴɪᴍᴜᴍ: {service['min']}
📈 Mᴀxɪᴍᴜᴍ: {service['max']}
━━━━━━━━━━━━━━━━━━━━━━━
💰 Pʀɪᴄᴇ: {service['price']} ᴄᴏɪɴꜱ / {service['unit']}
━━━━━━━━━━━━━━━━━━━━━━━
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
━━━━━━━━━━━━━━━━━━━━━━━
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 Eɴᴛᴇʀ Qᴜᴀɴᴛɪᴛʏ: 
━━━━━━━━━━━━━━━━━━━━━━━"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_youtube_quantity, 
        service
    )

def process_youtube_quantity(message, service):
    """Process YouTube order quantity"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ ᴛᴏ YᴏᴜTᴜʙᴇ ꜱᴇʀᴠɪᴄᴇꜱ...", reply_markup=youtube_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Mɪɴɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['min']}", reply_markup=youtube_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Mᴀxɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['max']}", reply_markup=youtube_services_markup)
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Iɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ. Yᴏᴜ ɴᴇᴇᴅ {cost} ᴄᴏɪɴꜱ.", reply_markup=youtube_services_markup)
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, f"🔗 Pʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ {service['link_hint']}:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_youtube_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Pʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ", reply_markup=youtube_services_markup)

def process_youtube_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    if not re.match(r'^https?://(www\.)?(youtube\.com|youtu\.be)/', link):
        bot.reply_to(message, "❌ Iɴᴠᴀʟɪᴅ YᴏᴜTᴜʙᴇ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ", reply_markup=youtube_services_markup)
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
        print(f"SMM Panel Response: {result}")  # Debug print
        
        if result and result.get('order'):
            # Deduct balance
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            # Prepare complete order data
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
            
            # Add to order history
            add_order(str(message.from_user.id), order_data)
            
            # Generate notification image
            try:
                user_img = get_profile_photo(message.from_user.id)
                bot_img = get_profile_photo(bot.get_me().id)
                image_path = generate_notification_image(
                    user_img,
                    bot_img,
                    message.from_user.first_name,
                    bot.get_me().first_name,
                    service['name']
                )
                
                if image_path:
                    # Create buttons
                    markup = InlineKeyboardMarkup()
                    markup.row(
                        InlineKeyboardButton("🔗 View Order Link", url=link),
                        InlineKeyboardButton("🤖 Visit Bot", url=f"https://t.me/{bot.get_me().username}")
                    )
                    
                    # Stylish notification to payment channel
                    caption = f"""⭐️ ｢ɴᴇᴡ ᴏʀᴅᴇʀ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
➠ 🕵🏻‍♂️ Uꜱᴇʀɴᴀᴍᴇ: @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Uꜱᴇʀ Iᴅ: {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 📦 Sᴇʀᴠɪᴄᴇ: {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 💰 Cᴏꜱᴛ: {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Oʀᴅᴇʀ Iᴅ: <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
➠ ⚡ Sᴛᴀᴛᴜꜱ: <code>{result.get('status', 'pending').capitalize()}</code>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━"""
                    
                    with open(image_path, 'rb') as photo:
                        bot.send_photo(
                            payment_channel,
                            photo,
                            caption=caption,
                            parse_mode='HTML',
                            reply_markup=markup
                        )
                    
                    # Clean up
                    os.remove(image_path)
                    
            except Exception as e:
                print(f"Error generating notification image: {e}")
                # Fallback to text message if image generation fails
                bot.send_message(
                    payment_channel,
f"""⭐️ ｢Nᴇᴡ {service['name'].upper()} Oʀᴅᴇʀ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name}
━━━━━━━━━━━━━━━━━━━━━━━
🕵🏻‍♂️ <b>Uꜱᴇʀɴᴀᴍᴇ:</b> @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>Uꜱᴇʀ Iᴅ:</b> {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>{result.get('status', 'pending').capitalize()}</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━""",
                    disable_web_page_preview=True,
                    parse_mode='HTML'
                )

            # Create "Check Order Status" button for user
            markup = InlineKeyboardMarkup()
            check_status_button = InlineKeyboardButton(
                text="📊 Check Order Status",
                url=f"https://t.me/{payment_channel.lstrip('@')}"
            )
            markup.add(check_status_button)
            
            # Stylish confirmation message
            bot.reply_to(
                message,
f"""✅ <b>{service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
━━━━━━━━━━━━━━━━━━━━━━━
😊 <b>Tʜᴀɴᴋꜱ ꜰᴏʀ ᴏʀᴅᴇʀɪɴɢ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
⚠️ <b>𝙒𝙖𝙧𝙣𝙞𝙣𝙜:</b> Dᴏ ɴᴏᴛ ꜱᴇɴᴅ ᴛʜᴇ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏɴᴇ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ʏᴏᴜ ᴍɪɡʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!""",
                reply_markup=markup,
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
            "name": "FB Profile Followers",
            "quality": "High Quality",
            "min": 100,
            "max": 100000,
            "price": 7704,
            "unit": "1k followers",
            "service_id": "18977",
            "link_hint": "Facebook profile link"
        },
        "📄 Page Followers": {
            "name": "FB Page Followers",
            "quality": "Refill 30 Days",
            "min": 100,
            "max": 10000,
            "price": 5597,
            "unit": "1k followers",
            "service_id": "18984",
            "link_hint": "Facebook page link"
        },
        "🎥 Video/Reel Views": {
            "name": "FB Video/Reel Views",
            "quality": "Non Drop",
            "min": 1000,
            "max": 10000,
            "price": 579,
            "unit": "1k views",
            "service_id": "17859",
            "link_hint": "Facebook video/reel link"
        },
        "❤️ Post Likes": {
            "name": "FB Post Likes",
            "quality": "No Refill",
            "min": 100,
            "max": 10000,
            "price": 4567,
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
    
    msg = f"""⭐️ ｢{service['name']} Dᴇᴛᴀɪʟꜱ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📌 Oʀᴅᴇʀ ID: {service['service_id']}
━━━━━━━━━━━━━━━━━━━━━━━
📉 Mɪɴɪᴍᴜᴍ: {service['min']}
📈 Mᴀxɪᴍᴜᴍ: {service['max']}
━━━━━━━━━━━━━━━━━━━━━━━
💰 Pʀɪᴄᴇ: {service['price']} ᴄᴏɪɴꜱ / {service['unit']}
━━━━━━━━━━━━━━━━━━━━━━━
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
━━━━━━━━━━━━━━━━━━━━━━━
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 Eɴᴛᴇʀ Qᴜᴀɴᴛɪᴛʏ: 
━━━━━━━━━━━━━━━━━━━━━━━"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_facebook_quantity, 
        service
    )

def process_facebook_quantity(message, service):
    """Process Facebook order quantity"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ ᴛᴏ Fᴀᴄᴇʙᴏᴏᴋ ꜱᴇʀᴠɪᴄᴇꜱ...", reply_markup=facebook_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Mɪɴɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['min']}", reply_markup=facebook_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Mᴀxɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['max']}", reply_markup=facebook_services_markup)
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Iɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ. Yᴏᴜ ɴᴇᴇᴅ {cost} ᴄᴏɪɴꜱ.", reply_markup=facebook_services_markup)
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, f"🔗 Pʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ {service['link_hint']}:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_facebook_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Pʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ", reply_markup=facebook_services_markup)

def process_facebook_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    if not re.match(r'^https?://(www\.|m\.)?(facebook\.com|fb\.watch)/', link):
        bot.reply_to(message, "❌ Iɴᴠᴀʟɪᴅ Fᴀᴄᴇʙᴏᴏᴋ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ", reply_markup=facebook_services_markup)
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
        print(f"SMM Panel Response: {result}")  # Debug print
        
        if result and result.get('order'):
            # Deduct balance
            if not cutBalance(str(message.from_user.id), cost):
                raise Exception("Failed to deduct balance")
            
            # Prepare complete order data
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
            
            # Add to order history
            add_order(str(message.from_user.id), order_data)
            
            # Generate notification image
            try:
                user_img = get_profile_photo(message.from_user.id)
                bot_img = get_profile_photo(bot.get_me().id)
                image_path = generate_notification_image(
                    user_img,
                    bot_img,
                    message.from_user.first_name,
                    bot.get_me().first_name,
                    service['name']
                )
                
                if image_path:
                    # Create buttons
                    markup = InlineKeyboardMarkup()
                    markup.row(
                        InlineKeyboardButton("🔗 View Order Link", url=link),
                        InlineKeyboardButton("🤖 Visit Bot", url=f"https://t.me/{bot.get_me().username}")
                    )
                    
                    # Stylish notification to payment channel
                    caption = f"""⭐️ ｢ɴᴇᴡ ᴏʀᴅᴇʀ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
➠ 🕵🏻‍♂️ Uꜱᴇʀɴᴀᴍᴇ: @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Uꜱᴇʀ Iᴅ: {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 📦 Sᴇʀᴠɪᴄᴇ: {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 💰 Cᴏꜱᴛ: {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Oʀᴅᴇʀ Iᴅ: <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
➠ ⚡ Sᴛᴀᴛᴜꜱ: <code>{result.get('status', 'pending').capitalize()}</code>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━"""
                    
                    with open(image_path, 'rb') as photo:
                        bot.send_photo(
                            payment_channel,
                            photo,
                            caption=caption,
                            parse_mode='HTML',
                            reply_markup=markup
                        )
                    
                    # Clean up
                    os.remove(image_path)
                    
            except Exception as e:
                print(f"Error generating notification image: {e}")
                # Fallback to text message if image generation fails
                bot.send_message(
                    payment_channel,
f"""⭐️ ｢Nᴇᴡ {service['name'].upper()} Oʀᴅᴇʀ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name}
━━━━━━━━━━━━━━━━━━━━━━━
🕵🏻‍♂️ <b>Uꜱᴇʀɴᴀᴍᴇ:</b> @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>Uꜱᴇʀ Iᴅ:</b> {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>{result.get('status', 'pending').capitalize()}</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━""",
                    disable_web_page_preview=True,
                    parse_mode='HTML'
                )

            # Create "Check Order Status" button for user
            markup = InlineKeyboardMarkup()
            check_status_button = InlineKeyboardButton(
                text="📊 Check Order Status",
                url=f"https://t.me/{payment_channel.lstrip('@')}"
            )
            markup.add(check_status_button)
            
            # Stylish confirmation message
            bot.reply_to(
                message,
f"""✅ <b>{service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
━━━━━━━━━━━━━━━━━━━━━━━
😊 <b>Tʜᴀɴᴋꜱ ꜰᴏʀ ᴏʀᴅᴇʀɪɴɢ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
⚠️ <b>𝙒𝙖𝙧𝙣𝙞𝙣𝙜:</b> Dᴏ ɴᴏᴛ ꜱᴇɴᴅ ᴛʜᴇ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏɴᴇ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ʏᴏᴜ ᴍɪɡʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!""",
                reply_markup=markup,
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
#======================== End of Facebook Orders =====================# 

#======================== Send Orders for Whastapp =====================#
@bot.message_handler(func=lambda message: message.text == "💬 Order WhatsApp")
def order_whatsapp_menu(message):
    """Show WhatsApp service options"""
    bot.reply_to(message, "💬 WhatsApp Services:", reply_markup=whatsapp_services_markup)

@bot.message_handler(func=lambda message: message.text in ["👥 Channel Subscribers", "😀 Post EmojiReaction"])
def handle_whatsapp_order(message):
    """Handle WhatsApp service selection"""
    user_id = str(message.from_user.id)
    
    services = {
        "👥 Channel Subscribers": {
            "name": "WhatsApp Channel Members",
            "quality": "EU Users",
            "min": 100,
            "max": 40000,
            "price": 20856,
            "unit": "1k members",
            "service_id": "18848",
            "link_hint": "WhatsApp channel invite link"
        },
        "😀 Post EmojiReaction": {
            "name": "WhatsApp Channel EmojiReaction",
            "quality": "Mixed",
            "min": 100,
            "max": 10000,
            "price": 10627,
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
    
    msg = f"""⭐️ ｢{service['name']} Dᴇᴛᴀɪʟꜱ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📌 Oʀᴅᴇʀ ID: {service['service_id']}
━━━━━━━━━━━━━━━━━━━━━━━
📉 Mɪɴɪᴍᴜᴍ: {service['min']}
📈 Mᴀxɪᴍᴜᴍ: {service['max']}
━━━━━━━━━━━━━━━━━━━━━━━
💰 Pʀɪᴄᴇ: {service['price']} ᴄᴏɪɴꜱ / {service['unit']}
━━━━━━━━━━━━━━━━━━━━━━━
🔗 Lɪɴᴋ Hɪɴᴛ: {service['link_hint']}
━━━━━━━━━━━━━━━━━━━━━━━
💎 Qᴜᴀʟɪᴛʏ: {service['quality']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 Eɴᴛᴇʀ Qᴜᴀɴᴛɪᴛʏ: 
━━━━━━━━━━━━━━━━━━━━━━━"""
    
    bot.reply_to(message, msg, reply_markup=cancel_back_markup)
    bot.register_next_step_handler(
        message, 
        process_whatsapp_quantity, 
        service
    )

def process_whatsapp_quantity(message, service):
    """Process WhatsApp order quantity"""
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    elif message.text == "↩️ Go Back":
        bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ ᴛᴏ WʜᴀᴛꜱAᴘᴘ ꜱᴇʀᴠɪᴄᴇꜱ...", reply_markup=whatsapp_services_markup)
        return
    
    try:
        quantity = int(message.text)
        if quantity < service['min']:
            bot.reply_to(message, f"❌ Mɪɴɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['min']}", reply_markup=whatsapp_services_markup)
            return
        if quantity > service['max']:
            bot.reply_to(message, f"❌ Mᴀxɪᴍᴜᴍ ᴏʀᴅᴇʀ ɪꜱ {service['max']}", reply_markup=whatsapp_services_markup)
            return
            
        cost = (quantity * service['price']) // 1000
        user_data = getData(str(message.from_user.id))
        
        if float(user_data['balance']) < cost:
            bot.reply_to(message, f"❌ Iɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ. Yᴏᴜ ɴᴇᴇᴅ {cost} ᴄᴏɪɴꜱ.", reply_markup=whatsapp_services_markup)
            return
            
        cancel_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_markup.add(KeyboardButton("✘ Cancel"))
        
        bot.reply_to(message, f"🔗 Pʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ {service['link_hint']}:", reply_markup=cancel_markup)
        bot.register_next_step_handler(
            message, 
            process_whatsapp_link, 
            service,
            quantity,
            cost
        )
        
    except ValueError:
        bot.reply_to(message, "❌ Pʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴀ ᴠᴀʟɪᴅ ɴᴜᴍʙᴇʀ", reply_markup=whatsapp_services_markup)

def process_whatsapp_link(message, service, quantity, cost):
    if message.text == "✘ Cancel":
        bot.reply_to(message, "❌ Oʀᴅᴇʀ ᴄᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)
        return
    
    link = message.text.strip()
    
    if not re.match(r'^https?://(chat\.whatsapp\.com|wa\.me)/', link):
        bot.reply_to(message, "❌ Iɴᴠᴀʟɪᴅ WʜᴀᴛꜱAᴘᴘ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ", reply_markup=whatsapp_services_markup)
    
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
            
            # Add to order history
            add_order(str(message.from_user.id), order_data)
            
            # Generate notification image
            try:
                user_img = get_profile_photo(message.from_user.id)
                bot_img = get_profile_photo(bot.get_me().id)
                image_path = generate_notification_image(
                    user_img,
                    bot_img,
                    message.from_user.first_name,
                    bot.get_me().first_name,
                    service['name']
                )
                
                if image_path:
                    # Create buttons
                    markup = InlineKeyboardMarkup()
                    markup.row(
                        InlineKeyboardButton("🔗 View Order Link", url=link),
                        InlineKeyboardButton("🤖 Visit Bot", url=f"https://t.me/{bot.get_me().username}")
                    )
                    
                    # Stylish notification to payment channel
                    caption = f"""⭐️ ｢ɴᴇᴡ ᴏʀᴅᴇʀ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
➠ 🕵🏻‍♂️ Uꜱᴇʀɴᴀᴍᴇ: @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Uꜱᴇʀ Iᴅ: {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 📦 Sᴇʀᴠɪᴄᴇ: {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🔢 Qᴜᴀɴᴛɪᴛʏ: {quantity}
━━━━━━━━━━━━━━━━━━━━━━━
➠ 💰 Cᴏꜱᴛ: {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
➠ 🆔 Oʀᴅᴇʀ Iᴅ: <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
➠ ⚡ Sᴛᴀᴛᴜꜱ: <code>{result.get('status', 'pending').capitalize()}</code>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━"""
                    
                    with open(image_path, 'rb') as photo:
                        bot.send_photo(
                            payment_channel,
                            photo,
                            caption=caption,
                            parse_mode='HTML',
                            reply_markup=markup
                        )
                    
                    # Clean up
                    os.remove(image_path)
                    
            except Exception as e:
                print(f"Error generating notification image: {e}")
                # Fallback to text message if image generation fails
                bot.send_message(
                    payment_channel,
f"""⭐️ ｢Nᴇᴡ {service['name'].upper()} Oʀᴅᴇʀ 」⭐️
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
👤 <b>Uꜱᴇʀ:</b> {message.from_user.first_name}
━━━━━━━━━━━━━━━━━━━━━━━
🕵🏻‍♂️ <b>Uꜱᴇʀɴᴀᴍᴇ:</b> @{message.from_user.username or 'Not set'}
━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>Uꜱᴇʀ Iᴅ:</b> {message.from_user.id}
━━━━━━━━━━━━━━━━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> <code>{result['order']}</code>
━━━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Sᴛᴀᴛᴜꜱ:</b> <code>{result.get('status', 'pending').capitalize()}</code>
🤖 <b>Bᴏᴛ:</b> @{bot.get_me().username}
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━""",
                    disable_web_page_preview=True,
                    parse_mode='HTML'
                )

            # Create "Check Order Status" button for user
            markup = InlineKeyboardMarkup()
            check_status_button = InlineKeyboardButton(
                text="📊 Check Order Status",
                url=f"https://t.me/{payment_channel.lstrip('@')}"
            )
            markup.add(check_status_button)
            
            # Stylish confirmation message
            bot.reply_to(
                message,
f"""✅ <b>{service['name']} Oʀᴅᴇʀ Sᴜʙᴍɪᴛᴛᴇᴅ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
📦 <b>Sᴇʀᴠɪᴄᴇ:</b> {service['name']}
━━━━━━━━━━━━━━━━━━━━━━━
🔢 <b>Qᴜᴀɴᴛɪᴛʏ:</b> {quantity}
💰 <b>Cᴏꜱᴛ:</b> {cost} ᴄᴏɪɴꜱ
━━━━━━━━━━━━━━━━━━━━━━━
📎 <b>Lɪɴᴋ:</b> {link}
🆔 <b>Oʀᴅᴇʀ ID:</b> {result['order']}
━━━━━━━━━━━━━━━━━━━━━━━
😊 <b>Tʜᴀɴᴋꜱ ꜰᴏʀ ᴏʀᴅᴇʀɪɴɢ!</b>
━━━━━━━━•❅•°•❈•°•❅•━━━━━━━━
⚠️ <b>𝙒𝙖𝙧𝙣𝙞𝙣𝙜:</b> Dᴏ ɴᴏᴛ ꜱᴇɴᴅ ᴛʜᴇ ꜱᴀᴍᴇ ᴏʀᴅᴇʀ ᴏɴ ᴛʜᴇ ꜱᴀᴍᴇ ʟɪɴᴋ ʙᴇꜰᴏʀᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴏɴᴇ ɪꜱ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀ ʏᴏᴜ ᴍɪɡʜᴛ ɴᴏᴛ ʀᴇᴄᴇɪᴠᴇ ᴛʜᴇ ꜱᴇʀᴠɪᴄᴇ!""",
                reply_markup=markup,
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
#======================== End of Whastapp Orders =====================#

#=================== The back button handler =========================================
@bot.message_handler(func=lambda message: message.text in ["↩️ Go Back", "✘ Cancel"])
def handle_back_buttons(message):
    """Handle all back/cancel buttons"""
    if message.text == "↩️ Go Back":
        # Determine where to go back based on context
        if message.text in ["👀 Order Views", "❤️ Order Reactions", "👥 Order Members"]:
            bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Tᴇʟᴇɢʀᴀᴍ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=telegram_services_markup)
        elif message.text in ["👀 TikTok Views", "❤️ TikTok Likes", "👥 TikTok Followers"]:
            bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Tɪᴋᴛᴏᴋ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=tiktok_services_markup)
        elif message.text in ["🎥 Insta Vid Views", "❤️ Insta Likes", "👥 Insta Followers"]:
            bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Iɴꜱᴛᴀɢʀᴀᴍ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=instagram_services_markup)
        elif message.text in ["▶️ YT Views", "👍 YT Likes", "👥 YT Subscribers"]:
            bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Yᴏᴜᴛᴜʙᴇ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=youtube_services_markup)
        elif message.text in ["👤 Profile Followers", "📄 Page Followers", "🎥 Video/Reel Views", "❤️ Post Likes"]:
            bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Fᴀᴄᴇʙᴏᴏᴋ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=facebook_services_markup)
        elif message.text in ["👥 Channel Members", "😀 Channel EmojiReaction"]:
            bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Wʜᴀꜱᴛᴀᴘᴘ Sᴇʀᴠɪᴄᴇꜱ...", reply_markup=whatsapp_services_markup)
        else:
            # Default back to Send Orders menu
            bot.reply_to(message, "Rᴇᴛᴜʀɴɪɴɢ Tᴏ Oʀᴅᴇʀ Oᴘᴛɪᴏɴꜱ...", reply_markup=send_orders_markup)
    else:
        # Cancel goes straight to main menu
        bot.reply_to(message, "Oᴘᴇʀᴀᴛɪᴏɴ Cᴀɴᴄᴇʟʟᴇᴅ.", reply_markup=main_markup)


#=================== The back button handler =========================================
@bot.message_handler(func=lambda message: message.text == "🔙 Main Menu")
def back_to_main(message):
    if message.from_user.id in admin_user_ids:
        # For admins, show both admin and user keyboards
        combined_markup = ReplyKeyboardMarkup(resize_keyboard=True)
        combined_markup.row("🛒 Buy Services", "👤 My Account")
        combined_markup.row("💳 Pricing", "📊 Order Stats")
        combined_markup.row("🗣 Invite", "🏆 Leaderboard")
        combined_markup.row("📜 Help")
        
        bot.reply_to(message,
            "🔄 *Rᴇᴛᴜʀɴɪɴɢ ᴛᴏ Mᴀɪɴ Mᴇɴᴜ*\n\n",
            parse_mode="Markdown",
            reply_markup=combined_markup)
    else:
        # For regular users, show normal keyboard
        bot.reply_to(message,
            "🔄 *Rᴇᴛᴜʀɴɪɴɢ ᴛᴏ Mᴀɪɴ Mᴇɴᴜ*",
            parse_mode="Markdown",
            reply_markup=main_markup)

# ================= ADMIN COMMANDS ================== #

@bot.message_handler(commands=['adminpanel'])
def admin_panel(message):
    if message.from_user.id not in admin_user_ids:
        bot.reply_to(message,
            "🔒 *Rᴇꜱᴛʀɪᴄᴛᴇᴅ Aʀᴇᴀ*\n\n"
            "Tʜɪꜱ Pᴀɴᴇʟ ɪꜱ ꜰᴏʀ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ Aᴅᴍɪɴɪꜱᴛʀᴀᴛᴏʀꜱ ᴏɴʟʏ\n\n"
            "⚠️ Yᴏᴜʀ ᴀᴄᴄᴇꜱꜱ ᴀᴛᴛᴇᴍᴘᴛ ʜᴀꜱ ʙᴇᴇɴ ʟᴏɢɢᴇᴅ",
            parse_mode="Markdown")
        return
    
    bot.reply_to(message,
        "⚡ *SMM Bᴏᴏꜱᴛᴇʀ Aᴅᴍɪɴ Cᴇɴᴛᴇʀ*\n\n"
        "▸ Uꜱᴇʀ Mᴀɴᴀɢᴇᴍᴇɴᴛ\n"
        "▸ Cᴏɪɴ Tʀᴀɴꜱᴀᴄᴛɪᴏɴꜱ\n"
        "▸ Sʏꜱᴛᴇᴍ Cᴏɴᴛʀᴏʟꜱ\n\n"
        "Sᴇʟᴇᴄᴛ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ:",
        parse_mode="Markdown",
        reply_markup=admin_markup)
    

#============================= Add and Remove Coins ==============================================#
@bot.message_handler(func=lambda message: message.text in ["➕ Add Coins", "➖ Remove Coins"] and message.from_user.id in admin_user_ids)
def admin_actions(message):
    """Enhanced admin command guidance"""
    if "Add" in message.text:
        bot.reply_to(message,
            "💎 *Aᴅᴅ Cᴏɪɴꜱ Gᴜɪᴅᴇ*\n\n"
            "Cᴏᴍᴍᴀɴᴅ: `/addcoins <user_id> <amount>`\n\n"
            "Exᴀᴍᴘʟᴇ:\n"
            "`/addcoins 123456789 500.00`\n\n"
            "⚠️ Wɪʟʟ ᴄʀᴇᴀᴛᴇ ᴀᴄᴄᴏᴜɴᴛ ɪꜰ ɴᴏᴛ ᴇxɪꜱᴛꜱ",
            parse_mode="Markdown",
            reply_markup=ForceReply(selective=True))
    elif "Remove" in message.text:
        bot.reply_to(message,
            "⚡ *Rᴇᴍᴏᴠᴇ Cᴏɪɴꜱ Gᴜɪᴅᴇ*\n\n"
            "Cᴏᴍᴍᴀɴᴅ: `/removecoins <user_id> <amount>`\n\n"
            "Exᴀᴍᴘʟᴇ:\n"
            "`/removecoins 123456789 250.50`\n\n"
            "⚠️ Fᴀɪʟꜱ ɪꜰ ɪɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ",
            parse_mode="Markdown",
            reply_markup=ForceReply(selective=True))

@bot.message_handler(commands=['addcoins', 'removecoins'])
def handle_admin_commands(message):
    if message.from_user.id not in admin_user_ids:
        bot.reply_to(message, 
            "⛔ *Aᴅᴍɪɴ Aᴄᴄᴇꜱꜱ Dᴇɴɪᴇᴅ*\n\n"
            "Tʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪꜱ ʀᴇꜱᴛʀɪᴄᴛᴇᴅ ᴛᴏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ꜱᴛᴀꜰꜰ ᴏɴʟʏ\n"
            "Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴀᴄᴄᴇꜱꜱ ᴀᴛᴛᴇᴍᴘᴛꜱ ᴀʀᴇ ʟᴏɢɢᴇᴅ",
            parse_mode="Markdown")
        return
    
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(message,
"⚡ *Uꜱᴀɢᴇ Gᴜɪᴅᴇ*\n\n"
"▸ Aᴅᴅ ᴄᴏɪɴꜱ: `/addcoins <user_id> <amount>`\n"
"▸ Rᴇᴍᴏᴠᴇ ᴄᴏɪɴꜱ: `/removecoins <user_id> <amount>`\n\n"
"💡 Exᴀᴍᴘʟᴇ: `/addcoins 123456789 100.50`",
parse_mode="Markdown")
            return
            
        user_id = args[1]
        try:
            # Handle both integer and float inputs
            amount = float(args[2]) if '.' in args[2] else int(args[2])
            if amount <= 0:
                raise ValueError
        except ValueError:
            bot.reply_to(message,
"⚠️ *Iɴᴠᴀʟɪᴅ Aᴍᴏᴜɴᴛ*\n\n"
"Amount must be:\n"
"▸ A ᴘᴏꜱɪᴛɪᴠᴇ ɴᴜᴍʙᴇʀ\n"
"▸ Dᴇᴄɪᴍᴀʟ ᴠᴀʟᴜᴇꜱ ᴀʟʟᴏᴡᴇᴅ\n"
"▸ Mɪɴɪᴍᴜᴍ: 0.01",
parse_mode="Markdown")
            return
            
        if args[0] == '/addcoins':
            if not isExists(user_id):
                initial_data = {
                    "user_id": user_id,
                    "balance": 0.00,  # Changed from string to float
                    "ref_by": "none",
                    "referred": 0,
                    "welcome_bonus": 0,
                    "total_refs": 0,
                }
                insertUser(user_id, initial_data)
                
            if addBalance(user_id, amount):
                user_data = getData(user_id)
                new_balance = user_data.get('balance', 0) if user_data else 0
                
                bot.reply_to(message,
f"💎 *Cᴏɪɴꜱ Aᴅᴅᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ*\n\n"
f"▸ Uꜱᴇʀ ID: `{user_id}`\n"
f"▸ Aᴍᴏᴜɴᴛ: +{amount:.2f} ᴄᴏɪɴꜱ\n"
f"▸ Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance:.2f}\n\n"
"📝 _Tʀᴀɴꜱᴀᴄᴛɪᴏɴ ʟᴏɢɢᴇᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ_",
parse_mode="Markdown")
                
                # Premium user notification
                try:
                    bot.send_message(
                        user_id,
f"🎉 *Aᴄᴄᴏᴜɴᴛ Cʀᴇᴅɪᴛᴇᴅ*\n\n"
f"Yᴏᴜʀ SMM Bᴏᴏꜱᴛᴇʀ ᴡᴀʟʟᴇᴛ ʜᴀꜱ ʙᴇᴇɴ ᴛᴏᴘᴘᴇᴅ ᴜᴘ!\n\n"
f"▸ Aᴍᴏᴜɴᴛ: +{amount:.2f} ᴄᴏɪɴꜱ\n"
f"▸ Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance:.2f}\n"
f"▸ Tʀᴀɴꜱᴀᴄᴛɪᴏɴ ID: {int(time.time())}\n\n"
"💎 Tʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ʙᴇɪɴɢ ᴀ ᴠᴀʟᴜᴇᴅ ᴄᴜꜱᴛᴏᴍᴇʀ!",
parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton("🛍️ Shop Now", callback_data="show_send_orders")
                        )
                    )
                except Exception as e:
                    print(f"Credit notification failed: {e}")
            else:
                bot.reply_to(message,
"❌ *Tʀᴀɴꜱᴀᴄᴛɪᴏɴ Fᴀɪʟᴇᴅ*\n\n"
"Cᴏᴜʟᴅ ɴᴏᴛ ᴀᴅᴅ ᴄᴏɪɴꜱ ᴛᴏ ᴜꜱᴇʀ ᴀᴄᴄᴏᴜɴᴛ\n"
"Pᴏꜱꜱɪʙʟᴇ ʀᴇᴀꜱᴏɴꜱ:\n"
"▸ Dᴀᴛᴀʙᴀꜱᴇ ᴇʀʀᴏʀ\n"
"▸ Iɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ID",
parse_mode="Markdown")
                
        elif args[0] == '/removecoins':
            if cutBalance(user_id, amount):
                user_data = getData(user_id)
                new_balance = user_data.get('balance', 0) if user_data else 0
                
                bot.reply_to(message,
f"⚡ *Cᴏɪɴꜱ Dᴇᴅᴜᴄᴛᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ*\n\n"
f"▸ Uꜱᴇʀ ID: `{user_id}`\n"
f"▸ Aᴍᴏᴜɴᴛ: -{amount:.2f} ᴄᴏɪɴꜱ\n"
f"▸ Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance:.2f}\n\n"
"📝 _Tʀᴀɴꜱᴀᴄᴛɪᴏɴ ʟᴏɢɢᴇᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ_",
parse_mode="Markdown")
                
                # Premium user notification
                try:
                    bot.send_message(
                        user_id,
f"🔔 *Aᴄᴄᴏᴜɴᴛ Dᴇʙɪᴛᴇᴅ*\n\n"
f"Cᴏɪɴꜱ ʜᴀᴠᴇ ʙᴇᴇɴ ᴅᴇᴅᴜᴄᴛᴇᴅ ꜰʀᴏᴍ ʏᴏᴜʀ SMM Bᴏᴏꜱᴛᴇʀ ᴡᴀʟʟᴇᴛ\n\n"
f"▸ Aᴍᴏᴜɴᴛ: -{amount:.2f} ᴄᴏɪɴꜱ\n"
f"▸ Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {new_balance:.2f}\n"
f"▸ Tʀᴀɴꜱᴀᴄᴛɪᴏɴ ID: {int(time.time())}\n\n"
"⚠️ Cᴏɴᴛᴀᴄᴛ Sᴜᴘᴘᴏʀᴛ ɪꜰ ᴛʜɪꜱ ᴡᴀꜱ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ",
parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton("📩 Contact Support", url="https://t.me/SocialHubBoosterTMbot")
                        )
                    )
                except Exception as e:
                    print(f"Debit notification failed: {e}")
            else:
                bot.reply_to(message,
"❌ *Tʀᴀɴꜱᴀᴄᴛɪᴏɴ Fᴀɪʟᴇᴅ*\n\n"
"Cᴏᴜʟᴅ ɴᴏᴛ ʀᴇᴍᴏᴠᴇ ᴄᴏɪɴꜱ ꜰʀᴏᴍ ᴜꜱᴇʀ ᴀᴄᴄᴏᴜɴᴛ\n"
"Pᴏꜱꜱɪʙʟᴇ ʀᴇᴀꜱᴏɴꜱ:\n"
"▸ Iɴꜱᴜꜰꜰɪᴄɪᴇɴᴛ ʙᴀʟᴀɴᴄᴇ\n"
"▸ Iɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ID\n"
"▸ Dᴀᴛᴀʙᴀꜱᴇ ᴇʀʀᴏʀ",
parse_mode="Markdown")
                
    except Exception as e:
        bot.reply_to(message,
            f"⚠️ *System Error*\n\n"
            f"Command failed: {str(e)}\n\n"
            "Please try again or contact developer",
            parse_mode="Markdown")
        print(f"Admin command error: {traceback.format_exc()}")

#=========================== Batch Coin Commands =================================#
@bot.message_handler(func=lambda m: m.text == "📦 Batch Coins")
def show_batch_coins_help(message):
    if message.from_user.id not in admin_user_ids:
        return
    bot.reply_to(message,
        "🧮 *Bᴀᴛᴄʜ Cᴏɪɴꜱ Pᴀɴᴇʟ*\n\n"
        "Uꜱᴇ ᴛʜᴇ ꜰᴏʟʟᴏᴡɪɴɢ ᴄᴏᴍᴍᴀɴᴅꜱ ᴛᴏ ᴀᴅᴅ ᴏʀ ʀᴇᴍᴏᴠᴇ ᴄᴏɪɴꜱ ꜰᴏʀ ᴀʟʟ ᴜꜱᴇʀꜱ:\n\n"
        "▸ `/alladdcoins <amount>`\n"
        "▸ `/allremovecoins <amount>`\n\n"
        "⚠️ *Nᴏᴛᴇ:* Aʟʟ ᴜꜱᴇʀꜱ ᴡɪʟʟ ʙᴇ ɴᴏᴛɪꜰɪᴇᴅ.",
        parse_mode="Markdown")

@bot.message_handler(commands=['alladdcoins', 'allremovecoins'])
def handle_batch_coins(message):
    if message.from_user.id not in admin_user_ids:
        bot.reply_to(message,
            "⛔ *Aᴅᴍɪɴ Aᴄᴄᴇꜱꜱ Dᴇɴɪᴇᴅ*\n\n"
            "Tʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪꜱ ʀᴇꜱᴛʀɪᴄᴛᴇᴅ ᴛᴏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ꜱᴛᴀꜰꜰ ᴏɴʟʏ\n"
            "Uɴᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴀᴄᴄᴇꜱꜱ ᴀᴛᴛᴇᴍᴘᴛꜱ ᴀʀᴇ ʟᴏɢɢᴇᴅ",
            parse_mode="Markdown")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message,
"⚡ *Uꜱᴀɢᴇ Gᴜɪᴅᴇ*\n\n"
"▸ Aᴅᴅ ᴄᴏɪɴꜱ: `/alladdcoins <amount>`\n"
"▸ Rᴇᴍᴏᴠᴇ ᴄᴏɪɴꜱ: `/allremovecoins <amount>`\n\n"
"💡 Exᴀᴍᴘʟᴇ: `/alladdcoins 100`",
            parse_mode="Markdown")
        return

    try:
        amount = float(args[1]) if '.' in args[1] else int(args[1])
        if amount <= 0:
            raise ValueError
    except ValueError:
        bot.reply_to(message,
"⚠️ *Iɴᴠᴀʟɪᴅ Aᴍᴏᴜɴᴛ*\n\n"
"Amount must be:\n"
"▸ A positive number\n"
"▸ Decimal values allowed\n"
"▸ Minimum: 0.01",
            parse_mode="Markdown")
        return

    users = get_all_users()
    success = 0
    failed = 0

    for uid in users:
        try:
            if args[0] == '/alladdcoins':
                if addBalance(uid, amount):
                    data = getData(uid)
                    bot.send_message(
                        uid,
f"🎉 *Aᴄᴄᴏᴜɴᴛ Cʀᴇᴅɪᴛᴇᴅ*\n\n"
f"Yᴏᴜʀ SMM Bᴏᴏꜱᴛᴇʀ ᴡᴀʟʟᴇᴛ ʜᴀꜱ ʙᴇᴇɴ ᴛᴏᴘᴘᴇᴅ ᴜᴘ!\n\n"
f"▸ Aᴍᴏᴜɴᴛ: +{amount:.2f} ᴄᴏɪɴꜱ\n"
f"▸ Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {data['balance']:.2f}\n"
f"▸ Tʀᴀɴꜱᴀᴄᴛɪᴏɴ ID: {int(time.time())}\n\n"
"💎 Tʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ʙᴇɪɴɢ ᴀ ᴠᴀʟᴜᴇᴅ ᴄᴜꜱᴛᴏᴍᴇʀ!",
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup().add(
                            InlineKeyboardButton("🛍️ Shop Now", callback_data="show_send_orders")
                        )
                    )
                    success += 1
                else:
                    failed += 1
            elif args[0] == '/allremovecoins':
                if cutBalance(uid, amount):
                    data = getData(uid)
                    bot.send_message(
                        uid,
                    f"🔔 *ACCOUNT DEBITED*\n\n"
                    f"Cᴏɪɴꜱ ʜᴀᴠᴇ ʙᴇᴇɴ Dᴇᴅᴜᴄᴛᴇᴅ ꜰʀᴏᴍ ʏᴏᴜʀ Sᴍᴍ Bᴏᴏꜱᴛᴇʀ Wᴀʟʟᴇᴛ\n\n"
                    f"▸ Aᴍᴏᴜɴᴛ: -{amount:.2f} coins\n"
                    f"▸ Nᴇᴡ Bᴀʟᴀɴᴄᴇ: {data['balance']:.2f}\n"
                    f"▸ Tʀᴀɴꜱᴀᴄᴛɪᴏɴ ID: {int(time.time())}\n\n"
                    "⚠️ Cᴏɴᴛᴀᴄᴛ Sᴜᴘᴘᴏʀᴛ ɪꜰ ᴛʜɪꜱ ᴡᴀꜱ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup().add(
                        InlineKeyboardButton("📩 Contact Support", url="https://t.me/SocialHubBoosterTMbot")
                        )
                    )
                    success += 1
                else:
                    failed += 1
        except Exception as e:
            print(f"Batch update failed for {uid}: {e}")
            failed += 1

    bot.reply_to(message,
        f"📊 *Bᴀᴛᴄʜ Oᴘᴇʀᴀᴛɪᴏɴ Cᴏᴍᴘʟᴇᴛᴇᴅ*\n\n"
        f"✅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟ: {success}\n"
        f"❌ Fᴀɪʟᴇᴅ: {failed}",
        parse_mode="Markdown")

#=============================== Admin Stats Command =====================================#
@bot.message_handler(func=lambda m: m.text == "📊 Analytics" and m.from_user.id in admin_user_ids)
def show_analytics(message):
    """Show comprehensive bot analytics with premium dashboard"""
    try:
        # Store the original message ID if this is a new request
        if not hasattr(message, 'is_callback'):
            message.original_message_id = message.message_id + 1  # Next message will be +1
            
        show_analytics_dashboard(message)
        
    except Exception as e:
        print(f"Analytics error: {e}")
        bot.reply_to(message, 
"⚠️ <b>Aɴᴀʟʏᴛɪᴄꜱ Dᴀꜱʜʙᴏᴀʀᴅ Uɴᴀᴠᴀɪʟᴀʙʟᴇ</b>\n\n"
"Our ᴘʀᴇᴍɪᴜᴍ ᴍᴇᴛʀɪᴄꜱ ꜱʏꜱᴛᴇᴍ ɪꜱ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ᴏꜰꜰʟɪɴᴇ\n"
"Pʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ",
            parse_mode='HTML')

def show_analytics_dashboard(message, is_refresh=False):
    """Show or update the analytics dashboard"""
    try:
        # Get all stats
        total_users = get_user_count()
        active_users = get_active_users(7)
        new_users_24h = get_new_users(1)
        total_orders = get_total_orders()
        completed_orders = get_completed_orders()
        total_deposits = get_total_deposits()
        top_referrer = get_top_referrer()
        
        # Format top referrer
        if top_referrer['user_id']:
            username = f"@{top_referrer['username']}" if top_referrer['username'] else f"User {top_referrer['user_id']}"
            referrer_display = f"🏆 {username} (Invited {top_referrer['count']} users)"
        else:
            referrer_display = "📭 No referrals yet"
        
        # Calculate conversion rates
        conversion_rate = (completed_orders/total_orders)*100 if total_orders > 0 else 0
        deposit_per_user = total_deposits/total_users if total_users > 0 else 0
        
        # Create premium dashboard
        msg = f"""
<blockquote>
📈 <b>SMM Bᴏᴏꜱᴛᴇʀ Aɴᴀʟʏᴛɪᴄꜱ</b>
━━━━━━━━━━━━━━━━━━━━

👥 <b>Uꜱᴇʀ Sᴛᴀᴛɪꜱᴛɪᴄꜱ</b>
├ 👤 Tᴏᴛᴀʟ Uꜱᴇʀꜱ: <code>{total_users}</code>
├ 🔥 Aᴄᴛɪᴠᴇ (7ᴅ): <code>{active_users}</code>
├ 🆕 Nᴇᴡ (24ʜ): <code>{new_users_24h}</code>
└ 💰 Aᴠɢ Dᴇᴘᴏꜱɪᴛ/Uꜱᴇʀ: <code>{deposit_per_user:.2f}</code> ᴄᴏɪɴꜱ

🛒 <b>Oʀᴅᴇʀ Mᴇᴛʀɪᴄꜱ</b>
├ 🚀 Tᴏᴛᴀʟ Oʀᴅᴇʀꜱ: <code>{total_orders}</code>
├ ✅ Cᴏᴍᴘʟᴇᴛᴇᴅ: <code>{completed_orders}</code>
├ 📊 Cᴏɴᴠᴇʀꜱɪᴏɴ: <code>{conversion_rate:.1f}%</code>
└ 💸 Tᴏᴛᴀʟ Dᴇᴘᴏꜱɪᴛꜱ: <code>{total_deposits:.2f}</code> ᴄᴏɪɴꜱ

🔗 <b>Rᴇꜰᴇʀʀᴀʟ Pʀᴏɢʀᴀᴍ</b>
└ {referrer_display}

⏳ <i>Lᴀꜱᴛ Uᴘᴅᴀᴛᴇᴅ: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>
</blockquote>
"""
        
        # Add quick action buttons
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🔄 Refresh", callback_data="refresh_analytics"),
            InlineKeyboardButton("📊 Full Report", callback_data="full_report")
        )
        
        if hasattr(message, 'is_callback') or is_refresh:
            # Edit existing message
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=msg,
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            # Send new message
            sent_msg = bot.send_message(
                message.chat.id,
                msg,
                parse_mode='HTML',
                reply_markup=markup
            )
            message.original_message_id = sent_msg.message_id
        
    except Exception as e:
        print(f"Analytics dashboard error: {e}")

# Handle Refresh Analytics button
@bot.callback_query_handler(func=lambda call: call.data == "refresh_analytics")
def handle_refresh_analytics(call):
    try:
        call.message.is_callback = True
        show_analytics_dashboard(call.message, is_refresh=True)
        bot.answer_callback_query(call.id, "🔄 Data refreshed")
    except Exception as e:
        print(f"Error refreshing analytics: {e}")
        bot.answer_callback_query(call.id, "⚠️ Failed to refresh", show_alert=True)

# Handle Back button in analytics
@bot.callback_query_handler(func=lambda call: call.data == "analytics_back")
def handle_analytics_back(call):
    try:
        call.message.is_callback = True
        show_analytics_dashboard(call.message)
        bot.answer_callback_query(call.id)
    except Exception as e:
        print(f"Error going back in analytics: {e}")
        bot.answer_callback_query(call.id, "⚠️ Failed to go back", show_alert=True)

# Handle Full Report button
@bot.callback_query_handler(func=lambda call: call.data == "full_report")
def handle_full_report(call):
    try:
        bot.answer_callback_query(call.id, "📊 Generating report...")

        total_users = get_user_count()
        active_users = get_active_users(7)
        new_users_24h = get_new_users(1)
        total_orders = get_total_orders()
        completed_orders = get_completed_orders()
        total_deposits = get_total_deposits()
        top_referrer = get_top_referrer()
        banned_users = len(get_banned_users())

        conversion_rate = (completed_orders/total_orders)*100 if total_orders > 0 else 0
        deposit_per_user = total_deposits/total_users if total_users > 0 else 0
        active_rate = (active_users/total_users)*100 if total_users > 0 else 0

        if top_referrer['user_id']:
            username = f"@{top_referrer['username']}" if top_referrer['username'] else f"User {top_referrer['user_id']}"
            referrer_display = f"🏆 {username} (Invited {top_referrer['count']} users)"
        else:
            referrer_display = "📭 No referrals yet"

        msg = f"""
<blockquote>
📊 <b>Fᴜʟʟ Aɴᴀʟʏᴛɪᴄꜱ Rᴇᴘᴏʀᴛ</b>
━━━━━━━━━━━━━━━━━━━━

👥 <b>Uꜱᴇʀ Sᴛᴀᴛɪꜱᴛɪᴄꜱ</b>
├ Tᴏᴛᴀʟ Uꜱᴇʀꜱ: <code>{total_users}</code>
├ Aᴄᴛɪᴠᴇ (7ᴅ): <code>{active_users}</code> ({active_rate:.1f}%)
├ Nᴇᴡ (24ʜ): <code>{new_users_24h}</code>
├ Bᴀɴɴᴇᴅ Uꜱᴇʀꜱ: <code>{banned_users}</code>
└ Aᴠɢ Dᴇᴘᴏꜱɪᴛ/Uꜱᴇʀ: <code>{deposit_per_user:.2f}</code> ᴄᴏɪɴꜱ

🛒 <b>Oʀᴅᴇʀ Mᴇᴛʀɪᴄꜱ</b>
├ Tᴏᴛᴀʟ Oʀᴅᴇʀꜱ: <code>{total_orders}</code>
├ Cᴏᴍᴘʟᴇᴛᴇᴅ: <code>{completed_orders}</code>
└ Cᴏɴᴠᴇʀꜱɪᴏɴ Rᴀᴛᴇ: <code>{conversion_rate:.1f}%</code>

💰 <b>Fɪɴᴀɴᴄɪᴀʟꜱ</b>
├ Tᴏᴛᴀʟ Dᴇᴘᴏꜱɪᴛꜱ: <code>{total_deposits:.2f}</code> ᴄᴏɪɴꜱ
└ Aᴠɢ Oʀᴅᴇʀ Vᴀʟᴜᴇ: <code>{(total_deposits/total_orders):.2f}</code> ᴄᴏɪɴꜱ

🔗 <b>Rᴇꜰᴇʀʀᴀʟ Pʀᴏɢʀᴀᴍ</b>
└ {referrer_display}

📅 Gᴇɴᴇʀᴀᴛᴇᴅ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
</blockquote>
"""

        # Add back button
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 Back to Overview", callback_data="analytics_back"))

        # Overwrite the current message
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=msg,
            parse_mode="HTML",
            reply_markup=markup
        )

    except Exception as e:
        print(f"Error sending full report: {e}")
        bot.answer_callback_query(call.id, "⚠️ Failed to load full report", show_alert=True)

# =========================== Broadcast Command ================= #
@bot.message_handler(func=lambda m: m.text == "📤 Broadcast" and m.from_user.id in admin_user_ids)
def broadcast_start(message):
    """Start normal broadcast process (unpinned)"""
    msg = bot.reply_to(message, "📢 ✨ <b>Cᴏᴍᴘᴏꜱᴇ Yᴏᴜʀ Bʀᴏᴀᴅᴄᴀꜱᴛ Mᴇꜱꜱᴀɢᴇ</b> ✨\n\n"
                              "Pʟᴇᴀꜱᴇ ᴇɴᴛᴇʀ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ʏᴏᴜ'ᴅ ʟɪᴋᴇ ᴛᴏ ꜱᴇɴᴅ ᴛᴏ ᴀʟʟ ᴜꜱᴇʀꜱ.\n"
                              "Tʜɪꜱ ᴡɪʟʟ ʙᴇ ꜱᴇɴᴛ ᴀꜱ ᴀ ʀᴇɢᴜʟᴀʀ (ᴜɴᴘɪɴɴᴇᴅ) ᴍᴇꜱꜱᴀɢᴇ.\n\n"
                              "🖋️ Yᴏᴜ ᴄᴀɴ ɪɴᴄʟᴜᴅᴇ ᴛᴇxᴛ, ᴘʜᴏᴛᴏꜱ, ᴏʀ ᴅᴏᴄᴜᴍᴇɴᴛꜱ.\n"
                              "❌ Tʏᴘᴇ <code>✘ Cᴀɴᴄᴇʟ</code> ᴛᴏ ᴀʙᴏʀᴛ.", 
                       parse_mode="HTML")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    """Process and send the broadcast message (unpinned)"""
    if message.text == "Cancel":
        bot.reply_to(message, "🛑 <b>Broadcast cancelled.</b>", 
                     parse_mode="HTML", reply_markup=admin_markup)
        return
    
    users = get_all_users()
    if not users:
        bot.reply_to(message, "❌ No users found to broadcast to", reply_markup=admin_markup)
        return
    
    success = 0
    failed = 0
    
    # Enhanced sending notification with progress bar concept
    progress_msg = bot.reply_to(message, f"""📨 <b>Bʀᴏᴀᴅᴄᴀꜱᴛ Iɴɪᴛɪᴀᴛᴇᴅ</b>
    
📊 Tᴏᴛᴀʟ Rᴇᴄɪᴘɪᴇɴᴛꜱ: <code>{len(users)}</code>
⏳ Sᴛᴀᴛᴜꜱ: <i>Processing...</i>

[░░░░░░░░░░] 0%""", parse_mode="HTML")
    
    # Calculate update interval (at least 1)
    update_interval = max(1, len(users) // 10)
    
    for index, user_id in enumerate(users):
        try:
            if message.content_type == 'text':
                # Enhanced text message format
                formatted_text = f"""✨ <b>Aɴɴᴏᴜɴᴄᴇᴍᴇɴᴛ</b> ✨\n\n{message.text}\n\n"""
                if not message.text.endswith(('🌐', '📢', '🔔', '📣', '📩')):
                    formatted_text += "━━━━━━━━━━━━━━\n"
                    formatted_text += "💌 Tʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ʙᴇɪɴɢ ᴘᴀʀᴛ ᴏꜰ ᴏᴜʀ ᴄᴏᴍᴍᴜɴɪᴛʏ!\n"
                    formatted_text += "🔔 Sᴛᴀʏ ᴛᴜɴᴇᴅ ꜰᴏʀ ᴍᴏʀᴇ ᴜᴘᴅᴀᴛᴇꜱ."
                bot.send_message(user_id, formatted_text, parse_mode="HTML")
            elif message.content_type == 'photo':
                # Enhanced photo caption
                caption = f"📸 {message.caption}" if message.caption else "✨ Community Update"
                bot.send_photo(user_id, message.photo[-1].file_id, caption=caption)
            elif message.content_type == 'document':
                # Enhanced document caption
                caption = f"📄 {message.caption}" if message.caption else "📁 Important Document"
                bot.send_document(user_id, message.document.file_id, caption=caption)
            success += 1
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")
            failed += 1
        
        # Update progress periodically
        if (index+1) % update_interval == 0 or index+1 == len(users):
            progress = int((index+1)/len(users)*100)
            progress_bar = '█' * (progress//10) + '░' * (10 - progress//10)
            try:
                bot.edit_message_text(f"""📨 <b>Bʀᴏᴀᴅᴄᴀꜱᴛ Pʀᴏɢʀᴇꜱꜱ</b>
                
📊 Tᴏᴛᴀʟ Rᴇᴄɪᴘɪᴇɴᴛꜱ: <code>{len(users)}</code>
✅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{success}</code>
❌ Fᴀɪʟᴇᴅ: <code>{failed}</code>
⏳ Sᴛᴀᴛᴜꜱ: <i>Sᴇɴᴅɪɴɢ...</i>

[{progress_bar}] {progress}%""", 
                    message.chat.id, progress_msg.message_id, parse_mode="HTML")
            except Exception as e:
                print(f"Failed to update progress: {e}")
        
        time.sleep(0.1)  # Rate limiting
    
# Enhanced completion message
    bot.reply_to(message, f"""📣 <b>Bʀᴏᴀᴅᴄᴀꜱᴛ Cᴏᴍᴘʟᴇᴛᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!</b>
    
📊 <b>Sᴛᴀᴛɪꜱᴛɪᴄꜱ:</b>
├ 📤 <i>Sᴇɴᴛ:</i> <code>{success}</code>
└ ❌ <i>Fᴀɪʟᴇᴅ:</i> <code>{failed}</code>

⏱️ <i>Fɪɴɪꜱʜᴇᴅ ᴀᴛ:</i> <code>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>

✨ <i>Tʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴜꜱɪɴɢ ᴏᴜʀ ʙʀᴏᴀᴅᴄᴀꜱᴛ ꜱʏꜱᴛᴇᴍ!</i>""", 
                 parse_mode="HTML", reply_markup=admin_markup)

#====================== Ban User Command ================================#
# ============================= Enhanced Ban User Command ============================= #
@bot.message_handler(func=lambda m: m.text == "🔒 Ban User" and m.from_user.id in admin_user_ids)
def ban_user_start(message):
    """Start ban user process"""
    msg = bot.reply_to(message, 
        "⚡ *SMM Aᴅᴍɪɴ Pᴀɴᴇʟ - Bᴀɴ Uꜱᴇʀ*\n\n"
        "Eɴᴛᴇʀ Uꜱᴇʀ Iᴅ Tᴏ Bᴀɴ:\n"
        "▸ *Fᴏʀᴍᴀᴛ*: `123456789`\n"
        "▸ *Nᴏᴛᴇ*: Uꜱᴇʀ ᴡɪʟʟ ʟᴏꜱᴇ ᴀʟʟ ꜱᴇʀᴠɪᴄᴇ ᴀᴄᴄᴇꜱꜱ\n\n"
        "✘ Tʏᴘᴇ *'Cᴀɴᴄᴇʟ'* ᴛᴏ ᴀʙᴏʀᴛ",
        parse_mode="Markdown",
        reply_markup=ForceReply(selective=True))
    bot.register_next_step_handler(msg, process_ban_user)

def process_ban_user(message):
    """Ban a user with enhanced features"""
    if message.text == "Cancel":
        bot.reply_to(message, "❌ Ban cancelled.", reply_markup=admin_markup)
        return
    
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.reply_to(message, 
            "❌ *Iɴᴠᴀʟɪᴅ Iɴᴘᴜᴛ*\n"
            "Uꜱᴇʀ Iᴅ ᴍᴜꜱᴛ ᴄᴏɴᴛᴀɪɴ ᴏɴʟʏ ɴᴜᴍʙᴇʀꜱ\n"
            "Exᴀᴍᴘʟᴇ: `123456789`",
            parse_mode="Markdown",
            reply_markup=admin_markup)
        return
    
    if is_banned(user_id):
        bot.reply_to(message, 
            "⚠️ *User Already Banned*\n"
            f"User `{user_id}` is already in ban list",
            parse_mode="Markdown",
            reply_markup=admin_markup)
        return
    
    ban_user(user_id)
    
    # Enhanced ban notification to user
    try:
        appeal_markup = InlineKeyboardMarkup()
        appeal_markup.row(
            InlineKeyboardButton("📩 Appeal Ban", url="https://t.me/SocialHubBoosterTMbot"),
            InlineKeyboardButton("📋 View Terms", callback_data="ban_terms")
        )

        
        bot.send_message(
            user_id,
            f"⛔ *ACCOUNT SUSPENDED*\n\n"
f"⛔ *Aᴄᴄᴏᴜɴᴛ Sᴜꜱᴘᴇɴᴅᴇᴅ*\n\n"
f"Yᴏᴜʀ ᴀᴄᴄᴇꜱꜱ ᴛᴏ *SMM Bᴏᴏꜱᴛᴇʀ* ꜱᴇʀᴠɪᴄᴇꜱ ʜᴀꜱ ʙᴇᴇɴ ʀᴇꜱᴛʀɪᴄᴛᴇᴅ.\n\n"
f"▸ *Rᴇᴀꜱᴏɴ*: Vɪᴏʟᴀᴛɪᴏɴ ᴏꜰ Tᴇʀᴍꜱ\n"
f"▸ *Aᴘᴘᴇᴀʟ*: Aᴠᴀɪʟᴀʙʟᴇ ᴠɪᴀ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ\n"
f"▸ *Sᴛᴀᴛᴜꜱ*: Pᴇʀᴍᴀɴᴇɴᴛ (ᴜɴᴛɪʟ ᴀᴘᴘᴇᴀʟ)\n\n"
f"⚠️ Aᴛᴛᴇᴍᴘᴛɪɴɢ ᴛᴏ ʙʏᴘᴀꜱꜱ ᴡɪʟʟ ʀᴇꜱᴜʟᴛ ɪɴ IP ʙʟᴀᴄᴋʟɪꜱᴛ",
parse_mode="Markdown",
reply_markup=appeal_markup
        )
        notified_success = True
    except Exception as e:
        print(f"Ban notification error: {e}")
        notified_success = False
    
    # Enhanced admin confirmation
    bot.reply_to(message,
    f"✅ *Uꜱᴇʀ Bᴀɴɴᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ*\n\n"
    f"▸ Uꜱᴇʀ Iᴅ: `{user_id}`\n"
    f"▸ Aᴄᴛɪᴏɴ: Fᴜʟʟ ꜱᴇʀᴠɪᴄᴇ ʀᴇꜱᴛʀɪᴄᴛɪᴏɴ\n"
    f"▸ Nᴏᴛɪꜰɪᴇᴅ: {'Yᴇꜱ' if notified_success else 'Fᴀɪʟᴇᴅ'}\n\n"
    f"📝 _Tʜɪꜱ ᴜꜱᴇʀ ʜᴀꜱ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ ᴛᴏ ʙᴀɴ ᴅᴀᴛᴀʙᴀꜱᴇ_",
    parse_mode="Markdown",
    reply_markup=admin_markup)

# Add this callback handler for the terms button 
@bot.callback_query_handler(func=lambda call: call.data == "ban_terms")
def show_ban_terms(call):
    """Show the policy message when View Terms is clicked"""
    try:
        # Get the policy message from the policy_command function
        policy_text = """
<blockquote>
📜 <b>🤖 Bᴏᴛ Uꜱᴀɢᴇ Pᴏʟɪᴄʏ & Gᴜɪᴅᴇʟɪɴᴇꜱ</b> 📜
━━━━━━━━━━━━━━━━━━━━

🔹 <b>1. Aᴄᴄᴇᴘᴛᴀʙʟᴇ Uꜱᴇ</b>
   ├ ✅ Pᴇʀᴍɪᴛᴛᴇᴅ: Lᴇɢᴀʟ, ɴᴏɴ-ʜᴀʀᴍꜰᴜʟ ᴄᴏɴᴛᴇɴᴛ
   └ ❌ Pʀᴏʜɪʙɪᴛᴇᴅ: Sᴘᴀᴍ, ʜᴀʀᴀꜱꜱᴍᴇɴᴛ, ɪʟʟᴇɢᴀʟ ᴍᴀᴛᴇʀɪᴀʟ

🔹 <b>2. Fᴀɪʀ Uꜱᴀɢᴇ Pᴏʟɪᴄʏ</b>
   ├ ⚖️ Aʙᴜꜱᴇ ᴍᴀʏ ʟᴇᴀᴅ ᴛᴏ ʀᴇꜱᴛʀɪᴄᴛɪᴏɴꜱ
   └ 📊 Exᴄᴇꜱꜱɪᴠᴇ ᴜꜱᴀɢᴇ ᴍᴀʏ ʙᴇ ʀᴀᴛᴇ-ʟɪᴍɪᴛᴇᴅ

🔹 <b>3. Fɪɴᴀɴᴄɪᴀʟ Pᴏʟɪᴄʏ</b>
   ├ 💳 Aʟʟ ᴛʀᴀɴꜱᴀᴄᴛɪᴏɴꜱ ᴀʀᴇ ꜰɪɴᴀʟ
   └ 🔄 Nᴏ ʀᴇꜰᴜɴᴅꜱ ꜰᴏʀ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ꜱᴇʀᴠɪᴄᴇꜱ

🔹 <b>4. Pʀɪᴠᴀᴄʏ Cᴏᴍᴍɪᴛᴍᴇɴᴛ</b>
   ├ 🔒 Yᴏᴜʀ ᴅᴀᴛᴀ ꜱᴛᴀʏꜱ ᴄᴏɴꜰɪᴅᴇɴᴛɪᴀʟ
   └ 🤝 Nᴇᴠᴇʀ ꜱʜᴀʀᴇᴅ ᴡɪᴛʜ ᴛʜɪʀᴅ ᴘᴀʀᴛɪᴇꜱ

🔹 <b>5. Pʟᴀᴛꜰᴏʀᴍ Cᴏᴍᴘʟɪᴀɴᴄᴇ</b>
   ├ ✋ Mᴜꜱᴛ ꜰᴏʟʟᴏᴡ Tᴇʟᴇɢʀᴀᴍ'ꜱ TᴏS
   └ 🌐 Aʟʟ ᴄᴏɴᴛᴇɴᴛ ᴍᴜꜱᴛ ʙᴇ ʟᴇɢᴀʟ ɪɴ ʏᴏᴜʀ ᴊᴜʀɪꜱᴅɪᴄᴛɪᴏɴ

⚠️ <b>CᴏɴꜱᴇQᴜᴇɴᴄᴇꜱ ᴏꜰ Vɪᴏʟᴀᴛɪᴏɴ</b>
   ├ ⚠️ Fɪʀꜱᴛ ᴏꜰꜰᴇɴꜱᴇ: Wᴀʀɴɪɴɢ
   ├ 🔇 Rᴇᴘᴇᴀᴛᴇᴅ ᴠɪᴏʟᴀᴛɪᴏɴꜱ: Tᴇᴍᴘᴏʀᴀʀʏ ꜱᴜꜱᴘᴇɴꜱɪᴏɴ
   └ 🚫 Sᴇᴠᴇʀᴇ ᴄᴀꜱᴇꜱ: Pᴇʀᴍᴀɴᴇɴᴛ ʙᴀɴ

📅 <i>Lᴀꜱᴛ ᴜᴘᴅᴀᴛᴇᴅ: {update_date}</i>
━━━━━━━━━━━━━━━━━━━━
💡 Nᴇᴇᴅ ʜᴇʟᴘ? Cᴏɴᴛᴀᴄᴛ @SocialHubBoosterTMbot
</blockquote>
""".format(update_date=datetime.now().strftime('%Y-%m-%d'))

        
        # Answer the callback first
        bot.answer_callback_query(call.id)
        
        # Send the policy message
        bot.send_message(
            call.message.chat.id,
            policy_text,
            parse_mode="HTML"
        )
        
    except Exception as e:
        print(f"Error showing ban terms: {e}")
        bot.answer_callback_query(call.id, "⚠️ Failed to load terms", show_alert=True)
    

# ============================= Premium Unban Command ============================= #
@bot.message_handler(func=lambda m: m.text == "✅ Unban User" and m.from_user.id in admin_user_ids)
def unban_user_start(message):
    """Start unban user process"""
    msg = bot.reply_to(message,
"⚡ *SMM Aᴅᴍɪɴ Pᴀɴᴇʟ - Uɴʙᴀɴ Uꜱᴇʀ*\n\n"
"Eɴᴛᴇʀ Uꜱᴇʀ Iᴅ Tᴏ Uɴʙᴀɴ:\n"
"▸ Wɪʟʟ ʀᴇꜱᴛᴏʀᴇ ᴀʟʟ ꜱᴇʀᴠɪᴄᴇꜱ\n"
"▸ Aᴜᴛᴏᴍᴀᴛɪᴄ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ꜱᴇɴᴛ\n\n"
"✘ Tʏᴘᴇ *'Cancel'* ᴛᴏ ᴀʙᴏʀᴛ",
        parse_mode="Markdown",
        reply_markup=ForceReply(selective=True))
    bot.register_next_step_handler(msg, process_unban_user)

def process_unban_user(message):
    """Unban a user with premium features"""
    if message.text == "Cancel":
        bot.reply_to(message, "❌ Unban cancelled.", reply_markup=admin_markup)
        return
    
    user_id = message.text.strip()
    
    if not user_id.isdigit():
        bot.reply_to(message,
            "❌ *Iɴᴠᴀʟɪᴅ Iɴᴘᴜᴛ*\n"
            "Uꜱᴇʀ Iᴅ ᴍᴜꜱᴛ ᴄᴏɴᴛᴀɪɴ ᴏɴʟʏ Nᴜᴍʙᴇʀꜱ\n"
            "Exᴀᴍᴘʟᴇ: `987654321`",
            parse_mode="Markdown",
            reply_markup=admin_markup)
        return
    
    if not is_banned(user_id):
        bot.reply_to(message,
            f"ℹ️ *User Not Banned*\n"
            f"User `{user_id}` isn't in ban records",
            parse_mode="Markdown",
            reply_markup=admin_markup)
        return
    
    unban_user(user_id)
    
    # Premium unban notification
    try:
        markup = InlineKeyboardMarkup()
        # Changed callback_data to trigger the send_orders_menu directly
        markup.add(InlineKeyboardButton("🛒 Return to Services", callback_data="show_send_orders"))
        
        bot.send_message(
            user_id,
            f"✅ *Aᴄᴄᴏᴜɴᴛ Rᴇɪɴꜱᴛᴀᴛᴇᴅ*\n\n"
            f"Yᴏᴜʀ *SMM Bᴏᴏꜱᴛᴇʀ* ᴀᴄᴄᴇꜱꜱ ʜᴀꜱ ʙᴇᴇɴ ʀᴇꜱᴛᴏʀᴇᴅ!\n\n"
            f"▸ Aʟʟ ꜱᴇʀᴠɪᴄᴇꜱ: Rᴇᴀᴄᴛɪᴠᴀᴛᴇᴅ\n"
            f"▸ Oʀᴅᴇʀ ʜɪꜱᴛᴏʀʏ: Pʀᴇꜱᴇʀᴠᴇᴅ\n"
            f"▸ Bᴀʟᴀɴᴄᴇ: Uɴᴀꜰꜰᴇᴄᴛᴇᴅ\n\n"
            f"⚠️ Pʟᴇᴀꜱᴇ ʀᴇᴠɪᴇᴡ ᴏᴜʀ ᴛᴇʀᴍꜱ ᴛᴏ ᴀᴠᴏɪᴅ ꜰᴜᴛᴜʀᴇ ɪꜱꜱᴜᴇꜱ",
            parse_mode="Markdown",
            reply_markup=markup
        )
        notified_success = True
    except Exception as e:
        print(f"Unban notification error: {e}")
        notified_success = False
    
    # Admin confirmation with flair
    bot.reply_to(message,
        f"✨ *Uꜱᴇʀ Uɴʙᴀɴɴᴇᴅ Sᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ*\n\n"
        f"▸ Uꜱᴇʀ Iᴅ: `{user_id}`\n"
        f"▸ Sᴇʀᴠɪᴄᴇꜱ: Rᴇᴀᴄᴛɪᴠᴀᴛᴇᴅ\n"
        f"▸ Nᴏᴛɪꜰɪᴇᴅ: {'Yᴇꜱ' if notified_success else 'Fᴀɪʟᴇᴅ'}\n\n"
        f"📝 _Rᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ʙᴀɴ ᴅᴀᴛᴀʙᴀꜱᴇ_",
        parse_mode="Markdown",
        reply_markup=admin_markup)

# Add this new handler for showing send orders menu
@bot.callback_query_handler(func=lambda call: call.data == "show_send_orders")
def show_send_orders_menu(call):
    """Show the send orders menu when 'Return to Services' is clicked"""
    try:
        # Delete the unban notification message
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
            
        # Show the send orders menu
        bot.send_message(
            call.message.chat.id,
            "📤 Sᴇʟᴇᴄᴛ Pʟᴀᴛꜰᴏʀᴍ Tᴏ Sᴇɴᴅ Oʀᴅᴇʀꜱ:",
            reply_markup=send_orders_markup
        )
        
        # Answer the callback
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        print(f"Error showing send orders menu: {e}")
        bot.answer_callback_query(call.id, "⚠️ Failed to load services", show_alert=True)

# ============================= VIP Banned Users List ============================= #
@bot.message_handler(func=lambda m: m.text == "📋 List Banned" and m.from_user.id in admin_user_ids)
def list_banned(message):
    """Show enhanced list of banned users"""
    banned_users = get_banned_users()
    
    if not banned_users:
        bot.reply_to(message,
            "🛡️ *Bᴀɴ Lɪꜱᴛ Sᴛᴀᴛᴜꜱ*\n\n"
            "Nᴏ ᴜꜱᴇʀꜱ ᴄᴜʀʀᴇɴᴛʟʏ ʀᴇꜱᴛʀɪᴄᴛᴇᴅ\n\n"
            "▸ Dᴀᴛᴀʙᴀꜱᴇ: 0 Entries\n"
            "▸ Lᴀꜱᴛ ʙᴀɴ: None",
            parse_mode="Markdown",
            reply_markup=admin_markup)
        return
    
    # Enhanced list formatting
    msg = [
        "⛔ *SMM Bᴏᴏꜱᴛᴇʀ Bᴀɴ Lɪꜱᴛ*\n",
        f"▸ Tᴏᴛᴀʟ Bᴀɴɴᴇᴅ: {len(banned_users)}",
        f"▸ Lᴀꜱᴛ Uᴘᴅᴀᴛᴇᴅ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    
    # Paginate if more than 10 banned users
    if len(banned_users) > 10:
        msg.append("\n*Showing first 10 entries:*\n")
        banned_users = banned_users[:10]
    
    for i, user_id in enumerate(banned_users, 1):
        try:
            user = bot.get_chat(user_id)
            name = user.first_name or f"User {user_id}"
            msg.append(f"{i}. {name} (`{user_id}`)")
        except:
            msg.append(f"{i}. User `{user_id}`")
    
    msg.append("\n🔍 Use /baninfo [ID] for details")
    
    bot.reply_to(message, "\n".join(msg), 
                parse_mode="Markdown",
                reply_markup=admin_markup)

# ============================= Premium Leaderboard ============================= #
@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def show_leaderboard(message):
    """Show VIP leaderboard with enhanced features"""
    top_users = get_top_users(10)
    
    if not top_users:
        bot.reply_to(message,
            "🌟 * SMM Bᴏᴏꜱᴛᴇʀ Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ*\n\n"
            "Nᴏ ᴏʀᴅᴇʀ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ʏᴇᴛ\n\n"
            "Bᴇ ᴛʜᴇ ꜰɪʀꜱᴛ ᴛᴏ ᴀᴘᴘᴇᴀʀ ʜᴇʀᴇ!",
            parse_mode="Markdown",
            reply_markup=main_markup)
        return
    
    leaderboard = [
        "🏆 *SMM Bᴏᴏꜱᴛᴇʀ Tᴏᴘ Cʟɪᴇɴᴛꜱ*",
        "Rᴀɴᴋᴇᴅ ʙʏ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ᴏʀᴅᴇʀꜱ\n",
        "━━━━━━━━━━━━━━━━━━━━"
    ]
    
    medal_emoji = ["🥇", "🥈", "🥉", "🔹", "🔹", "🔹", "🔹", "🔹", "🔹", "🔹"]
    
    for i, (user_id, count) in enumerate(top_users, 1):
        try:
            user = bot.get_chat(user_id)
            name = user.first_name or f"User {user_id}"
            leaderboard.append(f"{medal_emoji[i-1]} {name}: *{count}* orders")
        except:
            leaderboard.append(f"{medal_emoji[i-1]} User {user_id}: *{count}* orders")
    
    leaderboard.extend([
        "\n💎 *Vɪᴘ Bᴇɴᴇꜰɪᴛꜱ Aᴠᴀɪʟᴀʙʟᴇ*",
        "Tᴏᴘ 3 Cʟɪᴇɴᴛꜱ ɢᴇᴛ ᴍᴏɴᴛʜʟʏ ʙᴏɴᴜꜱᴇꜱ!"
    ])
    
    bot.reply_to(message, "\n".join(leaderboard),
                parse_mode="Markdown",
                reply_markup=main_markup)

#======================= Function to Pin Annoucement Messages ====================#
@bot.message_handler(func=lambda m: m.text == "📌 Pin Message" and m.from_user.id in admin_user_ids)
def pin_message_start(message):
    """Start pin message process"""
    msg = bot.reply_to(message, 
                      "📌 Sᴇɴᴅ ᴛʜᴇ ᴍᴇꜱꜱᴀɢᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴘɪɴ ɪɴ ᴀʟʟ ᴜꜱᴇʀꜱ' ᴄʜᴀᴛꜱ:\n\n"
                      "Tʏᴘᴇ 'Cancel' ᴛᴏ ᴀʙᴏʀᴛ.",
                      reply_markup=admin_markup)
    bot.register_next_step_handler(msg, process_pin_message)

def process_pin_message(message):
    """Process and send the pinned message to all users"""
    if message.text.lower() == "cancel":
        bot.reply_to(message, "❌ Pin cancelled.", reply_markup=admin_markup)
        return
    
    users = get_all_users()
    success, failed = 0, 0
    
    bot.reply_to(message, "⏳ Pɪɴɴɪɴɢ ᴍᴇꜱꜱᴀɢᴇꜱ...")
    
    for user_id in users:
        try:
            if message.content_type == 'text':
                sent = bot.send_message(user_id, message.text, parse_mode="Markdown")
            elif message.content_type == 'photo':
                sent = bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'document':
                sent = bot.send_document(user_id, message.document.file_id, caption=message.caption)
            else:
                continue

            bot.pin_chat_message(user_id, sent.message_id)
            save_pinned_message(user_id, sent.message_id)  # Save in MongoDB
            success += 1
        except Exception as e:
            print(f"Error pinning for {user_id}: {e}")
            failed += 1
        
        time.sleep(0.1)

    bot.reply_to(message, 
                 f"📌 𝗣𝗶𝗻𝗻𝗶𝗻𝗴 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲:\n"
                 f"✅ Successfully pinned in {success} chats\n"
                 f"❌ Failed in {failed} chats",
                 reply_markup=admin_markup)

# --- UNPIN Button Handler ---
@bot.message_handler(func=lambda m: m.text == "📍 Unpin" and m.from_user.id in admin_user_ids)
def unpin_and_delete_all(message):
    """Unpin and delete pinned messages for all users"""
    
    # Give guidance first
    confirm_msg = bot.reply_to(
        message,
        "📍 You are about to unpin and delete pinned messages from ALL users.\n\n"
        "⚠️ This action cannot be undone.\n\n"
        "➤ Type 'CONFIRM' to proceed or 'Cancel' to abort."
    )
    bot.register_next_step_handler(confirm_msg, confirm_unpin_process)

def confirm_unpin_process(message):
    """Confirm and perform the unpinning"""
    if message.text.strip().lower() != "confirm":
        bot.reply_to(message, "❌ Unpin cancelled.", reply_markup=admin_markup)
        return
    
    users_pins = get_all_pinned_messages()
    success, failed = 0, 0
    
    bot.reply_to(message, "⏳ Unpinning and deleting pinned messages...")
    
    for user_id, message_id in users_pins.items():
        try:
            bot.unpin_chat_message(user_id, message_id=message_id)
            bot.delete_message(user_id, message_id)
            success += 1
        except Exception as e:
            print(f"Error unpinning for {user_id}: {e}")
            failed += 1
        
        time.sleep(0.1)
    
    clear_all_pinned_messages()  # Clear from MongoDB
    
    bot.reply_to(message,
                 f"📌 𝗨ɴᴘɪɴɴɪɴɢ 𝗖𝗼𝗺𝗽𝗹𝗲𝘁𝗲:\n"
                 f"✅ Successfully unpinned and deleted in {success} chats\n"
                 f"❌ Failed in {failed} chats",
                 reply_markup=admin_markup)



#================= Check User Info by ID ===================================#
@bot.message_handler(func=lambda m: m.text == "👤 User Info" and m.from_user.id in admin_user_ids)
def user_info_start(message):
    msg = bot.reply_to(message, "Enter user ID or username (@username):")
    bot.register_next_step_handler(msg, process_user_info)

def process_user_info(message):
    query = message.text.strip()
    try:
        if query.startswith('@'):
            user = bot.get_chat(query)
            user_id = user.id
        else:
            user_id = int(query)
            user = bot.get_chat(user_id)
        
        user_data = getData(user_id) or {}
        
        info = f"""
<blockquote>
┌──────────────────────
│ 🔍 <b>𝗨𝘀𝗲𝗿 𝗜𝗻𝗳𝗼𝗿𝗺𝗮𝘁𝗶𝗼𝗻</b>:
│ ━━━━━━━━━━━━━━━━━━━━━━
│ 🆔 Iᴅ: <code>{user_id}</code>
│ 👤 Nᴀᴍᴇ: {user.first_name} {user.last_name or ''}
│ 📛 Uꜱᴇʀɴᴀᴍᴇ: @{user.username if user.username else 'N/A'}
│ 💰 Bᴀʟᴀɴᴄᴇ: {user_data.get('balance', 0)}
│ 📊 Oʀᴅᴇʀꜱ: {user_data.get('orders_count', 0)}
│ 👥 Rᴇꜰᴇʀʀᴀʟꜱ: {user_data.get('total_refs', 0)}
│ 🔨 Sᴛᴀᴛᴜꜱ: {"BANNED ⛔" if is_banned(user_id) else "ACTIVE ✅"}
└─────────────────────
</blockquote>
        """
        bot.reply_to(message, info, parse_mode="HTML")
    except ValueError:
        bot.reply_to(message, "❌ Invalid user ID. Must be numeric.")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

#============================== Server Status Command ===============================#
@bot.message_handler(func=lambda m: m.text == "🖥 Server Status" and m.from_user.id in admin_user_ids)
def server_status(message):
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
<blockquote>
┌─────────────────────
│ 🖥 <b>𝙎𝙮𝙨𝙩𝙚𝙢 𝙎𝙩𝙖𝙩𝙪𝙨</b>
│ ━━━━━━━━━━━━━━━━━━━━━━
│ 💻 <b>Sʏꜱᴛᴇᴍ</b>: {uname.system} {uname.release}
│ ⏱ <b>Uᴘᴛɪᴍᴇ</b>: {datetime.now() - boot_time}
│ ━━━━━━━━━━━━━━━━━━━━━━
│ 🧠 <b>Cᴘᴜ</b>: {psutil.cpu_percent()}% usage
│ 💾 <b>Mᴇᴍᴏʀʏ</b>: {mem.used/1024/1024:.1f}MB / {mem.total/1024/1024:.1f}MB
│ 🗄 <b>Dɪꜱᴋ</b>: {disk.used/1024/1024:.1f}MB / {disk.total/1024/1024:.1f}MB
│ ━━━━━━━━━━━━━━━━━━━━━━
│ 📊 <b>𝙈𝙤𝙣𝙜𝙤𝘿𝘽 𝙎𝙩𝙖𝙩𝙨</b>
│ 📦 Dᴀᴛᴀ ꜱɪᴢᴇ: {mongo_stats['dataSize']/1024/1024:.1f}MB
│ 🗃 Sᴛᴏʀᴀɢᴇ: {mongo_stats['storageSize']/1024/1024:.1f}MB
│ 📂 Cᴏʟʟᴇᴄᴛɪᴏɴꜱ: {mongo_stats['collections']}
└─────────────────────
</blockquote>
        """
        bot.reply_to(message, status, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"❌ Error getting status: {str(e)}")

#========================== Export User Data (CSV) =================#
@bot.message_handler(func=lambda m: m.text == "📤 Export Data" and m.from_user.id in admin_user_ids)
def export_data(message):
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
        bot.send_document(
            message.chat.id,
            ('users_export.csv', output.getvalue()),
            caption="📊 Uꜱᴇʀ Dᴀᴛᴀ Exᴘᴏʀᴛ"
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Export failed: {str(e)}")

#======================= Maintenance Mode command ==================================#

# Add this at the top with other global variables
maintenance_mode = False
maintenance_message = "🚧 𝙏𝙝𝙚 𝙗𝙤𝙩 𝙞𝙨 𝙘𝙪𝙧𝙧𝙚𝙣𝙩𝙡𝙮 𝙪𝙣𝙙𝙚𝙧 𝙢𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚. 𝙋𝙡𝙚𝙖𝙨𝙚 𝙩𝙧𝙮 𝙖𝙜𝙖𝙞𝙣 𝙡𝙖𝙩𝙚𝙧."

# Maintenance toggle command
@bot.message_handler(func=lambda m: m.text == "🔧 Maintenance" and m.from_user.id in admin_user_ids)
def toggle_maintenance(message):
    global maintenance_mode, maintenance_message
    
    if maintenance_mode:
        maintenance_mode = False
        bot.reply_to(message, "✅ 𝙈𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚 𝙢𝙤𝙙𝙚 𝘿𝙄𝙎𝘼𝘽𝙇𝙀𝘿")
    else:
        msg = bot.reply_to(message, "✍️ Eɴᴛᴇʀ Mᴀɪɴᴛᴇɴᴀɴᴄᴇ Mᴇꜱꜱᴀɢᴇ Tᴏ Sᴇɴᴅ Tᴏ Uꜱᴇʀꜱ:")
        bot.register_next_step_handler(msg, set_maintenance_message)

def set_maintenance_message(message):
    global maintenance_mode, maintenance_message
    maintenance_message = message.text
    maintenance_mode = True
    
    # Send to all users
    users = get_all_users()
    sent = 0
    for user_id in users:
        try:
            bot.send_message(user_id, f"⚠️ 𝙈𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚 𝙉𝙤𝙩𝙞𝙘𝙚:\n{maintenance_message}")
            sent += 1
            time.sleep(0.1)
        except:
            continue
    
    bot.reply_to(message, f"🔧 𝙈𝙖𝙞𝙣𝙩𝙚𝙣𝙖𝙣𝙘𝙚 𝙢𝙤𝙙𝙚 𝙀𝙉𝘼𝘽𝙇𝙀𝘿\nMessage sent to {sent} users")

def auto_disable_maintenance():
    global maintenance_mode
    time.sleep(3600)  # 1 hour
    maintenance_mode = False

# Then in set_maintenance_message():
threading.Thread(target=auto_disable_maintenance).start()

#============================ Order Management Commands =============================#
@bot.message_handler(func=lambda m: m.text == "📦 Order Manager" and m.from_user.id in admin_user_ids)
def check_order_start(message):
    msg = bot.reply_to(message, "Enter Order ID:")
    bot.register_next_step_handler(msg, process_check_order)

def process_check_order(message):
    order_id = message.text.strip()
    try:
        from functions import orders_collection
        order = orders_collection.find_one({"order_id": order_id})
        
        if order:
            status_time = datetime.fromtimestamp(order.get('timestamp', time.time())).strftime('%Y-%m-%d %H:%M')
            status = f"""
<blockquote>
┌─────────────────────
│ 📦 <b>Order #{order_id}</b>
│ ━━━━━━━━━━━━━━
│ 👤 Uꜱᴇʀ: {order.get('username', 'N/A')} (<code>{order.get('user_id', 'N/A')}</code>)
│ 🛒 Sᴇʀᴠɪᴄᴇ: {order.get('service', 'N/A')}
│ 🔗 Lɪɴᴋ: {order.get('link', 'N/A')}
│ 📊 Qᴜᴀɴᴛɪᴛʏ: {order.get('quantity', 'N/A')}
│ 💰 Cᴏꜱᴛ: {order.get('cost', 'N/A')}
│ 🔄 Sᴛᴀᴛᴜꜱ: {order.get('status', 'N/A')}
│ ⏱ Dᴀᴛᴇ: {status_time}
└─────────────────────
</blockquote>
            """
            bot.reply_to(message, status, parse_mode="HTML", disable_web_page_preview=True)
        else:
            bot.reply_to(message, "❌ Order not found")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")


#========================== Add this handler for the /policy command =================#

@bot.message_handler(commands=['policy'])
def policy_command(message):
    """Show the bot's usage policy"""
    policy_text = """
<blockquote>
📜 <b> Bᴏᴛ Uꜱᴀɢᴇ Pᴏʟɪᴄʏ & Gᴜɪᴅᴇʟɪɴᴇꜱ</b>
━━━━━━━━━━━━━━━━━━━━

🔹 <b>1. Aᴄᴄᴇᴘᴛᴀʙʟᴇ Uꜱᴇ</b>
  ├ ✅ Pᴇʀᴍɪᴛᴛᴇᴅ: Lᴇɢᴀʟ, ɴᴏɴ-ʜᴀʀᴍꜰᴜʟ ᴄᴏɴᴛᴇɴᴛ
  └ ❌ Pʀᴏʜɪʙɪᴛᴇᴅ: Sᴘᴀᴍ, ʜᴀʀᴀꜱꜱᴍᴇɴᴛ, ɪʟʟᴇɢᴀʟ ᴍᴀᴛᴇʀɪᴀʟ

🔹 <b>2. Fᴀɪʀ Uꜱᴀɢᴇ Pᴏʟɪᴄʏ</b>
   ├ ⚖️ Aʙᴜꜱᴇ ᴍᴀʏ ʟᴇᴀᴅ ᴛᴏ ʀᴇꜱᴛʀɪᴄᴛɪᴏɴꜱ
   └ 📊 Exᴄᴇꜱꜱɪᴠᴇ ᴜꜱᴀɢᴇ ᴍᴀʏ ʙᴇ ʀᴀᴛᴇ-ʟɪᴍɪᴛᴇᴅ

🔹 <b>3. Fɪɴᴀɴᴄɪᴀʟ Pᴏʟɪᴄʏ</b>
   ├ 💳 Aʟʟ ᴛʀᴀɴꜱᴀᴄᴛɪᴏɴꜱ ᴀʀᴇ ꜰɪɴᴀʟ
   └ 🔄 Nᴏ ʀᴇꜰᴜɴᴅꜱ ꜰᴏʀ ᴄᴏᴍᴘʟᴇᴛᴇᴅ ꜱᴇʀᴠɪᴄᴇꜱ

🔹 <b>4. Pʀɪᴠᴀᴄʏ Cᴏᴍᴍɪᴛᴍᴇɴᴛ</b>
   ├ 🔒 Yᴏᴜʀ ᴅᴀᴛᴀ ꜱᴛᴀʏꜱ ᴄᴏɴꜰɪᴅᴇɴᴛɪᴀʟ
   └ 🤝 Nᴇᴠᴇʀ ꜱʜᴀʀᴇᴅ ᴡɪᴛʜ ᴛʜɪʀᴅ ᴘᴀʀᴛɪᴇꜱ

🔹 <b>5. Pʟᴀᴛꜰᴏʀᴍ Cᴏᴍᴘʟɪᴀɴᴄᴇ</b>
   ├ ✋ Mᴜꜱᴛ ꜰᴏʟʟᴏᴡ Tᴇʟᴇɢʀᴀᴍ'ꜱ TᴏS
   └ 🌐 Aʟʟ ᴄᴏɴᴛᴇɴᴛ ᴍᴜꜱᴛ ʙᴇ ʟᴇɢᴀʟ ɪɴ ʏᴏᴜʀ ᴊᴜʀɪꜱᴅɪᴄᴛɪᴏɴ

⚠️ <b>CᴏɴꜱᴇQᴜᴇɴᴄᴇꜱ ᴏꜰ Vɪᴏʟᴀᴛɪᴏɴ</b>
   ├ ⚠️ Fɪʀꜱᴛ ᴏꜰꜰᴇɴꜱᴇ: Wᴀʀɴɪɴɢ
   ├ 🔇 Rᴇᴘᴇᴀᴛᴇᴅ ᴠɪᴏʟᴀᴛɪᴏɴꜱ: Tᴇᴍᴘᴏʀᴀʀʏ ꜱᴜꜱᴘᴇɴꜱɪᴏɴ
   └ 🚫 Sᴇᴠᴇʀᴇ ᴄᴀꜱᴇꜱ: Pᴇʀᴍᴀɴᴇɴᴛ ʙᴀɴ

📅 <i> Lᴀꜱᴛ ᴜᴘᴅᴀᴛᴇᴅ: {update_date}</i>
━━━━━━━━━━━━━━━━━━━━
💡 Nᴇᴇᴅ ʜᴇʟᴘ? Cᴏɴᴛᴀᴄᴛ @SocialHubBoosterTMbot
</blockquote>
""".format(update_date=datetime.now().strftime('%Y-%m-%d'))  # Fixed datetime reference
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="✅ Accept Policy", callback_data="accept_policy"))
    
    bot.reply_to(message, policy_text, parse_mode="HTML", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "accept_policy")
def accept_policy_callback(call):
    bot.answer_callback_query(
        call.id,
        text="🙏 Tʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ʏᴏᴜʀ Cᴏᴏᴘᴇʀᴀᴛɪᴏɴ!",
        show_alert=True
    )

    try:
        # Remove the button
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=None
        )

        # Delete the message after a short delay (optional)
        bot.delete_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
    except Exception as e:
        print(f"Error deleting policy message: {e}")




#======================= Function to periodically check order status ====================#
def update_order_statuses():
    """Periodically check SMM panel and update order statuses in MongoDB"""
    try:
        # Get pending/processing orders from MongoDB
        pending_orders = orders_collection.find({
            "status": {"$in": ["pending", "processing"]}
        })
        
        for order in pending_orders:
            # Check status with SMM panel API
            response = requests.post(
                SmmPanelApiUrl,
                data={
                    'key': SmmPanelApi,
                    'action': 'status',
                    'order': order['order_id']
                }
            )
            result = response.json()
            
            # Update status in MongoDB if different
            if result.get('status') and result['status'] != order['status']:
                orders_collection.update_one(
                    {"_id": order['_id']},
                    {"$set": {"status": result['status'].lower()}}
                )
                
    except Exception as e:
        print(f"Error updating order statuses: {e}")

def status_updater():
    while True:
        update_order_statuses()
        time.sleep(300)  # Check every 5 minutes

# Start the updater in a separate thread
Thread(target=status_updater, daemon=True).start()

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
<blockquote>
🚀 <b>Bᴏᴛ {status}</b> !

📅 Dᴀᴛᴇ : {dt['date']}
⏰ Tɪᴍᴇ : {dt['time']}
🌐 Tɪᴍᴇᴢᴏɴᴇ : {dt['timezone']}
🛠️ Bᴜɪʟᴅ Sᴛᴀᴛᴜs: v2 [ Sᴛᴀʙʟᴇ ]
</blockquote>
"""
        bot.send_message(
            chat_id=payment_channel,  # Or your specific logs channel ID
            text=message,
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending startup message: {e}")
      
#========= Send Notification with image ==========#
def get_profile_photo(user_id):
    """Download and process profile photo"""
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if not photos.photos:
            raise Exception("No profile photo available")
            
        file_info = bot.get_file(photos.photos[0][-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(f"{user_id}.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)
            
        original_img = Image.open(f"{user_id}.jpg").convert("RGB")
        
        # Create circular mask
        size = (500, 500)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size[0], size[1]), fill=255)
        
        # Resize and apply mask
        img = ImageOps.fit(original_img, size, method=Image.LANCZOS)
        img.putalpha(mask)
        
        os.remove(f"{user_id}.jpg")
        return img
    except Exception as e:
        print(f"Using default profile photo: {e}")
        # Create default gray circle (now matching the 500x500 size)
        img = Image.new("RGBA", (500, 500), (70, 70, 70, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse((0, 0, 500, 500), fill=(100, 100, 100, 255))
        return img

def generate_notification_image(user_img, bot_img, user_name, bot_name, service_name):
    """Generate a pro-quality notification image."""
    try:
        # Create base image with rich gradient background
        width, height = 800, 400
        bg = Image.new("RGB", (width, height), (30, 30, 45))
        gradient = Image.new("L", (1, height), color=0xFF)

        for y in range(height):
            gradient.putpixel((0, y), int(255 * (1 - y/height)))
        alpha_gradient = gradient.resize((width, height))
        black_img = Image.new("RGB", (width, height), color=(10, 10, 25))
        bg = Image.composite(bg, black_img, alpha_gradient)

        draw = ImageDraw.Draw(bg)

        # Fonts - added fallback for each font individually
        try:
            title_font = ImageFont.truetype("arialbd.ttf", 40)
        except:
            title_font = ImageFont.load_default().font_variant(size=40)
            
        try:
            name_font = ImageFont.truetype("arialbd.ttf", 28)
        except:
            name_font = ImageFont.load_default().font_variant(size=28)
            
        try:
            service_font = ImageFont.truetype("arialbd.ttf", 24)
        except:
            service_font = ImageFont.load_default().font_variant(size=24)

        # Draw top title
        draw.text((width // 2, 40), "NEW ORDER NOTIFICATION", font=title_font,
                 fill="white", anchor="mm")

        # Helper to draw glowing circular image
        def draw_glowing_circle(base, img, pos, size, glow_color=(255, 215, 0)):
            glow = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            center = (glow.size[0] // 2, glow.size[1] // 2)

            for radius in range(size // 2 + 10, size // 2 + 20):
                glow_draw.ellipse([
                    center[0] - radius, center[1] - radius,
                    center[0] + radius, center[1] + radius
                ], fill=glow_color + (10,), outline=None)

            glow = glow.filter(ImageFilter.GaussianBlur(8))
            base.paste(glow, (pos[0] - 20, pos[1] - 20), glow)

            # Golden ring
            ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            ring_draw = ImageDraw.Draw(ring)
            ring_draw.ellipse((0, 0, size - 1, size - 1), outline=(255, 215, 0), width=6)

            # Add mask to image (ensure we're working with RGBA)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img = img.resize((size, size))
            mask = Image.new('L', (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, size, size), fill=255)
            img.putalpha(mask)

            base.paste(img, pos, img)
            base.paste(ring, pos, ring)

        # Paste profile images
        user_pos = (130, 120)
        bot_pos = (520, 120)
        draw_glowing_circle(bg, user_img, user_pos, 150)
        draw_glowing_circle(bg, bot_img, bot_pos, 150)

        # Draw usernames (with text length safety)
        max_name_length = 15
        safe_user_name = (user_name[:max_name_length] + '..') if len(user_name) > max_name_length else user_name
        safe_bot_name = (bot_name[:max_name_length] + '..') if len(bot_name) > max_name_length else bot_name
        
        draw.text((user_pos[0] + 75, 290), safe_user_name, font=name_font,
                 fill="white", anchor="ma")
        draw.text((bot_pos[0] + 75, 290), safe_bot_name, font=name_font,
                 fill="white", anchor="ma")

        # Draw service name in the middle (with safety check)
        max_service_length = 30
        safe_service_name = (service_name[:max_service_length] + '..') if len(service_name) > max_service_length else service_name
        draw.text((width // 2, 330), f"Service: {safe_service_name}", font=service_font,
                 fill=(255, 215, 0), anchor="ma")

        # Bottom banner
        draw.rectangle([0, 370, width, 400], fill=(255, 215, 0))
        draw.text((width // 2, 385), "Powered by SMMHub Booster", font=name_font,
                 fill=(30, 30, 30), anchor="mm")

        output_path = f"order_{user_name[:50]}.png"  # Limit filename length
        bg.save(output_path, quality=95)
        return output_path

    except Exception as e:
        print(f"Image generation error: {e}")
        return None
# ==================== FLASK INTEGRATION ==================== #

# Configure API helper settings
telebot.apihelper.READ_TIMEOUT = 30
telebot.apihelper.CONNECT_TIMEOUT = 10
telebot.apihelper.RETRY_ON_ERROR = True
telebot.apihelper.MAX_RETRIES = 3


log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# File handler with rotation
file_handler = RotatingFileHandler('bot.log', maxBytes=5*1024*1024, backupCount=3)
file_handler.setFormatter(log_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Get logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[408, 429, 500, 502, 503, 504]
)

session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

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
        "memory_usage": f"{psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.2f} MB",
        "active_threads": threading.active_count()
    }), 200

@web_app.route('/ping')
def ping():
    """Endpoint for keep-alive pings"""
    return "pong", 200

def notify_admins(message):
    """Helper function to notify admins of errors"""
    for admin_id in admin_user_ids:
        try:
            bot.send_message(
                admin_id,
                f"⚠️ Bot Notification ⚠️\n\n{message}",
                parse_mode='HTML'
            )
            break  # Notify just one admin to avoid rate limits
        except Exception as admin_error:
            logger.error(f"Failed to notify admin {admin_id}: {admin_error}")

# ==================== KEEP-ALIVE SYSTEM ==================== #
def keep_alive():
    """Pings the server periodically to prevent shutdown"""
    while True:
        try:
            # Ping our own health endpoint
            session.get(f'http://localhost:{os.getenv("PORT", "10000")}/ping', timeout=5)
            # Optionally ping external services
            session.get('https://www.google.com', timeout=5)
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        time.sleep(300)  # Ping every 5 minutes

# ==================== BOT POLLING ==================== #
def run_bot():
    set_bot_commands()
    logger.info("Bot is starting...")
    
    # Initial delay to prevent immediate restart storms
    time.sleep(10)
    
    while True:
        try:
            logger.info("Starting bot polling...")
            # Use skip_pending=True to skip old updates after restart
            bot.polling(none_stop=True, timeout=30, skip_pending=True)
            
        except ConnectionError as e:
            error_msg = f"Connection error: {e}. Reconnecting in 30 seconds..."
            logger.warning(error_msg)
            notify_admins(error_msg)
            time.sleep(30)
            
        except telebot.apihelper.ApiException as e:
            error_msg = f"Telegram API error: {str(e)[:200]}"
            logger.warning(error_msg)
            time.sleep(30)
            
        except Exception as e:
            error_msg = f"Bot polling failed: {str(e)[:200]}"
            logger.error(error_msg)
            
            # Don't notify for common, expected errors
            if not isinstance(e, (ConnectionError, telebot.apihelper.ApiException)):
                notify_admins(error_msg)
                
            # Longer delay for more serious errors
            time.sleep(30)
            
        # Small delay before restarting to prevent tight loops
        time.sleep(5)

# ==================== MAIN EXECUTION ==================== #
if __name__ == '__main__':
    try:
        logger.info("Initializing bot...")
        
        # Start keep-alive thread
        keep_alive_thread = threading.Thread(target=keep_alive)
        keep_alive_thread.daemon = True
        keep_alive_thread.start()
        
        # Start bot in background thread
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        # Configure Flask server
        logger.info("Starting Flask server...")
        web_app.run(
            host='0.0.0.0',
            port=int(os.getenv('PORT', '10000')),
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.critical(f"Fatal error in main execution: {e}")
        notify_admins(f"Bot crashed: {str(e)[:200]}")
        raise
