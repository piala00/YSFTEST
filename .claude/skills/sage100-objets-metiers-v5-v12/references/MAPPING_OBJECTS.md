# Matrice des objets à documenter (interfaces exactes depuis SDK)

| Domaine | Objet conceptuel attendu | Vérification |
|---|---|---|
| Connexion société | Application/connexion/dossier | Authentification et droits, architecture 32/64 |
| Tiers | Client / fournisseur | Création, modification, catégories et contrôles |
| Catalogue | Article / familles / tarifs | Prix, stock, taxe et conditions |
| Documents ventes | En-tête et lignes, usine/factory | Type et transformation, numérotation |
| Documents achats | En-tête et lignes | Commande, réception, facturation |
| Stock | Mouvement / dépôt | Régularisation, transfert, inventaire |
| Compta | Compte, journal, écriture | Équilibre, validation, exercice, période |
| Finance | Règlement / échéance | Affectation, lettrage, réconciliation |

**Attention** : ces noms sont **conceptuels** et ne sont pas les noms de classes SDK prouvés. Pour chaque version, remplir type library GUID + interface exacte + signature + manuel officiel.
