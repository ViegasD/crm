"""Reconcile the delivery-first backlog. Default is preview; --apply writes ClickUp.

Credentials are read locally and never included in plans or reports. Re-running
matches lists by name and tasks by stable Dxx codes; mutations are sequential.
"""
import argparse
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FOLDER = "901318283724"
PLAN = ROOT / "docs/planning/clickup/CLICKUP_DELIVERY_PLAN_2026-11-11.json"
RESULT = ROOT / "docs/planning/clickup/CLICKUP_REWORK_RESULT_2026-11-11.json"


def configuration():
    values = dict(os.environ)
    env_file = ROOT / "scripts/.env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip().strip("\"'")
    token = values.get("CLICKUP_API_TOKEN")
    if not token:
        raise SystemExit("CLICKUP_API_TOKEN missing; no changes made")
    return token


def run(apply=False):
    plan = json.loads(PLAN.read_text(encoding="utf-8-sig"))
    if not apply:
        print(json.dumps({"folderId": FOLDER, "legacyLists": len(plan["legacyLists"]),
                          "newLists": len(plan["lists"]),
                          "newTasks": sum(len(x["tasks"]) for x in plan["lists"])}, indent=2))
        return
    token = configuration()

    def api(method, path, body=None):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            "https://api.clickup.com/api/v2/" + path, data=payload,
            headers={"Authorization": token, "Content-Type": "application/json"}, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            # Do not log request headers, credential values, or raw task bodies.
            raise RuntimeError(f"ClickUp {method} {path}: HTTP {exc.code}; stopped. Re-run to reconcile.") from None

    api("GET", "user")
    folder = api("GET", f"folder/{FOLDER}")
    if folder["name"] != "CRM2":
        raise RuntimeError("Unexpected folder name; stopped")
    available = api("GET", f"folder/{FOLDER}/list")["lists"]
    by_id = {str(item["id"]): item for item in available}
    by_name = {item["name"]: item for item in available}
    result = {"date": "2026-11-11", "folderId": FOLDER, "legacyLists": [], "lists": []}

    def save():
        RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for legacy in plan["legacyLists"]:
        current = by_id.get(legacy["id"])
        if not current:
            raise RuntimeError(f"Legacy list {legacy['id']} missing; stopped")
        expected = "[LEGADO CRM] " + legacy["name"]
        if current["name"] not in {legacy["name"], expected}:
            raise RuntimeError(f"Legacy list {legacy['id']} renamed externally; stopped")
        if current["name"] != expected:
            api("PUT", f"list/{legacy['id']}", {"name": expected})
        result["legacyLists"].append({"id": legacy["id"], "before": legacy["name"], "after": expected})
        save()
        print(f"LEGACY {legacy['id']}", flush=True)

    for group in plan["lists"]:
        current = by_name.get(group["name"])
        if not current:
            current = api("POST", f"folder/{FOLDER}/list",
                          {"name": group["name"], "content": group["description"]})
        list_id = str(current["id"])
        tasks = []
        page = 0
        while True:
            batch = api("GET", f"list/{list_id}/task?include_closed=true&subtasks=true&page={page}")
            tasks.extend(batch["tasks"])
            if batch.get("last_page") is True or len(batch["tasks"]) < 100:
                break
            page += 1
        entry = {"id": list_id, "name": group["name"], "tasks": []}
        result["lists"].append(entry)
        save()
        for task in group["tasks"]:
            matches = [item for item in tasks if re.match(r"^" + re.escape(task["code"]) + r"\b", item["name"])]
            if len(matches) > 1:
                raise RuntimeError(f"Duplicate task code {task['code']}; stopped")
            if matches:
                created = matches[0]
            else:
                description = (
                    "Diretriz confirmada em 09/11/2026: priorizar entregas de marketing e e-commerce; "
                    "CRM comercial em segundo plano.\n\n" + task["description"] +
                    "\n\nAceite:\n" + "\n".join("- " + x for x in task["acceptance"]) +
                    "\n\nDependencias: " + (", ".join(task.get("dependsOn", [])) or "nenhuma") +
                    "\n\nPlanejamento em 11/11/2026. Detalhamento funcional proposto; validar decisoes D00 antes de implementa-lo. "
                    "So encerrar com implementacao integrada, evidencias tecnicas e aceite manual quando aplicavel. "
                    "Sem prazo ou responsavel presumido. Fontes: docs/context/HANDOFF_COMPLETO.md e docs/planning/REALINHAMENTO_2026-11-11.md."
                )
                created = api("POST", f"list/{list_id}/task",
                              {"name": task["code"] + " - " + task["name"], "description": description,
                               "status": "Open", "priority": task.get("priority", 3), "notify_all": False})
                tasks.append(created)
            entry["tasks"].append({"code": task["code"], "id": created["id"],
                                   "url": created["url"], "name": created["name"],
                                   "status": created["status"]["status"]})
            save()
            print(f"TASK {task['code']} {created['id']}", flush=True)
    print("Reconciliation finished; read-back verification still required.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    run(parser.parse_args().apply)
