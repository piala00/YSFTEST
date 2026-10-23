# Mettre l'ERP en ligne sur PythonAnywhere (gratuit)

PythonAnywhere héberge gratuitement un site Python, sans carte bancaire. Contrairement à l'offre gratuite de
Render, **la base de données est conservée** : ce que vous saisissez reste enregistré d'une mise à jour à l'autre.
L'adresse sera `https://VOTRE-NOM.pythonanywhere.com`.

## Installation (une seule fois, environ 10 minutes)

1. **Créer le compte** sur https://www.pythonanywhere.com › *Pricing & signup* › *Create a Beginner account*
   (gratuit). Le nom d'utilisateur choisi devient l'adresse du site.
2. **Créer l'application web** : onglet **Web** › *Add a new web app* › *Next* › **Manual configuration**
   (pas « Django ») › **Python 3.13** (ou 3.12) › *Next*.
3. **Installer l'ERP** : onglet **Consoles** › **Bash**, puis coller ces deux lignes (remplacez `MOT_DE_PASSE`
   par le mot de passe que vous voulez pour le compte `admin`) :

       git clone -b ccr-5592a371-fusjt2 https://github.com/piala00/YSFTEST.git ~/erp
       bash ~/erp/deploy/pythonanywhere_installer.sh MOT_DE_PASSE --demo

   `--demo` ajoute la société de démonstration (clients, articles, factures fictifs). Sans `--demo`, la société
   démarre vide. L'installation prend quelques minutes.
4. **Relier l'environnement** : onglet **Web**, rubrique *Virtualenv* › saisir `/home/VOTRE-NOM/.virtualenvs/erp`
   › valider. Puis cliquer sur le bouton vert **Reload**.
5. Ouvrir `https://VOTRE-NOM.pythonanywhere.com` et se connecter avec `admin` et votre mot de passe.

## Mettre à jour après mes modifications

Chaque fois que je pousse une nouvelle version sur GitHub : onglet **Consoles** › **Bash**, puis :

    bash ~/erp/deploy/pythonanywhere_mettre_a_jour.sh

Le script récupère la nouvelle version, met la base à jour (vos données restent) et recharge le site. Une copie de
la base est gardée avant chaque mise à jour (`db.sqlite3.avant-mise-a-jour`).

## Ce qu'il faut savoir sur l'offre gratuite

À revérifier sur la page des tarifs de PythonAnywhere, qui peut changer :
- un seul site, toujours éveillé (pas de mise en veille comme sur Render) ;
- tous les **3 mois**, cliquer sur **Run until 3 months from today** dans l'onglet Web, sinon le site est arrêté ;
- espace disque et temps de calcul limités : suffisants pour tester et concevoir, pas pour une grosse société ;
- le site ne peut pas appeler n'importe quel site Internet (sans effet pour l'ERP aujourd'hui).

Faites des sauvegardes depuis l'ERP (**Fichier › Sauvegarde et restauration**). Si l'adresse ne s'ouvre pas chez
vous, essayez en données mobiles : certains réseaux bloquent des hébergeurs.
