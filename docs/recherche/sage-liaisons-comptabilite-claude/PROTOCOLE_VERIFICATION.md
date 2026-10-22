# Protocole de vérification sur installation autorisée

Le présent dossier n’a exécuté aucun test sur Sage. Les scénarios de la recette distinguent les comportements natifs à observer et les résultats attendus de la conception ERP proposée.

1. Inventorier les produits, versions, éditions, pays/législations, licences, serveur/base et fichiers logiques. Noter les connecteurs réellement déployés.
2. Préparer une copie cohérente et anonymisée, avec connecteurs d’envoi désactivés. Utiliser les procédures de sauvegarde/restauration adaptées ; ne pas copier des fichiers MDF/LDF ouverts comme méthode de sauvegarde.
3. Constituer une situation initiale : références des tiers et comptes, paramètres, documents ouverts, totaux et droits effectifs. Les captures et journaux ne doivent contenir aucun secret.
4. Exécuter chaque scénario pertinent dans une copie distincte si l’opération modifie durablement une période, une pièce ou un référentiel. Ne changer qu’un facteur à la fois.
5. Relever : version, compte utilisateur, compte de service, société, date, entrée utilisée, paramètres avant/après, message exact, référence créée et totaux. Un menu masqué ne suffit pas à conclure au refus de tous les canaux.
6. Pour les observations techniques SQL, rester en lecture seule. Distinguer les index et jointures du manuel de ceux observés dans le catalogue SQL. Aucun INSERT/UPDATE/DELETE de tiers, droits ou marqueurs de comptabilisation n’est prévu ici.
7. Après échec ou coupure, contrôler ce qui a réellement été intégré avant de relancer. Garder une trace des pièces acceptées et des éléments d’état inconnu.
8. Joindre une preuve à chaque conclusion et mettre à jour la question correspondante dans INCONNUES. Sans preuve, conserver la question ouverte.

## Fiche de résultat à remplir

| Champ | Contenu à relever |
|---|---|
| Scénario | Txx |
| Produit / version / édition | Valeurs exactes |
| Société / dossier / copie | Références anonymisées |
| Identité humaine / technique | Rôles, sans secret |
| Paramètres initiaux | Valeurs utiles |
| Action | Point d’entrée et séquence |
| Résultat | Message et effet réellement constatés |
| Rapprochement | Totaux et références avant/après |
| Conclusion | Confirmé / divergence / inconnu |
| Pièce de preuve | Capture ou journal anonymisé |

Ces contrôles sur Sage et ces développements ERP sont des travaux à réaliser ultérieurement sur un environnement autorisé, pas des validations déjà obtenues.
