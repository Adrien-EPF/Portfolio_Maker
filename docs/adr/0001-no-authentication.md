# No authentication — fully open access

Any visitor can create a User, view any Portfolio, and delete any User (`/users/{id}/delete` has no ownership check). This is deliberate, not an oversight: this is a school project graded on the FastAPI/CRUD mechanics, and the data involved is public résumé information a User would willingly publish anyway, so accounts would add friction without protecting anything sensitive. It's treated as a permanent characteristic of this project, not a placeholder to close later.
