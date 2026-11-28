---
name: sage100-matrices-menus-complement
description: "Exploiter le découpage fonctionnel Comptabilité S02 et les extraits Gestion commerciale S03 ; utiliser pour comparer les huit offres, préserver les libellés et signaler les chemins UI et différences non établis."
---

# Matrices de menus Sage

1. Lire [REPONSES.csv](references/REPONSES.csv) pour la réponse à la question. Lire [SOURCES.csv](references/SOURCES.csv) pour la version et le passage exact.
2. Respecter la qualification : FAIT_TECHNIQUE_V12.20 décrit un contrat de données, SANS_BUILD une aide non datée par version, HISTORIQUE une preuve ancienne. Ne jamais les fusionner avec une observation UI V12.
3. Lire [INCONNUES.csv](references/INCONNUES.csv) avant de proposer une implémentation. Une inconnue n’est ni une absence de fonction ni une autorisation d’inventer.
4. Lire OFFRES.csv avant la matrice. Rechercher dans COMPTA_MATRICE_8_OFFRES.csv par libellé ou menu ; consulter COMPTA_LIGNES_DOCUMENTAIRES.csv pour les intertitres. Ne pas appeler chemin complet un chemin minimal ; vérifier les cellules ambiguës dans le PDF source. Ne calculer aucun diff sans le fichier de référence.
5. Citer document, URL, version et localisation pour chaque fait. Présenter les choix ERP comme propositions et les déductions comme déductions. Préserver les libellés exacts, notamment Etat dans les matrices.
6. Pour compléter la recherche, relever version affichée, offre, produit, société de test, profil, chemin, écran complet, défaut avant action et résultat. Ne déclencher aucun traitement dans un dossier réel pour faire un relevé.

## Références disponibles

- [COMPTA_CELLULES_A_VERIFIER.csv](references/COMPTA_CELLULES_A_VERIFIER.csv)
- [COMPTA_LIGNES_DOCUMENTAIRES.csv](references/COMPTA_LIGNES_DOCUMENTAIRES.csv)
- [COMPTA_MATRICE_8_OFFRES.csv](references/COMPTA_MATRICE_8_OFFRES.csv)
- [GESCOM_FENETRE_RELEVE.csv](references/GESCOM_FENETRE_RELEVE.csv)
- [INCONNUES.csv](references/INCONNUES.csv)
- [OFFRES.csv](references/OFFRES.csv)
- [REPONSES.csv](references/REPONSES.csv)
- [SOURCES.csv](references/SOURCES.csv)
- [SYNTHESE.md](references/SYNTHESE.md)
- [SYNTHESE.md](references/SYNTHESE.md) : lire pour une réponse narrative par question.
