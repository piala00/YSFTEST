# 09 — Audit ciblé de l'archive source consultée (constats limités à cette version)

Dossier inspecté : `ERP_OHADA_Transport_Code_Source_MAJ_7_Chiffres_Deux_Modules.zip`.

1. `apps/transport/management/commands/simulation.py` : simule un mois, prépare une société fictive huit gares, soixante cars voyageurs et cinq camions, trois cents salariés, opérations et clôture en fin de mois. Il est conçu pour une SQLite isolée. Il ne peut pas être lancé une seconde fois sur la même base de simulation contenant des départs.
2. `apps/core/management/commands/simulateur.py` : autre outil, génère des écrans HTML autonomes de simulation **à partir d'une base déjà remplie**. Ne pas confondre avec la simulation comptable des mois.
3. `apps/transport/analytique.py` : états spécialisés véhicule/propriétaire à partir des lignes GL validées ; ne couvre pas actuellement tous les dix plans analytiques avec une ventilation multidimensionnelle.
4. `apps/comptabilite/models.py` : `LigneEcriture.section` unique champ FK vers `SectionAnalytique`, insuffisant pour les dix plans simultanés. Nécessite un vrai modèle de ventilation multi-axes avec migration non destructive et tests.
5. `apps/reporting/services.py` : reporting commerciaux/financiers déjà partiellement disponible ; ne pas réécrire à l'aveugle et ne pas fusionner métriques commerciales et comptables sans définitions.
6. `desktop/COMPILER.bat` : cinq exécutables client, pas le serveur Django ; `packaging/windows/` proposé ajoute le volet serveur.
7. `apps/core/management/commands/init_erp.py` : longueur par défaut des comptes nouveaux dossiers = 7 ; conversion existant via `longueur_comptes` sous contrôle. Ne pas changer directement des numéros GL en base.
8. Il n'a pas été possible, dans le contexte de préparation de ce Skill, de lancer les tests fonctionnels Django ni de compiler des `.exe` Windows. Les scripts ajoutés sont donc des propositions à valider avec Claude Code sur l'environnement réel.

### Points à traiter en priorité
**P0** : source GL unique, modèle multi-axes, rapprochements, contrôle DB simulations.
**P1** : catalogue d'états complet, interface périodes, comparateurs, reporting unifié.
**P2** : simulation de 3/6/12/24 mois, scénarios d'anomalie, qualification Windows.
