# Portfolio Maker

A small FastAPI app that lets someone fill in a form and get a public, résumé-style page generated from it.

## Language

**User**:
The person who filled in the form. Holds the profile fields (name, email, phone, GitHub, bio) plus their Skills, Education, and Experience. There are no accounts or sessions — a User is just a database row, not an authenticated identity.
_Avoid_: Client, account

**Portfolio**:
The public résumé-style page rendered from one User's active Sections (French usage: "portefolio" = online CV). Not a separate stored entity — it's a view over a User's data, and every User has exactly one, inseparably. There is no concept of a User with zero or multiple Portfolios.
_Avoid_: Profile, CV, resume

**Section**:
One of a fixed catalog of Portfolio building blocks — Skills, Experience, Education, or Photo — that a User explicitly adds ("Ajouter"). A new User starts with none; each Section must be added individually before it appears. A User can also retire ("Retirer") a Section: this hides it and its underlying data from the Portfolio without deleting anything, and re-adding it restores exactly what was there. "Supprimer" (delete) is reserved for the separate, permanent removal of an individual Skill/Experience/Education entry — it is never used for a Section, since a Section action is always reversible.
_Avoid_: Block, module, widget, tab; "Supprimer" for the section-level action

**Skill**, **Education**, **Experience**:
Child records attached to a single User, shown within their respective Section on the Portfolio. Each belongs to exactly one User, and each is individually orderable and permanently deletable within its Section.
