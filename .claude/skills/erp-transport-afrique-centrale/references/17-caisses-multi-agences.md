# 17 — Gestion des caisses multi-agences (règle métier confirmée)

Chaque agence peut fonctionner avec **une caisse commune** à plusieurs services ou **plusieurs caisses distinctes** selon son organisation réelle. Les agences du siège et les grandes agences peuvent créer des caisses Billetterie, Courrier, Garage et Centrale ; ce n'est pas une obligation. Les petites agences peuvent fonctionner sur une caisse unique. Paramétrage dynamique par agence, sans règle rigide selon taille et localisation.

- Une opération service (billetterie, colis, garage, RH) n'est pas une opération caisse par elle-même : seul l'encaissement/paiement réel alimente trésorerie.
- Une caisse physique espèces n'est pas un portefeuille Mobile Money ni un compte bancaire.
- Toutes les caisses ont journaux, sessions, caissiers, affectations, soldes, rapprochements et droits individualisés.
- Les transferts caisse à caisse ou agence→siège ne créent pas de nouveaux revenus/charges et restent identifiables en transit jusqu'à confirmation.
- Le rapport d'agence reste **des tableaux simples** : recettes par activité, dépenses sorties, situation par caisse si plusieurs et total agence ; la direction voit agrégats agence / toutes agences avec complétude de synchronisation.
- Ne pas confondre caisse réceptrice des fonds, service source, agence d'encaissement et agence d'exploitation du véhicule. L'imputation analytique véhicule reste liée au voyage/à la prestation, non au lieu de garde des espèces.

**Lire et appliquer** `.claude/skills/erp-transport-caisses-multi-agences/SKILL.md` et ses sept références pour implémenter ce chantier. Conserver les référentiels et modules existants ; audit préalable obligatoire.
