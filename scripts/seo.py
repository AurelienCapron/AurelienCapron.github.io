#!/usr/bin/env python3
"""Construit le référencement et les versions anglaises du portfolio statique.

Auteur : Aurélien Capron
Création : 9 novembre 2026

Les pages françaises et leurs dictionnaires anglais restent les sources du site.
Le générateur ne dépend que de la bibliothèque standard de Python 3. Il conserve
les médias, les interactions et les dates de création déjà documentées. Une
sauvegarde précède toute écriture ; --check vérifie les fichiers sans les modifier.
"""

import argparse
import ast
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET


BASE = 'https://aureliencapron.github.io/'
PERSON = BASE + '#aurelien-capron'
PROJECTS = ['telecommande', 'amplificateur', 'tipe', 'domethic', 'poulailler', 'backyard']
HOBBIES = ['sacha-heritage', 'bds', 'judo', 'perouges', 'saxhorn']
PAGES = ['index'] + PROJECTS + HOBBIES + ['mentions-legales']
LABELS = {
    'index': ('Accueil', 'Home'),
    'telecommande': ('Télécommande autonome', 'Autonomous infrared remote'),
    'amplificateur': ('Amplificateur audio piézoélectrique', 'Piezoelectric audio amplifier'),
    'tipe': ('TIPE : vision et lanceur de badminton', 'TIPE: vision and badminton launcher'),
    'domethic': ('Myha · Domethic System', 'Myha · Domethic System'),
    'poulailler': ('Porte de poulailler automatisée', 'Automatic chicken coop door'),
    'backyard': ('Chronométrage Backyard Ultra', 'Backyard Ultra race timing'),
    'sacha-heritage': ('Sacha Heritage', 'Sacha Heritage'),
    'bds': ('Bureau des Sports de Phelma', 'Phelma Sports Office'),
    'judo': ('Judo et vie de club', 'Judo and club life'),
    'perouges': ('Salon du mariage de Pérouges', 'Pérouges wedding fair'),
    'saxhorn': ('Saxhorn alto et musique', 'Tenor horn and music'),
    'mentions-legales': ('Mentions légales et confidentialité', 'Legal notice and privacy'),
}
META = {
    'index': (
        ('Aurélien Capron | Portfolio élève-ingénieur en électronique',
         'Portfolio d’Aurélien Capron, élève-ingénieur à Phelma : électronique, systèmes embarqués, prototypes et essais. Six projets et leurs résultats documentés.'),
        ('Aurélien Capron | Electronics Engineering Student Portfolio',
         'Aurélien Capron’s portfolio: electronics and embedded systems at Phelma, prototype building and bench testing. Six projects with documented contributions and results.')),
    'telecommande': (
        ('Télécommande infrarouge autonome | Aurélien Capron',
         'Projet Phelma : commande autonome de vidéoprojecteurs, rétro-ingénierie infrarouge NEC, PCB KiCad et Pico 2WH. Coordination, intégration et démonstration.'),
        ('Autonomous Infrared Projector Remote | Aurélien Capron',
         'Phelma project: autonomous projector control, NEC infrared reverse engineering, KiCad PCB and Pico 2WH. Project coordination, integration and demonstration.')),
    'amplificateur': (
        ('Amplificateur audio : KiCad, SPICE et essais | Aurélien Capron',
         'Du capteur piézo au haut-parleur : deux cartes CMS, correcteur de Baxandall et amplification. Conception en binôme, simulations et mesures sur banc.'),
        ('Audio Amplifier: KiCad, SPICE and Testing | Aurélien Capron',
         'From piezo pickup to loudspeaker: two SMD boards, Baxandall tone control and amplification. Paired design work, simulations and bench measurements.')),
    'tipe': (
        ('TIPE : stéréovision et lanceur de badminton | Aurélien Capron',
         'Python, OpenCV et Arduino pour localiser un joueur de badminton : calibration, triangulation et prototype testé. Résultats et limites de l’automatisation.'),
        ('TIPE: Stereo Vision and Badminton Launcher | Aurélien Capron',
         'Python, OpenCV and Arduino for badminton player localisation: calibration, triangulation and a tested prototype. Results and limits of automatic shot control.')),
    'domethic': (
        ('Myha : assemblage et essais électroniques | Aurélien Capron',
         'Ma contribution chez Domethic System depuis 2022 : assemblage des centrales Myha, configuration, appairage radio et essais de robustesse sur charges réelles.'),
        ('Myha: Electronics Assembly and Testing | Aurélien Capron',
         'My contribution at Domethic System since 2022: Myha controller assembly, configuration, radio pairing and robustness tests with real loads.')),
    'poulailler': (
        ('Porte de poulailler automatisée : ATmega328P | Aurélien Capron',
         'Projet personnel : pont-levis motorisé, mesure de luminosité, ATmega328P, relais et contact de fermeture. Mécanique, électronique et programme embarqué.'),
        ('Automatic Chicken Coop Door: ATmega328P | Aurélien Capron',
         'Personal project: motorised drawbridge, light sensing, ATmega328P, relays and a closed-position switch. Mechanics, electronics and embedded programming.')),
    'backyard': (
        ('Chronométrage Backyard Ultra : Python et Flask | Aurélien Capron',
         'Système de pointage Python/Flask utilisé à la Backyard Phelma : saisie multi-postes, suivi des coureurs, affichage public et export des résultats.'),
        ('Backyard Ultra Timing: Python and Flask | Aurélien Capron',
         'Python/Flask timing system used at Phelma’s Backyard Ultra: multi-desk bib entry, runner tracking, public displays and results export.')),
}
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
LITERAL = r"'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\""
PAIR = re.compile('(?P<key>' + LITERAL + r'|[A-Za-z_$][\w$]*)\s*:\s*(?P<value>' + LITERAL + ')', re.S)
ASSIGN = re.compile(r'EN\[\s*(?P<key>' + LITERAL + r')\s*\]\s*=\s*(?P<value>' + LITERAL + ')', re.S)


