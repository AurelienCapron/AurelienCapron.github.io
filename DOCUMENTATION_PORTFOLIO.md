# Portfolio — navigation et organisation des sources

Auteur : Aurélien Capron  
Version documentée : 9 novembre 2026

## Installation de cette mise à jour

Remplacer les douze fichiers HTML à la racine du dépôt. Fusionner le dossier
`assets` avec celui du site en conservant les médias déjà présents. Cette archive
de mise à jour contient les pages, les styles et le script partagés, ainsi que la
licence des styles utilitaires. Elle ne répète pas les photos et vidéos existantes.

## Organisation

- `index.html` présente le parcours, les compétences, les projets et les loisirs.
- Les six pages de projets décrivent les réalisations techniques et leurs ressources.
- Les cinq pages de loisirs présentent les engagements personnels et associatifs.
- `assets/site-media.css` regroupe la progression de lecture, les états de chargement
  des images et la navigation entre les loisirs.
- `assets/site-media.js` suit le chargement, les erreurs et les changements de source
  des images, y compris celles ajoutées au document après son affichage initial.
- `assets/licenses/tailwindcss.txt` conserve la licence MIT de Tailwind CSS.

## Navigation entre les loisirs

L’ordre de l’accueil et des boutons de bas de page est identique : Sacha Heritage,
BDS Phelma, Judo, Pérouges, puis Saxhorn. La navigation est circulaire : le dernier
loisir mène au premier, et le premier permet de revenir au dernier. Le lien central
renvoie à la section des loisirs sur l’accueil.

Les clés de traduction existantes des cartes de l’accueil sont conservées : leur
numéro identifie une activité et ne représente pas sa position dans le carrousel.
Les boutons de navigation utilisent les clés communes `hobbyNav.*`.

## Présentation et interactions

Les styles utilitaires sont précompilés dans chaque page. Leur affichage ne dépend
pas d’un téléchargement de Tailwind ni d’une compilation JavaScript dans le
navigateur. Les règles propres à chaque page restent dans ses blocs `style` ; les
règles communes sont dans `site-media.css`. Les polices et les services externes
conservent leurs dépendances respectives.

Une nouvelle classe utilitaire ajoutée au HTML doit disposer d’une règle dans le
CSS livré : aucun compilateur ne la créera à la volée. Les styles personnalisés
peuvent être modifiés directement dans les blocs de présentation concernés.

Les scripts intégrés assurent les préférences de thème et de langue, les commandes
de navigation, les carrousels et les dialogues. Les JSDoc décrivent les fonctions
importantes et leurs paramètres ; les commentaires de structure délimitent les
sections et les responsabilités des modules.

## Dates et vérification

Les en-têtes identifient l’auteur et le rôle du fichier. Par convention, `@created`
reprend la date du premier ajout du fichier dans Git, en suivant ses renommages.
La date de documentation des sources est conservée séparément dans `@documented`.

La mise à jour a été contrôlée pour la syntaxe JavaScript, les traductions des
loisirs, les liens précédent/suivant et la conservation des sources des médias.
La navigation a également été vérifiée dans le navigateur, sur ordinateur et dans
une fenêtre de 390 pixels de large. Le nettoyage des commentaires et du formatage
ne modifie pas la logique JavaScript ; les changements fonctionnels concernent
l’ordre et les destinations de navigation des loisirs.

## Parcours de consultation

Les sommaires des pages détaillées sont repliables et suivent la section consultée.
Les liens entre pages utilisent des ancres explicites, notamment entre le BDS et
le projet Backyard. Les compétences interactives de l’accueil renvoient aux projets
qui les documentent ; les autres compétences restent des libellés simples.

`assets/site-experience.js` synchronise ces interactions avec la langue du document
et prépare les courriels de contact. `assets/site-media.js` gère les erreurs des
images et vidéos : nouvelle tentative, publication originale lorsqu’elle est connue
ou autre ressource associée. Le bilan de la Backyard renvoie à l’export PDF présent
dans `assets/projets/backyard/resultats.pdf`.
