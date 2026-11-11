"""Assign the confirmed Fabio/Thiago split and add audit/frontend work.

Preview by default. --apply preserves statuses/history, assigns one owner,
updates provisional dates and adds native dependencies. Safe to reconcile
after interruption: codes identify tasks and the allocation section is replaced.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import re
import time
import urllib.error
import urllib.request

from clickup_rework_delivery import configuration, ROOT, FOLDER

PLAN = ROOT / "docs/planning/clickup/CLICKUP_OWNERSHIP_PLAN_2026-11-11.json"
RESULT = ROOT / "docs/planning/clickup/CLICKUP_OWNERSHIP_RESULT_2026-11-11.json"
MARKER = "--- Divisao confirmada Fabio/Thiago - 11/11/2026 ---"
END = "--- Fim da divisao Fabio/Thiago ---"
CODE = re.compile(r"^(D\d{2}\.\d+|AUD\d{2}|UI\d{2}|API\d{2})\b")


def run(apply=False):
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    owners = plan["confirmedSplit"]
    specs = {t["code"]: t for t in plan["tasks"]}
    assert len(specs) == len(plan["tasks"]) == 49
    done, visiting = set(), set()

    def visit(code):
        if code in visiting:
            raise SystemExit("Dependency cycle: " + code)
        if code in done:
            return
        visiting.add(code)
        for dep in specs[code]["dependsOn"]:
            visit(dep)
            assert specs[dep]["due"] <= specs[code]["due"], (code, dep)
        visiting.remove(code)
        done.add(code)
    for code in specs:
        visit(code)

    token = configuration()
    last_request = 0.0

    def api(method, path, body=None):
        nonlocal last_request
        for attempt in range(5):
            time.sleep(max(0, .8 - (time.monotonic() - last_request)))
            last_request = time.monotonic()
            req = urllib.request.Request(
                "https://api.clickup.com/api/v2/" + path,
                data=json.dumps(body, ensure_ascii=False).encode() if body is not None else None,
                headers={"Authorization": token, "Content-Type": "application/json"}, method=method)
            try:
                with urllib.request.urlopen(req, timeout=40) as response:
                    raw = response.read()
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as exc:
                if exc.code == 429 and attempt < 4:
                    time.sleep(min(50, max(2, int(exc.headers.get("Retry-After", "15")))))
                    continue
                why = "; key expired or access denied" if exc.code in (401, 403) else ""
                raise SystemExit(f"ClickUp {method} {path}: HTTP {exc.code}{why}; reconcile after checking") from None

    api("GET", "user")
    lists = api("GET", f"folder/{FOLDER}/list")["lists"]
    listing = {item["name"]: item for item in lists}
    current = {}
    snapshot = []
    for group in lists:
        page = 0
        while True:
            batch = api("GET", f"list/{group['id']}/task?include_closed=true&subtasks=true&page={page}")
            snapshot.extend(batch["tasks"])
            for task in batch["tasks"]:
                match = CODE.match(task["name"])
                if match:
                    if match[1] in current:
                        raise SystemExit("Duplicate code: " + match[1])
                    current[match[1]] = task
            if batch.get("last_page") or len(batch["tasks"]) < 100:
                break
            page += 1
    for spec in specs.values():
        if spec["existing"] and spec["code"] not in current:
            raise SystemExit("Missing existing code " + spec["code"])
    print(json.dumps({"credential": "valid", "apply": apply, "existing": 30,
                      "plannedNew": 19, "owners": {o: sum(t["owner"] == o for t in specs.values()) for o in owners}}), flush=True)
    if not apply:
        return

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / f"var/backups/clickup-before-allocation-{stamp}.json"
    backup.parent.mkdir(parents=True, exist_ok=True)
    backup.write_text(json.dumps({"lists": lists, "tasks": snapshot}, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"date": "2026-11-11", "verified": False, "folderId": FOLDER,
              "owners": owners, "tasks": [], "nativeDependencies": 0}

    def save():
        RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for spec in specs.values():
        if spec["list"] not in listing:
            listing[spec["list"]] = api("POST", f"folder/{FOLDER}/list", {
                "name": spec["list"],
                "content": "Divisao confirmada: Fabio backend/deploy; Thiago frontend. Marketing e e-commerce no MVP. Datas provisorias e dependencias por tarefa."})

    def millis(day):
        # Date-only ClickUp fields; 12:00 UTC is 09:00 in the project timezone.
        return int(datetime.fromisoformat(day + "T12:00:00+00:00").timestamp() * 1000)

    def project_day(value):
        # ClickUp normalizes date-only values (observed 07:00 UTC). Verify the
        # calendar day users see in America/Araguaina, not the input instant.
        return datetime.fromtimestamp(int(value) / 1000, timezone(timedelta(hours=-3))).date().isoformat()

    for spec in specs.values():
        code = spec["code"]
        old = current.get(code)
        if old:
            old = api("GET", f"task/{old['id']}")
        before = (old or {}).get("description") or ""
        # Replace only our bounded section on retries, keeping prior history.
        before = re.sub(re.escape(MARKER) + r".*?" + re.escape(END), "", before, flags=re.S).rstrip()
        section = f"\n\n{MARKER}\nResponsavel: {spec['owner']}. Revisor: {spec['reviewer']}.\n"
        section += "Fabio: backend, contratos, migrations, workers e deploy. Thiago: frontend, tipos/client API, stores e integracao visual.\n"
        section += "Marketing/e-commerce incluidos; comercial secundario. Backend inseguro ou ausente nao pode ser mascarado por sucesso simulado na UI.\n"
        if spec.get("deliverable"):
            section += "Entrega desta tarefa: " + spec["deliverable"] + "\n"
        if spec.get("acceptance"):
            section += "Aceite:\n" + "\n".join("- " + a for a in spec["acceptance"]) + "\n"
        if spec.get("files"):
            section += "Referencias de codigo: " + "; ".join(spec["files"]) + "\n"
        section += "Depende de: " + (", ".join(spec["dependsOn"]) or "nenhuma dependencia tecnica adicionada; validar decisoes de produto") + "\n"
        section += f"Janela PROVISORIA: {spec['start']} a {spec['due']}. Reestimar em UI01/AUD08: escopo acrescido nao garante termino em 14/12.\n"
        section += "Evidencia: branch/commit, comandos e resultados, revisao e aceite manual quando aplicavel. Nao alterar status sem evidencia.\n"
        section += "Plano: docs/planning/DIVISAO_TRABALHO_2026-11-11.md; inventario: docs/reports/BACKEND_FRONTEND_COVERAGE_2026-11-11.md.\n" + END
        owner_id = owners[spec["owner"]]["clickupUserId"]
        body = {"description": before + section, "start_date": millis(spec["start"]),
                "due_date": millis(spec["due"]), "start_date_time": False, "due_date_time": False}
        if old:
            existing_assignees = [u["id"] for u in old.get("assignees", [])]
            allowed = {item["clickupUserId"] for item in owners.values()}
            if set(existing_assignees) - allowed:
                raise SystemExit("Unexpected assignee on " + code + "; stopped")
            body["assignees"] = {"add": [] if owner_id in existing_assignees else [owner_id],
                                 "rem": [uid for uid in existing_assignees if uid != owner_id]}
            api("PUT", f"task/{old['id']}", body)
            task_id = old["id"]
        else:
            body.update({"name": code + " - " + spec["name"], "assignees": [owner_id], "priority": 2 if spec["owner"] == "Fabio" else 3})
            task_id = api("POST", f"list/{listing[spec['list']]['id']}/task", body)["id"]
        after = api("GET", f"task/{task_id}")
        assert [u["id"] for u in after["assignees"]] == [owner_id], code
        assert project_day(after["start_date"]) == spec["start"], code
        assert project_day(after["due_date"]) == spec["due"], code
        assert before in after.get("description", ""), code
        assert MARKER in after.get("description", ""), code
        if old:
            assert after["status"]["status"] == old["status"]["status"], code
        current[code] = after
        result["tasks"].append({"code": code, "id": task_id, "owner": spec["owner"],
                                "status": after["status"]["status"], "start": spec["start"], "due": spec["due"]})
        save()
        print(f"Verified owner/dates/history {code}: {spec['owner']}", flush=True)

    # Add dependencies after all IDs exist; preserve any prior dependencies.
    for code, spec in specs.items():
        task_id = current[code]["id"]
        known = {d.get("depends_on") for d in current[code].get("dependencies", [])}
        for dependency in spec["dependsOn"]:
            dep_id = current[dependency]["id"]
            if dep_id not in known:
                api("POST", f"task/{task_id}/dependency", {"depends_on": dep_id})
            result["nativeDependencies"] += 1
        print("Dependencies reconciled " + code, flush=True)
    save()

    for code, spec in specs.items():
        after = api("GET", f"task/{current[code]['id']}")
        ids = {d.get("depends_on") for d in after.get("dependencies", [])}
        assert {current[d]["id"] for d in spec["dependsOn"]} <= ids, code
        assert [u["id"] for u in after["assignees"]] == [owners[spec["owner"]]["clickupUserId"]], code
    result["verified"] = True
    save()
    print(f"VERIFIED: {len(specs)} tasks, 19 additions, owners and {result['nativeDependencies']} native dependencies", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    run(parser.parse_args().apply)
