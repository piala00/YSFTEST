# Conditionnements : réalisation proposée pour cet ERP

## Base de travail

Les sources S01/S02 prouvent des mécanismes V12.20 ; elles ne constituent pas une spécification exhaustive d’écran. Les propositions ci-dessous sont propres à l’ERP de l’utilisateur et doivent conserver ses besoins de gros/détail, y compris hors ligne. Ne pas reproduire automatiquement les limitations de gamme/conditionnement de Sage.

## Modèle minimal proposé

Conserver l’article avec une unité de référence stable. Ajouter présentations identifiées globalement : intitulé, unité dimensionnelle, quantité de référence par présentation positive, précision, référence/code-barres éventuels, statut actif et dates de validité. Les prix client/catégorie/présentation sont distincts du facteur physique.

Sur chaque ligne BC, BL, facture, retour et mouvement pertinent, figer présentation, quantité saisie, unité de référence, facteur appliqué, quantité de référence calculée, prix de la présentation et montant résultant. Ne pas utiliser un seul champ ambigu prix_unitaire pour représenter alternativement prix du litre et prix du carton sans unité explicite.

Quantité de référence = quantité saisie × facteur. Pour les prix : montant avant remises = quantité saisie × prix de la présentation, ou quantité de référence × prix de référence selon un mode explicite, jamais les deux. Conserver l’origine du tarif et les arrondis appliqués. Utiliser Decimal et contraintes de précision ; ne pas convertir en flottants JSON.

Exemple fictif : 1 carton=15 L, prix carton 18000 ; 2 cartons →30 L et 36000 avant remises/taxes. Prix détail 1300/L ; 0,5 L →650. Le prix carton n’est pas forcé à 15×1300. La contribution au coût et à la marge utilise la même unité de référence que la valorisation de stock.

## Vrac ou emballage identifié

Le vrac peut utiliser un article unique avec conversions. Des bouteilles scellées et bidons distincts peuvent nécessiter des références/variantes séparées ; le reconditionnement produit une consommation et une production explicites, avec pertes contrôlées. Ne pas convertir kg et litres sans règle propre au produit.

## Écrans et contrôles

Ajouter présentations et tarifs dans la fiche article en conservant l’existant ; proposer unités en saisie de pièce. Afficher quantité et prix avec leur unité. Le fichiste saisit dans l’unité du BL, sans attendu, puis le serveur compare avec facteur historique. Un changement de facteur actuel ne change pas une ancienne pièce ni un ancien pointage.

À la transformation partielle, conserver les quantités en unité de référence et le reliquat exact ; éviter un arrondi qui ferme une commande encore ouverte. Les retours utilisent la présentation et les facteurs de la pièce d’origine, sauf correction explicite. Pour les articles existants, une migration vers facteur 1 préserve les quantités historiques sans prétendre reconstituer d’anciens cartons inconnus.

## États et tests à prévoir

Présenter stock canonique en unité de référence et, à titre de lecture, équivalences en présentations. Ne pas additionner les équivalences. Pour une représentation carton + reste, définir la règle de décomposition et la gestion des fractions.

Tester : achat 2 cartons de 15 L ; vente d’un carton +3 L +2 portions de 0,5 L →11 L restants ; changement ultérieur de facteur sans impact historique ; facture partielle ; retour ; prix client différent ; contrôle de précision ; mode hors ligne ; pointage dans une autre unité autorisée ; import central conservant les facteurs d’origine. Ces tests sont proposés et n’ont pas été exécutés, car la fonction n’est pas livrée dans le ZIP examiné.
