#!/usr/bin/env python3
"""동행복권 공개 API에서 회차별 당첨 결과·1등/2등 배출점을 받아 data/rounds/<회차>.json 에 저장한다.

- 표준 라이브러리만 사용한다(빌드 환경에 pip 의존 없음).
- 이미 저장된 회차는 건너뛴다(재실행 안전). 최신 회차는 미공개일 수 있어 응답에 없으면 멈춘다.
- 호출 사이에 지터를 둔다. 앱에서 레이트리밋을 겪은 적이 있어(24h 백오프) 한 번에 몰아치지 않는다.

사용법:
  python3 scripts/fetch_rounds.py                # 저장 안 된 회차를 최신부터 거꾸로 수집
  python3 scripts/fetch_rounds.py --from 1 --to 1244
  python3 scripts/fetch_rounds.py --latest       # 최신 회차 1개만(토요일 밤 갱신용)
  python3 scripts/fetch_rounds.py --max 50       # 이번 실행 상한
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import http.client
from pathlib import Path

HOST = "https://www.dhlottery.co.kr"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "rounds"
FIRST_DRAW = "20021207"  # 1회 추첨일(토)

HEADERS_BASE = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": "LottoTtoWeb/1.0 (+https://github.com/hosicompany)",
    "X-Requested-With": "XMLHttpRequest",
}


def get_json(path: str, query: dict, referer: str, timeout: int = 75) -> dict:
    url = f"{HOST}{path}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={**HEADERS_BASE, "Referer": referer})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        body = res.read().decode("utf-8")
    if body.lstrip().startswith("<"):
        raise RuntimeError("JSON이 아닌 응답(HTML) — 차단 가능성")
    return json.loads(body)


def fetch_result(round_no: int) -> dict | None:
    data = get_json(
        "/lt645/selectPstLt645Info.do",
        {"srchLtEpsd": round_no},
        referer=f"{HOST}/lt645/result",
    )
    items = (data.get("data") or {}).get("list") or []
    for it in items:
        if int(it.get("ltEpsd", -1)) == round_no:
            return it
    return None  # 요청 회차가 목록에 없으면 미공개(직전 회차가 오는 경우가 있어 직접 대조)


def fetch_shops(round_no: int, rank: int) -> list[dict]:
    data = get_json(
        "/wnprchsplcsrch/selectLtWnShp.do",
        {"srchLtEpsd": round_no, "srchWnShpRnk": rank},
        referer=f"{HOST}/wnprchsplcsrch/home",
    )
    items = (data.get("data") or {}).get("list") or []
    return [
        {
            "id": str(it.get("ltShpId") or ""),
            "name": (it.get("shpNm") or "").strip(),
            "address": (it.get("shpAddr") or "").strip(),
            "region": (it.get("region") or "").strip(),
            "purchaseType": (it.get("atmtPsvYnTxt") or "").strip() or None,
            "phone": (it.get("shpTelno") or "").strip() or None,
            "lat": it.get("shpLat"),
            "lng": it.get("shpLot"),
        }
        for it in items
    ]


def normalize(raw: dict, shops1: list[dict], shops2: list[dict]) -> dict:
    ymd = str(raw["ltRflYmd"])
    numbers = sorted(int(raw[f"tm{i}WnNo"]) for i in range(1, 7))
    prizes = []
    for rank in range(1, 6):
        prizes.append(
            {
                "rank": rank,
                "winners": int(raw.get(f"rnk{rank}WnNope") or 0),
                "amount": int(raw.get(f"rnk{rank}WnAmt") or 0),
                "total": int(raw.get(f"rnk{rank}SumWnAmt") or 0),
            }
        )
    return {
        "round": int(raw["ltEpsd"]),
        "drawDate": f"{ymd[0:4]}-{ymd[4:6]}-{ymd[6:8]}",
        "numbers": numbers,
        "bonus": int(raw["bnsWnNo"]),
        "prizes": prizes,
        "totalSales": int(raw.get("wholEpsdSumNtslAmt") or 0),
        "winners1": shops1,
        "winners2": shops2,
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def estimate_latest_round(today: time.struct_time | None = None) -> int:
    """1회(2002-12-07) 기준 주 단위로 최신 회차를 추정한다(추첨 전이면 1 작게 나올 수 있음)."""
    import datetime as dt

    first = dt.date(2002, 12, 7)
    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    today_d = now.date()
    weeks = (today_d - first).days // 7
    # 토요일 20:45 이전이면 이번 주 회차는 아직 없다.
    if today_d.weekday() == 5 and (now.hour, now.minute) < (20, 50):
        weeks -= 1
    return 1 + weeks


def sleep_jitter(base: float) -> None:
    time.sleep(base + random.uniform(0.2, 0.8))


def collect_round(round_no: int, delay: float, with_shops: bool = True) -> bool:
    out = OUT / f"{round_no}.json"
    if out.exists():
        return True
    raw = fetch_result(round_no)
    if raw is None:
        print(f"[{round_no}] 미공개 — 건너뜀", file=sys.stderr)
        return False
    shops1: list[dict] = []
    shops2: list[dict] = []
    if with_shops:
        sleep_jitter(delay)
        shops1 = fetch_shops(round_no, 1)
        sleep_jitter(delay)
        shops2 = fetch_shops(round_no, 2)
    doc = normalize(raw, shops1, shops2)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[{round_no}] 저장 — {doc['drawDate']} 1등 {len(shops1)}곳 2등 {len(shops2)}곳")
    return True


def backfill_shops(rounds: list[int], limit: int, delay: float) -> int:
    """`--no-shops` 로 받은 회차에 배출점을 채운다. 최신 회차부터, 상한까지만."""
    done = 0
    failures = 0
    for r in rounds:
        path = OUT / f"{r}.json"
        if not path.exists():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("winners1") or doc.get("shopsBackfilledAt"):
            continue
        if done >= limit:
            print(f"상한 {limit}회차 도달", file=sys.stderr)
            break
        try:
            doc["winners1"] = fetch_shops(r, 1)
            sleep_jitter(delay)
            doc["winners2"] = fetch_shops(r, 2)
        except urllib.error.HTTPError as e:
            print(f"[{r}] HTTP {e.code} — 중단", file=sys.stderr)
            return 2
        except (urllib.error.URLError, TimeoutError, RuntimeError, http.client.HTTPException, OSError) as e:
            failures += 1
            print(f"[{r}] 배출점 실패: {e}", file=sys.stderr)
            if failures >= 3:
                return 2
            sleep_jitter(delay * 5)
            continue
        doc["shopsBackfilledAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")  # 빈 결과도 '시도함'으로 남겨 무한 재시도 방지
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[{r}] 배출점 보강 — 1등 {len(doc['winners1'])}곳 2등 {len(doc['winners2'])}곳")
        done += 1
        failures = 0
        sleep_jitter(delay)
    print(f"배출점 보강 완료: {done}회차")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int)
    ap.add_argument("--to", dest="end", type=int)
    ap.add_argument("--latest", action="store_true", help="최신 회차 1개만")
    ap.add_argument("--max", type=int, default=400, help="이번 실행에서 새로 받을 회차 상한")
    ap.add_argument("--delay", type=float, default=1.0, help="호출 간 기본 대기(초)")
    ap.add_argument("--no-shops", action="store_true", help="당첨 결과만(호출 1/3) — 배출점은 --backfill-shops 로 나중에")
    ap.add_argument("--backfill-shops", action="store_true", help="배출점이 빈 저장 회차에 배출점만 채운다")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    latest = estimate_latest_round()
    if args.latest:
        rounds = [latest + 1, latest]  # 추정이 1 작을 수 있어 하나 위도 시도
    elif args.start or args.end:
        s, e = args.start or 1, args.end or latest
        rounds = list(range(e, s - 1, -1))
    else:
        rounds = list(range(latest + 1, 0, -1))

    if args.backfill_shops:
        return backfill_shops(rounds, args.max, args.delay)

    done = 0
    failures = 0
    for r in rounds:
        if (OUT / f"{r}.json").exists():
            continue
        if done >= args.max:
            print(f"상한 {args.max}회차 도달 — 다음 실행에서 이어서 수집", file=sys.stderr)
            break
        try:
            ok = collect_round(r, args.delay, with_shops=not args.no_shops)
        except urllib.error.HTTPError as e:
            print(f"[{r}] HTTP {e.code} — 중단(레이트리밋 가능성)", file=sys.stderr)
            return 2
        except (urllib.error.URLError, TimeoutError, RuntimeError, http.client.HTTPException, OSError) as e:
            failures += 1
            print(f"[{r}] 실패: {e}", file=sys.stderr)
            if failures >= 3:
                print("연속 실패 3회 — 중단", file=sys.stderr)
                return 2
            sleep_jitter(args.delay * 5)
            continue
        if ok:
            done += 1
            failures = 0
        elif r <= latest - 1:
            # 최신 추정 바로 아래까지 미공개면 더 내려가도 의미 없음(과거 회차는 항상 있음)
            print(f"[{r}] 과거 회차가 비어 있음 — 응답 이상, 중단", file=sys.stderr)
            return 2
        sleep_jitter(args.delay)
    print(f"완료: 새로 {done}회차, 저장된 파일 {len(list(OUT.glob('*.json')))}개")
    return 0


if __name__ == "__main__":
    sys.exit(main())
