# Demande de recherche — Sage 100 V12 (Comptabilité et Gestion commerciale)

**À l'attention de l'assistant chargé de la recherche.**
Contexte : nous développons un ERP (Django, OHADA / SYSCOHADA, Cameroun) qui reproduit l'ergonomie de
**Sage 100 V12 SQL Server** : mêmes menus (Fichier, Édition, Structure, Traitement, Etat, Fenêtre, ?), mêmes
sous-menus, et des **autorisations d'accès définies menu par menu**. La Gestion commerciale est déjà alignée sur
le « Découpage détaillé Sage 100 Gescom V11/V12 ». Il nous manque des sources vérifiées pour le reste.

Merci de livrer le résultat sous forme d'un **skill** (dossier zippé), au format décrit en fin de document.

---

## Règles impératives

1. **Ne rien inventer.** Chaque ligne doit citer sa source (URL, document, page). Si une information est
   introuvable, l'écrire dans le fichier des inconnues plutôt que la deviner.
2. **Libellés exacts**, avec la casse, les accents et la ponctuation de Sage (« Etat » sans accent dans la barre
   de menus, « Interrogation et lettrage », etc.). Conserver **l'ordre** des commandes et la position des
   **séparateurs** (traits horizontaux dans les menus).
3. Indiquer la **version** concernée (V12 de préférence ; V11 accepté si Sage indique que le découpage est
   identique). Signaler toute différence entre versions ou entre éditions (Standard, Premium, etc.).
4. Distinguer le niveau de preuve :
   - `DOC-OFFICIEL` : document Sage (base de connaissances fr-kb.sage.com, manuel, aide en ligne) ;
   - `DOC-TIERS` : partenaire, formation, forum (préciser lequel) ;
   - `A-CONFIRMER` : déduit, non trouvé noir sur blanc.
5. Aucune donnée réelle de société, aucun identifiant ni mot de passe.

---

## Recherche 1 — Arborescence complète des menus de Sage 100 Comptabilité V12 (prioritaire)

Source principale attendue : article Sage **« Découpage fonctionnel détaillé »**
https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126081806063
(un PDF par produit : prendre celui de **Comptabilité**, et celui de **Gestion commerciale** pour contrôle).
Compléments : manuel de référence Sage 100 Comptabilité (chapitres « Menu Fichier », « Menu Structure »,
« Menu Traitement », « Menu Etat »), aide en ligne Sage.

Pour **chaque** menu — Fichier, Édition, Structure, Traitement, Etat, Fenêtre, ? — relever **toutes** les
commandes et **tous les niveaux** de sous-menus (sous-menu › sous-sous-menu › …), dans l'ordre, avec :
- le libellé exact ;
- le niveau (1 = commande du menu, 2 = sous-commande, 3…) et le parent ;
- les séparateurs ;
- le raccourci clavier s'il existe ;
- l'édition / l'option qui conditionne la commande (ex. « Comptabilité Premium uniquement ») ;
- une phrase sur ce que fait la commande ;
- la source.

Points à couvrir sans faute :
- **Etat** : groupe **« Etats tiers »** et tout son contenu (grand-livre des tiers, balance des tiers,
  échéancier, balance âgée, relevés, justificatif de solde à date, statistiques tiers, historique des rappels…),
  « Etats analytiques », états budgétaires, « Analyse et contrôles », bilan / compte de résultat, déclarations
  de taxes, réimpressions, états de révision.
- **Traitement** : saisie des journaux, saisie par pièce, saisie par lot, interrogation et lettrage, lettrage
  automatique, rapprochement bancaire (manuel / automatique), gestion des extraits, règlements tiers, rappel /
  relance, abonnements, réimputation, recherche d'écritures, révision, fin d'exercice (clôture, reports à nouveau,
  archivage), etc.
- **Structure** : plan comptable, plan tiers, plan analytique, plan reporting, codes journaux, codes journaux
  analytiques, taux de taxes, banques, modèles (saisie, grille, règlement), postes budgétaires, devises…
- **Fichier** : paramètres de la société (tous les onglets / sous-commandes), autorisations d'accès,
  import / export, formats paramétrables, mise en page, impression, outils, maintenance, sauvegarde.
- **Fenêtre** et **?** : liste exacte (Réorganiser, Barre verticale, Préférences, liste des fenêtres ouvertes…).

## Recherche 2 — Menus Édition, Fenêtre et ? de Sage 100 Gestion commerciale V12

Le découpage officiel Gescom ne détaille pas ces trois menus. Relever leur contenu exact, comme en recherche 1.

## Recherche 3 — Autorisations d'accès (Comptabilité et Gestion commerciale)

