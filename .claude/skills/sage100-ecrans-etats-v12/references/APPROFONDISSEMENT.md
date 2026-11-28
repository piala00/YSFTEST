# Complément de l’étape 3 — version 0.2

## Lecture essentielle

Le catalogue enrichit les fiches tiers, les tarifs client, les calendriers fournisseur, le numéro externe de facture d’achat, les frais d’expédition et l’inventaire. Les ajouts d’interface restent versionnés ; les aides sans build ne deviennent pas des preuves V12. Lire les statuts avec les lignes de données.

## Type, provenance et quantités

Lire TYPES_DOCUMENTS_V12.csv et PROVENANCES_DOCUMENTS_V12.csv avant toute correspondance technique. Les symboles proviennent des énumérateurs du manuel M02 V12.20. Ils n’ont pas de valeurs numériques attestées dans ce complément. La création de facture reçoit une provenance ; ne pas inventer un code technique indépendant pour chaque forme affichée. La relation précise entre chaque forme UI et tous ses paramètres reste à contrôler.

MOUVEMENTS_ET_SIGNES_V12.csv transcrit les tableaux inspectés visuellement, en distinguant quantité UI, quantité OM, mouvement et quantité stockée. Une quantité stockée positive n’est pas à elle seule une augmentation du stock physique. Le sens du mouvement et l’unité (quantité ou montant) restent distincts. Ne pas appliquer deux fois une inversion de signe.

Les retours physiques et les avoirs financiers ne produisent pas le même mouvement. Un virement comporte une sortie et une entrée. Cette table ne calcule ni le CMUP, ni la valeur d’un avoir, ni les mouvements différentiels d’une transformation. Ne pas reposter une facture après son BL sans examiner l’historique et le processus métier.

## Témoins historiques et états

T02 est une copie d’un manuel Sage 8.50, pas V12. CONTRAINTES_HISTORIQUES.csv conserve les obligations Article trouvées sans remplir les cellules V12 inconnues avec ces valeurs. Les repères de stock, statistiques et inventaire du même manuel restent historiques. Aucun manuel complet ni capture de source n’est redistribué.

Les options des journaux comptables de H31 et celles d’inventaire de T02 ne prouvent pas une maquette V12 complète. DIVERGENCES_SOURCES.csv relève les formulations qui doivent être vérifiées avant d’en tirer une contrainte logicielle.

## Cas à rejouer sur le build cible

- Facture de retour vente : quantité UI positive, quantité OM négative ; comparer mouvement et quantité stockée à la table.
- Facture de retour achat : même contrôle du signe, avec sortie physique.
- Avoir financier achat : comparer son mouvement en montant au retour physique, sans modifier mécaniquement la quantité réelle.
- Virement : vérifier les deux dépôts et les deux lignes ; bilan global des quantités conservé pour un transfert simple.
- Passage BL vers facture : contrôler absence de double mouvement, prix modifié et reliquat éventuel.
- Centrale d’achat : vérifier l’avertissement sur les tarifs particuliers avant toute validation.
- Inventaire : comparer état préparatoire non valorisé, livre valorisé et format d’import tabulé du build cible.

Ces cas sont des propositions de recette, pas des essais réalisés sur Sage ni sur l’ERP en ligne.
