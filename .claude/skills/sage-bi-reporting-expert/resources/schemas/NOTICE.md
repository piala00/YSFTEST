# Définition du catalogue unifié

Chaque composant enregistré doit porter un identifiant stable `produit/version/build/edition/fonction/ecran/element`. Utiliser `catalogue_exemple.jsonl` comme exemple **non exhaustif** ; ne pas réinterpréter des exemples comme des résultats observés.

Champs obligatoires : `product`, `version`, `edition`, `menu_path`, `window_id`, `tab`, `element_id`, `label`, `kind`, `meaning`, `preconditions`, `default`, `required`, `visible_if`, `enabled_if`, `events`, `side_effects`, `database_mapping`, `evidence`, `verification_status`, `last_checked`.

Un composant ne devient **VALIDÉ** que si son intitulé, son type, ses conditions d'activation, son impact et ses droits ont tous été vérifiés sur une installation de test + source datée. La collecte Windows peut produire des noms incomplets : compléter manuellement sans supposer.

État de couverture par version : `NON_RECHERCHÉ`, `REPÉRÉ`, `DOCUMENTÉ`, `OBSERVÉ`, `TESTÉ`, `VALIDÉ`, `NON_APPLICABLE`.
