# Interface / périodes / consultation rapide

## Navigation souhaitée

Accueil → Comptabilité analytique → Plans analytiques → choix du plan (10 cartes/table) → sections du plan → choix de l'état (liste) → barres de filtre → résultats → ligne cliquable → écriture générale → pièce justificative.

Le module affiche des raccourcis « Véhicules » et « Propriétaires » comme favoris, MAIS le menu « Tous les plans » montre Agences/Gares, Services, Activités, Gammes, Lignes, Voyages, Contrats et Canaux également.

## Périodes réutilisables dans TOUS les états

- Boutons : **Aujourd'hui**, **Hier**, **Cette semaine**, **Ce mois**, **Mois précédent**, **Ce trimestre**, **Cette année**, **Exercice**, **Personnalisée**.
- Deux champs `Du` / `Au` (sélecteurs de dates) et sélection directe **mois + année** (janvier à décembre de toute année), indépendamment des paramètres d'une autre page.
- Flèches `← période précédente` / `période suivante →` et `Comparer à ...` (période précédente de même durée, même période année précédente, dates libres).
- Tous filtres conservés lors des changements d'état ou des passages au détail via paramètres d'URL ou session (ne pas perdre la période).
- Filtrage combiné : société, agence d'exploitation, gare, gamme, véhicule, propriétaire avec contrat à date, ligne, activité, service, canal, statut validé/provisoire.
- La valeur affichée doit indiquer sa **date comptable**; option documentée pour date métier/départ et encaissement. Ne jamais regrouper une même transaction deux fois.
- Une période **Du > Au** renvoie erreur de validation explicite. Exercice fermé/non synchronisé affiché.

## États et consultation

Toute page d'état : bandeau `Plan | Section | État | Période | Société | Statut données` puis tableau **simple** avec total au pied, recherche, tri, pagination, impression, CSV, PDF si implémenté, Excel si implémenté.

Raccourcis de consultation :
- cliquer véhicule → compte exploitation → rubrique carburant → lignes justificatives → écriture comptable source → facture/bon de carburant;
- cliquer agence → résultat de l'agence → gare/activité/vehicule → lignes sources;
- cliquer propriétaire → véhicules sous contrat à période → résultats → relevé financier (fixe/variable/avances/retraits) → écritures GL.

Par défaut, vue **mois courant**, à moins que la logique du dossier choisisse une période différente expressément; ne pas forcer l'exercice entier sur chaque écran. Les états historiques ne doivent pas être bloqués par le simple paramètre « exercice courant ».

Les rapports journaliers de caisses restent à part avec des tableaux lisibles, sans graphiques imposés.

## Compatibilité client bureau/web

Ajouter mêmes routes et droits de navigation dans le portail et dans `desktop/analytique.py` ou client bureau correspondant. Tester comportement sur Windows et mobile/tablette quand disponible.
