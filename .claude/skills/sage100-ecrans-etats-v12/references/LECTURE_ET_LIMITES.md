# Portée de la livraison

Relevé du 21 octobre 2026. R9, R10 et R11 restent partiels. Le tableau COUVERTURE.csv suit tous les objets demandés, y compris ceux dont aucun catalogue complet n’a pu être établi.

Le paquet contient 57 zones Gescom, 76 zones Comptabilité, 17 fonctions d’écran, 30 entrées d’options/colonnes/variantes d’états et 36 sources. Ces nombres mesurent le relevé, pas un pourcentage de complétude. Les 154 paires de transformations comprennent 11 possibilités OM confirmées sous conditions, 18 absences de fonction UI documentées sans build précis et 125 inconnues.

## Versions et preuves

L’article V01 rapproche le découpage fonctionnel V11/V12. Cette déclaration ne prouve pas l’identité de tous les contrôles UI. Les aides Hxx et Gxx sont officielles Sage 100, mais les pages consultées ne précisent pas systématiquement le build concerné. Elles documentent des éléments généraux ; leur présence identique en V12 reste A-CONFIRMER.

M02 porte explicitement V12.20 et une actualisation de juillet 2026. Il documente les Objets Métiers, pas toutes les pages de l’interface. M01 est un PDF composite de 1 071 pages dont la version annoncée est 8.50, juillet 2016 : ses quelques champs et états sont des témoins historiques. M03 est un manuel technique 2024 présentant une capture de banque ; ce n’est pas une fiche complète V12. Le support T01, attribué à Sage Training France mais hébergé chez un partenaire, est classé DOC-TIERS. Sa couverture datée 2026 ne démontre pas que les captures représentent V12.

Le format F01 est une description d’import/export 100cloud V5, pas une documentation de contrôles UI ni de tables SQL V12. Ses exemples restent dans un fichier séparé.

## Catalogues d’écrans

Les colonnes requises par le cahier sont conservées. STATUT_CHAMPS utilise le nom du fichier et le numéro de ligne CSV (en-tête = ligne 1). Les descriptions rappellent les conditions ; elles sont des synthèses. DOC-TEXTE signifie que le terme apparaît dans le texte consulté ; TERME_NARRATIF signifie que sa graphie exacte comme contrôle n’est pas démontrée. La présence dans une page ne prouve pas la liste exhaustive des champs.

Joindre chaque catalogue à son compagnon avant tout tri, insertion ou déduplication. Vérifier aussi ecran/onglet/champ, ou domaine/type_origine/type_cible pour les transformations ; le seul numéro de ligne n’est pas une clé stable après modification. Ne pas charger un catalogue isolé comme une définition exécutable de schéma. Employer un lecteur CSV qui respecte les guillemets : certaines cellules contiennent des points-virgules. Conserver les valeurs de statut comme des chaînes explicites ; les trois états de transformations ne sont pas des booléens.

La colonne type décrit une propriété de contrôle attestée : LISTE, CASE_A_COCHER, DATE avec calendrier, CHOIX entre options, CURSEUR ou TEXTE. CHOIX ne certifie pas s’il s’agit d’une liste déroulante ou de boutons radio. Aucune conversion automatique vers VARCHAR, DECIMAL ou autre type SQL n’est fournie. Une longueur NON_ETABLIE n’est pas une chaîne illimitée. La longueur 17 citée pour la pièce de trésorerie appartient au manuel historique M01, pas à une contrainte V12 certifiée. Dans Tiers > Codification, la limite documentée du numéro tiers est expliquée dans la description ; elle ne donne pas la largeur du contrôle Longueur lui-même.

L’obligation de paramétrer une colonne Référence/Désignation pour créer des documents ne signifie pas que chaque ligne de commentaire doit obligatoirement contenir une référence article. Les obligations des champs non établies restent explicites.

Les rubriques Paramètres société > Tiers sont des paramètres globaux. L’article H07, malgré son titre, ne décrit pas une fiche tiers complète. Ne pas les fusionner avec une fiche Client ou Fournisseur. Une page du parcours Code journal n’est pas un onglet réel.

## Fidélité des états

Les états historiques ne donnent pas un rendu V12 certifié. La colonne type sépare OPTION, COLONNE et VARIANTE. Les titres descriptifs ne garantissent pas la casse exacte de l’en-tête imprimé. Le modèle, la langue, la personnalisation et l’édition peuvent changer le résultat. Les colonnes non relevées ne sont pas inventées.

## Utilisation pour l’ERP OHADA

Ce paquet sert à préparer des écrans et des contrôles. Les comptes et exemples PCG français, les obligations françaises de facture électronique et les taux présents dans les sources ne doivent pas devenir des règles fiscales camerounaises. Consulter le paquet OHADA/Cameroun de l’étape 2 pour les questions légales et ses limites.

Aucune donnée d’entreprise, identité d’exemple, clé de licence, adresse de démonstration ou secret n’est livrée. Aucune action de modification ou transmission n’a été effectuée sur l’ERP en ligne.
