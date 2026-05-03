# TwinPoster

把“私有频道广播”变成“可审核发布”：  
频道消息自动抄送到关联讨论群后，由你点击按钮决定是否同步到公开频道。

## 这是什么

TwinPoster 是一个基于 `python-telegram-bot` 的机器人，核心目标是：

- 将私有频道的广播消息转发到公开频道（由你决定）
- 通过管理员按钮确认，避免自动误发
- 发布成功后返回公开链接，方便复核与分发

## 核心能力

- 监听指定群中的被关联频道的消息
- 提供内联按钮 `发布` / `取消`
- 仅允许 `admin_id` 执行回调操作
- 使用 `copy_message` 保留原消息内容样式
- 启动时自动执行配置与权限自检

## 工作流程

1. 私有频道发出广播消息并由 Telegram 自动转发到频道的关联群
2. Bot 识别到消息并回复操作按钮
3. 管理员点击 `发布` 后，消息被复制到公开频道
4. Bot 编辑提示消息，附上“查看”链接

## 环境要求

- Python `>=3.10`
- `python-telegram-bot==22.7`
- `pydantic>=2.13.3`

## 配置说明

将 `config.json.example` 复制为 `config.json` 并填写：

- `token`：Bot Token
- `admin_id`：允许点击发布按钮的管理员用户 ID
- `private_channel_linkchat`：私有频道关联讨论群 ID
- `to_public_channel`：目标公开频道 ID

注意事项：

- `to_public_channel` 必须是公开频道（有 `@username`）
- Bot 必须在目标公开频道中，且有发帖权限
- 必须在 BotFather 关闭隐私模式（`/setprivacy`）

## 快速开始

安装依赖：

```bash
uv sync
```

如果你不用 `uv`：

```bash
pip install -U python-telegram-bot==22.7 pydantic
```

运行：

```bash
python main.py
```

## 启动自检项

程序启动后会检查：

- Bot 是否关闭隐私模式（`can_read_all_group_messages`）
- `to_public_channel` 是否可访问
- `to_public_channel` 是否存在用户名
- Bot 是否拥有目标频道发帖权限（通过测试消息验证）

## 常见问题

- 提示“Bot 当前是隐私模式”
  - 到 BotFather 执行 `/setprivacy` 并关闭隐私模式
- 提示无法获取 `to_public_channel` 信息
  - 检查频道 ID 是否正确，Bot 是否已加入该频道
- 提示目标频道无发送权限
  - 给 Bot 授予发帖权限（建议设为管理员）
- 发布后链接打不开
  - 确认目标频道是公开频道且已设置用户名
