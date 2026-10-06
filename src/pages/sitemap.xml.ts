import type { APIRoute } from 'astro';
import { rounds, latest } from '../lib/data';

export const GET: APIRoute = ({ site }) => {
  const base = site?.toString().replace(/\/$/, '') ?? '';
  const url = (path: string, lastmod: string, priority: string) =>
    `<url><loc>${base}${path}</loc><lastmod>${lastmod}</lastmod><priority>${priority}</priority></url>`;
  const today = latest.drawDate;
  const items = [
    url('', today, '1.0'),
    url('/all', today, '0.8'),
    url('/shops', today, '0.8'),
    url('/generate', today, '0.5'),
    url('/app', today, '0.4'),
    ...rounds.map((r, i) => url(`/round/${r.round}`, r.drawDate, i === 0 ? '0.9' : i < 10 ? '0.7' : '0.5')),
  ];
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${items.join('\n')}\n</urlset>`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
