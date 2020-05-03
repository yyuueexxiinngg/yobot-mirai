# Author: https://github.com/yyuueexxiinngg

import asyncio
import logging
import re
from typing import Callable, Dict, List

from quart import Quart

if __package__:
    from .mirai import Mirai, EventType, Event
else:
    from mirai import Mirai, EventType, Event


# 本项目构建的框架非常粗糙且幼稚，不建议各位把时间浪费本项目上
# 此框架参照python-mirai实现
# 如果想开发自己的机器人，建议直接使用 python-mirai 框架
# https://github.com/NatriumLab/python-mirai

def cq_message_to_mirai_message_chain(message: str) -> List:
    splits = re.split(r"(\[CQ:at,qq=\d+\])", message)

    message_chain = []
    for text in splits:
        match = re.match(r"\[CQ:at,qq=(\d+)\]", text)
        if match is not None and match.group(1):
            message_chain.append({"type": "At", "target": int(match.group(1))})
        else:
            message_chain.append({"type": "Plain", "text": text})
    return message_chain


# Api为Yobot而生....
class Api:
    mirai_instance: Mirai

    def __init__(self, mirai_instance: Mirai):
        self.mirai_instance = mirai_instance

    async def send_msg(self, **message):
        logging.debug(message)
        message_chain = cq_message_to_mirai_message_chain(message["message"])
        target = message["user_id"]
        if message["message_type"] == "private":
            if message["sub_type"] == "group":
                from_group = message["from_group"]
                await self.mirai_instance.send_temp_message(qq=target, group=from_group, message_chain=message_chain)
            else:
                await self.mirai_instance.send_friend_message(target=target, message_chain=message_chain)
        elif message["message_type"] == "group":
            group_id = message["group_id"]
            await self.mirai_instance.send_group_message(target=group_id, message_chain=message_chain)
        else:
            logging.debug(message)
            raise NotImplementedError

    async def send_group_msg(self, group_id, message):
        message_chain = cq_message_to_mirai_message_chain(message)
        await self.mirai_instance.send_group_message(group_id, message_chain)

    async def send_private_msg(self, target: int, message: str):
        message_chain = [{"type": "Plain", "text": message}]
        await self.mirai_instance.send_friend_message(target=target, message_chain=message_chain)

    async def get_group_list(self):
        r = await self.mirai_instance.get_group_list()
        cq_group_list = []
        for group in r:
            cq_group_list.append({
                "group_id": group["id"],
                "group_name": group["name"]
            })
        return cq_group_list

    async def get_group_member_list(self, group_id: int):
        r = await self.mirai_instance.get_group_member_list(target=group_id)
        cq_group_member_list = []
        for member in r:
            cq_group_member_list.append({
                "group_id": group_id,
                "user_id": member["id"],
                "nickname": member["memberName"],
                "card": member["memberName"],
                "sex": "unknown",
                "age": 0,
                "area": "",
                "join_time": 0,
                "last_sent_time": 0,
                "level": "",
                "role": "",
                "unfriendly": False,
                "title": "",
                "title_expire_time": 0,
                "card_changeable": False,
            })
        return cq_group_member_list

    async def get_stranger_info(self, user_id: int):
        # Mirai 暂无此接口
        raise NotImplementedError

    async def get_group_member_info(self, group_id: int, user_id: int):
        r = await self.mirai_instance.get_group_member_info(target=group_id, member_id=user_id)
        cq_member_info = {
            "group_id": group_id,
            "user_id": user_id,
            "nickname": r["name"],
            "card": r["name"],
            "sex": "unknown",
            "age": 0,
            "area": "",
            "join_time": 0,
            "last_sent_time": 0,
            "level": "",
            "role": "",
            "unfriendly": False,
            "title": r["specialTitle"],
            "title_expire_time": 0,
            "card_changeable": False,
        }
        return cq_member_info


