/**
 * @file site-seo.js
 * @author Aurélien Capron
 * @description Conserve les liens de langue et la compatibilité des anciennes URL.
 */
(() => {
  document.addEventListener('click', (event) => {
    const link = event.target.closest?.('a[data-site-language]');
    if (!link) return;
    try { localStorage.setItem('lang', link.dataset.siteLanguage); } catch (_) {}
  });
  const requested = new URLSearchParams(location.search).get('lang');
  if (!['fr', 'en'].includes(requested) || requested === document.documentElement.lang) return;
  const target = document.querySelector(`link[hreflang="${requested}"]`);
  if (!target) return;
  const url = new URL(target.href);
  url.hash = location.hash;
  location.replace(url.href);
})();
