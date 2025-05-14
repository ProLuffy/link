# +++ Made By Obito [telegram username: @i_killed_my_clan] +++ #
import asyncio
import base64
from pyrogram import Client as Bot, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, FloodWait, ChatAdminRequired, RPCError
from pyrogram.errors import InviteHashExpired, InviteRequestSent
from database.database import save_channel, delete_channel, get_channels
from database.database import save_encoded_link, get_channel_by_encoded_link, save_encoded_link2, get_channel_by_encoded_link2
from config import ADMINS, OWNER_ID
from helper_func import encode
from datetime import datetime, timedelta
from typing import List

PAGE_SIZE = 6

async def revoke_invite_after_10_minutes(client: Bot, channel_id: int, link: str, is_request: bool = False) -> None:
    """Revoke an invite link after 10 minutes."""
    await asyncio.sleep(600)  # 10 minutes
    try:
        await client.revoke_chat_invite_link(channel_id, link)
        print(f"{'Join request' if is_request else 'Invite'} link revoked for channel {channel_id}")
    except Exception as e:
        print(f"Failed to revoke invite for channel {channel_id}: {e}")

# ------------------------------------------------------------------------------------
# Set Channel Command
# ------------------------------------------------------------------------------------

@Bot.on_message(filters.command('setchannel') & filters.private & filters.user(OWNER_ID))
async def set_channel(client: Bot, message: Message) -> None:
    """Add a channel to the database."""
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.reply("You are not authorized to use this command.")
        return

    try:
        channel_id = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply("Invalid channel ID. Usage: /setchannel <channel_id>")
        return

    try:
        chat = await client.get_chat(channel_id)

        # Check if the bot has sufficient permissions
        if chat.permissions and not (chat.permissions.can_post_messages or chat.permissions.can_edit_messages):
            await message.reply(f"Insufficient permissions in channel '{chat.title}'.")
            return

        success = await save_channel(channel_id)
        if success:
            await message.reply(f"✅ Channel '{chat.title}' ({channel_id}) added successfully.")
        else:
            await message.reply(f"Failed to add channel '{chat.title}'.")
    except UserNotParticipant:
        await message.reply("Bot is not a member of this channel. Add the bot and try again.")
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await set_channel(client, message)
    except RPCError as e:
        await message.reply(f"Telegram API error: {str(e)}")
    except Exception as e:
        await message.reply(f"Unexpected error: {str(e)}")

# ------------------------------------------------------------------------------------
# Delete Channel Command
# ------------------------------------------------------------------------------------

@Bot.on_message(filters.command('delchannel') & filters.private & filters.user(OWNER_ID))
async def del_channel(client: Bot, message: Message) -> None:
    """Remove a channel from the database."""
    user_id = message.from_user.id
    if user_id not in ADMINS:
        await message.reply("You are not authorized to use this command.")
        return

    try:
        channel_id = int(message.command[1])
    except (IndexError, ValueError):
        await message.reply("Invalid channel ID. Usage: /delchannel <channel_id>")
        return

    success = await delete_channel(channel_id)
    if success:
        await message.reply(f"❌ Channel {channel_id} removed successfully.")
    else:
        await message.reply(f"Channel {channel_id} not found or could not be removed.")

# ------------------------------------------------------------------------------------
# Channel Post Command
# ------------------------------------------------------------------------------------

@Bot.on_message(filters.command('channelpost') & filters.private & filters.user(OWNER_ID))
async def channel_post(client: Bot, message: Message) -> None:
    """Display a paginated list of channels for posting."""
    channels = await get_channels()
    if not channels:
        await message.reply("No channels available. Use /setchannel to add a channel.")
        return

    await send_channel_page(client, message, channels, page=0)

async def send_channel_page(client: Bot, message: Message, channels: List[int], page: int) -> None:
    """Send a paginated list of channels with inline buttons."""
    total_pages = (len(channels) + PAGE_SIZE - 1) // PAGE_SIZE
    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(channels))
    buttons = []

    row = []
    for channel_id in channels[start_idx:end_idx]:
        try:
            base64_invite = await save_encoded_link(channel_id)
            if not base64_invite:
                print(f"Failed to generate encoded link for channel {channel_id}")
                continue

            button_link = f"https://t.me/{client.username}?start={base64_invite}"
            chat = await client.get_chat(channel_id)
            row.append(InlineKeyboardButton(chat.title or f"Channel {channel_id}", url=button_link))

            if len(row) == 2:
                buttons.append(row)
                row = []
        except Exception as e:
            print(f"Error generating link for channel {channel_id}: {e}")

    if row:
        buttons.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅ Previous", callback_data=f"channelpage_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡", callback_data=f"channelpage_{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply("📢 Select a channel to post:", reply_markup=reply_markup)

@Bot.on_callback_query(filters.regex(r"channelpage_(\d+)"))
async def paginate_channels(client: Bot, callback_query) -> None:
    """Handle pagination for channel post selection."""
    page = int(callback_query.data.split("_")[1])
    channels = await get_channels()
    await callback_query.message.delete()
    await send_channel_page(client, callback_query.message, channels, page)

# ------------------------------------------------------------------------------------
# Request Post Command
# ------------------------------------------------------------------------------------

@Bot.on_message(filters.command('reqpost') & filters.private & filters.user(OWNER_ID))
async def req_post(client: Bot, message: Message) -> None:
    """Display a paginated list of channels for join requests."""
    channels = await get_channels()
    if not channels:
        await message.reply("No channels available. Use /setchannel to add a channel.")
        return

    await send_request_page(client, message, channels, page=0)

async def send_request_page(client: Bot, message: Message, channels: List[int], page: int) -> None:
    """Send a paginated list of channels for join request links."""
    total_pages = (len(channels) + PAGE_SIZE - 1) // PAGE_SIZE
    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(channels))
    buttons = []

    row = []
    for channel_id in channels[start_idx:end_idx]:
        try:
            base64_request = await encode(str(channel_id))
            saved_link = await save_encoded_link2(channel_id, base64_request)
            if not saved_link:
                print(f"Failed to save encoded link for channel {channel_id}")
                continue

            button_link = f"https://t.me/{client.username}?start=req_{base64_request}"
            chat = await client.get_chat(channel_id)
            row.append(InlineKeyboardButton(chat.title or f"Channel {channel_id}", url=button_link))

            if len(row) == 2:
                buttons.append(row)
                row = []
        except Exception as e:
            print(f"Error generating request link for channel {channel_id}: {e}")

    if row:
        buttons.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅ Previous", callback_data=f"reqpage_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡", callback_data=f"reqpage_{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply("📢 Select a channel to request access:", reply_markup=reply_markup)

@Bot.on_callback_query(filters.regex(r"reqpage_(\d+)"))
async def paginate_requests(client: Bot, callback_query) -> None:
    """Handle pagination for join request selection."""
    page = int(callback_query.data.split("_")[1])
    channels = await get_channels()
    await callback_query.message.delete()
    await send_request_page(client, callback_query.message, channels, page)
