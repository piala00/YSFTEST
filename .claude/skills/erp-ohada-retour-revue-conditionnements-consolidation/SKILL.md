---
name: erp-ohada-retour-revue-conditionnements-consolidation
description: "Exploiter le retour de revue du ZIP transmission-gpt-2026-10-24 pour Claude : anomalies ERP reproduites, décisions proposées, preuves Sage 100 V12.20 sur conditionnements et spécification des échanges entre agences hors ligne. Utiliser pour corriger le contrôle fichiste, les rapports datés, la traçabilité, préparer gros/détail et la vue regroupée sans doublons."
---

# Retour de revue pour Claude

## Lire et qualifier

Lire [SYNTHESE_RETOUR.md](references/SYNTHESE_RETOUR.md) et [BILAN_TESTS.md](references/BILAN_TESTS.md). Consulter les journaux [suite fournie](references/PREUVES_TESTS_BASE.md) et [tests complémentaires](references/PREUVES_TESTS_COMPLEMENTAIRES.md) pour les preuves brutes. Ce Skill complète le cahier métier erp-ohada-agences-hors-ligne-rapport-stock ; il ne le remplace pas et ne constitue pas une nouvelle implémentation ERP.

La copie examinée est identifiée par son archive et ses empreintes dans [PROVENANCE_FICHIERS.csv](references/PROVENANCE_FICHIERS.csv). Ne pas assimiler ce ZIP à la version GitHub ou à un site déployé non vérifiés.

Distinguer : REPRODUIT (test réellement exécuté), VERIFIE_CODE (lecture seulement), FAIT_DOCUMENTAIRE_V12.20, SANS_BUILD, PROPOSITION_ERP et A_ARBITRER. Les spécifications d’échange et d’unités sont des propositions, pas des fonctions livrées. Les 155 tests existants passent ; 8 tests complémentaires donnent 1 succès et 7 échecs attendus révélant les anomalies. Ne pas résumer cela par « tous les tests du logiciel passent ».

## Corriger les anomalies avant de généraliser

Lire [ANOMALIES.csv](references/ANOMALIES.csv) et [CORRECTIONS_PRIORITAIRES.csv](references/CORRECTIONS_PRIORITAIRES.csv). Exécuter les tests de reproduction de scripts/review_probes.py dans une copie locale de la version appropriée, selon BILAN_TESTS.md. Les échecs de ces tests sont le résultat de la revue, pas une panne du dispositif de test.

Ne pas fermer A01 en masquant simplement une colonne ou en bloquant la seule URL filtrée : contrôler les listes et objets côté serveur. Ne pas fermer A02 par required HTML seulement. Conserver la déclaration ancienne et son auteur avant de remplacer le fichiste. Ne pas déclarer un stock magasin indépendant en recopiant les mouvements non saisis. Pour A07, contrôler ensemble mode, journal, compte et rapport avant de séparer les totaux ; ne pas casser la concordance comptable.

## Préparer les choix et la suite

Lire [DECISIONS_ET_ORDRE.md](references/DECISIONS_ET_ORDRE.md) et [AVIS_DECISIONS.csv](references/AVIS_DECISIONS.csv). Présenter les recommandations comme propositions argumentées ; le choix final revient à l’utilisateur. Les points historiques du 22/10/2026 restent ouverts après les quatre priorités de cette transmission.

## Étudier les conditionnements

Lire ensemble [CONDITIONNEMENTS_SAGE.csv](references/CONDITIONNEMENTS_SAGE.csv), [SOURCES.csv](references/SOURCES.csv) et [INCONNUES_CONDITIONNEMENTS.csv](references/INCONNUES_CONDITIONNEMENTS.csv). Utiliser [SPEC_CONDITIONNEMENTS_ERP.md](references/SPEC_CONDITIONNEMENTS_ERP.md) pour la réalisation proposée.

Les correspondances d’onglets sont documentaires V12.20, pas des captures observées. Ne pas fabriquer l’ordre complet des champs, les boutons ou les valeurs par défaut. Ne pas confondre unité de vente, intitulé de conditionnement, quantité de colisage, prix d’une présentation et prix unitaire de référence. Ne pas copier les contraintes Sage comme des interdictions universelles du nouvel ERP. Ne jamais écrire dans une base Sage pour cette étude.

## Spécifier les échanges et le regroupement

Lire [SPEC_ECHANGES_AGENCES.md](references/SPEC_ECHANGES_AGENCES.md), [DICTIONNAIRE_ECHANGES.csv](references/DICTIONNAIRE_ECHANGES.csv), [CORRESPONDANCES_ET_REGROUPEMENT.csv](references/CORRESPONDANCES_ET_REGROUPEMENT.csv) et [RECETTE_ECHANGES.csv](references/RECETTE_ECHANGES.csv). Les exemples d’enveloppes dans [EXEMPLES_ECHANGES.json](references/EXEMPLES_ECHANGES.json) sont fictifs et ne sont ni des paquets authentifiés ni un export de la société.

Préserver une même société et plusieurs serveurs locaux autonomes. Proposer le central comme lecture regroupée avec faits d’origine et journal d’intégration ; ne pas recréer puis valider les pièces locales au central via des fonctions qui généreraient encore stock ou comptabilité. Prévoir identité de société/site/objet, versions, rejouabilité sans doublons, dépendances, acquittement durable et reprise. Conserver auteurs d’origine et dates métier. Ne pas importer un règlement manuel existant une deuxième fois lors de la première synchronisation.

## Livrer à l’utilisateur

Réutiliser le code présent ; rattacher chaque correction à A01–A07 et aux exigences E/P/R concernées. Rapporter les fichiers modifiés, migrations, tests réellement exécutés et limites. Aucun fichier applicatif ni serveur de production n’a été modifié pour la présente revue. Demander seulement les arbitrages nécessaires au prochain incrément ; ne pas effacer les fonctions déjà présentes.
