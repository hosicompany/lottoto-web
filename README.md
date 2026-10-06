# 로또또 웹

로또 회차별 당첨번호·당첨금·1등 배출점 정적 사이트. 자세한 운영 규칙은 `CLAUDE.md`.

```bash
npm install
python3 scripts/fetch_rounds.py --latest   # 데이터 수집
npm run dev                                # http://localhost:4321
npm run build
```
