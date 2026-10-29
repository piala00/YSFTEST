# Note méthodologique — préremplissage de la matrice globale

Commit de génération : `fe26f3d984902c5ec594550251c0da5bceadf78f`.

453 lignes ont été extraites **par reconnaissance textuelle conservatrice** des appels `E("code", "libellé", ...)` de `apps/core/navigation.py`, sur la branche de travail. Ventilation provisoire : socle 109, commercial 196, comptabilité 76, analytique 17, reporting 26, transport 29.

**Limites critiques :**
- Cette extraction ne couvre **pas** tous les boutons HTML, les actions JavaScript, les menus dynamiques, les contrôles générés en exécution, ni tous les logiciels métiers. Ce n'est ni le nombre global de boutons ni un test de conformité.
- L'association à un module repose sur les sections textuelles du fichier ; les fonctions communes sont classées « socle ». Les modules imbriqués et les menus partagés exigent une réconciliation par le code Python exécuté.
- Les routes ne sont relevées que lorsqu'un troisième argument littéral est sur la même ligne ; les arguments nommés, calculés et répartis sur plusieurs lignes peuvent manquer.
- Le statut `NON_IMPLEMENTE` signifie **uniquement « aucune cible détectée par l'extracteur »**, pas une preuve de défaut fonctionnel. Les sous-menus multilignes peuvent être mal classés. Il faut corriger ces faux positifs lors de la validation manuelle.
- Les numéros de ligne renvoient à la version analysée et peuvent changer. Aucune preuve Sage V12, aucun test HTTP, navigateur, permission, stock ou comptabilité n'a été exécuté.
- Les doublons de contexte sont possibles. La matrice ne doit pas être utilisée pour annoncer un taux de conformité, ni pour créer automatiquement 453 tickets.

**Suite exigée :** un extracteur AST Python vérifié sur le dépôt complet, identification des vrais modules, résolution des sous-menus et routes, inventaire HTML/JS, puis parcours dynamique multi-rôles. Chaque ligne doit recevoir un statut final uniquement avec preuve. La référence Sage doit être officielle et contextualisée (produit, édition, build) ou rester `A_VERIFIER_SAGE`.