Menu « Fichier › Autorisations d'accès » :
1. Organisation : profils (groupes) et utilisateurs, rattachement d'un utilisateur à un profil, administrateur /
   superviseur, mot de passe, onglets de la fiche utilisateur et de la fiche profil.
2. Présentation des droits : arbre des menus avec boutons + / −, jusqu'à quel niveau, droits globaux par menu.
3. **Libellés exacts des niveaux de droits** et leur effet précis. Nous avons retenu :
   « Tout autoriser », « Interdire la suppression », « Interdire l'écriture », « Tout interdire ».
   Confirmer ou corriger (ex. « Interdire en modification », « Lecture seule »…), et dire s'il en existe d'autres.
4. Droits particuliers hors menus : journaux protégés, types de journaux (Comptabilité), accès aux prix d'achat,
   aux marges, aux remises, aux dépôts, aux souches, aux collaborateurs (Gestion commerciale), etc.
5. Comportement à l'écran d'une commande interdite (grisée, masquée, message ?).

## Recherche 4 — Fenêtres et espace de travail (Sage 100 V12)

Comportement de la zone centrale : fenêtres réduire / agrandir / fermer, plusieurs fenêtres ouvertes, menu
Fenêtre (cascade, mosaïque, liste des fenêtres ?), barre verticale (activer / désactiver, contenu, personnalisation),
page d'accueil V12 (contenu, widgets, raccourcis).

## Recherche 5 — Fiscalité camerounaise utile à la facturation (sources officielles DGI Cameroun / CGI)

TVA (taux, assujettis et non assujettis, mentions obligatoires sur facture pour un non-assujetti), précompte sur
achats, acompte d'impôt sur le revenu (AIR), droit de timbre, centimes additionnels communaux, régimes
(réel, simplifié, impôt libératoire) et leurs obligations de facturation. Citer l'article du CGI et l'année de la loi
de finances.

---

## Format de livraison attendu (important : nous l'intégrons automatiquement)

Un dossier zippé `sage100-menus-droits-v12/` contenant :

```
sage100-menus-droits-v12/
  SKILL.md                         # en-tête YAML (name, description), résumé, mode d'emploi, limites
  references/
    MENUS_COMPTABILITE.csv         # recherche 1
    MENUS_GESCOM_COMPLEMENT.csv    # recherche 2 (Édition, Fenêtre, ?)
    AUTORISATIONS.md               # recherche 3 (texte + tableau des niveaux)
    NIVEAUX_DROITS.csv             # recherche 3, point 3
    DROITS_PARTICULIERS.csv        # recherche 3, point 4
    ESPACE_DE_TRAVAIL.md           # recherche 4
    FISCALITE_CAMEROUN.md          # recherche 5
    SOURCES.csv                    # toutes les sources consultées
    INCONNUES.csv                  # ce qui n'a pas pu être confirmé
```

### Colonnes de `MENUS_COMPTABILITE.csv` et `MENUS_GESCOM_COMPLEMENT.csv`

Séparateur `;`, encodage UTF-8, une ligne par commande **ou séparateur**, dans l'ordre d'affichage :

| Colonne | Contenu | Exemple |
|---|---|---|
| `produit` | COMPTABILITE ou GESCOM | COMPTABILITE |
| `version` | V12, V11… | V12 |
| `menu` | Fichier, Édition, Structure, Traitement, Etat, Fenêtre, ? | Etat |
| `ordre` | rang dans son parent (1, 2, 3…) | 5 |
| `niveau` | 1 = commande du menu, 2 = sous-commande… | 2 |
| `chemin` | chemin complet, niveaux séparés par ` > ` | Etat > Etats tiers > Balance âgée |
| `libelle` | libellé exact | Balance âgée |
| `type` | COMMANDE, SOUS_MENU ou SEPARATEUR | COMMANDE |
| `raccourci` | raccourci clavier, vide sinon | |
| `edition` | édition / option requise, vide si toutes | |
| `description` | une phrase | Créances échues par tranches d'ancienneté |
| `preuve` | DOC-OFFICIEL, DOC-TIERS ou A-CONFIRMER | DOC-OFFICIEL |
| `source` | URL ou document + page | KB 240126081806063, PDF Comptabilité p. 12 |

### Colonnes de `NIVEAUX_DROITS.csv`

`produit;libelle_exact;effet_consultation;effet_creation_modification;effet_suppression;preuve;source`

### Colonnes de `DROITS_PARTICULIERS.csv`

`produit;libelle_exact;emplacement_dans_l_ecran;effet;preuve;source`

Merci !