class MiraiHttp:
    auth_key: str
    host: str
    port: int
    qq: int
    _api: Api
    loop: asyncio.AbstractEventLoop
    server_app: Quart
    mirai_instance: Mirai

    def __init__(self, auth_key: str, host: str, port: int, qq: int):
        logging.info("Using Mirai backend")
        self.auth_key = auth_key
        self.host = host
        self.port = port
        self.qq = qq
        self.mirai_instance = Mirai(qq=self.qq, host=f"http://{self.host}:{self.port}", authKey=self.auth_key)
        self._api = Api(self.mirai_instance)
        self.server_app = Quart(__name__)

    def run(self, host: str, port: int, debug: bool, use_reloader: bool, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.mirai_instance.init_loop(self.loop)
        self.server_app.run(host=host, port=port, debug=debug, use_reloader=use_reloader, loop=self.loop)

    # 为了兼容原有代码... 别看我 ¯\_(ツ)_/¯
    def on_message(self, func: Callable):
        def on_message_handler(event: Event):
            # 将消息转换成CQ消息
            cq_message = self.mirai_message_to_cq_message(event.context)

            # 把消息传给订阅者
            async def call_receiver(context):
                # 获取要回复的消息
                reply = await func(context)
                # 如果有要回复的消息
                if reply is not None:
                    logging.debug(context)
                    text = reply["reply"]
                    if context["message_type"] == "group":
                        group_id = context["group_id"]
                        await self._api.send_group_msg(group_id=group_id, message=text)
                    elif context["message_type"] == "private":
                        message = context
                        message["message"] = text
                        message["raw_message"] = "reply"
                        await self._api.send_msg(**message)

            # 调用
            self.loop.create_task(call_receiver(cq_message))

        # 订阅消息事件
        self.mirai_instance.add_handler(EventType.Message, on_message_handler)
        return on_message_handler

    def mirai_message_to_cq_message(self, mirai_message: Dict) -> Dict:
        cq_message = {}

        # 消息类型
        if mirai_message["type"] == "GroupMessage":
            message_type = "group"
        elif mirai_message["type"] == "FriendMessage":
            message_type = "private"
        elif mirai_message["type"] == "TempMessage":
            message_type = "private"
        else:
            message_type = "NotImplemented"
        cq_message["message_type"] = message_type

        # 字体
        cq_message["font"] = 7228224  # 不去支持

        # 消息ID
        cq_message["message_id"] = mirai_message["messageChain"][0]["id"]

        # 上报类型
        cq_message["post_type"] = "message"  # 不去支持事件

        # 机器人QQ
        cq_message["self_id"] = self.qq

        # 发送者 QQ 号
        cq_message["user_id"] = mirai_message["sender"]["id"]

        # 存放发送人信息
        sender = {"age": 0,
                  "sex": "",
                  "user_id": mirai_message["sender"]["id"]
                  }

        # 群组消息
        if message_type == "group":
            # 匿名消息
            cq_message["anonymous"] = None  # 不去支持

            # 群号
            cq_message["group_id"] = mirai_message["sender"]["group"]["id"]

            # 消息子类型
            cq_message["sub_type"] = "normal"  # 不去支持事件

            sender["nickname"] = mirai_message["sender"]["memberName"]
            sender["area"] = ""
            sender["card"] = ""
            sender["level"] = ""
            sender["role"] = mirai_message["sender"]["permission"].lower()
        else:
            # 消息子类型
            if mirai_message["type"] == "FriendMessage":
                sender["nickname"] = mirai_message["sender"]["nickname"]
                cq_message["sub_type"] = "friend"
            elif mirai_message["type"] == "TempMessage":
                sender["nickname"] = mirai_message["sender"]["memberName"]
                cq_message["sub_type"] = "group"
                cq_message["from_group"] = mirai_message["sender"]["group"]["id"]  # 此块CQ中并不存在, 额外添加来回复临时会话
            else:
                cq_message["sub_type"] = "other"  # 不去支持来自谈论组

        # 发送人信息
        cq_message["sender"] = sender

        # 存放消息体
        message = ""
        raw_message = ""
        for chain in mirai_message["messageChain"]:
            if chain["type"] == "Source":
                continue  # 消息元数据
            elif chain["type"] == "Quote":
                continue  # 引用消息, CQ不支持
            elif chain["type"] == "At":
                message += f"[CQ:at,qq={chain['target']}]"
                raw_message += f"[CQ:at,qq={chain['target']}]"
            elif chain["type"] == "Plain":
                message += chain["text"]
                raw_message += chain["text"]
            elif chain["type"] == "Image":
                message += f"[CQ:image,file={chain['imageId'].replace('-', '')}.png,url={chain['url']}]"
                raw_message += f"[CQ:image,file={chain['imageId'].replace('-', '')}]"
            else:
                continue  # 不去支持

        cq_message["message"] = message
        cq_message["raw_message"] = raw_message
        return cq_message
