# Portfolio Maker

A small FastAPI app that lets someone fill in a form and get a public, résumé-style page generated from it.

## Language

**User**:
The person who filled in the form. Holds the profile fields (name, email, phone, GitHub, bio) plus their Skills, Education, and Experience. There are no accounts or sessions — a User is just a database row, not an authenticated identity.
_Avoid_: Client, account

**Portfolio**:
The public résumé-style page rendered from one User's Skills, Education, and Experience (French usage: "portefolio" = online CV). Not a separate stored entity — it's a view over a User's data, and every User has exactly one, inseparably. There is no concept of a User with zero or multiple Portfolios.
_Avoid_: Profile, CV, resume

**Skill**, **Education**, **Experience**:
Child records attached to a single User, shown on their Portfolio. Each belongs to exactly one User.
