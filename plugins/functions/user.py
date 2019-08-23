# SCP-079-MANAGE - One ring to rule them all
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-MANAGE.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from pyrogram import Client, InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.api.types import InputPeerUser, InputPeerChannel

from .. import glovar
from .channel import send_debug, share_data
from .etc import button_data, code, crypt_str, get_int, get_now, get_object, user_mention
from .file import save
from .telegram import resolve_peer

# Enable logging
logger = logging.getLogger(__name__)


def check_object(client: Client, message: Message) -> (str, InlineKeyboardMarkup):
    # Check object's status
    text = ""
    markup = None
    try:
        aid = message.from_user.id
        the_id = 0
        id_text, _, from_check = get_object(message)
        if id_text and from_check:
            the_id = get_int(id_text)
            if not the_id:
                _, the_id = resolve_peer(client, id_text)
        elif message.forward_from:
            the_id = message.forward_from.id
        elif message.forward_from_chat:
            the_id = message.forward_from_chat.id

        if the_id:
            if the_id > 0:
                now = get_now()
                is_bad = the_id in glovar.bad_ids["users"]
                is_watch_delete = glovar.watch_ids["delete"].get(the_id, 0) > now
                is_watch_ban = glovar.watch_ids["ban"].get(the_id, 0) > now
                text = (f"管理员：{user_mention(aid)}\n"
                        f"用户 ID：{code(the_id)}\n"
                        f"黑名单：{code(is_bad)}\n"
                        f"删除追踪：{code(is_watch_delete)}\n"
                        f"封禁追踪：{code(is_watch_ban)}\n")
                for project in glovar.default_user_status:
                    text += f"{project.upper()} 得分：{code(glovar.user_ids[the_id][project])}\n"

                bad_data = button_data("check", "bad", the_id)
                watch_data = button_data("check", "watch", the_id)
                cancel_data = button_data("check", "cancel", the_id)
                if is_bad or is_watch_delete or is_watch_ban:
                    markup_list = [
                        [],
                        [
                            InlineKeyboardButton(
                                text="取消",
                                callback_data=cancel_data
                            )
                        ]
                    ]
                    if is_bad:
                        markup_list[0].append(
                            InlineKeyboardButton(
                                text="解禁用户",
                                callback_data=bad_data
                            )
                        )

                    if is_watch_delete or is_watch_ban:
                        markup_list[0].append(
                            InlineKeyboardButton(
                                text="移除追踪",
                                callback_data=watch_data
                            )
                        )

                    markup = InlineKeyboardMarkup(markup_list)
            else:
                is_bad = the_id in glovar.bad_ids["channels"]
                is_except = the_id in glovar.except_ids["channels"]
                text = (f"管理员：{user_mention(aid)}\n"
                        f"频道 ID：{code(the_id)}\n"
                        f"黑名单：{code(is_bad)}\n"
                        f"白名单：{code(is_except)}\n")
                bad_data = button_data("check", "bad", the_id)
                except_data = button_data("check", "except", the_id)
                cancel_data = button_data("check", "cancel", the_id)
                if is_bad:
                    bad_text = "移除黑名单"
                else:
                    bad_text = "添加黑名单"

                if is_except:
                    except_text = "移除白名单"
                else:
                    except_text = "添加白名单"

                markup_list = [
                    [
                        InlineKeyboardButton(
                            text=bad_text,
                            callback_data=bad_data
                        ),
                        InlineKeyboardButton(
                            text=except_text,
                            callback_data=except_data
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="取消",
                            callback_data=cancel_data
                        )
                    ]
                ]
                markup = InlineKeyboardMarkup(markup_list)
        elif not (message.forward_from or message.forward_from_chat or message.forward_sender_name):
            text = (f"管理员：{user_mention(aid)}\n"
                    f"结果：{code('无法显示')}\n"
                    f"原因：{code('格式有误')}\n")
    except Exception as e:
        logger.warning(f"Check object error: {e}", exc_info=True)

    return text, markup


def receive_watch_user(watch_type: str, uid: int, until: str) -> bool:
    # Receive watch users that other bots shared
    try:
        # Decrypt the data
        until = crypt_str("decrypt", until, glovar.key)
        until = int(until)

        # Add to list
        if watch_type == "ban":
            glovar.watch_ids["ban"][uid] = until
        elif watch_type == "delete":
            glovar.watch_ids["delete"][uid] = until
        else:
            return False

        return True
    except Exception as e:
        logger.warning(f"Receive watch user error: {e}", exc_info=True)

    return False


def remove_bad_object(client: Client, the_id: int, debug: bool = False, aid: int = None, reason: str = None) -> str:
    # Remove bad user or bad channel from list, and share it
    result = ""
    try:
        if the_id > 0:
            action_text = "解禁用户"
            id_type = "users"
        else:
            action_text = "解禁频道"
            id_type = "channels"

        result += (f"操作：{code(action_text)}\n"
                   f"针对：{code(the_id)}\n")
        if the_id in glovar.bad_ids[id_type]:
            # Local
            glovar.bad_ids[id_type].discard(the_id)
            save("bad_ids")

            glovar.watch_ids["ban"].pop(the_id, 0)
            glovar.watch_ids["delete"].pop(the_id, 0)

            # Share
            id_type = id_type[:-1]
            share_data(
                client=client,
                receivers=glovar.receivers["bad"],
                action="remove",
                action_type="bad",
                data={
                    "id": the_id,
                    "type": id_type
                }
            )
            result += f"结果：{code('操作成功')}\n"
            if debug:
                send_debug(client, aid, action_text, None, str(the_id), None, None, reason)
        else:
            result += f"结果：{code('对象不在列表中')}\n"
    except Exception as e:
        logger.warning(f"Remove bad object error: {e}", exc_info=True)

    return result


def remove_watch_user(client: Client, the_id: int, aid: int = None, reason: str = None) -> str:
    # Remove watched user
    result = ""
    try:
        action_text = "移除追踪"
        result += (f"操作：{code(action_text)}\n"
                   f"针对：{code(the_id)}\n")
        if glovar.watch_ids["ban"].get(the_id, 0) and glovar.watch_ids["delete"].get(the_id, 0):
            # Local
            glovar.watch_ids["ban"].pop(the_id, 0)
            glovar.watch_ids["delete"].pop(the_id, 0)

            # Share
            share_data(
                client=client,
                receivers=glovar.receivers["watch"],
                action="remove",
                action_type="watch",
                data={
                    "id": the_id,
                    "type": "all"
                }
            )
            result += f"结果：{code('操作成功')}\n"
            send_debug(client, aid, action_text, None, str(the_id), None, None, reason)
        else:
            result += f"结果：{code('对象不在列表中')}\n"
    except Exception as e:
        logger.warning(f"Remove watch user error: {e}", exc_info=True)

    return result


def resolve_username(client: Client, username: str) -> (str, int):
    # Resolve peer by username
    peer_type = ""
    peer_id = 0
    try:
        if username:
            result = resolve_peer(client, username)
            if result:
                if isinstance(result, InputPeerChannel):
                    peer_type = "channel"
                    peer_id = result.channel_id
                    peer_id = get_int(f"-100{peer_id}")
                elif isinstance(result, InputPeerUser):
                    peer_type = "user"
                    peer_id = result.user_id
    except Exception as e:
        logger.warning(f"Resolve username error: {e}", exc_info=True)

    return peer_type, peer_id
