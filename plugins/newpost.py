import asyncio
import base64
from pyrogram import Client as Bot, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors import UserNotParticipant, FloodWait, ChatAdminRequired, RPCError
from pyrogram.errors import InviteHashExpired, InviteRequestSent
from database.database import save_channel, delete_channel, get_channels
from config import ADMINS, OWNER_ID
from database.database import save_encoded_link, get_channel_by_encoded_link, save_encoded_link2, get_channel_by_encoded_link2
from helper_func import encode
from datetime import datetime, timedelta

PAGE_SIZE = 6

# Revoke invite link after 10 minutes
async def revoke_invite_after_5_minutes(client: Bot, channel_id: int, link: str, is_request: bool = False):
    await asyncio.sleep(300)  # 10 minutes
    try:
        if is_request:
            await client.revoke_chat_invite_link(channel_id, link)
            print(f"Join request link revoked for channel {channel_id}")
        else:
            await client.revoke_chat_invite_link(channel_id, link)
            print(f"Invite link revoked for channel {channel_id}")
    except Exception as e:
        print(f"Failed to revoke invite for channel {channel_id}: {e}")

# Set channel command
@Bot.on_message(filters.command('setchannel') & filters.private & filters.user(OWNER_ID))
async def set_channel(client: Bot, message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.reply("<b><blockquote expandable>ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴛᴏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.")
    
    try:
        channel_id = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply("<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ID. Exᴀᴍᴘʟᴇ:{code} /setchannel <channel_id> {code}")
    
    try:
        chat = await client.get_chat(channel_id)

        if chat.permissions and not (chat.permissions.can_post_messages or chat.permissions.can_edit_messages):
            return await message.reply(f"<b><blockquote expandable>I ᴀᴍ ɪɴ {chat.title}, ʙᴜᴛ I ʟᴀᴄᴋ ᴘᴏsᴛɪɴɢ ᴏʀ ᴇᴅɪᴛɪɴɢ ᴘᴇʀᴍɪssɪᴏɴs.")
        
        await save_channel(channel_id)
        return await message.reply(f"<b><blockquote expandable>✅ Cʜᴀɴɴᴇʟ {chat.title} ({channel_id}) ʜᴀs ʙᴇᴇɴ ᴀᴅᴅᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.")
    
    except UserNotParticipant:
        return await message.reply("<b><blockquote expandable>I ᴀᴍ ɴᴏᴛ ᴀ ᴍᴇᴍʙᴇʀ ᴏғ ᴛʜɪs ᴄʜᴀɴɴᴇʟ. Pʟᴇᴀsᴇ ᴀᴅᴅ ᴍᴇ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ.")
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await set_channel(client, message)
    except RPCError as e:
        return await message.reply(f"RPC Error: {str(e)}")
    except Exception as e:
        return await message.reply(f"Unexpected Error: {str(e)}")

# Delete channel command
@Bot.on_message(filters.command('delchannel') & filters.private & filters.user(OWNER_ID))
async def del_channel(client: Bot, message: Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.reply("You are not authorized to use this command.")
    
    try:
        channel_id = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply("<b><blockquote expandable>Iɴᴠᴀʟɪᴅ ᴄʜᴀɴɴᴇʟ ID. Exᴀᴍᴘʟᴇ:{code} /delchannel <channel_id> {code}")
    
    await delete_channel(channel_id)
    return await message.reply(f"<b><blockquote expandable>❌ Cʜᴀɴɴᴇʟ {channel_id} ʜᴀs ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ.")

# Channel post command
@Bot.on_message(filters.command('channelpost') & filters.private & filters.user(OWNER_ID))
async def channel_post(client: Bot, message: Message):
    channels = await get_channels()
    if not channels:
        return await message.reply("<b><blockquote expandable>Nᴏ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀᴠᴀɪʟᴀʙʟᴇ. Pʟᴇᴀsᴇ ᴜsᴇ /setchannel ᴛᴏ ᴀᴅᴅ ᴀ ᴄʜᴀɴɴᴇʟ.")

    await send_channel_page(client, message, channels, page=0)

async def send_channel_page(client, message, channels, page):
    total_pages = (len(channels) + PAGE_SIZE - 1) // PAGE_SIZE
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    buttons = []

    row = []
    for channel_id in channels[start_idx:end_idx]:
        try:
            base64_invite = await save_encoded_link(channel_id)
            button_link = f"https://t.me/{client.username}?start={base64_invite}"
            chat = await client.get_chat(channel_id)
            
            row.append(InlineKeyboardButton(chat.title, url=button_link))
            
            if len(row) == 2:
                buttons.append(row)
                row = [] 
        except Exception as e:
            print(f"Error for channel {channel_id}: {e}")

    if row: 
        buttons.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("• Pʀᴇᴠɪᴏᴜs •", callback_data=f"channelpage_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("• Nᴇxᴛ •", callback_data=f"channelpage_{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply("📢 Select a channel to post:", reply_markup=reply_markup)

@Bot.on_callback_query(filters.regex(r"channelpage_(\d+)"))
async def paginate_channels(client, callback_query):
    page = int(callback_query.data.split("_")[1])
    channels = await get_channels()
    await callback_query.message.delete()
    await send_channel_page(client, callback_query.message, channels, page)

# Request post command
@Bot.on_message(filters.command('reqpost') & filters.private & filters.user(OWNER_ID))
async def req_post(client: Bot, message: Message):
    channels = await get_channels()
    if not channels:
        return await message.reply("<b><blockquote expandable>Nᴏ ᴄʜᴀɴɴᴇʟs ᴀʀᴇ ᴀᴠᴀɪʟᴀʙʟᴇ. Pʟᴇᴀsᴇ ᴜsᴇ /setchannel ᴛᴏ ᴀᴅᴅ ᴀ ᴄʜᴀɴɴᴇʟ")

    await send_request_page(client, message, channels, page=0)

async def send_request_page(client, message, channels, page):
    total_pages = (len(channels) + PAGE_SIZE - 1) // PAGE_SIZE
    start_idx = page * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    buttons = []

    row = []
    for channel_id in channels[start_idx:end_idx]:
        try:
            base64_request = await encode(str(channel_id))
            await save_encoded_link2(channel_id, base64_request)
            button_link = f"https://t.me/{client.username}?start=req_{base64_request}"
            chat = await client.get_chat(channel_id)

            row.append(InlineKeyboardButton(chat.title, url=button_link))

            if len(row) == 2:
                buttons.append(row)
                row = [] 
        except Exception as e:
            print(f"Error generating request link for channel {channel_id}: {e}")

    if row: 
        buttons.append(row)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("• Pʀᴇᴠɪᴏᴜs •", callback_data=f"reqpage_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("• Nᴇxᴛ •", callback_data=f"reqpage_{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons) 
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply("Sᴇʟᴇᴄᴛ ᴀ ᴄʜᴀɴɴᴇʟ ᴛᴏ ʀᴇǫᴜᴇsᴛ ᴀᴄᴄᴇss:", reply_markup=reply_markup)

@Bot.on_callback_query(filters.regex(r"reqpage_(\d+)"))
async def paginate_requests(client, callback_query):
    page = int(callback_query.data.split("_")[1])
    channels = await get_channels()
    await callback_query.message.delete()
    await send_request_page(client, callback_query.message, channels, page)
