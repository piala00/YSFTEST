# Registre des anomalies et limites — sans réaudit générique

| ID | Fait / source | État | Critère de clôture |
|---|---|---|---|
| ANO-H-001 | Refus identité éditeur absente, #1 commentaire6536186700 | Correction de chaîne de compilation dans #23 ; vraie personnalisation non acquise | Identité autorisée intégrée, licence réelle vérifiée et recette PC cible, sans nouvelle paire |
| ANO-H-002 | Réinstallation sans nouvelle autorisation, #1 commentaire6536201349 | Correctif .erpinst #25 en revue ; refus à neuf et après retrait vérifiés sous Windows au SHA dea6c916 | Recette acquise sur données fictives ; intégration et acceptation du propriétaire distinctes |
| ANO-H-003 | Résidus Program Files/ProgramData, même source | Nettoyage ciblé #25 vérifié sous Windows au SHA dea6c916 : sauvegarde relue, dossiers programme/données absents dans les deux recettes, autre édition et parent préservés. Verrou SQLite, WAL/SHM, lecture seule, état du planificateur et attente Inno corrigés | Les fichiers inconnus restent conservés et signalés ; aucune garantie universelle d'absence de résidus ni recette PC propriétaire déduite |
| ANO-D-001 | Validation/clôture sur objets périmés et publications non atomiques, audit #22 | Correctif testé SQLite/SQL ; PR non fusionnée | Conserver preuves/concurrence et revue ; ne pas compter 12 assertions comme 12 anomalies |
| ANO-D-002 | Actions comptables échappant au profil lecture, #22 | Correctif testé, PR non fusionnée | Droits des routes et refus GET/403 conservés dans la recette |
| ANO-G-001 | 250 départs testés à remplissage réduit, #20 | Limite connue, pas mesure d’un mois complet | Benchmark complet mesuré, sans extrapolation du petit essai |
| ANO-F-001 | Nouveaux faits d’incidents/garage/décomptes pas tous échangés, transmission #20 | Écart à traiter | Aller-retour siège/agences, doubles lots, désordre et reprise éprouvés |
| ANO-Q-001 | Recettes Windows10/11, deux services co-installés et PC propriétaire non acquises | Ouvert | Nommer OS/conditions réellement testés ; ne pas extrapoler un runner WindowsServer |

TR-01 annoncé corrigé au commit7e6f935 et déjà vérifié dans les travaux antérieurs : réutiliser ce résultat. Aucune nouvelle anomalie n’est déduite d’une simple déclaration. Les éléments de cette liste ne sont pas tous des bugs : les limites et couvertures manquantes restent explicitement distinguées.