class Document(HTMLParser):
    """Repère les limites des éléments sans réécrire le HTML existant."""

    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.offsets = [0]
        for match in re.finditer('\n', source):
            self.offsets.append(match.end())
        self.nodes = []
        self.stack = []
        self.feed(source)

    def position(self):
        row, column = self.getpos()
        return self.offsets[row - 1] + column

    def handle_starttag(self, tag, attrs):
        start = self.position()
        node = {'tag': tag, 'attrs': dict(attrs), 'start': start,
                'open_end': start + len(self.get_starttag_text()), 'end': None, 'close': None}
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)
        else:
            node['end'] = node['close'] = node['open_end']

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.stack and self.stack[-1]['tag'] == tag:
            node = self.stack.pop()
            node['end'] = node['close'] = node['open_end']

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]['tag'] == tag:
                node = self.stack[i]
                node['close'] = self.position()
                node['end'] = self.source.index('>', node['close']) + 1
                del self.stack[i:]
                break

    def find(self, tag=None, **attrs):
        return [n for n in self.nodes if (tag is None or n['tag'] == tag)
                and all(n['attrs'].get(k) == v for k, v in attrs.items())]

    def inner(self, node):
        return self.source[node['open_end']:node['close']]


def text(value):
    """Retourne un texte décodé et compact pour les métadonnées et exports."""
    return ' '.join(unescape(re.sub('<[^>]+>', ' ', value)).split())


def replace_ranges(source, changes):
    """Applique des remplacements non chevauchants depuis la fin du document."""
    for start, end, value in sorted(changes, reverse=True):
        source = source[:start] + value + source[end:]
    return source


def english_dictionary(source):
    """Lit les chaînes des dictionnaires anglais, sans exécuter de JavaScript."""
    if 'const EN = ' not in source or 'const DICT' not in source:
        raise ValueError('Dictionnaire de traduction introuvable.')
    block = source.split('const EN = ', 1)[1].split('const DICT', 1)[0]
    result = {}
    for match in sorted([*PAIR.finditer(block), *ASSIGN.finditer(block)], key=lambda m: m.start()):
        key = match['key']
        key = ast.literal_eval(key) if key[0] in "\"'" else key
        result[key] = ast.literal_eval(match['value'])
    return result


def page_url(slug, language='fr'):
    prefix = 'en/' if language == 'en' else ''
    return BASE + prefix + ('' if slug == 'index' else slug + '.html')


def local_url(value, language='fr'):
    """Garde les ressources communes et les liens internes dans la bonne langue."""
    if not value or value.startswith(('#', '//', 'data:', 'mailto:', 'tel:', 'javascript:')):
        return value
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        return value
    path = parts.path
    suffix = ('?' + parts.query if parts.query else '') + ('#' + parts.fragment if parts.fragment else '')
    site_path = path.lstrip('/')
    if site_path.startswith('en/'):
        site_path = site_path[3:]
    if site_path in ('', 'index.html'):
        return ('/en/' if language == 'en' else '/') + suffix
    if site_path.endswith('.html') and site_path[:-5] in PAGES + ['plan-du-site']:
        return ('/en/' if language == 'en' else '/') + site_path + suffix
    if value.startswith('/'):
        return value
    return '/' + path + suffix


def set_attribute(tag, key, value):
    """Écrit un attribut en conservant les autres attributs de la balise."""
    pattern = re.compile(r'\s' + re.escape(key) + r'\s*=\s*(?:"[^"]*"|\x27[^\x27]*\x27)', re.I)
    addition = ' ' + key + '="' + escape(str(value), quote=True) + '"'
    if pattern.search(tag):
        return pattern.sub(lambda _: addition, tag, count=1)
    return re.sub(r'\s*/?>$', lambda m: addition + m[0], tag)


