# 00 — Sources, périmètre et niveau de preuve

## Périmètre

- Produit : **Sage 100 Gestion Commerciale** (appellation historique « Sage 100C », ou Gescom).
- Version étudiée : **V12**, référence documentaire spécifique **V12.10** ; une V12.x ultérieure peut évoluer.
- Sujet : interface utilisateur Windows (menus, barres, listes, formulaires, onglets, boutons, commandes, impressions).
- Hors périmètre principal : Sage X3, tutoriel SQL Server, licence Sage Comptabilité seule.

## Sources vérifiées (liens officiels)

**S1 — Source majeure :** Sage, « Découpage fonctionnel détaillé — Sage 100 Gestion Commerciale », pièce jointe nommée « Découpage fonctionnel Sage 100 V1210 GestionCommerciale.pdf », mise à jour du 13 mars 2026, 14 pages.
- Article : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126080738580
- PDF direct : https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=240126080738580
- Pages : 1–6 (Fichier / Paramètres société), 6–10 (Structure), 11–12 (Traitement), 13–14 (État), 14 (Fenêtre).
- Limite : matrice de **fonctions/éditions**, pas une capture détaillée de chaque écran.

**S2 — Correspondance de versions :** Sage, « Découpage fonctionnel détaillé — Sage 100 » : le découpage V12 est annoncé identique au découpage V11.
- https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126081806063
- La similarité de l'inventaire fonctionnel ne garantit pas l'identité pixel par pixel.

**S3 — Ergonomie Windows classique :** Sage, « Menu Fenêtre » (ressource ancienne, à confirmer sur V12).
- https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=220125200004187

**S4 — Exemple de personnalisation :** Sage Community Hub, personnalisation d'une zone d'en-tête de facture.
- https://communityhub.sage.com/fr/sage-100/f/discussion-generale/234085/probleme-affichage-en-tete-de-facture/566443

**S5 — Programmes externes / Personnaliser :** Sage, documentation de l'onglet « Programmes externes » (disponibilité selon gamme et droits).
- https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095151540

## Règle de qualification

- `[DOC-V12]` : la fonction est dans la matrice S1. Ceci certifie le **nom d'une fonctionnalité** dans le découpage, et parfois un regroupement, pas nécessairement son emplacement exact à l'intérieur d'une fenêtre.
- `[ERG-CLASSIQUE]` : élément démontré pour l'interface classique dans S3 ou documentation historique, mais pas contrôlé en capture V12.
- `[OBSERVÉ]` : présence attestée dans l'installation de l'utilisateur ou une capture V12 datée.
- `[INDICATIF]` : proposition de description ou composant vraisemblable, à vérifier avant reproduction stricte.

## Distinctions indispensables

1. **Entrée menu** : commande ouverte depuis la barre horizontale de menus.
2. **Groupe de fonctions** : ligne de l'inventaire Sage qui regroupe des réglages, sans nécessairement être une fenêtre indépendante.
3. **Fenêtre** : écran/liste/dialogue affiché après action.
4. **Onglet** : composant visuel effectivement présent dans une fenêtre, pas simple regroupement du PDF.
5. **Sous-onglet** : niveau intérieur vérifié dans un onglet ; ne pas l'inventer.
6. **Bouton/action** : commande cliquable identifiée (libellé, icône, comportement).
7. **Champ/colonne** : contrôle de saisie / donnée listée, vérifié selon le contexte et la personnalisation.

## Remarques sur les éditions

S1 distingue les éditions sur site **Essentials**, **Standard**, **Premium**, puis les offres hébergées et partenaires. Les cases contiennent « Standard », « Option », « Non disponible » ou des limites. Le terme **Standard** dans une case signifie fonction de base, pas nécessairement « édition Standard ». Lire l'intersection ligne/colonne avant toute déclaration sur la licence. Les options et droits peuvent masquer une fonction.

## Attention réglementaire

Les références à la facturation électronique de la matrice Sage France ne démontrent pas leur obligation réglementaire au Cameroun. Toujours distinguer interface disponible et règles fiscales applicables.
