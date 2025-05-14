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

# plugins/start.py
import asyncio
import base64
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait

from bot import Bot
from datetime import datetime, timedelta
from config import ADMINS, OWNER_ID
from database.database import save_encoded_link, get_channel_by_encoded_link, save_encoded_link2, get_channel_by_encoded_link2
from database.database import add_user
from database.database import save_invite_link, get_current_invite_link
from plugins.newpost import revoke_invite_after_5_minutes

# Start picture file ID (replace with actual file ID)
START_PIC_FILE_ID = "AgACAgUAAxkBAAIBEWcO2rKz5z8AAV0Qz4m7f3qJAAH9EAACi7gxG3-VmVqL4W3rAAK5AAQBAAMCAAN4AAM1BA"

user_banned_until = {}

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Bot, message: Message):
    user_id = message.from_user.id

    if user_id in user_banned_until:
        if datetime.now() < user_banned_until[user_id]:
            return await message.reply_text(
                "<b>You are temporarily banned from using commands due to spamming. Try again later.</b>",
                parse_mode=ParseMode.HTML
            )

    await add_user(user_id)

    text = message.text
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
                return await message.reply_text(
                    "<b>Invalid or expired invite link.</b>",
                    parse_mode=ParseMode.HTML
                )
            
            old_link_info = await get_current_invite_link(channel_id)
            if old_link_info:
                try:
                    await client.revoke_chat_invite_link(channel_id, old_link_info["invite_link"])
                    print(f"Revoked old {'request' if old_link_info['is_request'] else 'invite'} link for channel {channel_id}")
                except Exception as e:
                    print(f"Failed to revoke old link for channel {channel_id}: {e}")

            invite = await client.create_chat_invite_link(
                chat_id=channel_id,
                expire_date=datetime.now() + timedelta(minutes=5),
                creates_join_request=is_request
            )

            await save_invite_link(channel_id, invite.invite_link, is_request)

            button_text = "Request to Join" if is_request else "Join Channel"
            button = InlineKeyboardMarkup([[InlineKeyboardButton(button_text, url=invite.invite_link)]])

            await message.reply_text(
                "<b>Here is your link! Click below to proceed:</b>",
                reply_markup=button,
                parse_mode=ParseMode.HTML
            )

            asyncio.create_task(revoke_invite_after_5_minutes(client, channel_id, invite.invite_link, is_request))

        except Exception as e:
            await message.reply_text(
                "<b>Invalid or expired invite link.</b>",
                parse_mode=ParseMode.HTML
            )
            print(f"Decoding error: {e}")
    else:
        inline_buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("About", callback_data="help"),
                 InlineKeyboardButton("Close", callback_data="close")]
            ]
        )
        
        welcome_message = (
            "<b>Welcome to the Advanced Links Sharing Bot!\n\n"
            "With this bot, you can share links and keep your channels safe from copyright issues.\n"
            f"Created by: <a href='https://t.me/i_killed_my_clan'>Obito</a></b>"
        )
        
        try:
            await message.reply_photo(
                photo=START_PIC_FILE_ID,
                caption=welcome_message,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error sending start picture: {e}")
            await message.reply_text(
                welcome_message,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )

@Bot.on_callback_query(filters.regex("help"))
async def help_callback(client: Bot, callback_query):
    new_text = (
        "<b>Creator: <a href='https://t.me/i_killed_my_clan'>Obito</a>\n"
        "Our Community: <a href='https://t.me/society_network'>Society Network</a>\n"
        "Anime Channel: <a href='https://t.me/animes_sub_society'>Anime Society</a>\n"
        "Ongoing Society: <a href='https://t.me/Ongoiing_society'>Ongoing Society</a>\n"
        "Manga Society: <a href='https://t.me/Manga_X_Society'>Manga Society</a>\n"
        "Developer: <a href='https://t.me/i_killed_my_clan'>Obito</a></b>"
    )
    inline_buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Close", callback_data="close")]
        ]
    )

    await callback_query.answer()
    current_text = callback_query.message.text.html if callback_query.message.text else ""
    if current_text != new_text or callback_query.message.reply_markup != inline_buttons:
        try:
            await callback_query.message.edit_text(
                new_text,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error editing help message: {e}")
    else:
        print("Skipped edit: Message content unchanged")

@Bot.on_callback_query(filters.regex("close"))
async def close_callback(client: Bot, callback_query):
    await callback_query.answer()
    await callback_query.message.delete()
#=====================================================================================##

WAIT_MSG = "<b>Processing...</b>"

REPLY_ERROR = "<code>Use this command as a reply to any Telegram message without any spaces.</code>"

#=====================================================================================##

@Bot.on_message(filters.command('status') & filters.private & filters.user(ADMINS))
async def info(client: Bot, message: Message):   
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close")]])
    
    start_time = time.time()
    temp_msg = await message.reply("<b><i>Processing...</i></b>", quote=True, parse_mode=ParseMode.HTML)
    end_time = time.time()
    
    # Calculate ping time in milliseconds
    ping_time = (end_time - start_time) * 1000
    
    users = await full_userbase()  # Updated to use correct database function
    now = datetime.now()
    delta = now - client.uptime
    bottime = get_readable_time(delta.seconds)
    
    await temp_msg.edit(
        f"<b>Users: {len(users)}\n\nUptime: {bottime}\n\nPing: {ping_time:.2f} ms</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

#=====================================================================================##

@Bot.on_message(filters.command('broadcast') & filters.private & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    global is_canceled
    async with cancel_lock:
        is_canceled = False
    mode = False
    broad_mode = ''
    store = message.text.split()[1:]
    
    if store and len(store) == 1 and store[0] == 'silent':
        mode = True
        broad_mode = 'Silent '

    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = len(query)
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        pls_wait = await message.reply("<i>Broadcasting message... This will take some time.</i>", parse_mode=ParseMode.HTML)
        bar_length = 20
        final_progress_bar = "●" * bar_length
        complete_msg = f"🤖 {broad_mode}Broadcast Completed ✅"
        progress_bar = ''
        last_update_percentage = 0
        percent_complete = 0
        update_interval = 0.05  # Update progress bar every 5%

        for i, chat_id in enumerate(query, start=1):
            async with cancel_lock:
                if is_canceled:
                    final_progress_bar = progress_bar
                    complete_msg = f"🤖 {broad_mode}Broadcast Canceled ❌"
                    break
            try:
                await broadcast_msg.copy(chat_id, disable_notification=mode)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await broadcast_msg.copy(chat_id, disable_notification=mode)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
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
                status_update = f"""<b>🤖 {broad_mode}Broadcast in Progress...

Progress: [{progress_bar}] {percent_complete:.0%}

Total Users: {total}
Successful: {successful}
Blocked Users: {blocked}
Deleted Accounts: {deleted}
Unsuccessful: {unsuccessful}</b>

<i>To stop the broadcast, use: /cancel</i>"""
                await pls_wait.edit(status_update, parse_mode=ParseMode.HTML)
                last_update_percentage = percent_complete

        # Final status update
        final_status = f"""<b>{complete_msg}

Progress: [{final_progress_bar}] {percent_complete:.0%}

Total Users: {total}
Successful: {successful}
Blocked Users: {blocked}
Deleted Accounts: {deleted}
Unsuccessful: {unsuccessful}</b>"""
        return await pls_wait.edit(final_status, parse_mode=ParseMode.HTML)

    else:
        msg = await message.reply(REPLY_ERROR, parse_mode=ParseMode.HTML)
        await asyncio.sleep(8)
        await msg.delete()

#=====================================================================================##

@Bot.on_callback_query(filters.regex("help"))
async def help_callback(client: Bot, callback_query):
    inline_buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Close", callback_data="close")]
        ]
    )
    
    await callback_query.answer()
    await callback_query.message.edit_text(
        "<b>Creator: <a href='https://t.me/i_killed_my_clan'>Obito</a>\n"
        "Our Community: <a href='https://t.me/society_network'>Society Network</a>\n"
        "Anime Channel: <a href='https://t.me/animes_sub_society'>Anime Society</a>\n"
        "Ongoing Society: <a href='https://t.me/Ongoiing_society'>Ongoing Society</a>\n"
        "Manga Society: <a href='https://t.me/Manga_X_Society'>Manga Society</a>\n"
        "Developer: <a href='https://t.me/i_killed_my_clan'>Obito</a></b>",
        reply_markup=inline_buttons,
        parse_mode=ParseMode.HTML
    )

@Bot.on_callback_query(filters.regex("close"))
async def close_callback(client: Bot, callback_query):
    await callback_query.answer()
    await callback_query.message.delete()

#=====================================================================================##

user_message_count = {}
user_banned_until = {}

MAX_MESSAGES = 3
TIME_WINDOW = timedelta(seconds=10)
BAN_DURATION = timedelta(hours=1)

@Bot.on_message(filters.private)
async def monitor_messages(client: Bot, message: Message):
    user_id = message.from_user.id
    now = datetime.now()

    if user_id in ADMINS:
        return 

    if user_id in user_banned_until and now < user_banned_until[user_id]:
        await message.reply_text(
            "<b>You are temporarily banned from using commands due to spamming. Try again later.</b>",
            parse_mode=ParseMode.HTML
        )
        return

    if user_id not in user_message_count:
        user_message_count[user_id] = []

    user_message_count[user_id].append(now)
    user_message_count[user_id] = [time for time in user_message_count[user_id] if now - time <= TIME_WINDOW]

    if len(user_message_count[user_id]) > MAX_MESSAGES:
        user_banned_until[user_id] = now + BAN_DURATION
        await message.reply_text(
            "<b>You are temporarily banned from using commands due to spamming. Try again later.</b>",
            parse_mode=ParseMode.HTML
        )
        return

# Utility function to format uptime (assumed to be defined elsewhere, included for completeness)
def get_readable_time(seconds: int) -> str:
    """Convert seconds to a human-readable time format."""
    intervals = [
        ('days', 86400),  # 60 * 60 * 24
        ('hours', 3600),  # 60 * 60
        ('minutes', 60),
        ('seconds', 1),
    ]
    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            result.append(f"{int(value)} {name}")
    return ' '.join(result) or '0 seconds'
