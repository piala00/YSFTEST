# Traitement — Cycle intégral des ventes

Menu documenté : `Traitement > Documents des ventes`. Voir `references/05-menu-traitement.md` [DOC-V12].

## Types de pièces recensés dans le découpage Sage

Devis ; bon de commande ; préparation de livraison ; bon de livraison ; bon de retour ; bon d'avoir financier ; facture ; facture de retour ; facture d'avoir. Les incidences sur les stocks et sur la comptabilisation **dépendent du type, du statut et des paramètres** : les vérifier dans les états avant/après.

## Processus de référence à expliquer

`Prospect/client → devis → acceptation → commande → préparation → livraison → facture → échéance/règlement → éventuellement retour/avoir`

Ce schéma est **pédagogique**, pas un ordre imposé à toutes les entreprises ; facturation directe, vente comptoir, livraisons partielles et pièces transformées peuvent modifier la chaîne.

## Procédure guidée 3.1 — Vente à crédit de A à Z

**Données d'exercice** : client `CLI-001`, dépôt TEST-PRINCIPAL, article `JUS-001`, quantité 10, prix de vente fictif 1 500 FCFA/unité HT (selon fiscalité du dossier), règlement crédit 30 jours.

1. Vérifier article, tarif client, stock disponible dans le dépôt, conditions du tiers et droits.
2. Ouvrir les documents des ventes ; créer un devis si l'édition et le processus le requièrent. Relever souche, date, client, dépôt et lignes.
3. Insérer article, quantité et prix ; vérifier réductions, taxes, total et conditions.
4. Transformer ou établir une commande client selon la commande réellement disponible. Conserver le lien de pièce dans la traçabilité documentaire.
5. Préparer et livrer suivant fonctions installées ; relever **stock avant et après chaque étape** pour identifier la pièce effectivement mouvementante.
6. Créer/transformer la facture, contrôler n° pièce, client, lignes, HT/TVA/TTC, échancier et statut.
7. Si nécessaire, **valider** selon le processus du dossier ; identifier précisément quel événement autorise ou déclenche la comptabilisation.
8. Vérifier le document dans la recherche et les états ; mesurer encours et état de règlement sans confusion entre facture et encaissement.
9. Produire compte rendu : n° pièces, quantités, stock avant/après, encours avant/après, écarts.

## Procédure guidée 3.2 — Retour et avoir

1. Ouvrir la facture d'origine et relever état/quantité.
2. Identifier le motif du retour et si des marchandises rentrent physiquement.
3. Choisir la pièce adaptée (bon de retour, facture de retour, facture d'avoir, avoir financier) **en fonction du processus Sage et des règles métier**, ne pas les traiter comme synonymes.
4. Examiner les incidences sur le stock et le solde client ; rapprocher facture d'origine, retour, avoir et règlement.
5. Si l'objectif est de solder une facture avec un avoir, utiliser le guide Sage S12 comme **cas spécifique**, en vérifiant la configuration et la comptabilité. Une facture d'avoir n'est pas nécessairement imputée comme un règlement direct.

## Tableau d'observation obligatoire

| Étape | Pièce | État avant | État après | Contrôle |
|---|---|---|---|---|
| Devis | numéro/type | stock, encours | stock, encours | A-t-il changé ? |
| Commande | numéro/type | stock, encours | stock, encours | Engagement ? |
| Livraison | numéro/type | stock, encours | stock, encours | Quantité sortie ? |
| Facture | numéro/type | stock, encours | stock, encours | Document et échéance ? |
| Retour | numéro/type | stock, encours | stock, encours | Entrée physique ? |
| Avoir | numéro/type | stock, encours | stock, encours | Réduction de créance ? |

## Erreurs fréquentes à faire diagnostiquer

- Prix inattendu : catégorie tarifaire, tarif d'exception, date, devise, remise, « Recalculer le prix de vente ».
- Document indisponible à transformer : nature de pièce, statut, droits, liens existants, contraintes du paramétrage.
- Double impact stock soupçonné : vérifier chaîne documentaire et mouvements réels, jamais conclure du seul nombre de pièces.
- Facture absente d'état : filtres/date/souche/type, validation, dossier et droits.

**Sources complémentaires** : Sage S11 et S12 dans `references/00-sources-et-perimetre.md`.
