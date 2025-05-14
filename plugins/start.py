# +++ Made By Obito [telegram username: @i_killed_my_clan] +++ #
import os
import asyncio
import sys
import time
import base64
from collections import defaultdict
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, UserNotParticipant, ChatIdInvalid

from bot import Bot
from datetime import datetime, timedelta
from config import ADMINS, OWNER_ID
from helper_func import encode, decode
from database.database import save_encoded_link, get_channel_by_encoded_link, save_encoded_link2, get_channel_by_encoded_link2
from database.database import add_user, del_user, full_userbase, present_user, is_admin
from plugins.newpost import revoke_invite_after_10_minutes
        
#=====================================================================================##

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Bot, message: Message):
    user_id = message.from_user.id

    # Check if the user is banned
    if user_id in user_banned_until:
        # Check if the ban duration has not expired
        if datetime.now() < user_banned_until[user_id]:
            # User is still banned, do not process the command
            return await message.reply_text("<b><blockquote expandable>»  Yᴏᴜ ᴀʀᴇ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴄᴏᴍᴍᴀɴᴅs ᴅᴜᴇ ᴛᴏ sᴘᴀᴍᴍɪɴɢ. Tʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")

    # Proceed with the original functionality if the user is not banned
    text = message.text
    await add_user(user_id)  # Add user to DB
    
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            is_request = base64_string.startswith("req_")
            
            if is_request:
                base64_string = base64_string[4:]
                channel_id = await get_channel_by_encoded_link2(base64_string)
            else:
                channel_id = await get_channel_by_encoded_link(base64_string)
            
            if not channel_id:
                return await message.reply_text("<b><blockquote expandable>» Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ")
            
            invite = await client.create_chat_invite_link(
                chat_id=channel_id,
                expire_date=datetime.now() + timedelta(minutes=10),
                creates_join_request=is_request
            )

            button_text = "• Rᴇǫᴜᴇsᴛ ᴛᴏ Jᴏɪɴ •" if is_request else "• Jᴏɪɴ Cʜᴀɴɴᴇʟ •"
            button = InlineKeyboardMarkup([[InlineKeyboardButton(button_text, url=invite.invite_link)]])

            await message.reply_text("<b>➪ Hᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ! Cʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ •<b>", reply_markup=button)

            asyncio.create_task(revoke_invite_after_10_minutes(client, channel_id, invite.invite_link, is_request))

        except Exception as e:
            await message.reply_text("<b>Iɴᴠᴀʟɪᴅ ᴏʀ ᴇxᴘɪʀᴇᴅ ɪɴᴠɪᴛᴇ ʟɪɴᴋ.<b>")
            print(f"Decoding error: {e}")
    else:
        inline_buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="help"),
                InlineKeyboardButton("ᴄʟᴏsᴇ •", callback_data="close")]
            ]
        )
        
        await message.reply_text(
            "<b><blockquote expandable>{fisrt} Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴅᴠᴀɴᴄᴇᴅ ʟɪɴᴋs sʜᴀʀɪɴɢ ʙᴏᴛ./nWɪᴛʜ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ sʜᴀʀᴇ ʟɪɴᴋs ᴀɴᴅ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs sᴀғᴇ ғʀᴏᴍ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs: ᴄʀᴇᴀᴛᴇᴅ ʙʏ: <a href=https://t.me/i_killed_my_clan>ᴏʙɪᴛᴏ</a><b>",
            reply_markup=inline_buttons
        )
        
#=====================================================================================##

WAIT_MSG = """"<b>Processing ....</b>"""

REPLY_ERROR = """<code>Use this command as a reply to any telegram message with out any spaces.</code>"""

#=====================================================================================##

@Bot.on_message(filters.command('status') & filters.private & is_admin)
async def info(client: Bot, message: Message):   
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Cʟᴏsᴇ ✖️", callback_data = "close")]])
    
    start_time = time.time()
    temp_msg = await message.reply("<b><i>Pʀᴏᴄᴇssɪɴɢ....</i></b>", quote=True)  # Temporary message
    end_time = time.time()
    
    # Calculate ping time in milliseconds
    ping_time = (end_time - start_time) * 1000
    
    users = await kingdb.full_userbase()
    now = datetime.now()
    delta = now - client.uptime
    bottime = get_readable_time(delta.seconds)
    
    await temp_msg.edit(f"🚻 : <b>{len(users)} USERS\n\n🤖 UPTIME » {bottime}\n\n📡 PING » {ping_time:.2f} ms</b>", reply_markup = reply_markup,)


