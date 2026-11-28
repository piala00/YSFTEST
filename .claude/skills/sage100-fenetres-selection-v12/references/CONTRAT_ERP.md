# Contrat proposé pour les fenêtres de sélection de l’ERP

Ce document est une proposition de développement destinée à Claude. Les noms techniques et règles de robustesse ci-dessous sont des choix ERP ; ils ne décrivent pas une API native Sage.

## Décrire chaque instance

Définir un identifiant stable de fenêtre, son objet métier, son champ parent, son mode (appel, filtre, état, traitement), son périmètre (société, exercice, dépôt, type de document), ses permissions, ses colonnes et critères autorisés, sa cardinalité et sa valeur de retour. Déclarer les conditions d’activation, les défauts et les critères effectivement supportés par chaque mode.

Conserver séparément : paramètres d’entrée ; filtres fixes du contexte ; critères saisis ; tri ; sélection d’objets ; options de sortie ; préférences utilisateur. Le changement d’un filtre ne doit pas devenir une autorisation supplémentaire. Les colonnes masquées ne constituent pas une protection de données.

## Retour d’un appel

Renvoyer un statut choisi/annulé, les identifiants métier retenus et les libellés nécessaires au parent. Sur annulation, conserver la valeur précédente du parent. Un choix n’enregistre pas le document et ne crée pas un tiers. Si la création en saisie est autorisée, traiter son résultat comme une opération distincte, puis décider explicitement si l’élément créé est rapatrié.

## Liste et recherche

Appliquer les permissions côté serveur, garder un tri stable avec clé de départage, définir pagination et comportement de la sélection hors page, puis afficher des compteurs cohérents avec le filtre. Prévoir liste vide, recherche sans résultat, codes homonymes, éléments en sommeil, chargement lent et modification concurrente. Ne pas exposer au client des résultats qu’il ne doit pas consulter.

## Critères et formats

Utiliser une structure explicite de groupes et prédicats ; conserver les types de valeurs et la sémantique des bornes. Ne pas assembler du SQL en concaténant les libellés reçus du navigateur. Définir les colonnes et opérateurs autorisés dans le code, paramétrer les valeurs, et valider les critères après chargement d’un format.

Un format ERP sauvegardé porte produit, fonction, version de schéma, propriétaire et portée. Il ne contient ni données de connexion ni résultats confidentiels incorporés. Réouvrir un format ne déclenche pas de remplacement, d’écriture comptable ou d’ajustement de stock.

## Avant exécution d’un traitement

Vérifier les critères réellement appliqués, les objets éligibles, le périmètre et les modifications prévues. Conserver un identifiant de traitement pour éviter les doublons lors d’une relance. Enregistrer un journal d’exécution et les rejets. Adapter la transaction au traitement métier ; sélectionner plusieurs lignes dans une liste ne suffit pas à définir une règle de comptabilisation.

## Web et bureau

Partager le contrat métier et le moteur de critères entre Django et CustomTkinter. Adapter seulement focus, touches, grille et ouverture des dialogues à l’interface. La même sélection, le même profil et le même dossier doivent donner le même périmètre dans les deux interfaces. Tester les divergences avant de déclarer l’équivalence.
