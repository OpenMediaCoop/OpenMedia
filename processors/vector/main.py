import asyncio
import logging
from transformers import logging as hf_logging
from .consumer import consume


# HuggingFace sin logs
hf_logging.set_verbosity_error()
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

# Logger general
logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M"
)
console_handler.setFormatter(formatter)
logger.handlers = [console_handler]

if __name__ == "__main__":
    asyncio.run(consume())