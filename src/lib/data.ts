// data/rounds/*.json 을 빌드 시점에 한 번 읽어 페이지들이 공유한다.
// 수집 스키마는 scripts/fetch_rounds.py normalize() 가 정본.

export interface Shop {
  id: string;
  name: string;
  address: string;
  region: string;
  purchaseType: string | null; // 자동·수동·반자동
  phone: string | null;
  lat: number | null;
  lng: number | null;
}

export interface Prize {
  rank: number;
  winners: number;
  amount: number; // 1인당
  total: number; // 등수별 총액
}

export interface Round {
  round: number;
  drawDate: string; // YYYY-MM-DD
  numbers: number[]; // 오름차순 6개
  bonus: number;
  prizes: Prize[];
  totalSales: number;
  winners1: Shop[];
  winners2: Shop[];
  fetchedAt: string;
}

const modules = import.meta.glob<Round>('../../data/rounds/*.json', {
  eager: true,
  import: 'default',
});

/** 최신 회차가 앞에 오도록 정렬된 전체 목록 */
export const rounds: Round[] = Object.values(modules).sort((a, b) => b.round - a.round);
export const latest: Round = rounds[0];
export const byRound = new Map(rounds.map((r) => [r.round, r]));

export function prevNext(r: Round): { prev?: Round; next?: Round } {
  return { prev: byRound.get(r.round - 1), next: byRound.get(r.round + 1) };
}

export const ballColor = (n: number): string =>
  n <= 10 ? 'y' : n <= 20 ? 'b' : n <= 30 ? 'r' : n <= 40 ? 'g' : 'gr';

const WEEKDAY = ['일', '월', '화', '수', '목', '금', '토'];

export function formatDate(iso: string, withWeekday = true): string {
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  const base = `${y}년 ${m}월 ${d}일`;
  return withWeekday ? `${base} (${WEEKDAY[dt.getUTCDay()]})` : base;
}

export function formatShortDate(iso: string): string {
  const [y, m, d] = iso.split('-');
  return `${y}.${m}.${d}`;
}

/** 원 단위를 '23억 5,210만 원' 식으로. 만 원 미만은 '5,000원'. */
export function formatWon(won: number): string {
  if (won <= 0) return '—';
  if (won < 10_000) return `${won.toLocaleString('ko-KR')}원`;
  const eok = Math.floor(won / 100_000_000);
  const man = Math.floor((won % 100_000_000) / 10_000);
  const parts: string[] = [];
  if (eok > 0) parts.push(`${eok.toLocaleString('ko-KR')}억`);
  if (man > 0) parts.push(`${man.toLocaleString('ko-KR')}만`);
  return `${parts.join(' ')} 원`;
}

export const formatCount = (n: number): string => `${n.toLocaleString('ko-KR')}명`;

export const PRIZE_CONDITION: Record<number, string> = {
  1: '6개 일치',
  2: '5개 + 보너스',
  3: '5개 일치',
  4: '4개 일치',
  5: '3개 일치',
};

/** 지역별 1등 배출점 수 (많은 순) */
export function regionCounts(shops: Shop[]): Array<[string, number]> {
  const m = new Map<string, number>();
  for (const s of shops) m.set(s.region || '기타', (m.get(s.region || '기타') ?? 0) + 1);
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
}

export function purchaseSummary(shops: Shop[]): string {
  const m = new Map<string, number>();
  for (const s of shops) m.set(s.purchaseType ?? '미상', (m.get(s.purchaseType ?? '미상') ?? 0) + 1);
  const order = ['자동', '수동', '반자동', '미상'];
  return order
    .filter((k) => m.has(k))
    .map((k) => `${k} ${m.get(k)}`)
    .join(' · ');
}

/** 판매점 키: id 가 비거나 재발급될 수 있어 상호|주소 정규화로 묶는다(앱 hall_of_fame_store 와 같은 규칙). */
export function shopKey(s: Shop): string {
  const norm = (v: string) => v.replace(/\s+/g, '').toLowerCase();
  return `${norm(s.name)}|${norm(s.address)}`;
}

export interface HallEntry {
  key: string;
  name: string;
  address: string;
  region: string;
  rounds: number[]; // 1등 배출 회차(최신순)
}

/** 동행복권 온라인 판매(인터넷 복권판매사이트)는 판매점이 아니므로 랭킹에서 뺀다 */
export const isOnlineShop = (s: Shop): boolean => /인터넷\s*복권판매사이트|dhlottery/.test(`${s.name} ${s.address}`);

/** 최근 window 회차의 1등 배출 이력을 판매점별로 누적(온라인 판매 제외) */
export function hallOfFame(window = 52): HallEntry[] {
  const m = new Map<string, HallEntry>();
  for (const r of rounds.slice(0, window)) {
    const seen = new Set<string>();
    for (const s of r.winners1) {
      if (isOnlineShop(s)) continue;
      const k = shopKey(s);
      if (seen.has(k)) continue; // 같은 회차에 여러 게임 당첨은 1회차로
      seen.add(k);
      const e = m.get(k) ?? { key: k, name: s.name, address: s.address, region: s.region, rounds: [] };
      e.rounds.push(r.round);
      m.set(k, e);
    }
  }
  return [...m.values()].sort((a, b) => b.rounds.length - a.rounds.length || b.rounds[0] - a.rounds[0]);
}

/** 네이버지도 모바일 검색 URL (앱 shopMapSearchUrl 과 동일 규칙: 좌표 없으면 상호+주소 검색) */
export function mapUrl(s: Shop): string {
  const q = encodeURIComponent(`${s.name} ${s.address}`.trim());
  return `https://m.map.naver.com/search2/search.naver?query=${q}`;
}

/** 번호 6개와 회차를 대조해 등수(1~5) 또는 0 */
export function matchRank(nums: number[], r: Round): number {
  const hit = nums.filter((n) => r.numbers.includes(n)).length;
  const bonus = nums.includes(r.bonus);
  if (hit === 6) return 1;
  if (hit === 5 && bonus) return 2;
  if (hit === 5) return 3;
  if (hit === 4) return 4;
  if (hit === 3) return 5;
  return 0;
}
