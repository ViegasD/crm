"""Restore the user-confirmed delivery MVP on existing tasks; preview by default.

No creation, deletion, comments, assignee or status mutations. Previous task
descriptions remain intact. Private pre-write backup stays in ignored var/.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

from clickup_rework_delivery import configuration, FOLDER, ROOT

MARKER = "Correcao de escopo confirmada pelo usuario - 11/11/2026"


def run(apply=False):
    plan = json.loads((ROOT / "docs/planning/clickup/CLICKUP_DELIVERY_PLAN_2026-11-11.json").read_text(encoding="utf-8-sig"))
    schedule = json.loads((ROOT / "docs/planning/clickup/CLICKUP_SCHEDULE_2026-11-11.json").read_text(encoding="utf-8-sig"))
    dates = {item["code"]: item for item in schedule["tasks"]}
    token = configuration()

    def api(method, path, body=None):
        request = urllib.request.Request(
            "https://api.clickup.com/api/v2/" + path,
            data=json.dumps(body, ensure_ascii=False).encode() if body is not None else None,
            headers={"Authorization": token, "Content-Type": "application/json"}, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            reason = "; credential expired or access denied" if exc.code in (401, 403) else ""
            raise SystemExit(f"ClickUp {method} {path}: HTTP {exc.code}{reason}") from None

    api("GET", "user")
    lists = api("GET", f"folder/{FOLDER}/list")["lists"]
    tasks = {}
    groups = {}
    for group in lists:
        page = 0
        while True:
            batch = api("GET", f"list/{group['id']}/task?include_closed=true&subtasks=true&page={page}")
            for task in batch["tasks"]:
                match = re.match(r"^(D\d{2}\.\d+)\b", task["name"])
                if match:
                    code = match[1]
                    if code in tasks:
                        raise SystemExit(f"Duplicate code {code}; stopped")
                    tasks[code] = task
                    groups[code] = group["id"]
            if batch.get("last_page") or len(batch["tasks"]) < 100:
                break
            page += 1

    changes = []
    list_changes = []
    for group in plan["lists"]:
        ids = {groups.get(task["code"]) for task in group["tasks"]}
        if len(ids) != 1 or None in ids:
            raise SystemExit(f"Unexpected task grouping for {group['name']}; stopped")
        list_changes.append((ids.pop(), group))
        for desired in group["tasks"]:
            code = desired["code"]
            task = tasks[code]
            if task["id"] != dates[code]["id"]:
                raise SystemExit(f"Unexpected task ID {code}; stopped")
            section = "\n\n" + MARKER + "\n"
            section += "Diretriz vigente: entregas de marketing e e-commerce INCLUIDAS no MVP; comercial em segundo plano.\n"
            section += "A exclusao dessas areas no realinhamento comercial anterior esta superada. Preservar seus achados tecnicos de seguranca, migrations e operacao.\n"
            section += "Objetivo: " + desired["description"] + "\nAceite:\n"
            section += "\n".join("- " + text for text in desired["acceptance"])
            section += "\nDependencias: " + (", ".join(desired["dependsOn"]) or "validacao da agencia quando aplicavel")
            section += f"\nJanela provisoria: {dates[code]['start']} a {dates[code]['due']}; calendario de 20 dias uteis, 16/11 a 14/12/2026."
            section += "\nReferencia: docs/planning/CORRECAO_ESCOPO_2026-11-11.md. Status anterior preservado; nao equivale a homologacao deste aceite."
            before = task.get("description") or ""
            if MARKER in before:
                raise SystemExit(f"Correction already present on {code}; inspect before repeating")
            body = {"name": code + " - " + desired["name"], "description": before + section,
                    "start_date": int(dates[code]["start_date"]), "due_date": int(dates[code]["due_date"]),
                    "start_date_time": False, "due_date_time": False}
            changes.append((code, task, body))
    print(json.dumps({"credential": "valid", "apply": apply, "lists": len(list_changes), "tasks": len(changes)}), flush=True)
    if not apply:
        return
    backup = ROOT / "var/backups" / ("clickup-before-scope-correction-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(json.dumps({"lists": lists, "tasks": tasks}, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"date": "2026-11-11", "folderId": FOLDER, "verified": False, "lists": [], "tasks": []}
    output = ROOT / "docs/planning/clickup/CLICKUP_SCOPE_CORRECTION_2026-11-11.json"

    def save():
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for list_id, group in list_changes:
        api("PUT", f"list/{list_id}", {"name": group["name"], "content": group["description"]})
        result["lists"].append({"id": list_id, "name": group["name"]})
        save()
    for code, before, body in changes:
        # Read again before writing to detect concurrent edits since the backup.
        current = api("GET", f"task/{before['id']}")
        if current.get("date_updated") != before.get("date_updated"):
            raise SystemExit(f"Concurrent edit on {code}; stopped; completed changes recorded")
        api("PUT", f"task/{before['id']}", body)
        after = api("GET", f"task/{before['id']}")
        assert after["name"] == body["name"], code
        assert after.get("description", "").startswith(before.get("description") or ""), code
        assert MARKER in after.get("description", ""), code
        assert after["status"]["status"] == before["status"]["status"], code
        assert sorted(u["id"] for u in after["assignees"]) == sorted(u["id"] for u in before["assignees"]), code
        assert str(after["start_date"]) == str(body["start_date"]), code
        assert str(after["due_date"]) == str(body["due_date"]), code
        result["tasks"].append({"code": code, "id": before["id"], "name": after["name"],
                                "status": after["status"]["status"], "start": dates[code]["start"], "due": dates[code]["due"]})
        save()
        print(f"Verified {code}", flush=True)
    observed = {item["id"]: item["name"] for item in api("GET", f"folder/{FOLDER}/list")["lists"]}
    assert all(observed[item["id"]] == item["name"] for item in result["lists"])
    result["verified"] = True
    save()
    print("Verified scope correction: 7 lists, 30 tasks; status, assignees and prior descriptions preserved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    run(parser.parse_args().apply)
