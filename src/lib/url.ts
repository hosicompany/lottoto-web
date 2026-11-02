// 사이트가 하위 경로(base, 예: /lottoto-web)에 배포돼도 내부 링크·에셋이 깨지지 않게 한다.
// astro.config.mjs 의 base 를 바꾸면 여기서 자동으로 따라간다.
export const BASE = import.meta.env.BASE_URL.replace(/\/$/, '');

/** 사이트 내부 경로('/round/1248')를 base 가 붙은 경로로 바꾼다. 홈('/')은 '<base>/'. */
export const u = (path: string): string => (path === '/' ? `${BASE}/` : `${BASE}${path}`);

/** 정식 주소(canonical·sitemap·JSON-LD)용 절대 URL. */
export const abs = (site: URL | undefined, path: string): string =>
  `${site?.origin ?? ''}${u(path)}`;
