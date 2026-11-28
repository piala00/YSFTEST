# Protocole d'audit local (sans modifier Sage)

1. Créer un compte SQL dédié à permissions minimales, limité aux métadonnées nécessaires.
2. Dans SQL Server Management Studio, sélectionner **explicitement** une base de test ou une base autorisée.
3. Exécuter `03_AUDIT_SCHEMA_AVANCE_LECTURE_SEULE.sql` et exporter chaque résultat en CSV distinct.
4. Vérifier les permissions de visibilité: une table absente du résultat ne prouve pas son absence réelle.
5. Comparer les tables, colonnes, index et FK; distinguer **contraintes SQL physiques** et **relations logiques du manuel Sage**.
6. Ajouter les statuts OBSERVÉ + build/édition/install + horodatage + empreinte de preuve.
7. Tester les rapprochements fonctionnels dans Sage sur un dossier de démonstration (ex. stock d'un article/dépôt, facture, échéance, compte tiers), sans écrire dans SQL Sage.
8. Produire les correspondances V5–V11 seulement quand les versions locales correspondantes ont été inventoriées. Les tables supplémentaires V12 ne prouvent rien sur V5–V11.

## Garde-fous
- Aucune donnée de client, montant, mot de passe, chaîne de connexion ou autre donnée de production dans les Skills.
- Les permissions accordées aux utilisateurs d'audit doivent être vérifiées par l'administrateur SQL; `ApplicationIntent=ReadOnly` ne suffit pas à garantir une connexion strictement en lecture.
- Ne pas interpréter « lecture/écriture » du manuel Sage driver comme une permission de muter via SQL direct.
- Ne pas créer de requêtes d'agrégation de CA et stocks sans déterminer grain, provenance, statuts et règles d'arrondis.
