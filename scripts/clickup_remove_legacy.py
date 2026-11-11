"""Back up and delete only the 138 legacy task IDs recorded in the audit.

User requested actual deletion on 2026-11-11. Preview by default; --apply first
backs up task details/comments outside the repository, then deletes sequentially.
Attachment metadata/URLs are retained; binary attachments are not downloaded.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import argparse
import json
from pathlib import Path
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from clickup_rework_delivery import ROOT, FOLDER, configuration


def run(apply=False):
    baseline = json.loads((ROOT / "docs/archive/clickup/CLICKUP_SNAPSHOT_2026-11-11.json").read_text(encoding="utf-8-sig"))
    legacy_ids = {task["id"] for task in baseline["tasks"]}
    list_ids = {task["listId"] for task in baseline["tasks"]}
    assert len(legacy_ids) == 138 and len(list_ids) == 23
    if not apply:
        print("Preview: back up/delete 138 specific legacy tasks; remove their lists only when empty.")
        return
    token = configuration()
    rate_lock = threading.Lock()
    next_request = 0.0

    def api(method, path):
        nonlocal next_request
        for attempt in range(5):
            with rate_lock:
                delay = max(0, next_request - time.monotonic())
                next_request = max(next_request, time.monotonic()) + 0.8
            if delay:
                time.sleep(delay)
            request = urllib.request.Request("https://api.clickup.com/api/v2/" + path,
                                             headers={"Authorization": token}, method=method)
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    body = response.read()
                    return json.loads(body) if body else {}
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < 4:
                    # An explicit throttle response means no mutation occurred.
                    reset = exc.headers.get("X-RateLimit-Reset", "")
                    delay = max(2, float(reset) - time.time() + 1) if reset.isdigit() else 30
                    print("ClickUp rate limit: waiting before retry", flush=True)
                    time.sleep(min(delay, 30))
                    continue
                raise RuntimeError(f"ClickUp {method} {path}: HTTP {exc.code}") from None

    backup = Path("C:/Users/fabio/.codex/backups/crm2-clickup-legacy-20261111")
    backup.mkdir(parents=True, exist_ok=True)

    folder = api("GET", f"folder/{FOLDER}")
    assert folder["name"] == "CRM2"
    existing_lists = api("GET", f"folder/{FOLDER}/list")["lists"]
    by_list = {item["id"]: item for item in existing_lists}
    assert list_ids <= set(by_list)
    assert all(by_list[list_id]["name"].startswith("[LEGADO CRM] ") for list_id in list_ids)

    def backup_task(task_id):
        cached = backup / (task_id + ".json")
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))
        detail = api("GET", f"task/{task_id}")
        assert detail["list"]["id"] in list_ids
        assert detail["folder"]["id"] == FOLDER
        comments = []
        query = ""
        while True:
            batch = api("GET", f"task/{task_id}/comment" + query)["comments"]
            comments.extend(batch)
            if len(batch) < 25:
                break
            tail = batch[-1]
            query = "?" + urllib.parse.urlencode({"start": tail["date"], "start_id": tail["id"]})
        record = {"task": detail, "comments": comments}
        cached.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    # All backups must succeed before the first deletion.
    records = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        for record in pool.map(backup_task, sorted(legacy_ids)):
            records.append(record)
            if len(records) % 20 == 0:
                print(f"Backed up {len(records)}/138 legacy tasks", flush=True)
    (backup / "tasks.json").write_text(json.dumps({"folder": folder, "lists": existing_lists,
                                                   "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"backupPath": str(backup), "deletedTaskIds": [], "deletedListIds": [],
              "attachmentBackup": "metadata and URLs only"}
    result_path = ROOT / "docs/archive/clickup/CLICKUP_LEGACY_DELETION_2026-11-11.json"

    def save():
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    save()
    print(f"Backup complete: {len(records)} task records and comments at {backup}", flush=True)
    for task_id in sorted(legacy_ids):
        api("DELETE", f"task/{task_id}")
        result["deletedTaskIds"].append(task_id)
        save()
        if len(result["deletedTaskIds"]) % 20 == 0:
            print(f"Deleted {len(result['deletedTaskIds'])}/138 legacy tasks", flush=True)
    for list_id in sorted(list_ids):
        # Do not remove a list containing any task added after the audit.
        remaining = api("GET", f"list/{list_id}/task?include_closed=true&subtasks=true")["tasks"]
        if not remaining:
            api("DELETE", f"list/{list_id}")
            result["deletedListIds"].append(list_id)
            save()
    plan_path = ROOT / "docs/planning/clickup/CLICKUP_DELIVERY_PLAN_2026-11-11.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["historicalLegacyLists"] = plan["legacyLists"]
    plan["legacyLists"] = []
    plan["legacyDeletedByUserRequest"] = "2026-11-11"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Deleted {len(result['deletedTaskIds'])} tasks and {len(result['deletedListIds'])} empty lists.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    run(parser.parse_args().apply)
