# Benchmark des deux logiciels — Transport vs Commerce (28/10/2026)

But : comparer ce que couvrent réellement aujourd'hui l'édition **Commerce** (référence : Sage 100 Gestion
commerciale + Comptabilité V12) et l'édition **Transport** (référence : ERP de transport interurbain / messagerie),
et dire, pour chacune, ce qu'il reste d'utile à développer, par ordre de priorité.

Méthode : inventaire automatique de **toutes** les commandes de menu des deux éditions (parcours de
`apps/core/navigation.py`), en comptant celles qui mènent à une page réelle. Les deux éditions partagent la même
charpente de menus (calquée sur Sage), mais chacune n'affiche que ses métiers.

## 1. Couverture actuelle (commandes de menu actives / total)

### Commerce
| Module | Actives / total | % |
|---|---|---|
| Gestion commerciale | 106 / 256 | 41 % |
| Comptabilité générale | 76 / 181 | 41 % |
| Comptabilité analytique | 23 / 66 | 34 % |
| Reporting | 32 / 75 | 42 % |
| Personnel et paie | 22 / 63 | 34 % |

### Transport
| Module | Actives / total | % |
|---|---|---|
| Reporting | 54 / 97 | 55 % |
| Comptabilité analytique | 49 / 92 | 53 % |
| Direction / exploitation | 43 / 88 | 48 % |
| Comptabilité générale | 77 / 182 | 42 % |
| Garage | 32 / 76 | 42 % |
| Billetterie | 26 / 68 | 38 % |
| Colis et fret | 26 / 69 | 37 % |
| Personnel et paie | 22 / 63 | 34 % |

**Lecture importante.** Ces pourcentages ne veulent pas dire « à moitié fini ». La charpente des menus reproduit
Sage V12 au complet : une grande partie des commandes « manquantes » sont des **entrées de menu standard** (Fichier,
Édition, Fenêtre : Nouveau, Ouvrir, Copier/Coller, Rechercher, Préférences…) et des écrans Sage que nous n'avons pas
voulu reproduire tels quels. Il faut donc séparer :
- le **décor de menu** (commun aux deux éditions, peu de valeur métier) ;
- les **vrais manques fonctionnels**, très différents entre Transport et Commerce.

## 2. Transport — presque complet sur son métier

Dans les modules opérationnels du Transport (**exploitation, billetterie, colis, garage, reporting**), les commandes
non actives sont **uniquement le décor de menu** (Fichier/Édition/Fenêtre : Imprimer, Import, Export, Annuler,
Rechercher, Préférences…). Les onglets métier (Structure, Traitement, État) sont, eux, câblés.

Autrement dit : **le Transport est l'édition la plus mûre.** Ce qui reste à faire y est limité :
- **P1 — États de reporting encore absents** (confié à Codex, lot 03) : remplissage par départ/heure, retards et
  incidents de voyage, recettes par chauffeur/convoyeur, coût au km par véhicule, colis non livrés depuis N jours.
  Règle : montants uniquement depuis les écritures validées.
- **P2 — Impression** des billets, manifestes de départ, bordereaux de colis, rapport journalier d'agence (le
  « Imprimer… » du décor, mais appliqué aux pièces du transport).
- **P2 — Import/Export CSV** des listes (véhicules, lignes, tarifs, partenaires).

## 3. Commerce — vrais manques par rapport à Sage Gescom

À l'inverse du Transport, l'édition Commerce a des **manques fonctionnels réels** par rapport à un logiciel de
gestion commerciale complet. Classés par priorité métier :

### P1 — utiles à beaucoup de commerces
- **Barèmes et conditions de vente** : rabais/remises/ristournes (RRR) clients et fournisseurs, soldes et promotions,
  commissions des représentants. (Structure › Barèmes — aujourd'hui inactif.)
- **Cadenciers** clients, fournisseurs et de livraison (État) : suivi des commandes récurrentes et des livraisons.
- **Rapprochement bancaire** et saisie des opérations bancaires (Comptabilité › Traitement).
- **Reports à-nouveaux** et **clôture de période/exercice** côté Commerce (le Transport a déjà ses contrôles de
  clôture ; à étendre au commerce).
- **Nomenclatures** d'articles (articles composés) si le client vend des ensembles.

### P2 — selon le type de client
- **Fabrication** (préparation, ordre et bon de fabrication, contremarque) : seulement si le client produit.
- **Bon à payer** et circuit de validation des factures fournisseurs.
- **Gestion des affaires** (codes affaires) et **abonnements** (facturation récurrente).
- **Traçabilité série / lot** et contrôle qualité : pour les activités réglementées.
- **Statistiques collaborateurs / ressources**, étiquettes articles et colisage.

### P3 — fiscal, à valider par l'expert-comptable (aucun taux inventé)
- **Paramètres fiscaux**, taux de taxes (TVA débit / encaissement, TP, surtaxe) : écrans présents mais non remplis,
  **à renseigner avec un expert-comptable** — nous n'inscrivons aucun taux de notre propre initiative (règle AGENTS.md).
- **Déclaration statistique et fiscale (DSF)**, rapport des délais de paiement : à cadrer avec les obligations
  camerounaises en vigueur, sources officielles à l'appui.

## 4. Commun aux deux éditions (décor de menu)

Présent partout, faible valeur métier, à traiter d'un bloc (confié à Codex, lot 05) :
- **Fichier** : Nouveau, Ouvrir, Fermer, Imprimer…, Import, Export, Quitter → implémenter (Export/Import CSV des
  listes), rediriger vers l'écran existant, ou marquer explicitement « hors périmètre ».
- **Édition** : Annuler, Couper/Copier/Coller, Rechercher, Atteindre, Calculette → pour une application web, la
  plupart sont assurées par le navigateur ; à retirer du menu ou à marquer hors périmètre pour ne pas tromper.
- **Fenêtre** : Réorganiser, Personnaliser, Préférences, Mode assistant → à réduire à ce qui a un sens dans le
  navigateur (préférences d'affichage), le reste marqué hors périmètre.

## 5. Ce que je recommande, dans l'ordre

1. **Transport (le plus mûr) → finir le reporting** (lot 03, Codex) : ce sont les états que le gérant réclame au
   quotidien. Impact immédiat, faible risque.
2. **Commerce → combler les P1** (barèmes/RRR, cadenciers, rapprochement bancaire, reports à-nouveaux) : c'est là
   que le Commerce est le plus en retard sur un vrai logiciel de gestion commerciale.
3. **Décor de menu** (lot 05, Codex) : nettoyer les deux éditions pour qu'aucune commande affichée ne soit morte.
4. **Fiscal (P3)** : seulement après validation d'un expert-comptable, sources officielles à l'appui.

Chaque évolution suit les règles du dépôt : montants uniquement depuis les écritures validées, migrations additives,
aucun taux inventé, tests réellement exécutés, et un graphique sous chaque nouvel état du reporting.

---
*Benchmark établi à partir de l'inventaire réel des menus au commit de référence ; les priorités P1/P2/P3 sont des
propositions, à arbitrer par le propriétaire.*
