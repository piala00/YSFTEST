# Transformations : portée et contraintes

## Matrice

La matrice couvre les paires du périmètre relevé, pas tous les types possibles du logiciel. Elle conserve INCONNU lorsqu’une règle manque. Les neuf types de vente viennent du périmètre du cahier. La matrice conserve les huit formes achat du premier relevé. Le complément V12.20 distingue maintenant les types OM (dont Demande d’achat, Facture comptabilisée et Archive) de la provenance ; il ne faut ni ajouter arbitrairement une Préparation de livraison achat ni assimiler formes UI et codes techniques. Les documents internes et la fabrication ne sont pas exhaustivement traités.

Onze paires sont positivement documentées par les processus V12.20 : vente devis vers commande ; devis/commande/préparation vers livraison ; devis/commande/préparation/livraison vers facture ; achat préparation vers commande et préparation/commande vers livraison. M02 : pages PDF 437–438, imprimées 436–437. L’existence d’une méthode Préparer ou Facturer achat (PDF p.297) ne prouve pas toutes ses origines. Le paragraphe descriptif reste incomplet par rapport à la liste des interfaces ; conserver cette divergence.

L’absence de Transformer sur facture de retour/avoir est décrite dans H01. Les lignes NON_FONCTION_UI sont limitées à ce canal et à cette aide sans version précise. Une API ou une duplication ne devient pas interdite par cette seule observation.

## Conditions V12.20

M02 (PDF p.438–441) traite des quantités disponibles, des reliquats, des séries/lots, des destinations et des conditions de fusion. Avant une intégration réelle, vérifier l’éligibilité avec le processus métier et examiner les erreurs retournées. Ne pas exécuter une mise à jour SQL pour reproduire un processus.

Pour réunir des pièces, les six critères impératifs décrits sont : tiers, 1 BL/Facture, catégorie comptable, devise, cours et souche. D’autres écarts d’en-tête peuvent empêcher la fusion selon son paramétrage. Tester également dépôt, payeur et informations de livraison. La disponibilité en stock peut laisser une quantité d’origine non transformée. Un lot/série indisponible peut faire échouer le processus entier, contrairement à un simple reliquat quantitatif. Ne pas considérer une absence d’exception comme une livraison totale.

## Différencier les actions

H03 distingue transformation, duplication et regroupement. Sa description de disparition puis régénération des pièces d’origine doit être revalidée sur le build cible, avec historique et statuts. Elle ne doit pas devenir une instruction de suppression dans l’ERP.

Les réglages de taxe, cours, échéance et frais ne se résument pas à changer le type du document. Conserver la traçabilité des liens et les quantités déjà transformées. Pour l’ERP, prévoir une transaction atomique et une protection contre les doubles traitements : ce sont des recommandations de conception, pas des fonctionnalités Sage certifiées par ce dossier.
