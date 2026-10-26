# Décisions métier : deux ERP, sept chiffres, deux modules

## A. Numérotation comptable à sept chiffres

- Le plan comptable d'entreprise est SYSCOHADA et l'ERP conserve ses classes et comptes racines ; la configuration **à sept chiffres** est une convention interne, distincte du nombre de chiffres publiés pour les racines SYSCOHADA.
- Un numéro court numérique est complété de zéros **à droite** ; aucun déplacement du préfixe d'origine : `101` → `1010000`, `401` → `4010000`, `4111` → `4111000`, `5211` → `5211000`, `6011` → `6011000`, `701` → `7010000`.
- Autoriser, après validation métier et sous les mêmes règles, des subdivisions propres à l'entreprise utilisant les sept positions. Ne pas convertir automatiquement des chiffres déjà trop longs ou des libellés atypiques.
- Interdire les collisions : `4111` et `4111000` désignent la même cible à sept chiffres et demandent une décision humaine préalable.
- Conserver les relations de clés étrangères vers le compte, les écritures, les tiers, les journaux, les factures, les taxes, les lettrages, les soldes et les historiques. Éviter de changer l'identifiant interne d'un compte.
- Ne pas modifier sans raison le numéro des pièces, les codes journaux, les plans de tiers ou les codes analytiques : l'exigence **sept chiffres** concerne les **comptes généraux**.

## B. Modules d'accueil séparés

- Afficher deux cartes distinctes et explicitement libellées : **Comptabilité générale** et **Comptabilité analytique**. Ne pas présenter le second comme une duplication, une base ou un journal différent.
- La générale permet le plan comptable, saisie, brouillard, validation, journaux, grand-livre, balance, états SYSCOHADA, etc.
- L'analytique est un espace spécialisé de présentation, ventilation et analyse ; sa matière financière de base provient des écritures de la comptabilité générale **validées**.
- Les droits d'accès peuvent autoriser l'un et pas l'autre, mais les mêmes contrôles d'accès serveur s'appliquent aux données et aux actions, pas seulement au menu visible.

## C. ERP Commercial

- L'analytique met en avant **sections**, **plan analytique**, **ventilation**, **balance analytique**, charges, produits et résultat par section.
- Aucune rubrique `Véhicules` / `Propriétaires` ne doit parasiter les états principaux d'une société classée `COMMERCE`.

## D. ERP Transport

- L'analytique a exactement deux rubriques **principales d'états/analyse** : **Véhicules** et **Propriétaires de véhicules**.
- Axes supplémentaires (agences, voyages, lignes, activités, sections, services, Classique/VIP, contrats...) sont des attributs d'imputation et filtres, pas de nouveaux modules principaux.
- Classique et VIP correspondent à des véhicules dédiés distincts ; le filtrage doit respecter cette classification.
- Pour chaque véhicule, suivre la rentabilité d'exploitation. Pour le propriétaire, distinguer ses résultats analytiques, ses droits contractuels, les versements et le **solde financier à lui payer**. Ne pas confondre le résultat du véhicule et la dette envers le propriétaire.

## E. ERP Mixte

- Si une même société exploite commerce et transport, conserver des axes permettant des restitutions pertinentes selon son activité sans créer de double comptabilité ; **valider l'ergonomie exacte des états mixtes avec le propriétaire du projet**.

## F. Conditions de reprise

- Pas de migration silencieuse d'une base métier existante.
- Pour un dossier lié en miroir à Sage, ne pas renuméroter sans bascule contrôlée : l'import/synchronisation peut reconstituer les numéros source.
- Un compte à huit chiffres ou plus est un conflit bloquant, non un cas à tronquer.
