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

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.etc import bold, code, general_link, get_callback_data, get_command_context
from ..functions.etc import get_int, message_link, thread, user_mention
from ..functions.filters import manage_group, test_group
from ..functions.manage import action_answer, get_admin, get_object
from ..functions.telegram import edit_message_text, send_message
from ..functions.user import remove_bad_object, remove_watch_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & manage_group
                   & Filters.command(["action"], glovar.prefix))
def action(client: Client, message: Message):
    try:
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        text = f"管理：{user_mention(uid)}\n"
        command_type, reason = get_command_context(message)
        if command_type and command_type in {"proceed", "delete", "cancel"}:
            if message.reply_to_message:
                r_message = message.reply_to_message
                aid = get_admin(r_message)
                if uid == aid:
                    callback_data_list = get_callback_data(r_message)
                    if r_message.from_user.is_self and callback_data_list:
                        r_mid = r_message.message_id
                        action_key = callback_data_list[0]["d"]
                        thread(action_answer, (client, uid, r_mid, action_key, command_type, reason))
                        text += (f"状态：{code('已操作')}\n"
                                 f"查看：{general_link(r_mid, message_link(r_message))}\n")
                    else:
                        text += (f"状态：{code('未操作')}\n"
                                 f"原因：{code('来源有误')}\n")
                else:
                    text += (f"状态：{code('未操作')}\n"
                             f"原因：{code('权限有误')}\n")
            else:
                text += (f"状态：{code('未操作')}\n"
                         f"原因：{code('用法有误')}\n")
        else:
            text += (f"状态：{code('未操作')}\n"
                     f"原因：{code('格式有误')}\n")

        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Action error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & manage_group
                   & Filters.command(["remove_bad", "remove_watch"], glovar.prefix))
def remove_object(client: Client, message: Message):
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = f"管理：{user_mention(aid)}\n"
        id_text, reason, from_check = get_object(message)
        if id_text:
            the_id = get_int(id_text)
            if the_id:
                if "remove_bad" in message.command:
                    result = remove_bad_object(client, the_id, True, aid, reason)
                else:
                    result = remove_watch_user(client, the_id, aid, reason)

                text += result
                if reason and result and "成功" in result:
                    text += f"原因：{code(reason)}\n"
            else:
                text += (f"针对：{code(id_text)}\n"
                         f"结果：{code('输入有误')}\n")
        else:
            text += f"结果：{code('缺少参数')}\n"

        if from_check:
            r_message = message.reply_to_message
            thread(edit_message_text, (client, cid, r_message.message_id, text))
            text = (f"管理：{user_mention(aid)}\n"
                    f"状态：{code('已操作')}\n"
                    f"查看：{general_link(r_message.message_id, message_link(r_message))}\n")
            thread(send_message, (client, cid, text, mid))
        else:
            thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Remove bad error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["version"], glovar.prefix))
def version(client: Client, message: Message):
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"管理员：{user_mention(aid)}\n\n"
                f"版本：{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)
