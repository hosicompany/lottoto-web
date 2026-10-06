import type { APIRoute } from 'astro';
import { rounds } from '../../lib/data';

// 전체 회차 CSV (엑셀에서 바로 열리도록 UTF-8 BOM). "당첨번호 엑셀" 검색 수요 대응.
export const GET: APIRoute = () => {
  const header = ['회차', '추첨일', '번호1', '번호2', '번호3', '번호4', '번호5', '번호6', '보너스', '1등당첨자', '1등당첨금', '2등당첨자', '2등당첨금', '3등당첨자', '3등당첨금', '총판매금액'];
  const lines = [header.join(',')];
  for (const r of [...rounds].sort((a, b) => a.round - b.round)) {
    const p = (k: number) => r.prizes[k - 1] ?? { winners: 0, amount: 0 };
    lines.push([r.round, r.drawDate, ...r.numbers, r.bonus, p(1).winners, p(1).amount, p(2).winners, p(2).amount, p(3).winners, p(3).amount, r.totalSales].join(','));
  }
  return new Response('﻿' + lines.join('\r\n'), {
    headers: { 'Content-Type': 'text/csv; charset=utf-8' },
  });
};