def translate(source, translations):
    """Matérialise l’anglais dans le HTML envoyé, y compris sans JavaScript."""
    doc = Document(source)
    changes = []
    rich_text = 'el.innerHTML = v' in source
    for node in doc.nodes:
        key = node['attrs'].get('data-i18n')
        if key:
            if key not in translations:
                raise ValueError('Traduction anglaise manquante : ' + key)
            if node['close'] is None:
                raise ValueError('Élément traduisible non fermé : ' + key)
            value = translations[key]
            changes.append((node['open_end'], node['close'], value if rich_text else escape(value)))
        aria_key = node['attrs'].get('data-i18n-aria')
        aria_labels = {
            'Navigation principale': 'Main navigation', 'Langue / Language': 'Language',
            'Basculer le thème clair/sombre': 'Toggle light/dark theme',
            'Profil LinkedIn': 'LinkedIn profile', 'Profil GitHub': 'GitHub profile',
            'Envoyer un email': 'Send an email', 'Appeler': 'Call', 'Retour en haut': 'Back to top',
            'Navigation entre les loisirs / Interest navigation': 'Interest navigation',
            'Navigation entre les projets': 'Project navigation', 'Fermer / Close': 'Close',
        }
        if aria_key:
            tag = source[node['start']:node['open_end']]
            tag = set_attribute(tag, 'aria-label', translations[aria_key])
            changes.append((node['start'], node['open_end'], tag))
        elif node['attrs'].get('aria-label') in aria_labels:
            tag = source[node['start']:node['open_end']]
            tag = set_attribute(tag, 'aria-label', aria_labels[node['attrs']['aria-label']])
            changes.append((node['start'], node['open_end'], tag))
    return replace_ranges(source, changes)


def fix_resource_paths(source, language):
    doc = Document(source)
    changes = []
    for node in doc.nodes:
        original = source[node['start']:node['open_end']]
        tag = original
        for attr in ('href', 'src', 'poster'):
            value = node['attrs'].get(attr)
            if value:
                tag = set_attribute(tag, attr, local_url(value, language))
        if node['attrs'].get('srcset'):
            value = ', '.join(' '.join([local_url(item.split()[0], language)] + item.split()[1:])
                              for item in node['attrs']['srcset'].split(','))
            tag = set_attribute(tag, 'srcset', value)
        if tag != original:
            changes.append((node['start'], node['open_end'], tag))
    source = replace_ranges(source, changes)
    # Les URL présentes dans les styles et scripts restent relatives à la racine.
    source = re.sub(r'(?P<quote>[\"\x27])assets/', lambda m: m['quote'] + '/assets/', source)
    return source


def clean_managed(source):
    # Deux valeurs restent disponibles comme sources au passage suivant.
    def preserve_meta(match):
        return '\n' + '\n'.join(re.findall(r'<meta\b[^>]*(?:name="description"|property="og:image")[^>]*>', match[0])) + '\n'
    source = re.sub(r'\s*<!-- seo:head:start -->[\s\S]*?<!-- seo:head:end -->', preserve_meta, source)
    # Le lien du plan du site inséré dans la ligne des mentions est retiré tel quel.
    source = re.sub(r'<!-- seo:footer-link:start -->[\s\S]*?<!-- seo:footer-link:end -->', '', source)
    for name in ('breadcrumb', 'footer'):
        source = re.sub(r'\s*<!-- seo:' + name + r':start -->[\s\S]*?<!-- seo:' + name + r':end -->\s*', '\n', source)
    source = re.sub(r'\s*/\* seo:translations:start \*/[\s\S]*?/\* seo:translations:end \*/\s*', '\n', source)
    return source


def metadata(source, slug):
    doc = Document(source)
    title = text(doc.inner(doc.find('title')[0]))
    description = next(n['attrs']['content'] for n in doc.find('meta', name='description'))
    image = next((n['attrs']['content'] for n in doc.find('meta', property='og:image')), '')
    modified = re.search(r'@updated\s+(\d{4}-\d{2}-\d{2})', source)
    published = re.search(r'@created\s+(\d{4}-\d{2}-\d{2})', source)
    summaries = {}
    for n in doc.nodes:
        key = n['attrs'].get('data-i18n', '')
        if key.startswith('brief.value.'):
            summaries[key.rsplit('.', 1)[-1]] = text(doc.inner(n))
    return {'slug': slug, 'title': title, 'description': description, 'image': image,
            'modified': modified[1] if modified else None,
            'published': published[1] if published else None, 'summary': summaries,
            'heading': text(doc.inner(doc.find('h1')[0]))}


