# Résultat de la revue du 24 octobre 2026

La transmission de Claude contient une réalisation réelle, pas seulement une maquette. La suite locale fournie exécute bien 155 tests avec succès. Un scénario supplémentaire de livraison partielle confirme 10 commandés → 4 livrés/facturés → 6 restant à livrer, avec une seule sortie du stock.

Huit contrôles complémentaires ont été exécutés : sept révèlent des anomalies et un réussit. Les anomalies sont détaillées et reproductibles dans ANOMALIES.csv ; leur gravité est une appréciation de revue, pas une décision de mise en production.

Priorité : corriger l’exposition des quantités via API, les validations de saisie magasin, l’auteur de l’ancienne déclaration, les soldes datés du rapport, la distinction modes/journaux et l’indépendance du registre magasin. Le solde « fiche » actuel inclut les mouvements non pointés, même s’ils sont signalés comme tels : le contrôle n’est pas encore un registre entièrement indépendant.

Les conditionnements bénéficient de nouvelles preuves explicites V12.20 : structures article/conditionnement/tarif, correspondances documentaires d’onglets et formule de quantité de ligne dans les Objets Métiers. Les détails d’écrans observés, certains prix appliqués en contexte et les états imprimés restent à relever. Aucun manuel ancien n’est présenté comme une preuve V12.

La spécification d’échanges proposée préserve les serveurs locaux et prévoit une collecte centrale traçable. Elle n’est pas encore codée, ni testée entre deux serveurs. L’import central doit créer une projection de données d’origine ; il ne doit pas rejouer les validations métier locales et leurs effets de stock/comptabilité.

Le travail livré ici est une revue et un dossier pour la suite. Le code applicatif de l’archive n’a pas été corrigé ; la version distante et la branche GitHub annoncées n’ont pas été vérifiées. Les simulateurs ne prouvent pas la persistance des saisies.
