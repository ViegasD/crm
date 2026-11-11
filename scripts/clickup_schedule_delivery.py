"""Apply the user-selected Nov 16 start and a provisional 20-business-day plan."""
from datetime import date, datetime, time, timedelta, timezone
import json
import time as clock
import urllib.error
import urllib.request

from clickup_rework_delivery import ROOT, configuration

# Weekdays excluding national holidays in the period. Municipal/state holidays
# and agency closures still need confirmation. User timezone is UTC-03.
START = date(2026, 11, 16)
HOLIDAYS = {date(2026, 11, 20)}
TZ = timezone(timedelta(hours=-3))
RANGES = {
    "D00.1": (1, 1), "D00.2": (1, 2), "D00.3": (1, 2), "D00.4": (1, 2), "D00.5": (3, 3),
    "D01.1": (1, 1), "D01.2": (2, 2), "D01.3": (2, 2), "D01.4": (3, 4), "D01.5": (2, 2),
    "D02.1": (3, 3), "D02.2": (4, 4), "D02.3": (4, 4),
    "D03.1": (5, 5), "D03.2": (6, 7), "D03.3": (8, 8), "D03.4": (9, 9), "D03.5": (10, 10),
    "D04.1": (11, 11), "D04.2": (12, 13), "D04.3": (14, 14), "D04.4": (15, 15),
    "D05.1": (16, 18), "D05.2": (19, 20), "D05.3": (16, 18), "D05.4": (20, 20),
    "D06.1": (3, 4), "D06.2": (5, 6), "D06.3": (7, 9), "D06.4": (10, 10),
}


def business_days():
    days = []
    current = START
    while len(days) < 20:
        if current.weekday() < 5 and current not in HOLIDAYS:
            days.append(current)
        current += timedelta(days=1)
    return days


def run():
    days = business_days()
    result_path = ROOT / "docs/planning/clickup/CLICKUP_REWORK_RESULT_2026-11-11.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    token = configuration()
    schedule = {"start": str(START), "finish": str(days[-1]), "businessDays": 20,
                "timezone": "America/Araguaina (UTC-03)", "provisional": True,
                "excludedNationalHolidays": [str(day) for day in sorted(HOLIDAYS)], "tasks": []}

    def api(method, task_id, body=None):
        clock.sleep(0.8)
        data = json.dumps(body, ensure_ascii=False).encode() if body else None
        request = urllib.request.Request("https://api.clickup.com/api/v2/task/" + task_id,
                                         headers={"Authorization": token, "Content-Type": "application/json"},
                                         data=data, method=method)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    for group in result["lists"]:
        for task in group["tasks"]:
            code = task["code"]
            first, last = RANGES[code]
            start, finish = days[first - 1], days[last - 1]
            current = api("GET", task["id"])
            description = current["description"].split("\n\nCRONOGRAMA PROVISORIO")[0]
            description = description.replace("Sem prazo ou responsavel presumido.", "Responsavel ainda nao definido.")
            description += (
                "\n\nCRONOGRAMA PROVISORIO - base aprovada pelo usuario: inicio em 16/11/2026. "
                f"Dias uteis {first}-{last}: {start:%d/%m/%Y} a {finish:%d/%m/%Y}. "
                "Envelope de 20 dias uteis da Proposta.pdf, secao 5; marcos adaptados ao novo foco de entregas "
                "conforme HANDOFF_COMPLETO.md (09/11). Fim global previsto: 14/12/2026. "
                "Excluidos fins de semana e feriado nacional de 20/11. Feriados locais e indisponibilidades a confirmar. "
                "Datas condicionadas a validacao do escopo, acessos e capacidade de execucao; nao sao garantia contratual. "
                "Tarefas WhatsApp permanecem condicionadas a D00.4. Dependencias no mesmo dia exigem sequenciamento interno."
            )
            updated = api("PUT", task["id"], {
                "start_date": int(datetime.combine(start, time(9), TZ).timestamp() * 1000),
                "start_date_time": False,
                "due_date": int(datetime.combine(finish, time(18), TZ).timestamp() * 1000),
                "due_date_time": False,
                "description": description,
            })
            entry = {"code": code, "id": task["id"], "start": str(start), "due": str(finish),
                     "businessDayStart": first, "businessDayEnd": last,
                     "start_date": updated["start_date"], "due_date": updated["due_date"]}
            schedule["tasks"].append(entry)
            (ROOT / "docs/planning/clickup/CLICKUP_SCHEDULE_2026-11-11.json").write_text(
                json.dumps(schedule, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"Scheduled {code}: {start} - {finish}", flush=True)
    assert len(schedule["tasks"]) == 30
    print(f"Schedule applied: {START} through {days[-1]} (20 business days).")


if __name__ == "__main__":
    run()