def schema(data, language, image):
    slug = data['slug']; url = page_url(slug, language)
    name = LABELS[slug][language == 'en']
    person = {'@type': 'Person', '@id': PERSON, 'name': 'Aurélien Capron', 'url': BASE,
              'jobTitle': 'Élève-ingénieur — Systèmes Électroniques Intégrés',
              'affiliation': {'@type': 'CollegeOrUniversity', 'name': 'Grenoble INP – Phelma'},
              'sameAs': ['https://github.com/AurelienCapron', 'https://www.linkedin.com/in/aurelien-capron'],
              'knowsAbout': ['Électronique', 'Systèmes embarqués', 'KiCad', 'Python', 'C/C++', 'Arduino', 'Essais sur banc']}
    website = {'@type': 'WebSite', '@id': BASE + '#website', 'url': BASE,
               'name': 'Aurélien Capron — Portfolio', 'inLanguage': ['fr', 'en'], 'publisher': {'@id': PERSON}}
    page = {'@type': 'ProfilePage' if slug == 'index' else 'WebPage', '@id': url + '#webpage',
            'url': url, 'name': data['title'], 'description': data['description'], 'inLanguage': language,
            'isPartOf': {'@id': BASE + '#website'}, 'author': {'@id': PERSON},
            'primaryImageOfPage': {'@type': 'ImageObject', 'url': image}}
    if data['modified']: page['dateModified'] = data['modified']
    if data['published']: page['datePublished'] = data['published']
    graph = [website, person, page]
    if slug == 'index':
        page['mainEntity'] = {'@id': PERSON}
        page['hasPart'] = [{'@id': page_url(p, language) + '#webpage'} for p in PROJECTS + HOBBIES]
    elif slug in PROJECTS + HOBBIES:
        category = ('Projets', 'Projects') if slug in PROJECTS else ('Loisirs et engagements', 'Activities and involvement')
        anchor = '#projets' if slug in PROJECTS else '#hobbies'
        breadcrumb = {'@type': 'BreadcrumbList', '@id': url + '#breadcrumb', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': LABELS['index'][language == 'en'], 'item': page_url('index', language)},
            {'@type': 'ListItem', 'position': 2, 'name': category[language == 'en'], 'item': page_url('index', language) + anchor},
            {'@type': 'ListItem', 'position': 3, 'name': name, 'item': url}]}
        article = {'@type': 'TechArticle' if slug in PROJECTS else 'Article', '@id': url + '#case-study',
                   'headline': data['heading'], 'description': data['description'], 'inLanguage': language,
                   'author': {'@id': PERSON}, 'mainEntityOfPage': {'@id': url + '#webpage'},
                   'image': image, 'articleSection': category[language == 'en']}
        if data['modified']: article['dateModified'] = data['modified']
        if data['published']: article['datePublished'] = data['published']
        if data['summary']:
            article['abstract'] = ' '.join(data['summary'].values())
        page['mainEntity'] = {'@id': article['@id']}
        page['breadcrumb'] = {'@id': breadcrumb['@id']}
        graph += [breadcrumb, article]
    return {'@context': 'https://schema.org', '@graph': graph}


def page_head(source, data, language, image):
    """Émet un jeu unique et cohérent de métadonnées, indépendant du navigateur."""
    doc = Document(source); changes = []
    for node in doc.nodes:
        attrs = node['attrs']
        if node['tag'] == 'meta' and (attrs.get('property', '').startswith('og:') or
                attrs.get('name', '').startswith('twitter:') or attrs.get('name') in ('description', 'robots', 'author')):
            changes.append((node['start'], node['open_end'], ''))
        if node['tag'] == 'link' and attrs.get('rel') in ('canonical', 'alternate'):
            changes.append((node['start'], node['open_end'], ''))
        if node['tag'] == 'script' and attrs.get('type') == 'application/ld+json':
            changes.append((node['start'], node['end'], ''))
    source = replace_ranges(source, changes)
    source = re.sub(r'<title>[\s\S]*?</title>', '<title>' + escape(data['title']) + '</title>', source, count=1)
    source = re.sub(r'<html\b[^>]*>', lambda m: set_attribute(m[0], 'lang', language), source, count=1)
    url = page_url(data['slug'], language)
    metas = [('name', 'description', data['description']), ('name', 'author', 'Aurélien Capron'),
             ('name', 'robots', 'index, follow, max-image-preview:large'),
             ('property', 'og:type', 'website' if data['slug'] in ('index', 'mentions-legales') else 'article'),
             ('property', 'og:site_name', 'Aurélien Capron — Portfolio'),
             ('property', 'og:title', data['title']), ('property', 'og:description', data['description']),
             ('property', 'og:url', url), ('property', 'og:image', image),
             ('property', 'og:image:alt', LABELS[data['slug']][language == 'en'] + ' — Aurélien Capron'),
             ('property', 'og:locale', 'en_US' if language == 'en' else 'fr_FR'),
             ('property', 'og:locale:alternate', 'fr_FR' if language == 'en' else 'en_US'),
             ('name', 'twitter:card', 'summary_large_image'), ('name', 'twitter:title', data['title']),
             ('name', 'twitter:description', data['description']), ('name', 'twitter:image', image),
             ('name', 'twitter:image:alt', LABELS[data['slug']][language == 'en'] + ' — Aurélien Capron')]
    if '/assets/seo/portfolio-social-' in image:
        metas.extend([('property', 'og:image:width', '1200'),
                      ('property', 'og:image:height', '630'),
                      ('property', 'og:image:type', 'image/png')])
    head = '\n    <!-- seo:head:start -->\n'
    for attr, key, value in metas:
        head += '    <meta ' + attr + '="' + key + '" content="' + escape(value, quote=True) + '" />\n'
    head += '    <link rel="canonical" href="' + url + '" />\n'
    for lang in ('fr', 'en'):
        head += '    <link rel="alternate" hreflang="' + lang + '" href="' + page_url(data['slug'], lang) + '" />\n'
    head += '    <link rel="alternate" hreflang="x-default" href="' + page_url(data['slug']) + '" />\n'
    head += '    <link rel="stylesheet" href="/assets/site-seo.css" />\n'
    head += '    <link rel="describedby" href="/portfolio.json" type="application/json" title="Portfolio data" />\n'
    head += '    <script src="/assets/site-seo.js" defer></script>\n'
    head += '    <script type="application/ld+json">\n' + json.dumps(schema(data, language, image), ensure_ascii=False, indent=2).replace('</', '<\\/') + '\n    </script>\n'
    head += '    <noscript><style>.reveal{opacity:1!important;transform:none!important}.typewriter{max-width:none!important;animation:none!important}</style></noscript>\n'
    head += '    <!-- seo:head:end -->\n'
    return re.sub(r'\s*</head>', lambda _: head + '  </head>', source, count=1)


