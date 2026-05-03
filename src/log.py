import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(stream=sys.stdout)],
)

tg_log = logging.getLogger("Telegram")

logging.getLogger("httpx").setLevel(logging.ERROR)