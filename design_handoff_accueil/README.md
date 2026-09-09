# Handoff : accueil, création, liste (Portfolio Maker)

## Overview
Refonte des trois pages publiques de `Adrien-EPF/Portfolio_Maker` (FastAPI + Jinja2)
dans le design system Broadsheet, en une seule passe :

| Route | Template | Écran |
| --- | --- | --- |
| `GET /` | `templates/index.html` | Accueil : deux chemins, rien d'autre |
| `GET /create` | `templates/create.html` | Formulaire de création |
| `GET /users` | `templates/users.html` | Liste des portfolios |

**Aucune route, aucun modèle, aucune logique métier ne change.** Les champs du
formulaire gardent exactement les mêmes `name` et `id` qu'aujourd'hui, la liste
garde `/portfolio/{id}` et `POST /users/{id}/delete`. C'est un remplacement de
templates + une feuille de style.

## About the Design Files
Les `.dc.html` de ce dossier sont des **références de design en HTML** —
prototypes montrant l'apparence et le comportement attendus, pas du code à
copier tel quel. Comme la cible est connue (Jinja2 + `static/`), le dossier
fournit la traduction prête à coller : quatre templates et une feuille de style.
Reprenez-les et adaptez-les aux conventions du dépôt.

## Fidelity
**Hi-fi.** Couleurs, typographie, échelles, états et espacements sont définitifs
et déjà encodés dans `broadsheet.css`. Le rendu doit être fidèle sur desktop et
fluide en dessous (voir Responsive).

## Le système, en cinq règles
1. **Aucune carte, aucune bordure, aucun filet.** Supprimez `.card` /
   `.directory-card` / `.directory-grid` de ces trois pages : la hiérarchie vient
   de la taille du texte et du blanc. C'est la règle à ne pas négocier.
2. **Chaque page = deux colonnes** : à gauche un chapeau (kicker en petites
   capitales, gros titre serif, sous-titre 34ch) qui reste collant au scroll ; à
   droite le contenu. Grille `repeat(auto-fit, minmax(300px, 1fr))`, gap
   `clamp(36px, 5vw, 80px)`, conteneur `max-width: 1280px`, gouttières
   `clamp(20px, 5vw, 80px)`.
3. **Titres en Instrument Serif 400**, tout le reste (corps, labels, boutons,
   nav) en **Instrument Sans**. Remplace le `<link>` Inter actuel.
4. **Le cyan `#0088b0` porte l'interactif**, le magenta `#d6006c` est le second
   spot, réservé aux astérisques de champ requis et au destructif (`Supprimer`,
   en `#aa0b56` pour le contraste du texte).
5. **Les libellés français cassent** : tout `.btn` porte
   `white-space: nowrap; flex: 0 0 auto`.

## Screens / Views

### 1. Accueil (`/`)
Colonne gauche : kicker « Au sommaire », h1 « Un CV en ligne, généré depuis un
formulaire. » (`clamp(42px, 5.4vw, 68px)`, `line-height: 1.04`,
`letter-spacing: -.02em`, `max-width: 20ch`), sous-titre « Pas de compte, pas de
mot de passe… ».

Colonne droite, décalée de `clamp(0, 3vw, 44px)` : deux **entrées de sommaire**,
séparées par `clamp(48px, 7vh, 84px)`. Une entrée = lien titre serif
`clamp(30px, 3.4vw, 44px)` + points de conduite extensibles
(`border-bottom: 1px dotted` encre 45 %, `align-self: flex-end`,
`margin-bottom: .42em`) + flèche « → » 22px en `#006786`. Sous chaque entrée, une
note 15.5px/27px, `max-width: 46ch`, encre 78 %.

- « Créer un portfolio » → `/create` — « Nom, contact, bio — puis les sections
  Compétences, Formation, Expérience et Photo, ajoutées à la demande. »
- « Voir les portfolios » → `/users` — « La liste des portfolios déjà créés :
  consultez-en un, ou revenez modifier le vôtre. »

Enfin les deux mêmes actions en boutons (`.btn-primary` cyan plein, `.btn-ghost`
cyan texte), marge haute `clamp(44px, 6vh, 72px)`.

### 2. Créer un portfolio (`/create`)
Chapeau gauche : « Nouveau portfolio » / « Remplissez, la page est générée. » /
« Seuls l'identité et le contact sont requis… » + lien « Voir les portfolios
existants → ».

