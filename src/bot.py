from typing import Any
import traceback
import signal

from telegram import CallbackQuery, User, Update, Message
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ExtBot, JobQueue
from telegram.ext import Application, filters
from telegram.ext import MessageHandler, CallbackQueryHandler
from telegram.constants import BOT_API_VERSION
from telegram.error import BadRequest

from src.log import tg_log
from src.config import cfg

BotData = dict[Any, Any]
ChatData = dict[Any, Any]
UserData = dict[Any, Any]
Context = CallbackContext[ExtBot[None], UserData, ChatData, BotData]
App = Application[ExtBot[None], Context, UserData, ChatData, BotData, JobQueue[Context]]

class TGbot:
    def __init__(self) -> None:
        self.bot = self._init_bot(cfg.token)

    def _init_bot(self, token: str) -> App:
        app = Application.builder()
        app.token(token)
        app.post_init(self._on_startup)
        app.post_shutdown(self._on_shutdown)
        return app.build()
    
    async def _on_startup(self, app: App) -> None:
        try:
            me: User = await app.bot.get_me()
            if not me.can_read_all_group_messages:
                raise RuntimeError("Bot 当前是隐私模式，请关闭后重试")
            tg_log.info(f"Bot 已启动 - {me.full_name} - {me.id}")
            tg_log.info(f"Telegram Bot API 版本 - {BOT_API_VERSION}")
            self.bot_id: int = me.id
            self.bot_username: str = (me.username or "").lower()
            await self.bot_self_test(app)
        except Exception:
            tg_log.exception("Bot 启动失败")
            raise
    
    async def _on_shutdown(self, app: App) -> None:
        tg_log.info("Bot 已关闭")
    
    async def bot_self_test(self, app: App):
        try:
            chat = await app.bot.get_chat(cfg.to_public_channel)
        except Exception as e:
            raise RuntimeError(
                "无法获取 to_public_channel 的信息，"
                "请检查 bot 是否在该频道内且有权限"
            ) from e

        if (username := chat.username) is None:
            raise RuntimeError(
                "你为 to_public_channel 设置了私人频道，"
                "此配置项需要一个拥有用户名的频道（公开频道）"
            )
        
        self.public_channel_username = username

        try:
            message = await chat.send_message("test")
        except BadRequest:
            raise RuntimeError(
                "to_public_channel 没有发送权限，"
                "请授予此权限后重试"
            )
        
        await message.delete()


    async def send_to_public_channel(self, query: CallbackQuery, chat_data: ChatData):
        await query.answer()
        msg: Message | None = chat_data.get("push_msg")
        if msg is None:
            await query.edit_message_text(
                "发生错误:\n数据缺失，请手动转发"
            )
            return
        try:
            message = await msg.copy(chat_id=cfg.to_public_channel)
        except Exception as e:
            await query.edit_message_text(
                f"发生错误:\n{e}\n请手动转发"
            )
            return
        return message.message_id

    async def channel_message_handler(self, update: Update, context: Context) -> None:
        if (msg := update.message) is None:
            return
        
        if not msg.is_automatic_forward:
            return
        
        if (chat_data := context.chat_data) is None:
            return

        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("发布", callback_data="action:push"),
                InlineKeyboardButton("取消", callback_data="action:cancel")
            ]
        ])

        chat_data["push_msg"] = msg

        await msg.reply_text(
            "是否发布到公开频道？",
            reply_markup=markup,
        )

    async def on_callback(self, update: Update, context: Context):
        """
        内联键盘回调
        """
        if (query := update.callback_query) is None:
            return
        if query.from_user.id != cfg.admin_id:
            await query.answer("你没有权限进行此操作", show_alert=True)
            return
        if (chat_data := context.chat_data) is None:
            await query.answer("数据缺失或错误", show_alert=True)
            return

        operation = query.data or ""

        match operation:
            case "action:cancel":
                await query.answer()
                await query.delete_message()
                return
            case "action:push":
                msgid = await self.send_to_public_channel(
                    query,chat_data
                )
                if msgid is None:
                    return
                
                await query.edit_message_text(
                    f"此消息已发布",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "查看",
                            url=f"https://t.me/{self.public_channel_username}/{msgid}"
                        )]
                    ])
                )
                return
    
    def register_handlers(self) -> None:
        self.bot.add_handler(
            MessageHandler(
                filters=filters.Chat(cfg.private_channel_linkchat),
                callback=self.channel_message_handler
            )
        )
        self.bot.add_handler(CallbackQueryHandler(self.on_callback))
    
    def stop(self, signum: int, frame) -> None:
        tg_log.info("Bot 关闭中 - 请稍候")
        tg_log.debug(f"信号: {signum}")
        tg_log.debug(f"当前栈信息: {traceback.format_stack(frame)}")
        self.bot.stop_running()

    def run(self) -> None:
        tg_log.info("Bot 启动中")
        self.register_handlers()
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        self.bot.run_polling(
            stop_signals=None,
            drop_pending_updates=True
        )
