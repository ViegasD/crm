import asyncio
import json
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def main():
    db_url = "postgresql+asyncpg://crm:crm@localhost:5432/crm"
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    query = text("""
        SELECT created_at, status, raw_payload
        FROM webhook_events
        WHERE raw_payload::text LIKE :pattern
        ORDER BY created_at DESC
        LIMIT 5
    """)

    async with async_session() as session:
        result = await session.execute(query, {"pattern": "%stickerMessage%"})
        rows = result.fetchall()

        for row in rows:
            created_at, status, raw_payload = row
            payload = raw_payload
            data = payload.get("data", {})
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            
            event = payload.get("event", "N/A")
            key = data.get("key", {})
            message = data.get("message", {})
            
            from_me = key.get("fromMe", "N/A")
            remote_jid = key.get("remoteJid", "N/A")
            msg_id = key.get("id", "N/A")
            message_keys = list(message.keys()) if isinstance(message, dict) else "N/A"

            print(f"Created At: {created_at}")
            print(f"Status: {status}")
            print(f"Event: {event}")
            print(f"Key: fromMe={from_me}, remoteJid={remote_jid}, id={msg_id}")
            print(f"Message Keys: {message_keys}")
            print("-" * 40)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
