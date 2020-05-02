# Author: https://github.com/yyuueexxiinngg

import asyncio
from enum import Enum

import aiohttp
import logging
from typing import Dict, Callable, Optional, List

# 本项目构建的框架非常粗糙且幼稚，不建议各位把时间浪费本项目上
# 此框架参照python-mirai实现
# 如果想开发自己的机器人，建议直接使用 python-mirai 框架
# https://github.com/NatriumLab/python-mirai

logging.basicConfig(format="%(asctime)s %(name)s:%(levelname)s:%(message)s",
                    datefmt="%d-%m-%Y %H:%M:%S",
                    level=logging.INFO
                    )


class http:
    @staticmethod
    async def get(url, params=None):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                resp.raise_for_status()
                try:
                    return await resp.json()
                except Exception as e:
                    logging.error(e)

    @staticmethod
    async def post(url, data=None, params=None):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params, json=data) as resp:
                resp.raise_for_status()
                try:
                    return await resp.json()
                except Exception as e:
                    logging.error(e)


class EventType(Enum):
    Message = "Message"
    Event = "Event"  # Not implemented


class Event:
    def __init__(self, event_type: EventType = None, context=None):
        self.event_type = event_type
        self.context = context


class Mirai:
    qq: int
    host: str
    authKey: str
    sessionKey: str
    event_queue: asyncio.Queue
    handlers: Dict  # {EventType:List}

    def __init__(self, qq: int, host: str, authKey: str):
        self.qq = qq
        self.host = host
        self.authKey = authKey
        self.handlers = {}

    def init_loop(self, loop: asyncio.AbstractEventLoop):
        self.event_queue = asyncio.Queue(loop=loop)
        loop.run_until_complete(self.auth())
        loop.run_until_complete(self.verify())
        loop.create_task(self.listen_message())
        loop.create_task(self.run_event())

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self.init_loop(loop)
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logging.info("Exiting")
            loop.run_until_complete(self.release())
        except SystemExit:
            logging.info("Exiting")
            loop.run_until_complete(self.release())

    async def auth(self):
        r = await http.post(f"{self.host}/auth", {"authKey": self.authKey})
        if "code" in r and r["code"] == 0 and "session" in r and r["session"]:
            self.sessionKey = r["session"]
            logging.debug("Authed: " + self.sessionKey)
        else:
            if "code" in r and r['code'] == 1:
                raise ValueError("Invalid authKey")
            else:
                raise ValueError("Invalid host")

    async def verify(self):
        r = await http.post(f"{self.host}/verify", {"sessionKey": self.sessionKey, "qq": self.qq})
        assert_success(r)

    async def release(self):
        r = await http.post(f"{self.host}/release", {"sessionKey": self.sessionKey, "qq": self.qq})
        assert_success(r)

    async def get_group_list(self):
        r = await http.get(f"{self.host}/groupList", {"sessionKey": self.sessionKey})
        return r

    async def get_group_member_list(self, target: int):
        r = await http.get(f"{self.host}/memberList", {"sessionKey": self.sessionKey, "target": target})
        return r

    async def get_group_member_info(self, target: int, member_id: int):
        r = await http.get(f"{self.host}/memberInfo",
                           {"sessionKey": self.sessionKey, "target": target, "memberId": member_id})
        return r

    async def send_group_message(self, target: int, message_chain: List, quote: int = None):
        r = await http.post(f"{self.host}/sendGroupMessage",
                            {"sessionKey": self.sessionKey, "target": target, "messageChain": message_chain})
        assert_success(r)
        return r

    async def send_friend_message(self, target: int, message_chain: List, quote: int = None):
        r = await http.post(f"{self.host}/sendFriendMessage",
                            {"sessionKey": self.sessionKey, "target": target, "messageChain": message_chain})

    async def send_temp_message(self, qq: int, group: int, message_chain: List, quote: int = None):
        r = await http.post(f"{self.host}/sendTempMessage",
                            {"sessionKey": self.sessionKey,
                             "qq": qq,
                             "group": group,
                             "messageChain": message_chain})
        assert_success(r)
        return r

    async def listen_message(self):
        logging.debug("Start listen message with sessionKey: " + self.sessionKey)
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(f"{self.host}/message?sessionKey={self.sessionKey}") as ws:
                while True:
                    try:
                        message = await ws.receive_json()
                        logging.debug(message)
                        self.event_queue.put_nowait(Event(EventType.Message, message))
                    except Exception as e:
                        logging.warning(e)

    async def listen_event(self):
        # 用不到, 无视ing
        raise NotImplementedError

    async def run_event(self):
        while True:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), 2)
                if event.event_type in self.handlers:
                    for handler in self.handlers[event.event_type]:
                        handler(event)
                self.event_queue.task_done()
            except asyncio.TimeoutError:
                continue

    def add_handler(self, event_type: EventType, handler: Callable):
        try:
            handlers = self.handlers[event_type]
        except KeyError:
            handlers = []
        self.handlers[event_type] = handlers
        if handler not in handlers:
            handlers.append(handler)


def assert_success(r):
    if "code" in r:
        if r["code"] != 0:
            logging.warning(r)
            raise ValueError("Invalid response")
    else:
        logging.warning(r)
        raise ValueError("Unknown response")
