# Installer l'ERP OHADA sur PythonAnywhere — du début à la fin

Durée : environ 15 minutes. Coût : gratuit, sans carte bancaire.
Résultat : votre ERP en ligne à l'adresse `https://VOTRE-NOM.pythonanywhere.com`, avec vos données conservées.

Ce qu'il faut : un ordinateur (ou une tablette) avec Internet et une adresse e-mail.
Vous n'avez rien à télécharger : les scripts de ce dossier sont récupérés automatiquement depuis GitHub (ils sont joints ici seulement pour information).

---------------------------------------------------------------------------------------------------

## Étape 1 — Créer le compte PythonAnywhere

1. Ouvrir **https://www.pythonanywhere.com**
2. Cliquer sur **Pricing & signup** (en haut à droite).
3. Cliquer sur **Create a Beginner account** (l'offre gratuite).
4. Remplir :
   - **Username** : votre nom d'utilisateur. ATTENTION : il devient l'adresse du site (exemple : `gtcerp` donnera `https://gtcerp.pythonanywhere.com`). Lettres et chiffres seulement.
   - **Email** et **Password** (mot de passe du compte PythonAnywhere, à ne pas confondre avec celui de l'ERP).
   - Cocher l'acceptation des conditions, puis **Register**.
5. Confirmer l'adresse e-mail en cliquant sur le lien reçu.

Vous arrivez sur le **Dashboard** (tableau de bord) de PythonAnywhere.

---------------------------------------------------------------------------------------------------

## Étape 2 — Créer l'application web (vide)

1. En haut à droite, cliquer sur l'onglet **Web**.
2. Cliquer sur **Add a new web app**.
3. Écran « Your web app's domain name » : cliquer sur **Next**.
4. Écran « Select a Python Web framework » : choisir **Manual configuration**
   (NE PAS choisir « Django »).
5. Écran « Select a Python version » : choisir **Python 3.13** (si absent : **Python 3.12**).
6. Écran suivant : cliquer sur **Next**.

L'application est créée (elle affiche pour l'instant une page « Hello world »). Laissez cet onglet ouvert.

---------------------------------------------------------------------------------------------------

## Étape 3 — Installer l'ERP (console Bash)

1. Cliquer sur l'onglet **Consoles** (en haut).
2. Dans « Start a new console », cliquer sur **Bash**. Une fenêtre noire s'ouvre avec une invite `$`.
3. Copier la ligne ci-dessous, la coller dans la console (clic droit › Coller, ou Ctrl+Maj+V), puis **Entrée** :

       git clone -b ccr-5592a371-fusjt2 https://github.com/piala00/YSFTEST.git ~/erp

   Attendre la fin (quelques secondes, l'invite `$` revient).
4. Choisir le **mot de passe de l'ERP** (compte `admin`) : au moins 8 caractères, sans espace.
   Remplacer `MOT_DE_PASSE` ci-dessous par ce mot de passe, coller la ligne, puis **Entrée** :

       bash ~/erp/deploy/pythonanywhere_installer.sh MOT_DE_PASSE --demo

   - `--demo` crée une société de démonstration (clients, articles, factures FICTIFS) pour découvrir le logiciel.
   - Pour démarrer avec une société **vide**, enlever `--demo` à la fin de la ligne.
5. Patienter **3 à 5 minutes**. Le script affiche ses étapes de 1/5 à 5/5, puis :

       Terminé. Dans l'onglet Web, indiquez Virtualenv : /home/VOTRE-NOM/.virtualenvs/erp, puis cliquez sur Reload.

   Notez ce chemin.

---------------------------------------------------------------------------------------------------

## Étape 4 — Relier et démarrer le site

1. Revenir dans l'onglet **Web**.
2. Descendre jusqu'à la rubrique **Virtualenv**.
3. Cliquer sur **Enter path to a virtualenv, if desired**, saisir :

       /home/VOTRE-NOM/.virtualenvs/erp

   (remplacer VOTRE-NOM par votre nom d'utilisateur), puis cliquer sur la coche ✓ pour valider.
4. Remonter en haut de la page et cliquer sur le gros bouton vert **Reload VOTRE-NOM.pythonanywhere.com**.

---------------------------------------------------------------------------------------------------

## Étape 5 — Se connecter à l'ERP

1. Ouvrir **https://VOTRE-NOM.pythonanywhere.com**
2. Utilisateur : **admin** — Mot de passe : celui choisi à l'étape 3.
3. Le portail affiche les trois logiciels : **Gestion commerciale**, **Comptabilité OHADA**, **Reporting**.

Première chose à faire dans la Gestion commerciale : **Fichier › Paramètres société › Identification**
pour saisir le nom de votre société, puis créer vos utilisateurs dans **Fichier › Autorisations d'accès**.

---------------------------------------------------------------------------------------------------

## Mettre à jour après une nouvelle version

Quand une nouvelle version est disponible :
1. Onglet **Consoles** › **Bash** (ou reprendre la console déjà ouverte).
2. Coller, puis **Entrée** :

       bash ~/erp/deploy/pythonanywhere_mettre_a_jour.sh

3. Attendre « Mise à jour terminée ». Le site est rechargé automatiquement. Vos données sont conservées
   (une copie de la base est faite juste avant : `db.sqlite3.avant-mise-a-jour`).

---------------------------------------------------------------------------------------------------

## Entretien

- **Tous les 3 mois** : onglet **Web** › cliquer sur **Run until 3 months from today**.
  Sans ce clic, PythonAnywhere arrête le site (vos données ne sont pas effacées pour autant).
- **Sauvegardes** : dans l'ERP, **Fichier › Sauvegarde et restauration** › télécharger une sauvegarde,
  et la garder sur votre ordinateur.
- **Changer le mot de passe admin** : console Bash, puis (remplacer NOUVEAU) :

      cd ~/erp && ~/.virtualenvs/erp/bin/python manage.py init_erp --admin NOUVEAU

---------------------------------------------------------------------------------------------------

## En cas de problème

| Ce que vous voyez | Que faire |
|---|---|
| La page PythonAnywhere ou le site ne s'ouvre pas du tout | Essayer en **données mobiles** : certains réseaux bloquent des hébergeurs. |
| « Python 3.12 ou 3.13 introuvable » | Onglet **Account** › **System image** › choisir l'image la plus récente, puis relancer l'étape 3.4. |
| « Fichier /var/www/... absent » | L'étape 2 n'a pas été faite : la faire, puis relancer la commande de l'étape 3.4. |
| Le site affiche « Hello world » ou « Something went wrong » | Vérifier le chemin Virtualenv (étape 4), puis **Reload**. Sinon, onglet Web › **Error log** : envoyer une capture des dernières lignes. |
| « destination path '~/erp' already exists » | L'ERP est déjà téléchargé : passer directement à l'étape 3.4. |
| « Bad Request (400) » | Vous utilisez une autre adresse que `VOTRE-NOM.pythonanywhere.com` : utiliser exactement celle-ci. |
| Mot de passe admin refusé | Le changer (voir « Entretien »). |

Pour toute autre erreur : faire une capture de la console ou de l'**Error log** et l'envoyer.

---------------------------------------------------------------------------------------------------

## Limites de l'offre gratuite (à revérifier sur pythonanywhere.com, elles peuvent changer)

- un seul site par compte ;
- espace disque et temps de calcul limités : suffisants pour concevoir et tester ;
- pour une utilisation réelle par plusieurs employés, prévoir plus tard une offre payante ou un autre hébergement.
