# Menu Fichier — Formation opérationnelle de prise en main et paramétrage

Sources : menu `references/02-menu-fichier.md` [DOC-V12] ; caractéristiques de configuration à confirmer sur dossier test.

## Cartographie pour former

| Zone/fonction | Enseigner précisément | Contrôle pédagogique |
|---|---|---|
| Nouveau / Ouvrir / Fermer | Dossier société, choix de base, utilisateurs, différences entre application et données | Identifier société active sans modification |
| Paramètres société > Identification | Informations société, adresse, pays, monnaie de tenue, formats | Contrôler l'identité d'une impression test |
| Paramètres société > Articles | Références, unités, familles, conditionnements, options de stock | Expliquer ce qui devient un défaut de création article |
| Paramètres société > Tiers | Modes de règlement, codes risques, catégories tarifaires, comptes collectifs | Créer un mode de règlement fictif si autorisé |
| Paramètres société > Documents | Souches/numérotation, types de documents, modèles d'impression, circuits | Relever numéros attendus d'un document de test |
| Paramètres société > Logistique | Dépôts, préparation/livraison, comportements stocks | Repérer les paramètres influant un BL |
| Paramètres société > Comptabilisation | Comptes, journaux, pièces et transferts comptables | Vérifier journal/état test avant comptabilisation |
| Paramètres société > TVA/taxes | Taxes et catégories ; conformité locale | Calcul HT/TVA/TTC fictif cohérent |
| Autorisations d'accès | Profils, droits, mots de passe, opérations sensibles | Comparer un rôle test avec un rôle administrateur |
| Importer / Exporter | Formats, champs, données de référence, sauvegarde avant import | Export de test en lecture et prévisualisation |
| Mise en page / Formats d'impression | Modèle d'état, champs, logo/mentions, impression | Aperçu sans émission définitive |
| Outils | Contrôles, réajustements, sauvegarde, archivage (selon édition) | Distinguer diagnostic sans impact et traitement destructif |

## Atelier 1.1 — Audit initial du dossier (sans modification)

1. Ouvrir une société **de formation** et noter version V12.xx, édition, connexion et nom du dossier.
2. Explorer `Fichier > Paramètres société` : identifier rubriques Identification, Articles, Tiers, Documents, Logistique et Comptabilisation si visibles ; marquer [OBSERVÉ].
3. Dans Documents, relever si les **souches** et règles de numérotation sont paramétrées ; ne pas les changer.
4. Dans Tiers, identifier catégories tarifaires, modes de règlements et codes risques ; noter le sens des valeurs.
5. Ouvrir une fiche article ou un document **sans enregistrement** pour constater les valeurs par défaut réellement propagées.
6. Produire la grille : paramètre → emplacement → valeur actuelle → impact probable → source → risque.

## Atelier 1.2 — Mise en place d'une société fictive

1. Concevoir identifiants, monnaie, dossiers et utilisateurs. Éviter d'appliquer des valeurs de production réelles.
2. Paramétrer les souches documentaires dans le dossier test selon les fonctions de l'édition.
3. Définir catégories tarifaires (gros/détail), modes de règlement (comptant/crédit), codes risques (contrôle des encours) et dépôts.
4. Prévisualiser un document commercial ; vérifier identité, souche, désignation, taxes et colonnes.
5. Conserver capture des paramètres et résultat attendu.

## Points de vigilance

- La **numérotation** ne doit pas être changée arbitrairement en cours d'exercice sur un dossier opérationnel.
- La présence d'une entrée dans une matrice Sage n'atteste pas de tous ses **onglets visuels**.
- Les modes de règlement, catégories et règles fiscales sont contextualisés : vérifier la configuration Cameroun/OHADA applicable sans transposer mécaniquement les obligations françaises.
- Les exports et impressions peuvent divulguer des données : utiliser fichiers de test anonymisés.

## Mini-évaluation

1. Où configurer une catégorie tarifaire et où l'affecter ensuite ?
2. Quelle différence entre une **souche** et le numéro d'une facture précise ?
3. Pourquoi vérifier le journal comptable paramétré avant une mise à jour ?
4. Que signifie une fonction visible mais grisée ? Citer trois causes.

## Réponses attendues

1. Les catégories relèvent des paramètres société/Tiers ; leur affectation se vérifie dans la fiche tiers et dans la tarification article selon dossier.
2. La souche est la série/règle de numérotation ; la pièce est une occurrence.
3. Éviter une affectation de journal inadaptée ou un transfert incorrect.
4. Édition, droits, statut/contexte, paramétrage, personnalisation, option absente.
