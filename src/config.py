from pathlib import Path
import sys
import json
from typing import Any

from pydantic import BaseModel

config_file_path = Path(__file__).parents[1] / "config.json"

class Config(BaseModel):
    token: str
    admin_id: int
    private_channel_linkchat: int
    to_public_channel: int

def load_config():
    if not config_file_path.exists():
        print("未找到配置文件")
        sys.exit(1)
    try:
        raw_data: dict[str, Any] = json.loads(
            config_file_path.read_text(encoding="utf-8")
        )
        return Config.model_validate(raw_data)
    except Exception as e:
        print(f"配置文件不合法: {e}")
        sys.exit(1)

cfg = load_config()