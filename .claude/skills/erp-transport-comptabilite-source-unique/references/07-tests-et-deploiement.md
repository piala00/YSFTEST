# 07 — Tests de réception, plan de développement et audit

## Scénarios non négociables

1. Billet vendu : avant `GL_POSTED`, montant absent des états analytiques définitifs ; après posting, exactement un produit rattaché au voyage/véhicule.
2. Vente reportée/remboursée : documents/GL corrigés selon règles comptables, impact analytique net retracé, pas de suppression d'audit.
3. Charge garage 100 000 GL : ventilation BUS-A 70 000 et BUS-B 30 000 ; total GL inchangé à 100 000 ; aucun GL supplémentaire.
4. Charge 100 000 avec 80 000 seulement affectés : 20 000 “non ventilé” et écart explicite ; rapport non étiqueté comme pleinement rapproché.
5. Tentative de créer allocation avec `gl_line_id` inexistant, en brouillard ou appartenant à une autre société → refus.
6. Contrepassation GL datée : projection d'annulation visible, recalcul de tous les états concernés ; historique conservé.
7. Achat de pièces en stock : ne pas présenter achat comme charge de BUS-A ; sortie stock et écritures correspondantes déclenchent coût analytique.
8. Paie mensualisée : salaire comptabilisé en GL une seule fois, réparti entre véhicules selon feuille de temps ; paiement bancaire ne double pas la charge.
9. Transfert interne caisse courrier → caisse centrale : trésorerie ajustée sans revenu analytique additionnel.
10. Propriétaire A cède BUS-A au propriétaire B : rapports A/B respectent dates d'effet et contrats historiques.
11. Droits du partenaire calculés mais écritures de dette non postées : estimation seulement, pas solde dû “validé” fictif.
12. Coupure et reprise de synchronisation : tout événement GL traité une seule fois ; analytique idem ; siège marqué provisoire tant qu'agence incomplète.
13. Comparatif de deux périodes : mêmes règles de reconnaissance et filtres ; KPI non monétaires clairement séparés.
14. Sécurité : guichetier, contrôleur bagages et mécanicien incapables d'insérer directement des lignes analytiques monétaires ; contrôle de rôles et audit.
15. Restauration depuis sauvegarde et replay d'outbox ne produisent aucun doublon de comptabilisation ni de projection.

## Stratégie migration

1. Faire inventaire du code et des écritures existantes, exécuter diagnostics en lecture seule ; sauvegarder base et schéma.
2. Lister les lignes analytiques historiques avec source GL absente, non validée ou ambiguë ; ne pas les supprimer automatiquement.
3. Exposer une file d'écarts et un rapprochement assisté vers de véritables écritures générales existantes ; tout ajustement financier requis doit passer par les validations comptables normales.
4. Ajouter les contraintes de références et migrations graduellement après nettoyage contrôlé ; maintenir compatibilité API/interface.
5. Sécuriser d'abord le moteur d'écriture GL, puis la projection analytique, puis les états véhicule/propriétaire et le reporting.
6. Tester sur jeux fictifs, puis sur copie anonymisée si disponible ; versionner barèmes et règles.
7. Restituer un tableau "déjà existant / adapté / ajouté / non vérifié", le journal des modifications et résultats de tests réellement exécutés.

**N'invente jamais de résultats de tests, migrations passées ou accès au dépôt.**
