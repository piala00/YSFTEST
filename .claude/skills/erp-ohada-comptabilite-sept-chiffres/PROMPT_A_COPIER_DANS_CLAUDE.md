# Message prêt à envoyer à Claude

Je t'envoie le Skill `erp-ohada-comptabilite-sept-chiffres`. Étudie `SKILL.md` et tous les documents de `references/` ; puis inspecte le **code actuel de mon ERP** (GitHub ou mon dossier de projet), sans le remplacer par une vieille version.

**Mission :** mettre en conformité mes deux ERP OHADA (Commercial et Transport) sur deux décisions définitives : (1) comptes généraux de l'entreprise sur **exactement 7 chiffres**, zéros à droite et conversion contrôlée des anciens plans ; (2) deux modules visibles sur l'accueil **Comptabilité générale** et **Comptabilité analytique**, mais une seule comptabilité, la seconde utilisant les écritures validées de la première. Commercial : analytique par sections ; Transport : analyses principales par véhicules et propriétaires, résultat du véhicule distinct de la dette au propriétaire.

Le Skill contient un `PATCH_CODE_COMMERCE.patch` basé sur deux ZIP précis. **Commence par comparer** le patch au code actuel et **ne l'applique que s'il est compatible** ; adapte sans écraser les travaux plus récents. Conserve les droits d'accès, les données et les soldes. Ne fais **aucune conversion de base ni déploiement en production** sans sauvegarde, simulation, vérification des collisions et mon autorisation explicite.

À la fin, indique les fichiers modifiés, les tests réellement exécutés, les éventuels échecs et les actions encore à effectuer pour les ERP Commercial et Transport séparément. Ne prétends pas que l'application est testée si elle ne l'est pas.
