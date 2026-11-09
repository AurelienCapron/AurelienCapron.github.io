#!/usr/bin/env python3
"""Contrôle le référencement public et les liens internes du portfolio.

Auteur : Aurélien Capron
Création : 9 novembre 2026

Les vérifications portent sur les pages canoniques, les variantes linguistiques,
les données structurées et les liens HTML. Elles ne prédisent pas un classement.
"""

from html import unescape
import importlib.util
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    spec = importlib.util.spec_from_file_location('portfolio_seo', root / 'scripts/seo.py')
    seo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(seo)
    expected = seo.build(root)
    seo.validate(expected)
    errors = []
    for path, content in expected.items():
        file = root / path
        if not file.exists() or file.read_bytes() != content:
            errors.append('Fichier généré désynchronisé : ' + path)
    documents = {path: seo.Document(content.decode('utf-8')) for path, content in expected.items() if path.endswith('.html')}
    sitemap = ET.fromstring(expected['sitemap.xml'])
    locations = [e.text for e in sitemap.iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
    if len(locations) != len(set(locations)) or len(locations) != 28:
        errors.append('Le sitemap doit contenir 28 URL canoniques distinctes.')
    links = 0
    for path, doc in documents.items():
        for element in doc.find('a'):
            href = unescape(element['attrs'].get('href', ''))
            parts = urlsplit(href)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            if not (parts.path.endswith('.html') or parts.path in ('/', '/en/')):
                continue
            target = parts.path.lstrip('/')
            target = target + 'index.html' if target.endswith('/') or not target else target
            if target not in documents and not (root / target).is_file():
                errors.append(path + ' : lien interne absent ' + href)
                continue
            links += 1
            if parts.fragment and target in documents:
                ids = {n['attrs'].get('id') for n in documents[target].nodes}
                if unquote(parts.fragment) not in ids:
                    errors.append(path + ' : ancre absente ' + href)
        graphs = [json.loads(doc.inner(n)) for n in doc.find('script', type='application/ld+json')]
        if not graphs:
            errors.append(path + ' : données structurées absentes.')
        if path not in ('plan-du-site.html', 'en/plan-du-site.html'):
            languages = doc.find('a')
            current = [n for n in languages if n['attrs'].get('data-site-language') and n['attrs'].get('aria-current') == 'page']
            if len(current) != 1:
                errors.append(path + ' : choix de langue courant ambigu.')
    for language in ('fr', 'en'):
        image = root / ('assets/seo/portfolio-social-' + language + '.png')
        if not image.is_file() or image.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
            errors.append('Image de partage manquante : ' + str(image))
    error_page = (root / '404.html').read_text(encoding='utf-8')
    if not re.search(r'name="robots"\s+content="noindex', error_page):
        errors.append('La page 404 doit conserver sa directive noindex.')
    if errors:
        sys.exit('\n'.join(errors))
    print('Contrôle réussi : 28 pages indexables, ' + str(links) + ' liens HTML internes, variantes FR/EN, sitemap, JSON-LD et exports synchronisés.')


if __name__ == '__main__':
    main()