Formulaire à droite, `max-width: 620px`, `display: flex; flex-direction: column`,
gap `clamp(40px, 5vh, 64px)` entre blocs. Quatre `<fieldset>` sans bordure, dont
la `<legend>` est un titre serif 28px — **`display: block; float: none`** (un
`float` sur une legend dans un conteneur flex/bloc la sort du flux et la fait
chevaucher le paragraphe suivant : le bug a été rencontré et corrigé).

Blocs et champs (identiques à l'existant) :
- **Identité** — `username`*, puis `firstname`* / `name`* sur une ligne.
- **Contact** — `email`* / `phone`* sur une ligne.
- **En savoir plus** (note « Optionnel. ») — `github` (placeholder
  `https://github.com/…`), `bio` (textarea 4 lignes, « Parlez de vous… »).
- **Sections** — note « Cochez celles que vous voulez remplir dès maintenant… »
  puis quatre groupes, chacun ouvert par une case à cocher au libellé serif 22px
  (`accent-color: var(--color-accent)`, case 18px) :
  `activate_skills` (`skill_name`, `skill_level` — select — / Débutant,
  Intermédiaire, Expert), `activate_experience` (`exp_title`, `exp_company`,
  `exp_start_date`, `exp_end_date` « Vide si poste actuel », `exp_description`),
  `activate_education` (`edu_degree`, `edu_school`, `edu_start_date`,
  `edu_end_date` « Vide si en cours », `edu_description`), `activate_photo`
  (`photo`, accept `.jpg,.jpeg,.png,.webp`).

Champs : label 12px en petites capitales espacées (`letter-spacing: .1em`, encre
70 %), astérisque magenta pour le requis, input `min-height: 44px`, fond
`#eae9e9`, bordure `color-mix(#201e1d 16%)`, rayon 2px, `font-size: 15px`. Deux
champs par ligne via `repeat(auto-fit, minmax(180px, 1fr))`.

Pied de formulaire : « Générer mon portfolio » (`.btn-primary`) + « Annuler »
(`.btn-ghost`, vers `/`).

### 3. Tous les portfolios (`/users`)
Chapeau gauche : compteur en kicker (« 4 portfolios », pluriel géré côté
template), h1 « Tous les portfolios. », note « Ouvrez celui qui vous intéresse…
La suppression est définitive. », puis le bouton « Créer un portfolio ».

À droite, une liste (`gap: 44px`, **pas de cartes**). Chaque élément :
- ligne d'entrée : `Prénom Nom` en serif `clamp(26px, 2.8vw, 36px)` (lien vers
  `/portfolio/{id}`) + points de conduite + `@username` 14px encre 70 % ;
- métadonnées : e-mail 15px encre 78 %, et — si la vue le fournit — les sections
  actives en petites capitales 13px encre 60 % (`user.active_sections`,
  facultatif : le template l'affiche seulement s'il existe) ;
- actions : « Voir » (`.btn-secondary`, 40px) et « Supprimer » (`.btn-ghost`
  `.btn-danger`, `#aa0b56`) dans le `<form method="post">` existant, `confirm()`
  conservé.

État vide : « Aucun portfolio pour l'instant. <a>Créer le premier →</a> » en
16px/27px — pas d'encadré.

## Interactions & Behavior
- Navigation par liens seulement ; aucun JS ajouté (le seul script reste le
  `confirm()` de suppression).
- Hover : lien d'entrée → `#006786` et sa flèche → `#0088b0` ; `.btn-primary` →
  `#1186ac` (actif `#006786`) ; `.btn-secondary` → fond encre 7 % ; `.btn-ghost`
  → fond cyan 10 % ; `.btn-danger` → fond magenta 10 % ; `.input` → bordure encre
  28 %.
- Focus clavier : `outline: 2px solid #0088b0; outline-offset: 2px` partout,
  jamais l'anneau par défaut. `.input:focus-visible` prend en plus la bordure cyan.
- Validation : `required` HTML sur `username`, `firstname`, `name`, `email`,
  `phone` — la validation serveur existante reste la référence ; si elle renvoie
  une erreur, affichez-la au-dessus du formulaire en texte 15px encre 78 %, sans
  encadré rouge.
- Responsive : sous ~760px les deux colonnes s'empilent (chapeau d'abord), la
  colonne collante redevient statique, les paires de champs passent en une
  colonne sous ~400px, gouttières à 20px. Aucune largeur fixe, aucune hauteur fixe.
