# Autorisations — observations et limites

## Libellés et version

S04 (8.50, pages imprimées 30–33) distingue Identification, Autorisations et Droits effectifs selon le profil. Les quatre libellés historiques sont dans NIVEAUX_DROITS.csv. La dernière restriction masque la commande. Leur identité en V12 reste à vérifier.

S05 confirme deux libellés dans un cas de numérotation de règlement : voir les CSV. Cette preuve locale ne définit pas une matrice universelle CRUD ou impression.

## Droits particuliers

S06, page 45 : les commandes externes respectent les restrictions ; la protection d’un journal de vente empêche aussi sa consultation par ce canal. Un message de refus est documenté. Cela ne prouve pas que chaque commande interdite apparaît grisée dans chaque contexte.

S07 atteste des autorisations propres au bon à payer, distinctes d’un simple accès au menu. La phrase décrivant « Affectation BAP tout acheteur » présente une inversion apparente entre interdire et autoriser : conserver le point BAP-01 ouvert. Ne pas coder une règle comptable sur cette phrase ambiguë.

## Consignes d’implémentation proposées, non attribuées à Sage

Séparer : accès au module, affichage du menu, accès à la ressource, création, modification, suppression, impression, export et opérations métier. Contrôler côté serveur, même si un lien est masqué. Une URL directe ou une commande externe doit subir le même contrôle. Ces choix sont des recommandations pour l’ERP, pas une description vérifiée de Sage V12.

Ne pas rebaptiser les niveaux existants de l’ERP avant validation des libellés V12. Conserver une correspondance interne stable et enregistrer les dérogations. Ne pas assimiler « Tout interdire » à un libellé officiel V12 sur la seule base du cahier de demande.
