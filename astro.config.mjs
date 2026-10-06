// @ts-check
import { defineConfig } from 'astro/config';

// 도메인 확정 전 임시 값. 확정되면 site 를 바꾸고 public/robots.txt 의 Sitemap 도 같이 고친다.
export default defineConfig({
  site: 'https://lottoto.pages.dev',
  output: 'static',
  trailingSlash: 'never',
  build: { format: 'file' },
  compressHTML: true,
});
