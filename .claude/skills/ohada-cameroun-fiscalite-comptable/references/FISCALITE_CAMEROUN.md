# Fiscalité camerounaise — cadrage au 1er janvier 2026

## Portée et sources

F01 est le CGI 2026 publié par la DGI. Les règles ci-dessous portent sur la facturation et les achats courants ; elles ne couvrent pas toutes les fiscalités sectorielles. L’arrêté du 5 janvier 2026 F03 est présenté comme complément postérieur au point de date demandé. F02 contient des annexes anciennes : leur présence dans une compilation intitulée2026 ne les rend pas applicables à 2026. F04, circulaire scannée, n’a pas été dépouillée intégralement et ne sert pas à combler les inconnues.

## Régimes : corriger le modèle de données

Les articles 93ter et93quater de F01 mentionnent l’IGS, le réel, les organismes à but non lucratif et les contribuables non professionnels. Les anciens régimes simplifié et impôt libératoire ne doivent pas être les catégories actuelles uniques. Conserver toutefois les valeurs historiques pour les documents des exercices précédents.

Pour les activités commerciales, industrielles, artisanales ou agropastorales, le seuil ordinaire IGS est strictement inférieur à 50 millions FCFA de CA annuel HT. Pour les professions libérales, le seuil est30 millions. Les exclusions et rattachements au réel sans condition de CA doivent être examinés. Le maintien deux ans lors d’une baisse de CA relève de 93quinquies. Les tranches et montants de l’IGS se trouvent dans BAREME_IGS.csv (C40) ; ce barème n’est pas un taux proportionnel de TVA ou d’AIR.

## TVA

Au taux général :17,5 % de principal plus10 % de ce principal de CAC, soit19,25 % au total. La loi prévoit aussi un taux réduit de 10 % pour les opérations précisément énumérées à 142(4) ; avec CAC de 10 % du principal, le taux effectif calculé est11 %. Le taux zéro vise les exportations de produits taxables, sous conditions de preuve. Ne pas confondre taux zéro et exonération.

Les règles de base sont celles des articles 135à141. L’article 141 prévoit l’arrondi de la base au millier inférieur ; ce texte ne justifie pas, à lui seul, de décider que chaque ligne de facture doit être arrondie séparément. Documenter la granularité, le calcul des CAC et les arrondis avant le développement.

Les exonérations de 128 et des annexes doivent être rattachées à un fondement légal et, le cas échéant, une position tarifaire. Un client exonéré, un fournisseur non assujetti et une vente au taux zéro sont trois situations distinctes. La mention littérale unique pour un fournisseur non assujetti n’a pas été confirmée : aucune formule supposée obligatoire n’est fournie.

## AIR et précompte sur achats : deux mécanismes distincts

L’AIR courant du réel prévu à 21(1-a) est de 2 % majoré des CAC, soit2,2 %. L’article 21(1-d) vise également l’IGS à 2 % plusCAC, sous ses dispositions propres. Les opérations à marge administrée, la commande publique inférieure à 5 millions, les professions libérales visées par F03, les contribuables hors fichier et la forêt nécessitent des règles séparées.

Pour le précompte, qualifier le régime de l’acheteur concerné ; ne pas appliquer mécaniquement une grille fondée sur le seul régime du fournisseur. Le précompte sur achats de 21(3) comporte notamment2 % pour les commerçants au réel,5 % pour ceux à l’IGS et10 % pour certaines importations IGS ou opérations hors fichier. Il n’est pas majoré des CAC. Les exemptions, la qualité de l’acheteur et celle du collecteur comptent autant que le taux. Ne pas appliquer l’ensemble AIR+précompte à toute facture sans examen de leur articulation. La règle « non récupérable sur le prix » doit être respectée ; ne pas la transformer en majoration systématique du prix client.

Le CGI impose une attestation générée dans le système fiscal pour les retenues concernées (22(3)). Un document interne de l’ERP ne remplace pas cette attestation. L’arrêté2026 prévoit l’habilitation des collecteurs et des exceptions ; leur taille ou leur nom commercial ne prouve pas l’habilitation.

## Comptabilisation

Le guide O03 (p. 35–37) distingue TVA facturée443, récupérable445, TVA due4441, crédit4449 et acomptes sur bénéfices441. Une TVA non déductible entre normalement dans le coût du bien ou la charge selon sa nature. Le montant retenu sur un encaissement ne doit pas être automatiquement passé en remise commerciale ou en réduction de chiffre d’affaires. Les sous-comptes AIR/précompte/TVA retenue doivent être validés selon le rôle de collecteur ou bénéficiaire. Les comptes détaillés non prouvés sont laissés ouverts.

## Timbre et facture

L’article 473(16) exempte généralement les quittances et reçus. Il ne faut pas en déduire un timbre à ajouter à tous les règlements, ni une règle universelle pour toute facture : qualification du document, contrat sous-jacent et éventuel texte spécial restent nécessaires. Les tarifs de papier timbré ne constituent pas un tarif automatique de facturation commerciale.

Les mentions de l’assujetti TVA sont structurées dans MENTIONS_FACTURE.csv d’après150(5). La numérotation continue, les délais de conservation et les mentions commerciales complémentaires ne sont pas certifiés par cet article dans cette livraison ; les prévoir techniquement ne permet pas de leur attribuer un fondement légal non relevé.

## Facturation électronique

L8bis organise un suivi électronique et renvoie à un arrêté pour ses conditions. Il vise notamment certains secteurs et la structure des grandes entreprises. Le CGI contient aussi des conditions de déductibilité liées au système de suivi (8bis et143). Aucun calendrier universel applicable à toute PME, aucune spécification API ni procédure d’homologation n’ont été établis ici. Ne pas présenter une facture PDF ou un simple envoi d’e-mail comme une conformité au dispositif fiscal.

## Paramétrage proposé pour l’ERP — recommandations, non texte légal

Versionner chaque règle par date de début/fin, opération, produit, régime, statut fiscal des parties, habilitation du collecteur, base, taux et arrondi. Enregistrer la preuve de l’exonération, de l’attestation fiscale et des retenues. Garder le montant facturé, le montant encaissé et les impôts retenus dans des champs distincts. Tester les changements d’exercice sans modifier les documents validés.

Pour le développement, utiliser des nombres décimaux exacts pour les montants, taux et arrondis. Ce choix technique évite les écarts d’égalité liés aux nombres flottants binaires ; il ne fixe pas une méthode légale d’arrondi.