def language_links(source, slug, language):
    """Les langues utilisent de vrais liens, utilisables au clavier et sans script."""
    doc = Document(source); changes = []
    for node in doc.nodes:
        if node['tag'] not in ('button', 'a'):
            continue
        lang = node['attrs'].get('data-lang') or node['attrs'].get('data-site-language')
        if lang not in ('fr', 'en'): continue
        classes = node['attrs'].get('class', 'lang-btn')
        current = ' aria-current="page"' if lang == language else ''
        anchor = '<a class="' + escape(classes) + '" href="' + page_url(slug, lang).replace(BASE, '/') + '" hreflang="' + lang + '" lang="' + lang + '" data-site-language="' + lang + '"' + current + '>' + lang.upper() + '</a>'
        changes.append((node['start'], node['end'], anchor))
    source = replace_ranges(source, changes)
    # Les anciens contrôles de traduction ne doivent pas doubler la navigation.
    def scripts(match):
        script = match[0].replace("$$('.lang-btn')", "$$('.legacy-lang-btn')")
        script = re.sub(r"const initialLang\s*=[\s\S]*?;", 'const initialLang = document.documentElement.lang;', script)
        script = re.sub(r"const initial\s*=[\s\S]*?;", 'const initial = document.documentElement.lang;', script)
        script = script.replace("let lang = 'fr';", 'let lang = document.documentElement.lang;')
        return script
    return re.sub(r'<script(?:\s[^>]*)?>[\s\S]*?</script>', scripts, source)


def footer_site_map(source, language):
    """Place le plan du site dans la ligne des mentions, sinon dans un paragraphe dédié."""
    plan = '/en/plan-du-site.html' if language == 'en' else '/plan-du-site.html'
    label = 'Site map' if language == 'en' else 'Plan du site'
    doc = Document(source)
    for footer in doc.find('footer'):
        if footer['end'] is None:
            continue
        for legal in doc.find('a'):
            href = legal['attrs'].get('href') or ''
            if (footer['start'] < legal['start'] and legal['end'] is not None
                    and legal['end'] <= footer['end']
                    and href.split('#')[0].endswith('mentions-legales.html')):
                classes = legal['attrs'].get('class')
                attribute = ' class="' + escape(classes) + '"' if classes else ''
                link = ('<!-- seo:footer-link:start --> · <a href="' + plan + '"' + attribute + '>' + label
                        + '</a><!-- seo:footer-link:end -->')
                return source[:legal['end']] + link + source[legal['end']:]
    block = ('\n<!-- seo:footer:start -->\n<p class="seo-footer"><a href="' + plan + '">' + label
             + '</a></p>\n<!-- seo:footer:end -->\n')
    return re.sub(r'\s*</footer>', lambda _: block + '</footer>', source, count=1)