- Accessibilité : flèches et points de conduite en `aria-hidden="true"` ;
  `aria-current="page"` sur le lien de nav actif ; toute cible tactile ≥ 44px
  (40px pour les actions secondaires de la liste) ; texte accent en `-700` sous
  24px pour tenir le 4.5:1.

## State Management
Aucun état client. Les trois vues restent rendues côté serveur ; `/users` reçoit
`users` comme aujourd'hui. Seul ajout **optionnel** : exposer
`user.active_sections` (liste de libellés) pour la ligne de métadonnées — le
template dégrade proprement sans elle.

## Design Tokens
`--color-bg #f3f2f2` · `--color-surface #eae9e9` · `--color-text #201e1d` ·
`--color-accent #0088b0` · `-600 #1186ac` · `-700 #006786` ·
`--color-accent-2 #d6006c` · `--color-accent-2-700 #aa0b56` ·
divider `color-mix(in srgb, #201e1d 16%, transparent)`.
Encres transparentes : 78 % (corps), 70 % (labels, kicker, pied), 60 % (méta,
placeholders), 45 % (points de conduite).
Espacement 10 / 15 / 20 / 30 / 44 / 64px. Rayon 2px. Aucune ombre.
Typo : Instrument Serif 400 (titres, légendes, cases à cocher), Instrument Sans
400/500 (corps, labels, boutons, nav).

## Assets
Aucune image, aucune icône. Flèche = caractère « → » (U+2192). Polices Google
Fonts, déclarées dans `base.html`.

## Files
- `base.html` — layout : nav `.site-nav`, pied, chargement des polices et de
  `broadsheet.css` (remplace `templates/base.html`).
- `index.html`, `create.html`, `users.html` — les trois templates.
- `broadsheet.css` — à poser dans `static/`, chargé **après** `style.css`.
- `Accueil.dc.html`, `Creer.dc.html`, `Portfolios.dc.html` — les prototypes de
  référence.
- `../github.md` — association au dépôt et carte écran → fichiers.

## Prompt de départ pour Claude Code
> Lis `design_handoff_accueil/README.md`, puis applique le handoff :
> copie `broadsheet.css` dans `static/`, remplace `templates/base.html`,
> `index.html`, `create.html` et `users.html` par ceux du dossier, et retire le
> `<link>` Inter au profit des deux polices Instrument. Ne touche ni aux routes
> ni aux modèles, et garde tous les `name`/`id` de formulaire à l'identique.
> Ensuite : `pytest tests/test_pages.py`, et vérifie que `/portfolio/{id}` (non
> refondue) reste lisible avec la nouvelle feuille — si des styles de
> `static/style.css` entrent en conflit (`.card`, `.directory-grid`,
> `.site-header`), nettoie-les plutôt que de surcharger.


---

# Handoff n°2 : le CV (route `GET /portfolio/{id}`)

La page d'un portfolio fini est désormais un **CV sur une page A4, exportable en PDF
par le navigateur**. Maquette de référence : `CV.dc.html` (page A4 réelle, 794 × 1123 px —
ce que vous voyez est ce qui s'imprime ; contenu mesuré à ~1015 px de haut, donc valide
aussi sur papier Letter).

