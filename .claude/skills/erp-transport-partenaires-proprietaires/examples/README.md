# Jeu de démonstration distinct — propriétaire fixe + variable
Ces fichiers sont volontairement indépendants du jeu « 8 agences, 300 employés » inclus dans le Skill principal. **Ne pas fusionner directement leurs écritures** : le simulateur global doit d'abord être modifié pour créer de nouvelles écritures générales, contreparties, imputations et rapprochements.

Aucun compte `*-DEMO` n'est un numéro SYSCOHADA à utiliser en production. L'exemple suppose une compagnie agissant pour son compte, des montants hors taxes et un contrat juridiquement valable, sans simulation fiscale.

Résultat attendu : recettes 1 000 000 ; coûts directs 400 000 ; fixe 150 000 ; variable 180 000 ; résultat après droits 270 000 ; rémunération propriétaire due 330 000 ; paiements 250 000 ; reste dû 80 000. Le paiement fixe, pas plus que le retrait variable, ne constitue une deuxième charge.

Exécuter `python .claude/skills/erp-transport-partenaires-proprietaires/scripts/validate_exemple.py` depuis la racine du projet.
