# Sage X3 — modèle relationnel du dictionnaire UI (à vérifier localement)

Les sources officielles confirment :
- `AMSK [AMK]` dictionnaire écrans
- `AMSKZON [AMZ]` dictionnaire champs écran
- `AWINDOW [AWI]` dictionnaire fenêtres
- `AWINBOUT [AWT]` boutons et menus
- `AWINBRO [AWB]` browsers de fenêtre
- `AWINPAR [AWP]` paramètres fenêtre
- `ATABLE [ATB]` dictionnaire tables
- `ATABZON [ATZ]` dictionnaire champs SQL
- `ACTION [ACT]` actions
- `AOBJET [AOB]` objets
- `ACTIV [ACV]` codes activité

**Ne pas inventer les clés de jointure** : inspecter les métadonnées du dossier Sage X3 avant de construire les SELECT. Voir :
https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/PRQ_AFC_GESAWI.htm

Chaîne logique cible : fonction → objet → fenêtre → écran → bloc → champ → action → tableau SQL → droits/activité. Ces relations peuvent dépendre de la transaction de saisie et des développements spécifiques.
