# Règles de sélection à préserver

## Valeurs vides, groupes et opérateurs

L’aide H01 donne un comportement précis pour les valeurs vides de sa recherche : elles englobent le fichier concerné. Cela ne décrit pas les bornes de toutes les autres fenêtres. H06 décrit une recherche multi-mots de type au moins un mot. Ne pas lui substituer automatiquement un ET entre les termes.

Le témoin T01 illustre une évaluation séquentielle : A et B ou C et D revient à ((A et B) ou C) et D. Pour (A et B) ou (C et D), il utilise des groupes. Un moteur SQL avec sa priorité native AND/OR peut produire un résultat différent. Les règles Soit, Sans, intervalles, dates relatives, NULL et valeurs absentes doivent faire l’objet de cas distincts sur le build cible. Cette observation historique ne certifie pas la grammaire complète V12.

## Mode de traitement et critères effectifs

Les guides M02 et M03, V10.00 et sup., distinguent Rapide simplifié et Avec des critères étendus. Un critère ajouté dans l’éditeur peut être ignoré par le traitement rapide lorsqu’il sort des critères pris en charge. La recette doit vérifier les résultats obtenus ; la présence visuelle d’un critère ne suffit pas à prouver son application.

Pour l’ERP, choix de conception proposé : afficher les critères actifs, signaler un critère incompatible avec le mode avant exécution et permettre un mode compatible. Ne pas reproduire un filtre ignoré silencieusement en le présentant comme correctement appliqué.

## Formats et mémorisation

Le témoin différencie la validation temporaire d’une ligne et la sauvegarde durable du format. H02/H03 documentent l’enregistrement puis la réouverture d’une recherche, mais citent .sma dans un article multi-produits. Ne pas imposer cette extension à Gescom. Un fichier de sélection .fma/.fgc, un format de recherche et un modèle .bma/.bgc répondent à des usages distincts. Leur conversion ou compatibilité binaire ne sont pas établies ici.

Changer le domaine Client/Fournisseur peut modifier les fichiers de critères requis ; T01 documente des ajustements manuels dans un format avancé. Enregistrer les identifiants du contexte et les versions dans un futur format ERP évite de réutiliser un critère sur le mauvais ensemble de données.

## Droits, tri et retour

Les droits sur la consultation, la création ou le traitement doivent être vérifiés séparément. La personnalisation d’un affichage ne doit pas étendre les droits. H05 documente des colonnes verrouillées. La disposition de ces contrôles et la persistance des choix doivent être relevées par utilisateur et dossier.

Pour une liste d’appel, préciser sélection simple/multiple, effet d’OK, Annuler, Echap, Entrée, double-clic, choix d’un élément en sommeil, création autorisée et restauration du focus. Ces comportements restent à observer lorsqu’ils ne sont pas attestés par les sources du contexte.