## Ce qu'il faut faire
1. Copier `portfolio.html` dans `templates/` (remplace l'existant).
2. Reprendre `broadsheet.css` **en entier** : il contient déjà le bloc `.cv-*`,
   la règle `@page { size: A4; margin: 14mm }` et le `@media print`. Rien d'autre à charger.
3. La vue `GET /portfolio/{id}` doit passer au template un objet `user` portant ses
   relations chargées (voir « Données attendues »). Aucun changement de route,
   ni de modèle, ni de logique métier n'est nécessaire au-delà de ça.

## Données attendues
Toutes issues du formulaire `/create` — rien de neuf à saisir :

| Dans le template | Source `/create` | Obligatoire |
| --- | --- | --- |
| `user.firstname`, `user.name`, `user.username` | `firstname`, `name`, `username` | oui |
| `user.email`, `user.phone` | `email`, `phone` | oui |
| `user.github` | `github` | non |
| `user.bio` | `bio` | non |
| `user.photo_url` | upload `photo` (`activate_photo`) | non |
| `user.skills[]` → `.name`, `.level` | `skill_name`, `skill_level` | non |
| `user.experiences[]` → `.title`, `.company`, `.start_date`, `.end_date`, `.description` | `exp_*` | non |
| `user.educations[]` → `.degree`, `.school`, `.start_date`, `.end_date` | `edu_*` | non |
| `user.headline` (accroche 1 ligne) | **n'existe pas encore** | non |

- `user.headline` est optionnel et purement additif : sans lui, la ligne est masquée
  (`{% if user.headline %}`). Si vous voulez l'activer, ajoutez une colonne texte
  `headline` au modèle et un champ du même nom dans le bloc « En savoir plus » de
  `/create` (label « Accroche », placeholder « Développeuse web — back-end Python… »,
  `maxlength="120"`).
- `user.photo_url` : chemin servi par `static/` (ex. `/static/uploads/3.jpg`). Si le
  modèle stocke autre chose (nom de fichier, blob), adaptez le `src` — le HTML ne change pas.
- Les noms de relations peuvent différer (`user.education`, `user.formations`…) :
  seuls ces noms changent, la structure du gabarit reste identique.
- **Aucune section n'est jamais vide** : chaque bloc est sous `{% if %}`, un portfolio
  minimal (identité + contact) rend une page propre.

## Mise en page
Une seule page, deux colonnes, aucune carte ni bordure (règle n°1 du système).

- **Tête** (`.cv-head`, flex, aligné sur la baseline) : à gauche le kicker
  « Portfolio · @username », le nom en Instrument Serif 58px / `line-height: 1` /
  `letter-spacing: -.025em`, puis l'accroche 16px/25px sur 42ch ; à droite la
  **photo** carrée 176px en traitement `halftone` (`.cv-photo`), masquée s'il n'y en a pas.
- **Corps** (`.cv-body`) : grille `minmax(0,1.62fr) minmax(0,.78fr)`, gap 44px,
  marge haute 46px. Empilement sous 860px.
- **Colonne principale** (`.cv-main`, gap 34px) : *Profil* (bio, 15.5px/26px) puis
  *Expériences* — par entrée : intitulé serif 21px et période à droite en petites
  capitales 11px encre 60 % sur la même ligne de base, entreprise 14.5px encre 70 %,
  description 15px/25px.
- **Colonne latérale** (`.cv-side`, gap 30px) : *Contact* (email, téléphone, GitHub
  en 14.5px), *Compétences* (nom à gauche, niveau en points `●●○` cyan `#006786`
  à droite, `aria-label` portant le libellé pour les lecteurs d'écran), *Formation*
  (diplôme serif 17px, établissement 14px encre 70 %, période en petites capitales 11px).
- **Pied de page** : « Portfolio Maker · @username » en petites capitales 11px encre 55 %.
- Titres de section : Instrument Serif 400, 28px en colonne principale, 24px en latérale.

## Export PDF
- Bouton « Télécharger en PDF » (`.btn-primary`, `onclick="window.print()"`) dans la
  colonne latérale, à côté de « Me contacter » et « Tous les portfolios ».
- `@page { size: A4; margin: 14mm }` + `@media print` recomposent le CV en points :
  nav, pied de page du site et boutons masqués, liens en noir sans soulignement,
  photo à 42mm, `break-inside: avoid` sur les sections, entrées et compétences.
- Rien côté serveur : pas de WeasyPrint, pas de wkhtmltopdf, aucune dépendance ajoutée.
- À vérifier après intégration : `/portfolio/{id}` → Ctrl/Cmd+P → « Enregistrer au
  format PDF » doit sortir **une seule page**, sans en-tête ni URL du navigateur.
  Si un CV très rempli déborde, réduisez d'abord `.cv-prose`/`.cv-item-desc` à 10pt
  dans le bloc print — ne touchez pas à l'échelle des titres.

## Prompt de départ pour Claude Code
> Lis `design_handoff_accueil/README.md` (section « Handoff n°2 : le CV »), puis :
> remplace `templates/portfolio.html` par celui du dossier et mets à jour
> `static/broadsheet.css` avec la version du dossier (elle ajoute le bloc `.cv-*`
> et les règles d'impression). Assure-toi que la vue `GET /portfolio/{id}` charge
> bien les relations `skills`, `experiences` et `educations` du user, et que
> `photo_url` pointe vers un fichier servi par `static/`. Ne modifie ni les routes
> ni les `name`/`id` du formulaire. Vérifie ensuite l'impression : `/portfolio/{id}`
> doit tenir sur une seule page A4 à l'export PDF du navigateur.

## Fichiers de ce handoff
- `portfolio.html` — le gabarit Jinja du CV.
- `broadsheet.css` — la feuille unique (pages 1-3 + CV + impression).
- `CV.dc.html` — le prototype A4 de référence (ouvrable dans un navigateur).

---

# Handoff n°3 : le logo

Marque retenue : **« repérage manqué »** — le monogramme PM imprimé comme trois plaques
mal calées (cyan #0088b0, magenta #d6006c, encre #201e1d), en Instrument Serif, la police
déjà chargée par `base.html`. Maquette de référence : `Logos.dc.html`.

## Ce qu'il faut faire
1. Copier `static/logo-pm.svg` et `static/favicon.svg` dans le dossier `static/` du projet.
2. Reprendre `broadsheet.css` (le bloc `.logo*` est en fin de fichier) et `base.html`
   du dossier : la nav y remplace `<span class="brand">` par le lockup, et le `<head>`
   gagne `<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">`.
3. Rien d'autre : pas de route, pas de dépendance, pas d'image bitmap.

## Le mark en HTML
Un seul élément, aucune image — le décalage vient de deux pseudo-éléments, donc le
mark suit la taille de police et reste net à tous les zooms :

```html
<a class="logo" href="/" aria-label="Portfolio Maker, accueil">
  <span class="logo-mark" aria-hidden="true"><span>PM</span></span>
  <span class="logo-word">Portfolio Maker</span>
</a>
```

- Taille : `style="--logo-size: 30px"` sur `.logo-mark` (30 px dans la nav, 150 px en grand).
- `.logo-mark aria-hidden` + `aria-label` sur le lien : le lecteur d'écran annonce le nom
  une seule fois, pas « PM PM PM ».
- Mark seul (sans le nom) : garder `.logo-mark`, supprimer `.logo-word`.

## Déclinaisons prévues par le CSS
| Usage | Classe | Note |
| --- | --- | --- |
| Nav, en-têtes | `.logo` + `.logo-mark` | 30 px, décalage 4 % du corps |
| Sous 16 px, tampon, fax | `.logo-mark .logo-mono` | plaques supprimées, encre pleine |
| Fond encre `#201e1d` | `.logo-on-ink` sur le parent | passe les plaques en `screen` |
| Impression | automatique (`@media print`) | monochrome, pas de trichromie sur papier |

## Règles à respecter
- Décalage des plaques = **4 % de la taille de police**, jamais plus (il est en `em`,
  donc ne le convertissez pas en px).
- **Sous 16 px : monochrome.** Le décalage brouille le tracé.
- Marge de protection : la hauteur du M.
- Fonds admis : papier `#f3f2f2`, blanc, encre `#201e1d`. **Jamais sur une photo.**
- `isolation: isolate` sur `.logo-mark` est nécessaire : sans lui le `multiply`
  déborde sur ce qu'il y a derrière la nav.

## Un point à surveiller
Les deux SVG déclarent `font-family: Instrument Serif, Georgia, serif`. Dans une page
web la police est chargée, donc le rendu est exact ; **dans l'onglet du navigateur le
favicon est rendu hors page** et retombe sur Georgia — proche, mais pas identique.
Si ça vous gêne, deux options : convertir les lettres en tracés (Inkscape → « Objet en
chemin »), ou générer un `favicon.png` 32×32 depuis `Logos.dc.html`. Le SVG suffit dans
tous les autres cas (README, exports, impression).

## Prompt de départ pour Claude Code
> Lis `design_handoff_accueil/README.md` (section « Handoff n°3 : le logo »), puis :
> copie `static/logo-pm.svg` et `static/favicon.svg` dans `static/`, mets à jour
> `static/broadsheet.css` avec la version du dossier (elle ajoute le bloc `.logo*` en
> fin de fichier) et remplace `templates/base.html` par celui du dossier — la nav y
> utilise le lockup PM et le `<head>` déclare le favicon SVG. Ne touche ni aux routes,
> ni aux `name`/`id` des formulaires, ni au reste de `static/style.css` ; si
> `style.css` définit déjà `.brand`, laisse-le, `.logo` prend le dessus dans la nav.
> Vérifie ensuite que le mark reste net à 30 px dans la nav et que l'impression d'un
> portfolio sort le logo en monochrome.
