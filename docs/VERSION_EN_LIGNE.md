# Suivre l'ERP en ligne pendant le développement

Deux adresses, mises à jour automatiquement à chaque envoi sur la branche `ccr-5592a371-fusjt2`.

## 1. Aperçu (GitHub Pages) — https://piala00.github.io/YSFTEST/

Construit par `.github/workflows/apercu.yml` : tests, puis simulateurs web et bureau et explorateur des menus,
avec les données de démonstration. Rien à installer ; les écrans et les chiffres sont ceux du vrai logiciel,
mais les saisies ne sont pas conservées (simulation).

Mise en place, une seule fois, par le propriétaire du dépôt (GitHub ne permet pas à l'automatisme de le faire) :
1. GitHub › dépôt `YSFTEST` › **Settings › Pages › Build and deployment › Source : GitHub Actions**.
2. **Settings › Environments › github-pages › Deployment branches and tags** : ajouter la branche
   `ccr-5592a371-fusjt2` (par défaut seule `main` a le droit de publier).
3. Onglet **Actions › Aperçu de l'ERP** › dernière exécution › **Re-run all jobs**.

L'état de chaque construction est visible dans l'onglet **Actions** du dépôt (vert = publié, rouge = un test a échoué :
l'ancienne version reste en ligne).

## 2. Version en ligne réelle (Render) — saisie de vraies données de test

Le vrai serveur Django, avec connexion, saisie, validation, états. Défini par `render.yaml`.

Mise en place, une seule fois :
1. Créer un compte gratuit sur https://render.com (connexion avec GitHub).
2. **New › Blueprint**, choisir le dépôt `piala00/YSFTEST`, valider (**Apply**).
3. Renseigner `DEMO_ADMIN_PASSWORD` : mot de passe du compte `admin` (choisissez-en un solide : le site est public).
4. Laisser `DATABASE_URL` vide pour commencer.

L'adresse est du type `https://erp-ohada-test.onrender.com`. Chaque envoi sur la branche redéploie le site.

À savoir :
- Offre gratuite : le site s'endort après 15 minutes sans visite ; la première ouverture prend alors ~1 minute.
- Sans `DATABASE_URL`, la base est **remise à la démonstration** à chaque redéploiement ou réveil : idéal pour tester,
  pas pour garder des saisies. Pour les conserver, créer une base PostgreSQL (Render, Neon, Supabase…) et coller son URL
  dans `DATABASE_URL` (Render › service › Environment).
- C'est un site de test public : **n'y mettez pas les données réelles d'une société**.
