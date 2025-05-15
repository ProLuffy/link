# +++ Made By Obito [telegram username: @i_killed_my_clan] +++ #
import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from config import ADMINS
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time

async def check_subscription_status(client, user_id: int, fsub_channels: list) -> tuple[bool, str, InlineKeyboardMarkup]:
    """Check if a user is subscribed to all required channels."""
    not_subscribed = []
    
    for channel_id in fsub_channels:
        try:
            chat = await client.get_chat(channel_id)
            member = await client.get_chat_member(channel_id, user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                not_subscribed.append((chat.title, chat.username or str(channel_id)))
        except UserNotParticipant:
            chat = await client.get_chat(channel_id)
            not_subscribed.append((chat.title, chat.username or str(channel_id)))
        except Exception as e:
            print(f"Error checking subscription for channel {channel_id}: {e}")
            not_subscribed.append(("Unknown Channel", str(channel_id)))
    
    if not not_subscribed:
        return True, "", None
    
    message = "<b>You must subscribe to the following channels to use this bot:</b>\n\n"
    buttons = []
    for title, username in not_subscribed:
        message += f"• {title} (@{username})\n"
        buttons.append([InlineKeyboardButton(f"Join {title}", url=f"https://t.me/{username}")])
    
    buttons.append([InlineKeyboardButton("Check Subscription", callback_data="check_sub")])
    reply_markup = InlineKeyboardMarkup(buttons)
    
    return False, message, reply_markup
