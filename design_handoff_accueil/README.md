# Handoff : page d'accueil (Portfolio Maker)

## Overview
Nouvelle page d'accueil pour `Adrien-EPF/Portfolio_Maker` (FastAPI + Jinja2). Elle
accueille le visiteur et lui propose deux chemins, et rien d'autre :

1. **Créer un portfolio** → `GET /create`
2. **Voir les portfolios** → `GET /users`

Elle remplace le contenu de `templates/index.html` (aujourd'hui deux `.card` dans
une `.directory-grid`). Aucune route, aucun modèle, aucun test métier n'est à
modifier : les deux cibles existent déjà.

## About the Design Files
Les fichiers de ce dossier sont des **références de design réalisées en HTML** :
des prototypes qui montrent l'apparence et le comportement attendus, pas du code
de production à copier tel quel. `Accueil.dc.html` est la source de vérité
visuelle (elle se lit dans un navigateur, mais elle dépend d'un runtime de
composants et de la feuille du design system).

Comme la cible ici est connue — Jinja2 + `static/style.css` — le dossier fournit
aussi une **traduction directe et prête à coller** : `index.html` (le template
Jinja) et `accueil.css` (les styles). Reprenez-les et adaptez-les aux
conventions du dépôt plutôt que de re-dériver le design depuis le prototype.

## Fidelity
**Hi-fi.** Couleurs, typographie, échelles et états sont définitifs et repris
tels quels dans `accueil.css`. Le rendu doit être fidèle au pixel près sur
desktop, et fluide en dessous (voir Responsive).

## Screens / Views

### Accueil (`/`)
- **Purpose** : choisir entre créer un portfolio et consulter ceux qui existent.
- **Layout** : barre de navigation en haut ; puis une grille de deux colonnes
  (`repeat(auto-fit, minmax(320px, 1fr))`, gap `clamp(40px, 6vw, 80px)`,
  `align-items: start`) dans un conteneur `max-width: 1280px` centré,
  gouttières `clamp(20px, 5vw, 80px)`, padding haut `clamp(48px, 8vh, 96px)`,
  padding bas 64px. La colonne de droite est décalée de `clamp(0, 3vw, 44px)`
  vers le bas — l'asymétrie est voulue.
- **Pas de cartes, pas de bordures, pas de filets.** La hiérarchie vient de
  l'échelle typographique et du blanc. C'est la règle la plus importante du
  design system : ne réintroduisez pas `.card`.

#### Colonne gauche
| Élément | Spéc |
| --- | --- |
| Kicker « Au sommaire » | 12px / 14px, `letter-spacing: .12em`, majuscules, encre à 70 % |
| Titre h1 | Instrument Serif 400, `clamp(42px, 5.4vw, 68px)`, `line-height: 1.04`, `letter-spacing: -.02em`, `max-width: 20ch`, marge haute 28px |
| Sous-titre | Instrument Sans 400, 16px / 27px, `max-width: 36ch`, encre à 78 %, marge haute 32px |

Copie exacte :
- Kicker : « Au sommaire »
- Titre : « Un CV en ligne, généré depuis un formulaire. »
- Sous-titre : « Pas de compte, pas de mot de passe. Vos informations, les
  sections dont vous avez besoin, une page publique — modifiable à tout moment. »

#### Colonne droite — les deux entrées de sommaire
Chaque entrée est une ligne `display: flex; align-items: baseline; gap: 20px` :
lien titre, points de conduite extensibles, flèche.

| Élément | Spéc |
| --- | --- |
| Lien titre | Instrument Serif 400, `clamp(30px, 3.4vw, 44px)`, `line-height: 1.15`, `letter-spacing: -.015em`, `#201e1d`, sans soulignement ; **hover** `#006786` |
| Points de conduite | `flex: 1; min-width: 32px`, `align-self: flex-end`, `margin-bottom: .42em`, `border-bottom: 1px dotted` encre à 45 % |
| Flèche → | 22px, `#006786` (passe à `#0088b0` au survol du lien) |
| Note sous l'entrée | 15.5px / 27px, `max-width: 46ch`, encre à 78 %, marge haute 14px |
| Écart entre les deux entrées | `clamp(48px, 7vh, 84px)` |

Copie exacte :
- « Créer un portfolio » → « Nom, contact, bio — puis les sections Compétences,
  Formation, Expérience et Photo, ajoutées à la demande. »
- « Voir les portfolios » → « La liste des portfolios déjà créés : consultez-en
  un, ou revenez modifier le vôtre. »

#### Boutons (rappel des deux actions, bas de colonne droite)
`display: flex; flex-wrap: wrap; gap: 20px`, marge haute `clamp(44px, 6vh, 72px)`.

| Bouton | Spéc |
| --- | --- |
| « Créer un portfolio » (`.btn .btn-primary`) | fond `#0088b0`, texte `#f3f2f2`, hover `#1186ac`, actif `#006786` |
| « Voir les portfolios » (`.btn .btn-ghost`) | fond transparent, texte `#006786`, hover fond `color-mix(in srgb, #0088b0 10%, transparent)` |
| Les deux | Instrument Sans 500, 14px, padding `10px 18px`, `border-radius: 2px`, `min-height: 44px`, `white-space: nowrap; flex: 0 0 auto` |

