# 15 cas pratiques — Énoncés, contrôle attendu et pistes de correction

Tous les cas sont exécutés sur **base fictive**, jamais sur société de production. Les résultats observables dépendent du dossier ; quand un impact est variable, il faut le **tester** et en expliquer la cause.

| N° | Cas | Mission | Preuve / correction attendue |
|---|---|---|---|
| 01 | Interface | Localiser et comparer `Structure > Articles` dans deux profils | Tableau de boutons actifs/masqués + source des droits |
| 02 | Société | Retrouver paramètres de souches, taxes et règlements | Chemins, valeurs, précautions avant modification |
| 03 | Article | Créer `JUS-001` dans BOISSONS | Article retrouvable et suivi stock cohérent |
| 04 | Tarification | Appliquer catégories GROS et DÉTAIL à deux clients | Deux devis justifiés par la source de prix |
| 05 | Entrée | Entrer 100 JUS-001 au dépôt principal | Mouvement + stock avant/après |
| 06 | Transfert | Déplacer 25 JUS-001 principal → boutique | A=-25, B=+25, total inchangé si mouvement bien validé |
| 07 | Vente | Devis → BC → BL → facture pour 10 JUS-001 | Chaîne traçable ; identifier l'étape stockante réelle |
| 08 | Livraison partielle | Livrer 6 unités sur commande de 10 | Preuve du reliquat et du suivi de commande |
| 09 | Achat | BC fournisseur → réception partielle 20/30 → facture | Stock, reliquat et documents rapprochés |
| 10 | Inventaire | Stock théorique 75, compté 73 | Écart -2, motif et mouvement d'inventaire tracé |
| 11 | Règlement | Facture 150 000 FCFA, encaissement 50 000 | Solde théorique 100 000 avant autres opérations |
| 12 | Encours | Dépasser un plafond de crédit dans le dossier test | Réaction observée, paramétrage et conditions expliqués |
| 13 | Avoir/retour | Reprendre 2 unités livrées et créer document adapté | Retour physique et effet financier distincts |
| 14 | État | Concilier un état de vente avec trois pièces | Filtre, date, type pièce, avoir et totaux expliqués |
| 15 | Maintenance | Établir checklist de sauvegarde et clôture annuelle | Plan documenté, AUCUNE clôture réelle lancée |

## Corrigés de logique (pas de captures universelles)

- **Cas 04** : différentiel dû au paramétrage catégories/tarifs d'exception/remises ; vérifier la source. Un prix différent n'est pas automatiquement une erreur.
- **Cas 06** : dans un transfert interne validé correctement, les quantités des deux dépôts sont contrepassées ; surveiller date et dépôt. Toute différence sur le total nécessite analyse.
- **Cas 07** : ne pas déduire qu'un devis/BC/BL/facture décrémente chacun le stock ; interroger les mouvements liés.
- **Cas 08/09** : présenter le reliquat et la chaîne documentaire ; les écrans exacts dépendent de la configuration.
- **Cas 10** : ne pas modifier directement les tables SQL ; passer par la fonction d'inventaire et vérifier valeur et quantité.
- **Cas 11** : `150000 - 50000 = 100000` FCFA en l'absence d'avoirs, frais, écarts, autres imputations.
- **Cas 12** : avertissement ou blocage selon code risque et contrôles ; reconnaître une fonction absente si licence.
- **Cas 13** : **avoir** et **retour de marchandises** peuvent être deux effets différents ; vérifier la chaîne et la pièce.
- **Cas 14** : un état peut calculer chiffres d'affaires HT/TTC et exclure certains documents ; les filtres commandent la réponse.

## Variante d'examen final

L'utilisateur tire au sort 5 cas dont un vente, un achat/stock, un tiers/règlement, un état et un cas de panne. Claude doit proposer un plan d'action avec contrôles et justifier ses choix ; l'utilisateur effectue les actions dans le dossier test puis fait examiner les preuves.
