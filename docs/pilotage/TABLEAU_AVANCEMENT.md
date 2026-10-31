# Tableau d’avancement — 31 octobre 2026

| Chantier | Avancement exact | Preuve / limite |
|---|---|---|
| Socle historique #2–#7 | Fusion historique observée dans GitHub | Ces fusions n’ont pas été réalisées dans cette session |
| Licences 3.1 #21 | Code en PR brouillon, essais CI/Windows acquis dans leur périmètre | Run41130741908 : 523 tests SQL/SQLite ; Windows Server2025, pas essais Windows10/11 séparés |
| P0 comptable/architecture #22 | Code en PR ; essais locaux et SQL acquis, audit technique documenté | Run41144731640 : 536 tests SQL sans ignoré, dont concurrence ; pas certification comptable exhaustive |
| Activation #23 | Code en PR ; huit contrôles CI réussis | [Run41152023209](https://github.com/piala00/YSFTEST/actions/runs/41152023209) : SQLite544 OK180,051s(4 ignorés), SQL544 OK1165,497s(0 ignoré) ; deux vrais EXE, identité/base fictives, activation fichier et redémarrage |
| Installation/nettoyage #25 | SHA dea6c916 en PR : huit contrôles CI réussis ; SQLite 558 tests OK (136,024 s, 4 ignorés), SQL Server 2022 558 tests OK (860,836 s, aucun ignoré) | [Run41196187906](https://github.com/piala00/YSFTEST/actions/runs/41196187906). Windows Server 2025, identité et données fictives : deux éditions compilées, service, redémarrage, mise à jour, refus sans autorisation, réinstallation autorisée, sauvegarde relue et retrait des dossiers contrôlés. Émission .erpinst compilée et activation fichier/texte avec persistance vérifiées. Ni certification Windows 10/11 ni recette sur le PC du propriétaire. |
| Personnalisation et PC du propriétaire | BLOQUÉ / non vérifié | Identité publique réelle non fournie ; ne pas remplacer la paire, ne pas demander le privé |
| Documents commerciaux #27/#28 | Correctif en PR au SHA ae724335, huit contrôles CI réussis ; 574 SQLite OK (240,154 s, 6 ignorés), 574 SQL Server OK (897,843 s, aucun ignoré) | [Run41201383014](https://github.com/piala00/YSFTEST/actions/runs/41201383014) : deux nouvelles recettes concurrentes SQL exécutées, doubles validations/annulations empêchées, rollback/reprise cohérents. Deux éditions Windows Server 2025 compilées/démarrées et parcours installateur/activation réussis sur données fictives ; aucune recette native métier exhaustive ni acceptation propriétaire inférée. Réutilisation #22. |
| Registre directeur | Premier rapport de réconciliation, 55 entrées ERP, neuf détails ajoutés en conservant les46 ID initiaux ; 81 sources de transmission rapprochées | 55 demandes et26 propositions séparées ; demandes non vérifiées et contradictions tracées. Réconciliation exhaustive et acceptation propriétaire non closes. |
| SN/SMT, Reporting03, P004, Menus05, échanges, charge et simulateur | À poursuivre selon dépendances | Réutiliser rapports/matrices existants ; décisions et preuves spécifiques restent nécessaires |
| Intégration et production | En attente d’autorisation distincte | Aucune fusion ni déploiement effectué |

Le succès d’une suite cumulée ne prouve pas toute la recette fonctionnelle ni tous les cas Windows. Toute mise à jour de ce tableau doit citer le SHA testé, les ignorés et les limites ; pas de pourcentage inventé.
