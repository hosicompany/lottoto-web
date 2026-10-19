# 로또또 웹 (lottoto-web) — 개발 가이드

> 새 세션은 이 문서 + `git log --oneline -10`을 먼저 읽는다. 앱 레포(`lotto-routine-app`)와 별개 레포다.

## 0. 정체성
로또또 앱의 **검색 유입 채널**. 동행복권 공개 API를 빌드 시점에 수집해 회차별 정적 페이지로 만든다.
수익은 AdSense(승인 전, 자리만 있음). 목적은 수익보다 Play 추천에 묶이지 않는 유입 채널 확보 — 기대 상한은 월 수만 원(2026-10-06 Ubersuggest 실측 근거).

## 1. 구조
- `scripts/fetch_rounds.py` — 수집(표준 라이브러리만). `data/rounds/<회차>.json` 이 정본, 스키마는 `normalize()`.
- `src/lib/data.ts` — JSON 을 `import.meta.glob` 으로 읽어 페이지에 공급. 포맷·집계 헬퍼.
- 페이지: `/`(최신 회차) · `/round/[n]`(핵심 유입처) · `/all`(전체 표+CSV) · `/shops`(최근 52회차 1등 배출점 누적) · `/check`(**내 번호 역대 당첨 확인** — 2026-10-19, 번호 6개를 브라우저 JS로 전 회차와 대조. 회차·날짜·번호·보너스만 추린 약 47KB 배열을 페이지에 내장, 결과 쿼리 `?n=3,11,19,27,35,44`로 공유. 앱의 '내 번호 타임머신'과 등수 규칙·고지 문구를 맞춘다. 고지에서도 `예측·확률·추천` 금지) · `/generate` · `/app` · `/sitemap.xml` · `/data/lotto.csv`.
- 디자인: 앱 `lotto_theme.dart` 토큰 그대로(블루 #3366FF, Pretendard, 다크모드 없음). Figma 시안 `https://www.figma.com/design/6UFu6PAd8aVQJsAa9D1UJC`.
- 배포: `.github/workflows/weekly.yml` — 토 21:10·일 12:00 KST 수집→커밋→빌드→GitHub Pages.

## 2. 규칙
- **카피 금지어**: 명당, 당첨 확률 높은 곳, 필승, 예측. "배출점"으로 통일. 랭킹 페이지에는 "판매량이 많을수록 높게 나타남" 고지 유지.
- 광고는 페이지당 2자리(모바일 히어로 아래 1, 데스크톱 사이드바 1). 번호 위에 두지 않는다.
- 사용자가 입력한 번호(맞춰보기·생성기)는 서버로 보내지 않는다 — 전부 브라우저 JS.
- 수집은 호출 간 지터 필수(앱에서 24h 백오프를 겪은 API). HTTP 오류면 즉시 중단.
- `site`(astro.config.mjs)·`public/robots.txt` 의 도메인은 도메인 확정 시 함께 바꾼다.

## 3. 검증 명령
```bash
npm run check     # astro check (타입)
npm run build     # 정적 빌드 — 회차 수만큼 페이지
python3 scripts/fetch_rounds.py --latest   # 수집 동작 확인
```

## 4. 남은 작업(2026-10-06)
- [ ] 도메인 결정 → `site`·robots·CNAME → GitHub Pages 커스텀 도메인
- [x] GitHub 레포 생성·푸시 — `hosicompany/lottoto-web` **비공개**(2026-10-19). ⚠️ 개인 계정의 GitHub Pages는 공개 레포에서만 무료다 — Pages를 켜기 전에 공개 전환 여부를 사용자가 정한다(코드·데이터에 비밀값 없음은 확인됨). Pages 활성화(Settings → Pages → Source: GitHub Actions)는 아직.
- [ ] Search Console·네이버 서치어드바이저 등록, 사이트맵 제출
- [ ] AdSense 신청(도메인 연결 후) → 승인 시 `Base.astro` 스크립트·`AdSlot.astro` 교체
- [ ] GA4 웹 스트림(앱과 같은 Firebase 프로젝트에 웹 앱 추가) — 유입 경로 측정
- [ ] `/app` 의 App Store 링크(심사 통과 후)
- 판정: 출시 8주 후 Search Console 노출 월 1만 미만이면 추가 투자 중단, 자동 갱신만 유지.
