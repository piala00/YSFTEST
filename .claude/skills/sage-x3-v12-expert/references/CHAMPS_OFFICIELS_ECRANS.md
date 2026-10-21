# Sage X3 V12 — champs du dictionnaire d'écrans (officiel)

Le **dictionnaire des écrans `GESAMK`** est un point d'entrée d'inventaire, **pas une liste de toutes les fiches X3**. Sage documente :

| Zone | Code X3 | Fonction |
|---|---|---|
| Code écran | `CODMSK` | Identifiant écran |
| Abréviation écran | `ABRMSK` | Préfixe de classe écran |
| Intitulé | `ZINTMSK` | Désignation |
| Champ de l'écran | `CODZON` | Code technique du champ |
| Numéro de bloc | `NUMBLOC` | Bloc de présentation |
| Position | `NOZONE` | Ordre de position |
| Code activité | `CODACT` | Activation conditionnelle |
| Obligatoire | `OBLIG` | Champ requis selon dictionnaire |
| Action | `ACTION` | Traitement associé à un événement de champ |

Les fenêtres `GESAWI` comprennent liste d'écrans, menus/boutons/actions/paramètres. Le code fenêtre est `WIN`; le type du bouton/menu est `TYPBOUT`, le code `CODBOUT`, le texte `ZTXTBOUT`, l'action `ACTBOUT` ; la fenêtre peut avoir des variantes par transaction.

## Cycle de capture recommandé
A. Export système des métadonnées tables à lecture seule ; B. requêtes via dictionnaire X3 confirmé ; C. observation UI des fonctions activées, avec droits de rôle ; D. test métier en dossier fictif ; E. catalogue versionné. Les conditions de codes activités peuvent supprimer de vrais champs malgré présence dans le dictionnaire.

Sources :
- https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/GESAMK.htm
- https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/GESAWI.htm
