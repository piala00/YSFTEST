# U6 — Fonctionnement transversal des fenêtres et captures Sage

## Portée et provenance

U6, 24 octobre 2026 : l’utilisateur fournit deux captures et précise que le fonctionnement des fenêtres doit être étudié pour tous les écrans concernés de comptabilité et gestion commerciale. Étendre le contrat ERP au bureau entier ; ne pas limiter la correction au bouton règlement de la facture. Le détail de chaque écran Sage et chaque produit ne sont pas tous observés. Le terme oral « mode de gestion » ne permet pas de certifier un produit supplémentaire.

Preuves visuelles : deux captures fournies par l’utilisateur (assets/captures/1000992153.png et 1000992154.png dans le zip d’origine ; non versées dans ce dépôt car elles contiennent des données réelles). Sage 100 Gestion commerciale Premium est visible ; le numéro de version/build n’est pas visible. Ne pas les présenter comme des captures V12.20 prouvées. Données métier réelles : conserver leur usage au dossier privé de transmission ; employer des données fictives pour tests et démonstrations.

## Relevé des deux captures

- Une fenêtre principale de l’application encadre une fenêtre interne « Saisie des règlements clients » ; le bureau reste visible autour.
- Barre de titre propre à la fenêtre interne, avec symboles réduire, agrandir/restaurer et fermer. Une image fixe montre les commandes, pas leur comportement après clic ni la persistance d’un brouillon.
- Barre d’actions locale : Fonctions, Historique, Sélectionner, Visualiser, Imprimer ; certaines actions sont grisées selon la capture. Le contenu de Fonctions n’est pas déployé.
- Volet gauche : Tous, Règlements non imputés, Règlements soldés ; lien Plus de critères.
- Filtre client en haut : critère Numéro, valeur client, bouton Afficher.
- Ligne de saisie et commandes Nouveau, Supprimer, Enregistrer. Sur la capture détaillée : date, numéro de pièce, libellé, compte général, montant, code journal.
- Tableau des règlements avec Date, N° pièce, Libellé, Compte général, Montant, Code journal ; ascenseurs et colonnes supplémentaires éventuellement hors champ ne sont pas inventoriés.
- Bas de fenêtre : Type de règlement, Total règlement, Total imputé, Solde ; bouton Fermer.
- La première capture montre un tableau vide avec Tous sélectionné ; la seconde un tableau rempli avec Règlements non imputés sélectionné. Les captures ne constituent pas une séquence de clics enregistrée : ne pas déduire la cause du vide ni le délai de chargement.

Ce tableau est une liste de règlements, pas la preuve visuelle du sélecteur des factures à affecter. L’action Sélectionner existe mais son effet exact n’est pas montré. La sélection de plusieurs factures reste confirmée par U5. La présentation finale de l’en-tête ERP n’est pas fournie par ces seules captures : distinguer en-tête d’écran et en-tête imprimé du reçu.

## Contrat transversal ERP — exigence U5/U6 et conception proposée

Les fenêtres de travail métier doivent rester ouvertes quand une nouvelle fenêtre métier est appelée. Appliquer à tous les modules de l’ERP concernés. L’indépendance visuelle ne signifie ni absence de lien métier ni absence de contrôles transactionnels.

| Famille | Exemples à couvrir | Contrat proposé |
| --- | --- | --- |
| Listes | clients, articles, factures, écritures, règlements | Conserver filtres, tri, position et sélection au retour depuis une fiche. |
| Fiches et documents | tiers, article, BC, BL, facture, reçu | Ouvrir sans remplacer la fenêtre d’origine ; fermer individuellement ; conserver les brouillons. |
| Saisies comptables | journal, pièce, consultation de compte | Isoler contexte société/agence/exercice/journal et état de saisie ; actualiser après validation sans effacer les autres saisies. |
| Appels de sélection | client, article, compte, facture, journal | Retourner uniquement la sélection au champ appelant ; Annuler laisse le parent intact. Le parent temporairement bloqué pendant ce choix est possible si nécessaire. |
| Critères et états | balance, grand livre, créances, stock, rapport commercial | Conserver critères ; résultat/aperçu accessible sans détruire le document de travail. |
| Paramétrage | société, agences, droits, journaux, unités | Protéger les saisies en cours, contrôler permissions, signaler quand un rafraîchissement est requis. |
| Confirmations | annulation, suppression, abandon de saisie | Dialogue bref pouvant être modal ; retour exact au contexte ; aucune action destructive par simple fermeture. |
| Traitements | validation, export, rapprochement, clôture | Empêcher lancement multiple et interruptions incohérentes ; afficher progression/erreur ; ne pas fermer silencieusement les documents ouverts. |

