# Points à vérifier avant validation complète

1. **Version réelle du dépôt** : le patch correspond aux deux ZIP fournis, pas nécessairement à l'état courant du GitHub ni à Render.
2. **ERP Transport autonome** : le ZIP s'appelle ERP OHADA Commerce et contient du code `apps/transport`; vérifier si le projet Transport séparé requiert une implémentation distincte.
3. **Interface bureau analytique** : le nouveau fichier lance une fenêtre analytique et oriente certains écrans vers le web. Cela ne prouve pas que tous les écrans analytiques sont entièrement natifs.
4. **Plan standard SYSCOHADA complet** : pas réaudité dans cette livraison ; ne pas confondre conversion de format et validation du contenu normatif du plan.
5. **Choix métier pour société MIXTE** : vérifier quels écrans commerciaux doivent être visibles dans le module analytique mixte.
6. **Intégrité en conditions réelles** : tests unitaires Django, tests d'interface Windows, droits/API, migrations base et contrôle de la production non exécutés ici.
7. **Comptes atypiques** : devises, codes à caractères, numéros d'un plan repris ou comptes à plus de sept caractères demandent des décisions d'harmonisation métier, pas un raccourcissement algorithmique.
