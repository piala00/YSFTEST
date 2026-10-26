# État observé dans les archives de référence

Archives comparées localement :

| Archive | Taille compressée | SHA256 |
|---|---:|---|
| `ERP-OHADA-Commerce-Windows.zip` | 45882915 octets | `604f4b9166f755f823ff41661c7b47eb9cebef67735902a801fec7afb2ee1519` |
| `ERP-OHADA-Commerce-Windows-Comptabilite-7-Chiffres.zip` | 45886310 octets | `c0d7be027013a116d3a7fadfb8d2280854d30478a74ebdf3887c2aa9d3b74aed` |

Entre ces archives, 11 fichiers ont changé et 2 ont été ajoutés. Les autres fichiers du ZIP du logiciel ne sont pas inclus dans le Skill.

## Déjà présent dans l'archive d'origine (avant ce correctif)

- `apps/core/management/commands/init_erp.py` : argument `--longueur-comptes` avec **7 par défaut pour les nouveaux dossiers**.
- `apps/comptabilite/models.py` : normalisation des numéros courts et longueur configurable ; `Societe.longueur_comptes` à 0 pour longueur libre selon le contexte.
- `apps/comptabilite/services.py` : fonctions de simulation et de conversion de longueur.
- `apps/core/navigation.py` : modules web `comptabilite` et `analytique` déjà définis.
- `apps/transport/analytique.py` : analyses des véhicules et propriétaires déjà présentes.

**Conséquence :** dire que le correctif a créé toutes ces fonctions serait trompeur ; il a surtout sécurisé un cas de migration et mieux intégré les modules dans les interfaces.

## Ajouts et modifications du correctif vérifiés par comparaison binaire

- `apps/comptabilite/management/commands/longueur_comptes.py` : refuse explicitement les numéros incompatibles, en plus des collisions.
- `apps/comptabilite/services.py` : valide la longueur demandée et les numéros non numériques/plus longs avant de renuméroter.
- `apps/comptabilite/tests.py` : test de refus d'un compte trop long.
- `apps/core/accueil.py` : affiche pour une société commerciale des indicateurs par section, plutôt que les indicateurs transports.
- `apps/core/navigation.py` : filtrage des éléments du menu analytique selon commerce/transport/mixte.
- `apps/transport/tests.py` : test d'accueil et de menu analytique Commerce.
- `desktop/shell.py`, `desktop/lanceur.py`, `desktop/comptabilite.py`, `desktop/pages.py` : 2 entrées comptables dans le lanceur Windows, interface analytique distincte.
- `desktop/COMPILER.bat` : compilation `ERP_Analytique.exe`.
- Nouveau `desktop/analytique.py` : lance l'interface analytique et son accès web pour les écrans dépourvus de composant natif.
- Nouveau fichier de note : `NOTE-MISE-A-JOUR-COMPTABILITE-7-CHIFFRES.txt` (copie dans ce Skill).

## Limites réelles du contrôle

- Le comparatif atteste des **modifications de fichiers**, pas de leur exécution effective, pas du rendu graphique ni du bon fonctionnement de la base de production.
- L'archive contient une application intégrée commerce/transport ; elle n'atteste pas qu'un ERP Transport indépendant a été corrigé.
- La validation fiscale/Cameroun, les noms complets du plan SYSCOHADA et les structures Sage sont hors de ce correctif.
- Vérifier l'état du dépôt actuel avant de copier ou patcher quoi que ce soit.
