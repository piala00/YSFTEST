# Mots de passe au quotidien : un seul login par session

Demande du propriétaire : « il ne faut pas qu'à chaque page il faut saisir un mot de passe… pas
que la saisie des mots de passe soit nombreuse. » Objectif : **un seul login par session** ;
ré-authentification **uniquement** pour des opérations sensibles rares.

## Constat (code existant)

- **Aucune page du logiciel ne redemande le mot de passe** en usage courant : une fois connecté,
  la navigation (billetterie, caisses, comptabilité, reporting…) ne repasse jamais par un mot de
  passe. Les écrans sensibles (Licence, Sauvegarde/Restauration, gestion des utilisateurs) sont
  **réservés à l'administrateur** par les droits, pas par une re-saisie de mot de passe.
- Le programme compilé ouvre l'interface dans un **profil navigateur dédié stable**
  (`…/ERP-OHADA-Navigateur`), donc le cookie de session **persiste** d'un lancement à l'autre.

## Amélioration livrée (fenêtre glissante)

Avant, la session avait une échéance **fixe** depuis le login (2 semaines par défaut) : un poste
laissé ouvert pouvait, au bout de ce délai, exiger une reconnexion **en plein travail**.

Désormais (`erp/settings.py`) :
- `SESSION_SAVE_EVERY_REQUEST = True` → **fenêtre glissante** : chaque page consultée repousse
  l'échéance. Tant que l'utilisateur travaille, il **ne se reconnecte jamais**.
- `SESSION_EXPIRE_AT_BROWSER_CLOSE = False` → la fermeture du navigateur ne déconnecte pas.
- `SESSION_COOKIE_AGE` réglable par `ERP_SESSION_HEURES` (défaut **168 h = 1 semaine**
  d'inactivité avant expiration).

Résultat : **un seul mot de passe par session de travail**, conforme à la demande.

## Reste à décider par le propriétaire : ré-authentification des opérations sensibles

Aujourd'hui les opérations sensibles sont protégées par les **droits administrateur** (pas de
re-saisie). Si vous voulez une **re-demande de mot de passe** juste avant les actions rares et
irréversibles, je propose de la limiter à :

- **Restauration** d'une sauvegarde (écrase toutes les données) ;
- **Dépôt / changement de licence** ;
- **Clôturer l'exercice et ouvrir le suivant** ;
- **Repartir à zéro** (effacer la société du poste).

Mécanique envisagée : une seule confirmation par mot de passe valable quelques minutes
(« mode sensible »), jamais sur les écrans de travail courant. **À confirmer** avant implémentation,
pour ne pas ré-introduire la friction que vous voulez supprimer.