Ne pas rendre toutes les petites confirmations et tous les sélecteurs obligatoirement non modaux. Le besoin porte sur la coexistence et la navigation entre fenêtres métier ; les dialogues de décision ou sélection peuvent avoir une dépendance courte et explicite. Ne pas prétendre que toutes les fenêtres de tous les produits Sage sont indépendantes.

Gestionnaire commun proposé : identité de fenêtre, type, identifiant du document, contexte société/agence, état brouillon, titre, géométrie, ordre de superposition et statut de chargement. Activer au clic ; rendre disponibles déplacement, redimensionnement, réduction/restauration et fermeture propre ; proposer un menu ou une liste des fenêtres ouvertes. Prévoir une disposition côte à côte/empilée si utile. Ces capacités sont des propositions ERP, pas des fonctions V12 attestées par les images.

Une même facture demandée deux fois : proposer la réactivation de la fenêtre existante pour éviter deux brouillons concurrents. Ce choix est à arrêter ; plusieurs documents différents doivent rester possibles. Aucun document ne devient « enregistré » par réduction ou changement de premier plan. Demander explicitement enregistrer/abandonner/revenir en cas de fermeture d’un brouillon modifié.

Conserver les droits côté serveur pour chaque action et résultat ; éviter les données d’une autre société lors d’un changement de contexte. Recontrôler version du document, état et reste dû lors d’une validation concurrente. Après règlement, diffuser un rafraîchissement ciblé aux vues concernées, sans recréer l’encaissement ni écraser un autre brouillon. Le travail hors ligne reste applicable ; une fenêtre ouverte n’est pas une garantie de données globales fraîches.

## Sources documentaires et limites

S1 — Sage, Programmes externes, V3.00 et sup., actualisation mars 2024, consulté le 24/10/2026 : https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095151540 . Le document décrit des dépendances de pages web intégrées à leur enregistrement appelant (page PDF 6), ainsi que le rôle de l’option Affichage libre des fenêtres dans leur affichage. Preuve limitée à ces contextes : elle ne démontre pas tous les comportements des fenêtres natives V12.

S2 — Sage Comptabilité i7, aide historique Les boutons : https://documentation.sage.fr/bupe/DOCS/Sage%20Comptabilit%C3%A9%20i7/_Generales/Les_boutons.htm . La navigation précédente/suivante peut changer de fiche dans la même fenêtre. Ne pas confondre navigation de fiche et ouverture indépendante, ni extrapoler cette aide i7 à toute version Sage 100.

Les références Multi Devis, X3 et autres produits ne doivent pas servir à affirmer la mécanique exacte de Comptabilité/Gestion commerciale V12. Les captures et l’exigence utilisateur suffisent à fixer le contrat ERP ; une observation interactive Sage reste nécessaire pour certifier raccourcis, modalités, préférences et exceptions par écran.

## Recette proposée, non exécutée

1. Depuis facture A, ouvrir règlement B ; A reste ouverte et accessible, son brouillon est identique après bascule A/B.
2. Ouvrir facture C, BL D et fiche client E ; activer, déplacer, réduire/restaurer, fermer B ; A/C/D/E restent ouvertes.
3. Depuis une liste filtrée, ouvrir une fiche puis fermer la fiche ; retrouver filtres, tri et position.
4. Sélectionner un tiers/article/compte dans un appel ; retour au bon champ du bon parent. Annuler ne modifie rien.
5. Ouvrir une saisie de journal puis un état ; revenir sans perdre les lignes comptables non enregistrées.
6. Sauver un règlement affecté à plusieurs factures ; actualiser les soldes concernés, une seule transaction monétaire, aucune destruction de brouillon.
7. Fermer une fenêtre modifiée puis choisir revenir ; retrouver saisie exacte. Fermer une fenêtre intacte ne ferme pas les autres.
8. Ouvrir confirmation de suppression et annuler ; ni suppression ni fermeture du document parent.
9. Deux fenêtres valident sur un même reste dû ; le serveur refuse le dépassement, même si l’affichage était ancien.
10. Répéter sur le vrai bureau web et le client bureau concerné ; tester clavier et écran réduit. Le mode mobile peut adapter l’affichage sans détruire les sessions de travail.

## Livraison à Claude

Inspecter le gestionnaire existant, les routes, liens, redirections et événements. Inventorier chaque appel avec : module, écran parent, commande, écran enfant, modalité, état conservé, événement de rafraîchissement, droit et preuve de test. Corriger le mécanisme partagé puis les appels qui le contournent. Ne pas réécrire toutes les fenêtres sans inventaire. Les captures livrées ne prouvent aucun correctif dans l’ERP.
