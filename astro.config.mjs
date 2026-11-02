// @ts-check
import { defineConfig } from 'astro/config';

// GitHub Pages 프로젝트 사이트(https://hosicompany.github.io/lottoto-web). 내부 링크는 src/lib/url.ts 의 u() 로 base 를 붙인다.
// 정식 도메인이 정해지면 site 를 그 도메인으로, base 를 지우고 public/robots.txt 의 Sitemap 도 같이 고친다.
export default defineConfig({
  site: 'https://hosicompany.github.io',
  base: '/lottoto-web',
  output: 'static',
  trailingSlash: 'never',
  build: { format: 'file' },
  compressHTML: true,
});
