# 09 — Editions, options et droits : précautions [DOC-V12]

## Editions et environnements dans la matrice V12.10

Sage distingue notamment :

- **Sur site (On premise)** : Essentials, Standard et Premium ; la matrice associe SQL Server Express aux deux premières éditions et SQL Server à Premium, selon cette version de l'offre.
- **Sage 100 hébergé** : éditions mentionnées dans la matrice, sous Azure SQL Database.
- **Cloud partenaire / 100 SPC** : éditions mentionnées dans la matrice, sous Azure SQL Database.

Ces indications proviennent de la matrice officielle ; elles ne constituent pas un engagement contractuel pour tous les pays, toutes les configurations et toutes les sous-versions.

## Options fréquemment conditionnelles

| Option / dépendance | Exemples de fonctionnalités affectées |
|---|---|
| Logistique | Contremarque, certaines préparations livraisons, réception fournisseurs, contrôle qualité, emplacements de contrôle |
| Fabrication | Ordres, projets, nomenclatures et planification fabrication |
| Services | Affaires, prestations, abonnements, documents internes |
| Traçabilité | Lots et numéros de série |
| Gamme | Variantes et codifications en gammes |
| Services connectés | Facturation électronique, paiements, Microsoft 365 et échanges |
| Profil utilisateur | Accès aux modules, modification, suppressions, paramétrages, imports/exports |

## Sources d'absence d'un bouton ou d'une commande

1. La fonction n'existe pas dans l'**édition**.
2. L'**option** n'est pas acquise ou activée.
3. Le **rôle utilisateur** ne possède pas le droit.
4. Le type de pièce, statut du document, stock ou situation métier rend la commande **inactive**.
5. La **personnalisation** de l'écran a masqué la zone ou le bouton.
6. Le **déploiement** ou un service connecté n'offre pas la fonction.
7. La **sous-version V12.x** a modifié l'affichage ou le comportement.

## Tableau de vérification pour un menu manquant

```text
Nom de la commande :
Version exacte :
Edition + options :
Déploiement :
Utilisateur et rôle :
Menu / fenêtre / contexte :
Commande absente, masquée ou grisée ?
Même résultat avec un administrateur autorisé ?
Personnalisation active ?
Etat de la pièce / document :
Preuve capture :
Conclusion + degré de confiance :
```

**Ne pas contourner les autorisations** pour obtenir une apparence similaire, et ne jamais affirmer que le compte administrateur voit nécessairement une édition supérieure.
