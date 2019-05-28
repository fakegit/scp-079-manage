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

from pyrogram import Client, Filters

from .. import glovar
from ..functions.etc import bold, code, general_link, get_callback_data, get_command_context
from ..functions.etc import message_link, thread, user_mention
from ..functions.filters import manage_group, test_group
from ..functions.manage import error_answer, get_admin
from ..functions.telegram import send_message

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & manage_group
                   & Filters.command(["error"], glovar.prefix))
def error(client, message):
    try:
        cid = message.chat.id
        mid = message.message_id
        uid = message.from_user.id
        text = f"管理：{user_mention(uid)}\n"
        command_list = list(filter(None, message.command))
        if len(command_list) == 2 and command_list[1] in {"process", "cancel"}:
            command_type = command_list[1]
            if message.reply_to_message:
                r_message = message.reply_to_message
                aid = get_admin(r_message)
                if uid == aid:
                    callback_data_list = get_callback_data(r_message)
                    if r_message.from_user.is_self and callback_data_list and callback_data_list[0]["a"] == "error":
                        r_mid = r_message.message_id
                        error_key = callback_data_list[0]["d"]
                        reason = get_command_context(message)
                        thread(error_answer, (client, cid, uid, r_mid, command_type, error_key, reason))
                        text += (f"状态：{code('已操作')}\n"
                                 f"查看：{general_link(cid, message_link(r_message))}\n")
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
        logger.warning(f"Ask word error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group
                   & Filters.command(["version"], glovar.prefix))
def version(client, message):
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"管理员：{user_mention(aid)}\n\n"
                f"版本：{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)
