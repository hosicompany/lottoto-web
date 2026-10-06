#!/bin/bash
# 과거 회차 백필: ① 당첨 결과만 전 회차(호출 1/3) → ② 배출점을 최신부터 40회차씩, 사이사이 10분 대기.
# 동행복권 API 가 수십 회 연속 호출 뒤 응답을 늦추므로(타임아웃) 한 번에 몰지 않는다. 중단돼도 재실행하면 이어진다.
cd "$(dirname "$0")/.." || exit 1
while [ "$(ls data/rounds | wc -l)" -lt 1244 ]; do
  python3 scripts/fetch_rounds.py --from 1 --to 1239 --no-shops --max 120 --delay 1.5 2>&1 | tee -a data/fetch.log
  echo "--- 결과 $(ls data/rounds | wc -l)/1244 · 5분 대기"; sleep 300
done
echo "=== 결과 수집 완료, 배출점 보강 시작"
while python3 - <<'PY'
import json, pathlib, sys
left = sum(1 for p in pathlib.Path('data/rounds').glob('*.json') if not (d:=json.loads(p.read_text())).get('winners1') and not d.get('shopsBackfilledAt'))
print(f'배출점 미보강 {left}회차'); sys.exit(0 if left else 1)
PY
do
  python3 scripts/fetch_rounds.py --backfill-shops --max 40 --delay 1.5 2>&1 | tee -a data/fetch.log
  echo "--- 10분 대기"; sleep 600
done
echo "=== 백필 전부 완료"