#=====================================================================================##
@Bot.on_message(filters.command('broadcast') & filters.private & is_admin)
async def send_text(client: Bot, message: Message):
    global is_canceled
    async with cancel_lock:
        is_canceled = False
    mode = False
    broad_mode = ''
    store = message.text.split()[1:]
    
    if store and len(store) == 1 and store[0] == 'silent':
        mode = True
        broad_mode = 'SILENT '

    if message.reply_to_message:
        query = await kingdb.full_userbase()
        broadcast_msg = message.reply_to_message
        total = len(query)
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ Mᴇssᴀɢᴇ... Tʜɪs ᴡɪʟʟ ᴛᴀᴋᴇ sᴏᴍᴇ ᴛɪᴍᴇ.</i>")
        bar_length = 20
        final_progress_bar = "●" * bar_length
        complete_msg = f"🤖 {broad_mode}BROADCAST COMPLETED ✅"
        progress_bar = ''
        last_update_percentage = 0
        percent_complete = 0
        update_interval = 0.05  # Update progress bar every 5%

        for i, chat_id in enumerate(query, start=1):
            async with cancel_lock:
                if is_canceled:
                    final_progress_bar = progress_bar
                    complete_msg = f"🤖 {broad_mode}BROADCAST CANCELED ❌"
                    break
            try:
                await broadcast_msg.copy(chat_id, disable_notification=mode)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id, disable_notification=mode)
                successful += 1
            except UserIsBlocked:
                await kingdb.del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await kingdb.del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1

            # Calculate percentage complete
            percent_complete = i / total

            # Update progress bar
            if percent_complete - last_update_percentage >= update_interval or last_update_percentage == 0:
                num_blocks = int(percent_complete * bar_length)
                progress_bar = "●" * num_blocks + "○" * (bar_length - num_blocks)
    
                # Send periodic status updates
                status_update = f"""<b>🤖 {broad_mode}BROADCAST IN PROGRESS...

<blockquote>⏳:</b> [{progress_bar}] <code>{percent_complete:.0%}</code></blockquote>

<b>🚻 Tᴏᴛᴀʟ Usᴇʀs: <code>{total}</code>
✅ Sᴜᴄᴄᴇssғᴜʟ: <code>{successful}</code>
🚫 Bʟᴏᴄᴋᴇᴅ Usᴇʀs: <code>{blocked}</code>
⚠️ Dᴇʟᴇᴛᴇᴅ Aᴄᴄᴏᴜɴᴛs: <code>{deleted}</code>
❌ Uɴsᴜᴄᴄᴇssғᴜʟ: <code>{unsuccessful}</code></b>

<i>➪ Tᴏ sᴛᴏᴘ ᴛʜᴇ ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ᴄʟɪᴄᴋ: <b>/cancel</b></i>"""
                await pls_wait.edit(status_update)
                last_update_percentage = percent_complete

        # Final status update
        final_status = f"""<b>{complete_msg}

<blockquote>Dᴏɴᴇ:</b> [{final_progress_bar}] {percent_complete:.0%}</blockquote>

<b>🚻 Tᴏᴛᴀʟ Usᴇʀs: <code>{total}</code>
✅ Sᴜᴄᴄᴇssғᴜʟ: <code>{successful}</code>
🚫 Bʟᴏᴄᴋᴇᴅ Usᴇʀs: <code>{blocked}</code>
⚠️ Dᴇʟᴇᴛᴇᴅ Aᴄᴄᴏᴜɴᴛs: <code>{deleted}</code>
❌ Uɴsᴜᴄᴄᴇssғᴜʟ: <code>{unsuccessful}</code></b>"""
        return await pls_wait.edit(final_status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
            
#=====================================================================================##

@Bot.on_callback_query(filters.regex("help"))
async def help_callback(client: Bot, callback_query):
    # Define the inline keyboard with the "Close" button
    inline_buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data="close")]
        ]
    )
    
    
    await callback_query.answer()
    await callback_query.message.edit_text("<b><blockquote expandable>» ᴄʀᴇᴀᴛᴏʀ: <a href=https://t.me/i_killed_my_clan>ᴏʙɪᴛᴏ</a>\n» ᴏᴜʀ ᴄᴏᴍᴍᴜɴɪᴛʏ : <a href=https://t.me/society_network>sᴏᴄɪᴇᴛʏ ɴᴇᴛᴡᴏʀᴋ</a>\n» ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ : <a href=https://t.me/animes_sub_society>ᴀɴɪᴍᴇ sᴏᴄɪᴇᴛʏ </a>\n» ᴏɴɢᴏɪɴɢ sᴏᴄɪᴇᴛʏ : <a href=https://t.me/Ongoiing_society>ᴏɴɢᴏɪɴɢ sᴏᴄɪᴇᴛʏ</a>\n» ᴍᴀɴɢᴀ sᴏᴄɪᴇᴛʏ : <a href=https://t.me/Manga_X_Society>ᴍᴀɴɢᴀ sᴏᴄɪᴇᴛʏ</a>\n» ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href=https://t.me/i_killed_my_clan>ᴏʙɪᴛᴏ</a></blockquote></b>", reply_markup=inline_buttons)

@Bot.on_callback_query(filters.regex("close"))
async def close_callback(client: Bot, callback_query):
    await callback_query.answer()
    await callback_query.message.delete()

#=====================================================================================##


user_message_count = {}
user_banned_until = {}

MAX_MESSAGES = 3
TIME_WINDOW = timedelta(seconds=10)  # Capturing frames
BAN_DURATION = timedelta(hours=1)  # User ko ban rakhne ka time. hours ko minutes karlena

@Bot.on_message(filters.private)
async def monitor_messages(client: Bot, message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    if user_id in ADMINS:
        return 

    
    if user_id in user_banned_until and now < user_banned_until[user_id]:
        await message.reply_text("<b><blockquote expandable>» Yᴏᴜ ᴀʀᴇ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴄᴏᴍᴍᴀɴᴅs ᴅᴜᴇ ᴛᴏ sᴘᴀᴍᴍɪɴɢ. Tʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")
        return

    if user_id not in user_message_count:
        user_message_count[user_id] = []

    user_message_count[user_id].append(now)

    user_message_count[user_id] = [time for time in user_message_count[user_id] if now - time <= TIME_WINDOW]

    if len(user_message_count[user_id]) > MAX_MESSAGES:
        user_banned_until[user_id] = now + BAN_DURATION
        await message.reply_text("<b><blockquote expandable>» Yᴏᴜ ᴀʀᴇ ᴛᴇᴍᴘᴏʀᴀʀɪʟʏ ʙᴀɴɴᴇᴅ ғʀᴏᴍ ᴜsɪɴɢ ᴄᴏᴍᴍᴀɴᴅs ᴅᴜᴇ ᴛᴏ sᴘᴀᴍᴍɪɴɢ. Tʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.")
        return
