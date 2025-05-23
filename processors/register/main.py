import asyncio
from consumer import consume_and_process

if __name__ == "__main__":
    asyncio.run(consume_and_process())