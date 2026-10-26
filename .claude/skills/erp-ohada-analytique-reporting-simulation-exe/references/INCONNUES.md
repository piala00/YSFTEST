# Inconnues et contraintes — ne pas inventer

1. L'ERP Transport est-il intégré au dépôt Commercial ou existe-t-il un autre dépôt plus récent ? Auditer avant d'agir.
2. Version du dépôt courant vs archive fournie le 26/10/2026 : les chemins et modèles peuvent avoir changé.
3. Quels sont les plans commerciaux réellement retenus par chaque entreprise ? Les axes Commerce du Skill sont des **propositions configurables**, pas une validation utilisateur définitive.
4. Existence de règles d'allocation indépendantes pour tous les plans : l'archive inspectée ne prouve pas un schéma multi-axes complet.
5. Couverture OHADA/SYSCOHADA officielle de chaque état, formule fiscale camerounaise et DSF : à vérifier sur sources légales avant validation normative.
6. Serveur API utilisé par la version Windows : Render, réseau local, serveur Windows, offline ? Définir modes de packaging et d'authentification ; ne pas deviner l'infrastructure de production.
7. Disponibilité Windows pour compilation et tests. Sur une machine Linux sans Windows, on peut écrire les scripts, **pas** certifier un `.exe` Windows fonctionnel.
8. Politiques opérationnelles : volume des données, durée de simulation, période et granularité, déploiement des rapports ; privilégier valeurs raisonnables mais paramétrables.
9. Les dix plans Transport doivent être navigables même si certaines mesures spécifiques n'ont pas encore de données : afficher clairement non affecté/inconnu, ne pas générer de chiffres fictifs hors simulation.
10. Aucune automatisation d'un déploiement Render ou migration base live sans accès autorisé, sauvegarde et accord explicite.