`white-space: nowrap; flex: 0 0 auto` n'est pas cosmétique : sans lui les
libellés français se cassent sur deux lignes dans la pilule de 44px.

#### Barre de navigation
Marque « Portfolio Maker » (Instrument Serif 18px, `margin-right: auto`,
`letter-spacing: -.01em`) puis trois liens 14px : Accueil (courant), Créer,
Tous les portfolios. `padding: 15px clamp(20px, 5vw, 80px)`, **aucune bordure
basse**, hover `#0088b0`. Cibles : `/`, `/create`, `/users`.

#### Pied de page
« Portfolio Maker — projet FastAPI », 13px / 24px, encre à 70 %, mêmes gouttières.

## Interactions & Behavior
- Aucun état, aucun JS : ce sont des `<a>` vers `/create` et `/users`.
- Hover : lien titre → `#006786` ; flèche → `#0088b0` ; boutons comme ci-dessus.
- Focus clavier : `outline: 2px solid #0088b0; outline-offset: 2px` — jamais
  l'anneau bleu par défaut. L'ordre de tabulation suit l'ordre du DOM (nav, puis
  entrée 1, entrée 2, puis les deux boutons).
- Pas de transitions requises ; si vous en ajoutez, 120 ms `ease-out` sur
  `color`/`background` uniquement.
- **Responsive** : sous ~760px la grille passe à une colonne (la colonne gauche
  d'abord), le décalage haut de la colonne droite tombe à 0, les gouttières
  descendent à 20px, les tailles suivent les `clamp()`. Rien n'est en largeur
  fixe.
- **Accessibilité** : la flèche et les points de conduite sont
  `aria-hidden="true"` (décor) ; le libellé du lien porte le sens. Contraste :
  corps de texte en encre à 78 % (≈ 8:1), texte accent en `-700` et non en
  `#0088b0` sous 24px.

## State Management
Aucun. La vue est statique ; la route `GET /` continue de rendre
`templates/index.html` sans contexte.

## Design Tokens
Couleurs : `--color-bg #f3f2f2` · `--color-surface #eae9e9` ·
`--color-text #201e1d` · `--color-accent #0088b0` ·
`--color-accent-600 #1186ac` · `--color-accent-700 #006786` ·
`--color-accent-2 #d6006c` (second spot, non utilisé ici hors hover de lien) ·
divider `color-mix(in srgb, #201e1d 16%, transparent)`.
Encres transparentes utilisées : 78 % (corps), 70 % (kicker, pied), 45 % (points).

Typographie : titres **Instrument Serif** 400 ; corps et chrome
**Instrument Sans** 400/500/600. (Le design system Broadsheet prescrit Source
Serif 4 ; le remplacement par ce duo plus moderne est une décision explicite du
client, à conserver.)

Espacement : 5 / 10 / 15 / 20 / 30 / 40px. Rayons : 1 / 2 / 4px (la page n'utilise
que 2px). Ombres : aucune sur cette page.

## Assets
Aucune image, aucune icône. La flèche est le caractère « → » (U+2192). Les deux
polices viennent de Google Fonts (voir l'en-tête de `accueil.css`) et remplacent
le `<link>` Inter actuel de `templates/base.html`.

## Deux options d'intégration
- **Option A — page d'accueil seulement.** Gardez `base.html` tel quel et ne
  reprenez que le `{% block content %}` de `index.html`. La marque et la nav
  restent celles de `.site-header` : plus rapide, mais l'accueil et le reste du
  site ne parleront pas la même langue visuelle.
- **Option B — recommandée.** Remplacez `.site-header` de `base.html` par la
  barre `.home-nav` (markup dans `index.html`, styles dans `accueil.css`), et
  chargez `accueil.css` après `static/style.css`. Les tokens en `:root`
  reteintent alors tout le site ; prévoyez une passe de vérification sur
  `create.html`, `users.html` et `portfolio.html` (surtout `.card`,
  `.directory-card` et les boutons).

## Files
- `index.html` — le template Jinja à poser sur `templates/index.html`.
- `accueil.css` — les styles à ajouter (à charger après `static/style.css`).
- `Accueil.dc.html` — le prototype de référence, source de vérité visuelle.
- `../github.md` — l'association avec le dépôt et la carte écran → fichiers.

## Prompt de départ pour Claude Code
> Lis `design_handoff_accueil/README.md`. Remplace le contenu de
> `templates/index.html` par la page d'accueil décrite (option B : la nav
> `.home-nav` passe dans `base.html`), ajoute `accueil.css` dans `static/` et
> charge-le après `style.css`, et remplace le `<link>` Inter par les deux polices
> Instrument. Ne touche ni aux routes ni aux modèles. Vérifie ensuite que
> `tests/test_pages.py` passe et que `/create`, `/users` et `/portfolio/{id}`
> restent lisibles.