def enhance_page(source, slug, language, data, image):
    source = fix_resource_paths(source, language)
    source = page_head(source, data, language, image)
    source = language_links(source, slug, language)
    if slug in PROJECTS + HOBBIES:
        category = ('Projets', 'Projects') if slug in PROJECTS else ('Loisirs et engagements', 'Activities and involvement')
        anchor = '#projets' if slug in PROJECTS else '#hobbies'
        home = page_url('index', language).replace(BASE, '/')
        label = ('Fil d’Ariane', 'Breadcrumb')[language == 'en']
        crumb = '\n<!-- seo:breadcrumb:start -->\n<nav class="seo-breadcrumb" aria-label="' + label + '"><ol><li><a href="' + home + '">' + LABELS['index'][language == 'en'] + '</a></li><li><a href="' + home + anchor + '">' + category[language == 'en'] + '</a></li><li aria-current="page">' + LABELS[slug][language == 'en'] + '</li></ol></nav>\n<!-- seo:breadcrumb:end -->\n'
        source = re.sub(r'(<main\b[^>]*>)\s*', lambda m: m[1] + crumb + '      ', source, count=1)
    source = footer_site_map(source, language)
    # L’image de tête est prioritaire ; les images de détail restent différées.
    doc = Document(source)
    main = doc.find('main')[0]
    images = [n for n in doc.find('img') if n['start'] > main['start']]
    if images:
        n = images[0]; tag = source[n['start']:n['open_end']]
        tag = set_attribute(set_attribute(tag, 'loading', 'eager'), 'fetchpriority', 'high')
        source = source[:n['start']] + tag + source[n['open_end']:]
    return source


CSS = '''/* Auteur : Aurélien Capron. Navigation éditoriale et variantes de langue. */
.lang-btn[aria-current="page"]{background:var(--chip-bg-active);color:var(--text-strong)}
a.lang-btn{text-decoration:none;display:inline-flex;align-items:center;justify-content:center}
.seo-breadcrumb{margin:0 0 24px;color:var(--text-muted);font:12px/1.7 'JetBrains Mono',monospace}
.seo-breadcrumb ol{list-style:none;display:flex;flex-wrap:wrap;gap:6px 10px;margin:0;padding:0}
.seo-breadcrumb li+li:before{content:'/';margin-right:10px;color:var(--text-faint)}
.seo-breadcrumb a{text-decoration:underline;text-underline-offset:3px}
.seo-breadcrumb [aria-current]{color:var(--text-strong)}
.seo-footer{text-align:center;padding:12px 20px;margin:0;font:12px/1.6 'JetBrains Mono',monospace;color:var(--text-muted)}
.seo-footer a{text-decoration:underline;text-underline-offset:3px}
'''
JS = '''/**
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
'''


def make_plan(records, language):
    """Propose un index utile aux visiteurs et lisible sans interaction."""
    en = language == 'en'; title = 'Site map' if en else 'Plan du site'
    prefix = '/en/' if en else '/'
    groups = [('Profile', ['index']) if en else ('Profil', ['index']),
              ('Engineering projects', PROJECTS) if en else ('Projets techniques', PROJECTS),
              ('Activities and involvement', HOBBIES) if en else ('Loisirs et engagements', HOBBIES),
              ('Legal information', ['mentions-legales']) if en else ('Informations légales', ['mentions-legales'])]
    body = ''
    for heading, slugs in groups:
        body += '<section><h2>' + heading + '</h2><ul>'
        for slug in slugs:
            d = records[(slug, language)]
            body += '<li><a href="' + page_url(slug, language).replace(BASE, '/') + '">' + LABELS[slug][en] + '</a><p>' + escape(d['description']) + '</p></li>'
        body += '</ul></section>'
    canon = BASE + ('en/' if en else '') + 'plan-du-site.html'
    graph = {'@context': 'https://schema.org', '@type': 'CollectionPage', 'url': canon, 'name': title,
             'inLanguage': language, 'isPartOf': {'@id': BASE + '#website'}, 'mainEntity': {
                 '@type': 'ItemList', 'itemListElement': [{'@type': 'ListItem', 'position': i + 1,
                      'name': LABELS[s][en], 'url': page_url(s, language)} for i, s in enumerate(PAGES)]}}
    return '''<!DOCTYPE html>
<!--
 @file plan-du-site.html
 @author Aurélien Capron
 @description Index généré des pages publiques du portfolio.
 @created Non renseignée — à renseigner au premier commit d’ajout.
 @source scripts/seo.py
-->
<html lang="''' + language + '''"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>''' + title + ''' — Aurélien Capron</title><meta name="description" content="''' + ('Profile, six technical projects, five activities and legal information.' if en else 'Profil, six projets techniques, cinq loisirs et engagements, et informations légales.') + '''">
<link rel="canonical" href="''' + canon + '''"><link rel="alternate" hreflang="fr" href="''' + BASE + '''plan-du-site.html"><link rel="alternate" hreflang="en" href="''' + BASE + '''en/plan-du-site.html"><link rel="alternate" hreflang="x-default" href="''' + BASE + '''plan-du-site.html">
<meta name="robots" content="index,follow"><script type="application/ld+json">''' + json.dumps(graph, ensure_ascii=False) + '''</script>
<style>body{margin:0;background:#f6f7f9;color:#334155;font:16px/1.7 system-ui,sans-serif}main,header,footer{max-width:850px;margin:auto;padding:24px}header{display:flex;justify-content:space-between;gap:20px}h1{font-size:clamp(30px,5vw,44px);color:#0f172a}h2{color:#0f172a;font-size:24px;margin-top:40px}a{color:#a94a13;text-underline-offset:3px}li{margin:24px 0}li>a{font-weight:650}p{margin:6px 0}footer{border-top:1px solid #d9dde4}a:focus-visible{outline:2px solid #a94a13;outline-offset:4px}</style></head><body>
<header><a href="''' + prefix + '''">Aurélien Capron</a><nav aria-label="Language"><a href="/plan-du-site.html" hreflang="fr" lang="fr">FR</a> · <a href="/en/plan-du-site.html" hreflang="en" lang="en">EN</a></nav></header>
<main><h1>''' + title + '''</h1><p>''' + ('Explore the profile, documented work and activities.' if en else 'Retrouver le profil, les réalisations documentées et les engagements.') + '</p>' + body + '</main><footer>© Aurélien Capron</footer></body></html>\n'


