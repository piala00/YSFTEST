# Cahier de contrôle — audit exhaustif des commandes ERP / Sage 100

## Objectif
Recenser chaque commande réellement rendue dans **tous** les modules de l'ERP, puis comparer, quand un équivalent existe, ses comportements à ceux de Sage 100 Gestion commerciale et Comptabilité, édition et version de référence précisées. Une équivalence d'intitulé ne suffit pas. Les modules métiers sans équivalent Sage (transport, échanges) sont audités selon leurs propres spécifications, sans fausse équivalence.

## Unité de recensement
Une ligne par **commande/action contextuelle** : menu, sous-menu terminal, barre d'outils, bouton, lien-action, raccourci clavier, icône interactive, menu contextuel, modal, dialogue, action JS, action serveur, bouton imprimé ou masqué par rôle. Une commande répétée sur plusieurs écrans a plusieurs contextes d'activation, reliés à un identifiant fonctionnel commun.

## Champs obligatoires de la matrice
ID ; grand module ; sous-module ; onglet ; écran ; menu et chemin ; libellé ERP ; identifiant DOM ; template ; fichier JS ; route ; méthode HTTP ; vue/service ; objet métier ; statut initial ; rôle ; société/agence ; conditions d'activation ; comportement clic ; fenêtre/champs/onglets ; validations ; mutation SQL ; stock ; comptabilité ; trésorerie ; journal/audit ; impression/export ; erreurs ; Sage produit/version/édition ; écran Sage ; libellé Sage ; source officielle/capture ; comportement Sage observé ; écart ; gravité ; test automatisé ; preuve navigateur ; correctif/PR ; responsable ; état de validation.

## Catégories
- CONFORME_PROUVE : recette ERP et Sage comparées, preuves conservées.
- ECART_PROUVE : comportement différent, preuves des deux côtés.
- INACTIF_VOLONTAIRE : contrôle indisponible conformément aux règles et permissions.
- INACTIF_ANORMAL : fonction requise mais indisponible.
- NON_IMPLEMENTE : entrée visible sans traitement réel.
- A_VERIFIER_SAGE : preuve V12 insuffisante.
- A_TESTER_ERP : comportement codé mais non testé en exécution.
- SPECIFIQUE_ERP : aucune équivalence Sage pertinente ; validation sur cahier métier.
- NON_APPLICABLE : fonction Sage absente de l'édition cible ou non pertinente.

## Étendue
1. Socle : Accueil, navigation, Fichier, Édition, Structure, Traitement, État, Fenêtre, Aide, utilisateurs, rôles, paramètres, sociétés, agences, import/export, impression, recherche.
2. Gestion commerciale : articles, tiers, tarifs, remises, devis, commandes, préparation, livraisons, retours, avoirs, factures, achats, réceptions, stocks, inventaires, transferts, règlements, caisse, états.
3. Comptabilité : plans de comptes, tiers, journaux, saisie, consultation, validation, lettrage, rapprochement, échéanciers, trésorerie, analytique, clôtures, états SYSCOHADA, éditions, contrôles.
4. Transport et services propres : billetterie, courrier, colis, véhicules, garage, caisses, agences, propriétaires, comptabilité analytique, reporting, simulations, échanges.
5. Interfaces : fenêtres MDI, modales, formulaires dynamiques, éléments conditionnels, boutons générés en JavaScript, raccourcis, profils, accès bureau/web, configurations Windows.

## Méthode et seuil de sortie
- Inventaire statique exhaustif du code, sans confondre occurrences et boutons effectivement affichés.
- Inventaire dynamique par parcours navigateur, rôle, écran, état et édition ; inspection des contrôles générés à l'exécution.
- Cartographie bouton → JS → route → vue → service → transaction → écritures/stock ; identification des actions sans effet, erreurs silencieuses, actions trompeuses et contrôles serveur manquants.
- Référence Sage : documentation officielle V12 et, pour chaque comportement non documenté, preuve par installation Sage V12 et captures. Ne jamais présenter une hypothèse comme une équivalence prouvée.
- Matrice de tests par types de pièces, statuts, rôles, agences, permissions, cas limites et transactions ; base de démonstration uniquement.
- Audit contradictoire GPT/Claude et correction progressive par PR ; CI et recette utilisateur obligatoires avant fusion.

## Point de départ connu
Inventaire Gestion commerciale historique : 227 commandes terminales de menus, 25 sous-menus, 175 occurrences HTML dans un périmètre limité ; 109 commandes de menus grisées sans cible et 16 contrôles HTML inactifs/désactivés au moment de l'inventaire. **Ces chiffres ne couvrent pas tous les modules et ne mesurent pas les anomalies confirmées.** Les correctifs ultérieurs doivent être réconciliés avec un nouvel inventaire.

## Livrables
1. Inventaire global horodaté par commit, modules et profils.
2. Matrice ERP ↔ Sage avec références de preuve.
3. Registre des commandes inactives, manquantes, trompeuses ou non conformes.
4. Tests automatisés et rapports d'exécution, y compris non-régression.
5. PR correctives indépendantes par fonction métier et état final signé.

**Aucune prétention de conformité totale avant la recette complète. Aucune fusion, déploiement ou modification de données de production sans autorisation.**
