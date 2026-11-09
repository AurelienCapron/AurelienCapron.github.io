# Référencement et lecture du portfolio par les outils d’IA

Auteur : Aurélien Capron · Documentation du 9 novembre 2026.

Le portfolio présente un élève-ingénieur, ses contributions et ses résultats documentés. Il ne présente pas un titre d’ingénieur déjà obtenu et ne prétend pas garantir un classement dans les moteurs de recherche.

## Sources éditoriales

Les treize pages françaises à la racine et leurs dictionnaires `EN` constituent les sources. Leurs textes restent présents dans le HTML, sans dépendre de l’exécution de JavaScript. Les six synthèses de projets alimentent aussi les exports : contexte, période, équipe, rôle, technologies et résultat.

Les pages anglaises dans `en/`, le plan du site, les graphes JSON-LD et les exports sont générés. Ne pas modifier les traductions directement dans `en/` : les modifier dans le dictionnaire de la page française, puis relancer la construction.

Les boutons de langue sont des liens vers des URL distinctes. Aucun changement automatique de langue n’est imposé selon le navigateur. Les anciennes URL avec `?lang=en` ou `?lang=fr` sont redirigées côté navigateur vers la variante correspondante, en conservant l’ancre. Les URL propres sont les URL canoniques.

## Construire et vérifier

Depuis la racine du dépôt, avec Python 3, sans paquet supplémentaire :

```bash
python3 scripts/seo.py .
python3 scripts/verifier_seo.py .
```

La première commande prépare les fichiers, vérifie leur structure et sauvegarde les fichiers remplacés dans un dossier temporaire indiqué dans le terminal. Les médias existants ne sont ni déplacés ni supprimés. Une seconde exécution sans changement ne modifie aucun fichier.

Pour vérifier uniquement la synchronisation :

```bash
python3 scripts/seo.py . --check
```

Le contrôle GitHub Actions exécute `scripts/verifier_seo.py` sur les push et les pull requests. Il n’a qu’un accès en lecture au dépôt, ne publie rien et ne modifie pas les sources.

Les styles et scripts partagés du référencement sont locaux : `assets/site-seo.css` et `assets/site-seo.js`. Les deux images de partage générales sont dans `assets/seo/`. Les images propres aux projets sont utilisées lorsqu’elles existent dans le dépôt ; sinon la carte générale sert de solution de repli.

## Ce que le site fournit

| Fichier ou mécanisme | Usage |
| --- | --- |
| Titres et descriptions uniques | Identifier chaque sujet et la contribution d’Aurélien. |
| Liens canoniques et `hreflang` réciproques | Distinguer les versions française et anglaise et limiter les ambiguïtés d’URL. |
| Open Graph et cartes de partage | Fournir un titre, une description et une image absolue lors du partage d’une page. |
| JSON-LD | Relier le site, la personne, les pages, les études de cas et leurs fils d’Ariane. |
| `sitemap.xml` | Énumérer 28 URL canoniques : treize contenus et un plan du site dans chaque langue. La page 404 en est exclue. |
| `robots.txt` | Autoriser l’exploration du contenu public et indiquer le sitemap, avec une règle explicite pour OAI-SearchBot. |
| `plan-du-site.html` | Proposer aux visiteurs un index des projets et engagements, sans carrousel ni JavaScript. |
| `portfolio.json` | Exposer un résumé structuré des faits et des URL sources. |
| `llms.txt` | Proposer un index textuel complémentaire aux systèmes qui choisissent de l’utiliser. |

Les graphes utilisent `ProfilePage`, `Person`, `WebSite`, `WebPage`, `TechArticle`, `Article`, `BreadcrumbList` et `CollectionPage` selon le contenu. Un article décrit l’étude de cas du portfolio : il n’attribue pas à Aurélien la création exclusive des produits ou travaux collectifs présentés. Phelma est décrite comme affiliation actuelle, pas comme diplôme déjà obtenu.

Les dates de création HTML sont conservées. Une date de publication n’est émise que si la source fournit une date ISO vérifiée. Les nouvelles pages générées n’inventent pas une date de premier commit : la convention Git du dépôt continue de s’appliquer.

Les `lastmod` du sitemap reprennent le champ `@updated` des pages sources. Lors d’une modification réelle du contenu, actualiser ce champ et relancer la construction. Ne pas changer les dates pour donner une impression artificielle de fraîcheur.

## Moteurs de recherche et IA : portée réelle

Google indique que les fondamentaux SEO s’appliquent aussi à ses fonctionnalités d’IA. Aucun fichier spécial ni balisage « IA » n’est exigé. `llms.txt` n’est pas utilisé par Google pour améliorer le classement ; il est fourni comme aide complémentaire et ne remplace pas les pages HTML.

OAI-SearchBot sert à la recherche dans ChatGPT. GPTBot correspond à un autre usage, lié à l’entraînement. Le fichier livré autorise l’exploration publique et n’ajoute pas de restriction spécifique à l’entraînement. L’accès technique des robots ne transfère aucun droit sur les contenus et ne remplace pas les licences et autorisations des ayants droit.

Les données structurées, un sitemap et des pages accessibles améliorent la compréhension et l’éligibilité. Ils ne garantissent ni exploration, ni indexation, ni résultat enrichi, ni citation par un assistant. Aucun score Lighthouse ou gain de trafic n’est déduit de ces changements.

## Après publication

1. Ouvrir les pages FR et EN, le sitemap et les fichiers d’export sur le domaine public. Vérifier également qu’une URL inexistante renvoie bien un statut HTTP 404 ; un aperçu local ne prouve pas le comportement de GitHub Pages.
2. Dans Google Search Console, conserver la vérification existante, soumettre `https://aureliencapron.github.io/sitemap.xml`, puis inspecter l’accueil et un projet dans chaque langue. Le jeton de vérification déjà présent dans l’accueil est conservé.
3. Vérifier la propriété dans Bing Webmaster Tools et y soumettre le même sitemap. Aucun faux jeton de vérification n’est ajouté dans le code.
4. Tester le JSON-LD avec Schema.org Validator et, pour les types pris en charge, Google Rich Results Test.
5. Contrôler les réglages d’inclusion dans les fonctionnalités d’IA disponibles dans Search Console et les éventuelles restrictions de l’hébergeur.
6. Observer les impressions, requêtes et clics avant de tirer une conclusion sur les effets du référencement. Améliorer les études de cas avec des mesures originales, des limites, des documents et des contributions précisément attribuées.

Les validations de comptes et la demande d’indexation doivent être réalisées depuis les comptes du propriétaire. Le générateur ne soumet pas de formulaire et ne publie pas le dépôt.

## Références officielles

- [Google : fonctionnalités d’IA et site web](https://developers.google.com/search/docs/appearance/ai-features)
- [Google : guide sur l’optimisation pour les fonctionnalités d’IA](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- [Google : sites multilingues](https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites)
- [Google : création et soumission d’un sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Google : données structurées de profil](https://developers.google.com/search/docs/appearance/structured-data/profile-page)
- [Bing : recommandations pour les webmasters](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)
- [OpenAI : robots d’exploration](https://developers.openai.com/api/docs/bots)
- [Schema.org : CreativeWork](https://schema.org/CreativeWork)
