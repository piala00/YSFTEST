# Saisie rapide billets et colis — Codex, 30 octobre 2026

## Résultat proposé

Les formulaires verticaux de Claude au commit `023cc8f` sont réutilisés. Le téléphone précède le nom et la pièce d'identité du voyageur. Le départ affiche ligne, heure et véhicule ; il reste choisi lors du passage au passager suivant. Les champs principaux suivent un ordre vertical stable. Bagages et paramètres complémentaires restent accessibles dans des sections dépliables.

Une recherche locale retrouve les coordonnées après saisie du téléphone ; une recherche par nom complète le dispositif. Les formats camerounais local, +237 et 00237 sont équivalents, les autres pays explicites sont conservés. Une réponse tardive ne remplace pas une saisie déjà corrigée. Plusieurs personnes au même numéro imposent un choix. « Nouvelle personne » permet de conserver le téléphone partagé sans reprendre l'identité précédente.

Une vente réussie mémorise nom, téléphone et CNI disponible dans un annuaire propre au dossier de l'agence. Une CNI corrigée met à jour la personne sélectionnée sans réécrire les billets antérieurs. Sans sélection explicite, deux CNI différentes ne fusionnent pas automatiquement. Les colis mémorisent expéditeur et destinataire séparément ; aucun champ CNI n'a été ajouté au colis. Aucun trajet, prix, siège, bagage, contenu ou paiement antérieur n'est repris par la recherche.

L'action principale enregistre une nouvelle pièce, ouvre l'impression puis retourne à une saisie vierge ; un lien permet de continuer si le navigateur ne déclenche pas `afterprint`. Fermer ou annuler le dialogue d'impression ne supprime pas la vente déjà enregistrée. Les anciennes actions de vente sans impression restent disponibles. Entrée avance dans les champs de texte ; les boutons, listes, zones de texte et la composition de caractères gardent leur comportement natif. Tab conserve la navigation normale.

## Droits, données et doubles envois

Les recherches sont des POST protégés par CSRF et les droits d'écriture du service ; elles ne modifient aucune donnée. Les réponses ne sont pas mises en cache et la CNI n'est pas transmise au service colis. L'annuaire ne publie pas les contacts dans les échanges interagences.

La migration additive `0017` crée l'annuaire et les reçus de saisie. Elle reprend uniquement les coordonnées des pièces locales (`site_origine=""`), sur l'alias de la migration, sans modifier les pièces financières. Les anciens numéros invalides ne sont pas indexés. Les contacts sont réutilisables hors ligne dans ce dossier, sans base centrale extérieure.

Chaque ouverture du nouveau formulaire fournit un jeton signé lié à l'utilisateur et au service, valable douze heures. Le serveur conserve le résultat dans la transaction de vente : un renvoi identique retrouve cette pièce et une réutilisation avec d'autres informations est refusée. L'interface bloque aussi le double clic. Les anciens clients qui n'envoient pas `interface_rapide` ni jeton conservent leur comportement antérieur ; leur protocole n'est pas couvert par cette nouvelle garantie. Ce lot ne remplace pas l'ensemble de la recette P0 des autres écritures.

## Dépendance et validation

Branche `gpt/saisie-rapide-contacts-transport`, empilée sur la PR licences #11 (`5530ce2`) afin que le paquet demandé conserve les licences simplifiées. La PR cible provisoirement cette branche pour isoler le diff ; l'intégration finale vers `ccr-5592a371-fusjt2` reste soumise au propriétaire. Aucune fusion, aucun déploiement ni accès en écriture à une production.

Avant publication : 13 scénarios Node du script livré, quatre tests Python de normalisation et compilation syntaxique exécutés localement. Django manque dans cet environnement et le proxy ne permet pas son installation ; la suite complète sera exécutée par la CI sur la PR en brouillon, puis ses résultats exacts seront consignés. Les tests ajoutés couvrent aussi les parcours HTTP et financiers, les droits/CSRF, la reprise historique, les doublons et l'impression. La compilation Windows et ses essais automatisés sont attendus avant livraison du nouveau paquet. La validation visuelle du rythme de saisie et l'impression sur l'imprimante réelle de l'agence restent à effectuer sur Windows.
