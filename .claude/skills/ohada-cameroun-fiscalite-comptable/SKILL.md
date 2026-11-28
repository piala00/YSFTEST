---
name: ohada-cameroun-fiscalite-comptable
description: Vérifier la fiscalité de facturation camerounaise 2026, les régimes fiscaux, le SMT, les états financiers et les formats DSF avant leur intégration dans un ERP OHADA.
---

# Étape 2 — Cameroun et SYSCOHADA

Livraison du 21 octobre 2026, version 0.1 documentaire. Traiter R5 à R8. Ce paquet n’est ni une homologation du logiciel ni une nomenclature finale complète prête à importer.

## Mode d’emploi

1. Lire `references/COUVERTURE_ET_LIMITES.md` puis `SOURCES.csv` et `INCONNUES.csv`.
2. Lire `FISCALITE_CAMEROUN.md`, `TAUX_ET_REGLES.csv`, `BAREME_IGS.csv` et `MENTIONS_FACTURE.csv` pour le paramétrage fiscal. Vérifier les conditions, les exceptions et la date de prise d’effet ; ne pas utiliser le seul taux.
3. Lire `DSF_CAMEROUN.md`, `STRUCTURE_DSF.csv` et `NOTES_ET_ANNEXES_DSF.csv` pour l’export.
4. Lire `ETATS_FINANCIERS_SYSCOHADA.csv` avec `STATUT_ETATS_FINANCIERS.csv`. Les colonnes comptes non établies restent explicites. Les expressions Excel sont des traces non exécutables et doivent être auditées.
5. Lire `ANOMALIES_MODELES_DGI.csv` avant de reprendre une formule. Ne pas confondre publication officielle d’un modèle et exactitude arithmétique de toutes ses cellules.
6. Utiliser `PLAN_SYSCOHADA.csv` seulement comme extrait technique de comptes fiscaux. Lire `PLAN_COMPTABLE.md` avant de compléter le plan.

## Quarantaine obligatoire

Ne jamais importer automatiquement `PLAN_CANDIDAT_NON_CERTIFIE.csv` ni `CORRESPONDANCES_CANDIDATES_NON_CERTIFIEES.csv`. Ils proviennent d’une copie portant PROJET et contiennent des anomalies. Le fait que leur titre évoque SYSCOHADA ne leur donne pas valeur normative. Leur seule utilisation autorisée par ce skill est la comparaison avec une publication finale authentifiée.

## Règles de lecture

- UTF-8 ; séparateur CSV point-virgule ; une ligne d’en-tête.
- DOC-OFFICIEL concerne un texte ou modèle publié par l’autorité ; il ne supprime pas les limites de date et de périmètre.
- Les éléments de guide technique ne constituent pas une loi fiscale camerounaise.
- Ne pas transformer une inconnue ou une proposition de calcul en fait légal.
- Distinguer régime fiscal, système comptable, assujettissement TVA, exonération par opération et habilitation à retenir à la source.
- Les modèles publics DGI relevés datent de 2021. Ne pas leur attribuer un schéma de téléversement 2026 certifié.
- SMT n’impose pas le tableau des flux du système normal (cela n’interdit pas un tableau volontaire complémentaire) ; se référer aux articles 26 et28 du texte signé O01, p. 22 imprimée.
- Conserver l’historique des règles ; ne pas recalculer rétroactivement des documents validés après une modification de taux ou de statut.
- Ne pas lancer les lots Sage écrans, SQL ou hébergement sans instruction de l’utilisateur.