def build(root):
    """Prépare toutes les sorties avant la première écriture dans le dépôt."""
    sources = {}; output = {}; records = {}
    for slug in PAGES:
        p = root / (slug + '.html')
        if not p.is_file(): raise ValueError('Page source absente : ' + p.name)
        sources[slug] = clean_managed(p.read_text(encoding='utf-8'))
    for slug, source in sources.items():
        original = metadata(source, slug)
        en_dict = english_dictionary(source)
        fr_meta = META.get(slug, ((original['title'], original['description']), (en_dict['meta.title'], en_dict['meta.desc'])))[0]
        en_meta = META.get(slug, (None, (en_dict['meta.title'], en_dict['meta.desc'])))[1]
        # Ces clés restent alignées avec les métadonnées servies statiquement.
        assignment = '\n/* seo:translations:start */\nObject.assign(EN, ' + json.dumps({'meta.title': en_meta[0], 'meta.desc': en_meta[1]}, ensure_ascii=False) + ');\n/* seo:translations:end */\n'
        source = re.sub(r'\s*const DICT =', lambda _: assignment + 'const DICT =', source, count=1)
        en_dict.update({'meta.title': en_meta[0], 'meta.desc': en_meta[1]})
        for language in ('fr', 'en'):
            html = translate(source, en_dict) if language == 'en' else source
            data = metadata(html, slug)
            data['title'], data['description'] = en_meta if language == 'en' else fr_meta
            if language == 'en':
                # La traduction générée possède une histoire Git distincte de sa source.
                html = re.sub(r'@created[^\n]*', '@created Non renseignée — à renseigner au premier commit d’ajout.', html, count=1)
                data['published'] = None
            image = original['image']
            local_image = urlsplit(urljoin(BASE, image)).path.lstrip('/')
            if slug == 'index' or local_image.startswith('assets/seo/') or not local_image or not (root / local_image).is_file():
                image = BASE + 'assets/seo/portfolio-social-' + language + '.png'
            else:
                image = urljoin(BASE, image)
            html = enhance_page(html, slug, language, data, image)
            if language == 'en':
                html = re.sub(r'(id="cv-download"[\s\S]*?href=")[^"]+', r'\g<1>/assets/CV_Aurelien_Capron_EN.pdf', html, count=1)
            path = ('en/' if language == 'en' else '') + slug + '.html'
            output[path] = html.encode('utf-8')
            records[(slug, language)] = data
    for language in ('fr', 'en'):
        output[('en/' if language == 'en' else '') + 'plan-du-site.html'] = make_plan(records, language).encode('utf-8')
    # Les seules URL du sitemap sont des pages canoniques publiques.
    ET.register_namespace('', 'http://www.sitemaps.org/schemas/sitemap/0.9')
    ET.register_namespace('xhtml', 'http://www.w3.org/1999/xhtml')
    ns = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    tree = ET.Element(ns + 'urlset')
    for slug in PAGES + ['plan-du-site']:
        for language in ('fr', 'en'):
            node = ET.SubElement(tree, ns + 'url')
            ET.SubElement(node, ns + 'loc').text = page_url(slug, language)
            modified = records.get((slug, language), {}).get('modified')
            if modified: ET.SubElement(node, ns + 'lastmod').text = modified
            for lang in ('fr', 'en', 'x-default'):
                ET.SubElement(node, '{http://www.w3.org/1999/xhtml}link', {'rel': 'alternate', 'hreflang': lang,
                    'href': page_url(slug, 'fr' if lang == 'x-default' else lang)})
    ET.indent(tree)
    output['sitemap.xml'] = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
    output['robots.txt'] = ('# Aurélien Capron — exploration des pages publiques.\nUser-agent: *\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\nSitemap: ' + BASE + 'sitemap.xml\n').encode('utf-8')
    output['.nojekyll'] = b''
    output['assets/site-seo.css'] = CSS.encode('utf-8')
    output['assets/site-seo.js'] = JS.encode('utf-8')
    # Les exports reprennent les faits affichés, sans consignes destinées à influencer une IA.
    profile = {'name': 'Aurélien Capron', 'role': 'Élève-ingénieur en Systèmes Électroniques Intégrés',
               'school': 'Grenoble INP – Phelma', 'url': BASE,
               'source': BASE, 'languages': {'fr': BASE, 'en': BASE + 'en/'},
               'projects': [{'name': LABELS[s][0], 'url': page_url(s), 'english_url': page_url(s, 'en'),
                              **records[(s, 'fr')]['summary']} for s in PROJECTS],
               'activities': [{'name': LABELS[s][0], 'url': page_url(s), 'description': records[(s, 'fr')]['description']} for s in HOBBIES]}
    output['portfolio.json'] = (json.dumps(profile, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    lines = ['# Aurélien Capron — Portfolio', '', '> Portfolio personnel d’un élève-ingénieur à Grenoble INP – Phelma, en Systèmes Électroniques Intégrés.', '',
             '## Profil', '', '[Profil et parcours](' + BASE + ') : conception électronique, réalisation de prototypes, essais sur banc et travail en équipe.',
             '[English version](' + BASE + 'en/).', '', '## Projets techniques', '']
    for slug in PROJECTS:
        d = records[(slug, 'fr')]
        lines.append('- [' + LABELS[slug][0] + '](' + page_url(slug) + ') : ' + ' '.join(d['summary'].values()))
    lines += ['', '## Loisirs et engagements', '']
    for slug in HOBBIES:
        lines.append('- [' + LABELS[slug][0] + '](' + page_url(slug) + ') : ' + records[(slug, 'fr')]['description'])
    lines += ['', '## Ressources', '', '- [Plan du site](' + BASE + 'plan-du-site.html)',
              '- [Données structurées du portfolio](' + BASE + 'portfolio.json)',
              '- [Mentions légales et confidentialité](' + BASE + 'mentions-legales.html)', '',
              'Les pages liées constituent les sources détaillées. Les travaux collectifs et contributions sont distingués dans chaque étude de cas. Les contenus de tiers conservent leurs droits respectifs.', '']
    output['llms.txt'] = '\n'.join(lines).encode('utf-8')
    return output


def validate(output):
    """Vérifie les métadonnées, les liens de langue et les graphes avant écriture."""
    titles = set()
    for path, content in output.items():
        if not path.endswith('.html'): continue
        doc = Document(content.decode('utf-8'))
        if len(doc.find('h1')) != 1: raise ValueError(path + ' : un seul titre h1 est requis.')
        if len(doc.find('link', rel='canonical')) != 1: raise ValueError(path + ' : URL canonique ambiguë.')
        title = text(doc.inner(doc.find('title')[0]))
        if title in titles: raise ValueError('Titre dupliqué : ' + title)
        titles.add(title)
        for script in doc.find('script', type='application/ld+json'):
            json.loads(doc.inner(script))
        expected = 'en' if path.startswith('en/') else 'fr'
        if doc.find('html')[0]['attrs'].get('lang') != expected: raise ValueError(path + ' : langue incorrecte.')
        for lang in ('fr', 'en', 'x-default'):
            if len(doc.find('link', hreflang=lang)) != 1: raise ValueError(path + ' : variante de langue manquante.')
    ET.fromstring(output['sitemap.xml'])
    json.loads(output['portfolio.json'])



def main():
    """Exécute une construction reproductible ou un contrôle sans écriture."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', default='.', help='Racine du portfolio')
    parser.add_argument('--check', action='store_true', help='Vérifier sans modifier les fichiers')
    args = parser.parse_args()
    root = Path(args.directory).expanduser().resolve()
    output = build(root)
    validate(output)
    changes = {path: data for path, data in output.items() if not (root / path).is_file() or (root / path).read_bytes() != data}
    if args.check:
        if changes:
            raise ValueError('Fichiers SEO à actualiser : ' + ', '.join(changes))
        print('SEO vérifié : 28 pages FR/EN, graphes JSON-LD, sitemap, robots et exports cohérents.')
        return
    if not changes:
        print('Le référencement est déjà à jour.')
        return
    backup = Path(tempfile.mkdtemp(prefix='portfolio-avant-seo-'))
    for path, data in changes.items():
        target = root / path
        if target.is_file():
            saved = backup / path
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(str(len(changes)) + ' fichiers actualisés. Sauvegarde : ' + str(backup))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, SyntaxError) as exc:
        sys.exit('Mise à jour SEO interrompue : ' + str(exc))
