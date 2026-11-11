"""One-shot script: resolve placeholder group contact names from Evolution API.

Run once from repo root:
    backend\.venv\Scripts\python.exe backend\tools\backfill_group_names.py
"""
import asyncio

import asyncpg
import httpx

EVOLUTION_URL = "http://localhost:8080"
EVOLUTION_KEY = "evolution-secret-key"
EVOLUTION_INSTANCE = "test"
DB_DSN = "postgresql://crm:crm@localhost:5432/crm"


async def main() -> None:
    # 1. Get placeholder group JIDs from Postgres
    print(f"Connecting to Postgres ...")
    conn = await asyncpg.connect(DB_DSN)
    print("  Connected.")

    try:
        rows = await conn.fetch(
            """
            SELECT c.id, cp.phone, c.name
            FROM contacts c
            JOIN contact_phones cp ON cp.contact_id = c.id
            WHERE cp.phone LIKE '%@g.us'
              AND c.name LIKE 'Group %'
            """
        )
        print(f"Found {len(rows)} placeholder group contacts")

        if not rows:
            print("Nothing to do.")
            return

        # 2. Fetch each group's subject individually (fast — one call per JID)
        timeout = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=5.0)
        updated = 0
        with httpx.Client(timeout=timeout) as client:
            for row in rows:
                jid = row["phone"]
                print(f"  Fetching subject for {jid} ...", end=" ", flush=True)
                try:
                    r = client.get(
                        f"{EVOLUTION_URL}/group/findGroupInfos/{EVOLUTION_INSTANCE}",
                        params={"groupJid": jid},
                        headers={"apikey": EVOLUTION_KEY},
                    )
                    r.raise_for_status()
                    data = r.json()
                    subject = (data.get("subject") or "").strip()
                    if subject and subject != row["name"]:
                        await conn.execute(
                            "UPDATE contacts SET name = $1 WHERE id = $2",
                            subject,
                            row["id"],
                        )
                        print(f"→ {subject}")
                        updated += 1
                    else:
                        print(f"(no change: {data.get('subject')!r})")
                except Exception as exc:
                    print(f"ERROR: {exc}")

        print(f"\nDone. Updated {updated}/{len(rows)} contacts.")
    finally:
        await conn.close()


asyncio.run(main())

