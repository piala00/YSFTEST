---
name: sage100-v12-etats-fiches-achats-complement
description: "Vérifier les états P006 à P011, fiches tiers et articles et documents achats-stock Sage 100 ; utiliser pour distinguer les contrats techniques V12.20 des écrans non observés et préparer une reproduction ERP."
---

# Etats, fiches et achats Sage

1. Lire [REPONSES.csv](references/REPONSES.csv) pour la réponse à la question. Lire [SOURCES.csv](references/SOURCES.csv) pour la version et le passage exact.
2. Respecter la qualification : FAIT_TECHNIQUE_V12.20 décrit un contrat de données, SANS_BUILD une aide non datée par version, HISTORIQUE une preuve ancienne. Ne jamais les fusionner avec une observation UI V12.
3. Lire [INCONNUES.csv](references/INCONNUES.csv) avant de proposer une implémentation. Une inconnue n’est ni une absence de fonction ni une autorisation d’inventer.
4. Ne jamais convertir une initialisation SQL/OM en valeur par défaut UI. Distinguer les neuf catégories de la matrice et les neuf symboles OM incluant Archive. Refuser une formule de correction CMUP non sourcée.
5. Citer document, URL, version et localisation pour chaque fait. Présenter les choix ERP comme propositions et les déductions comme déductions. Préserver les libellés exacts, notamment Etat dans les matrices.
6. Pour compléter la recherche, relever version affichée, offre, produit, société de test, profil, chemin, écran complet, défaut avant action et résultat. Ne déclencher aucun traitement dans un dossier réel pour faire un relevé.

## Références disponibles

- [ACHATS_CATEGORIES_MATRICE.csv](references/ACHATS_CATEGORIES_MATRICE.csv)
- [ACHATS_ENUM_OM_V1220.csv](references/ACHATS_ENUM_OM_V1220.csv)
- [ARTICLES_INITIALISATIONS_V1220.csv](references/ARTICLES_INITIALISATIONS_V1220.csv)
- [DOCUMENTS_INITIALISATIONS_V1220.csv](references/DOCUMENTS_INITIALISATIONS_V1220.csv)
- [ETATS_ET_CRITERES.csv](references/ETATS_ET_CRITERES.csv)
- [FICHES_ET_ACHATS_EXTRAITS_S03.csv](references/FICHES_ET_ACHATS_EXTRAITS_S03.csv)
- [INCONNUES.csv](references/INCONNUES.csv)
- [REPONSES.csv](references/REPONSES.csv)
- [SOURCES.csv](references/SOURCES.csv)
- [SYNTHESE.md](references/SYNTHESE.md)
- [TIERS_INITIALISATIONS_V1220.csv](references/TIERS_INITIALISATIONS_V1220.csv)
- [SYNTHESE.md](references/SYNTHESE.md) : lire pour une réponse narrative par question.
