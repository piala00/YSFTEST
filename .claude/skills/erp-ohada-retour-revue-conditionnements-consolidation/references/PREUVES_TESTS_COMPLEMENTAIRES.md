# Journal brut : contrôles complémentaires

```text
Creating test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
Found 8 test(s).
Operations to perform:
  Synchronize unmigrated apps: api, humanize, messages, reporting, rest_framework, staticfiles
  Apply all migrations: admin, auth, authtoken, commercial, comptabilite, contenttypes, core, sessions
Synchronizing apps without migrations:
  Creating tables...
    Running deferred SQL...
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying authtoken.0001_initial... OK
  Applying authtoken.0002_auto_20160226_1747... OK
  Applying authtoken.0003_tokenproxy... OK
  Applying authtoken.0004_alter_tokenproxy_options... OK
  Applying core.0001_initial... OK
  Applying core.0002_societe_stock_negatif_autorise... OK
  Applying core.0003_regime_tva... OK
  Applying core.0004_autorisations_acces... OK
  Applying core.0005_journal_evenements... OK
  Applying core.0006_journal_sauvegarde... OK
  Applying core.0007_regime_fiscal... OK
  Applying core.0008_configuration_tva... OK
  Applying core.0009_acces_logiciels... OK
  Applying core.0010_droits_menu_fichier_comptabilite... OK
  Applying core.0011_menu_services_connectes... OK
  Applying commercial.0001_initial... OK
  Applying comptabilite.0001_initial... OK
  Applying comptabilite.0002_structure_banques_taxes_analytique... OK
  Applying core.0012_agences_caisse_acomptes... OK
  Applying commercial.0002_initial... OK
  Applying commercial.0003_stocks_depots_documents_sage... OK
  Applying commercial.0004_reprise_stock_depots... OK
  Applying commercial.0005_tarifs_risque_reappro... OK
  Applying commercial.0006_regime_tva... OK
  Applying commercial.0007_regime_fiscal... OK
  Applying commercial.0008_compte_bloque... OK
  Applying commercial.0009_tiers_payeur... OK
  Applying commercial.0010_agences_caisse_acomptes... OK
  Applying commercial.0011_agences_caisse_acomptes... OK
  Applying commercial.0012_fiche_de_stock... OK
  Applying commercial.0013_auteurs_recus... OK
  Applying comptabilite.0003_auteurs_recus... OK
  Applying sessions.0001_initial...test_R09_mobile_money_must_not_increase_cash (review_probes.ReportReview.test_R09_mobile_money_must_not_increase_cash) ...  OK
System check identified no issues (0 silenced).
PROBE MOBILE {'mode': 'MOBILE_MONEY', 'cash_before': '0', 'cash_after': '3000.00'}
FAIL
test_R26_old_report_does_not_change_with_future_payment (review_probes.ReportReview.test_R26_old_report_does_not_change_with_future_payment) ... PROBE RAPPORT PASSE {'credit_initial': '3000.00', 'credit_apres_paiement_futur': '0.00'}
FAIL
test_R13_partial_delivery_then_invoice (review_probes.StockReview.test_R13_partial_delivery_then_invoice) ... PROBE PARTIEL {'ordered': 10, 'delivered': '4', 'remaining': '6.000', 'invoice_quantity': '4.000', 'stock': '86.000'}
ok
test_R14_restricted_api_list (review_probes.StockReview.test_R14_restricted_api_list) ... /workspace/scratch/cd623cc88cfb/revue_transmission_20261024/venv/lib/python3.12/site-packages/django/core/handlers/base.py:61: UserWarning: No directory at: /workspace/scratch/cd623cc88cfb/revue_transmission_20261024/transmission-gpt/source/staticfiles/
  mw_instance = middleware(adapted_handler)
PROBE R14 {'filtered_http': 403, 'broad_http': 200, 'expected_quantity_exposed': True}
FAIL
test_R17_blank_is_not_zero (review_probes.StockReview.test_R17_blank_is_not_zero) ... PROBE R17 {'http': 302, 'pointages_after_blank': 1}
FAIL
test_R17_negative_quantity_rejected (review_probes.StockReview.test_R17_negative_quantity_rejected) ... PROBE NEGATIVE {'http': 302, 'saved': True, 'quantity': '-5.000'}
FAIL
test_R18_missing_pointage_not_complete_stock (review_probes.StockReview.test_R18_missing_pointage_not_complete_stock) ... PROBE FICHE {'fiche_balance': '90.000', 'machine_balance': '90.000', 'pending_rows': 1, 'pending_outgoing': '10.000'}
FAIL
test_R19_original_fichiste_preserved (review_probes.StockReview.test_R19_original_fichiste_preserved) ... PROBE HISTORIQUE {'createur': 'fichiste', 'ancien_fichiste_historique': 'second-fichiste', 'correcteur': 'second-fichiste'}
FAIL

======================================================================
FAIL: test_R09_mobile_money_must_not_increase_cash (review_probes.ReportReview.test_R09_mobile_money_must_not_increase_cash)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/cd623cc88cfb/revue_transmission_20261024/review_probes.py", line 102, in test_R09_mobile_money_must_not_increase_cash
    self.assertEqual(before,after,'Un mode Mobile Money ne doit pas alimenter une caisse espèces sans règle explicite.')
AssertionError: Decimal('0') != Decimal('3000.00') : Un mode Mobile Money ne doit pas alimenter une caisse espèces sans règle explicite.

======================================================================
FAIL: test_R26_old_report_does_not_change_with_future_payment (review_probes.ReportReview.test_R26_old_report_does_not_change_with_future_payment)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/cd623cc88cfb/revue_transmission_20261024/review_probes.py", line 91, in test_R26_old_report_does_not_change_with_future_payment
    self.assertEqual(after,before,'Un rapport de la veille doit calculer le reste dû à sa date, pas le solde courant.')
AssertionError: Decimal('0.00') != Decimal('3000.00') : Un rapport de la veille doit calculer le reste dû à sa date, pas le solde courant.

======================================================================
FAIL: test_R14_restricted_api_list (review_probes.StockReview.test_R14_restricted_api_list)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/cd623cc88cfb/revue_transmission_20261024/review_probes.py", line 39, in test_R14_restricted_api_list
    self.assertFalse(expected_exposed,'L’API sans filtre ne doit pas révéler les quantités interdites.')
AssertionError: True is not false : L’API sans filtre ne doit pas révéler les quantités interdites.

======================================================================
FAIL: test_R17_blank_is_not_zero (review_probes.StockReview.test_R17_blank_is_not_zero)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/cd623cc88cfb/revue_transmission_20261024/review_probes.py", line 24, in test_R17_blank_is_not_zero
    self.assertEqual(count,0,'Une quantité absente ne doit pas produire un pointage validé.')
AssertionError: 1 != 0 : Une quantité absente ne doit pas produire un pointage validé.

======================================================================
FAIL: test_R17_negative_quantity_rejected (review_probes.StockReview.test_R17_negative_quantity_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/cd623cc88cfb/revue_transmission_20261024/review_probes.py", line 62, in test_R17_negative_quantity_rejected
    self.assertIsNone(p,'La sortie déclarée est une quantité absolue ; une valeur négative doit être rejetée.')
AssertionError: <PointageFiche: PF2026-00001 - BL2026-00001> is not None : La sortie déclarée est une quantité absolue ; une valeur négative doit être rejetée.

======================================================================
FAIL: test_R18_missing_pointage_not_complete_stock (review_probes.StockReview.test_R18_missing_pointage_not_complete_stock)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/cd623cc88cfb/revue_transmission_20261024/review_probes.py", line 55, in test_R18_missing_pointage_not_complete_stock
    self.assertNotEqual(f['solde_fiche'],f['solde_machine'],'Une sortie non déclarée ne doit pas être reprise automatiquement dans un registre indépendant.')
AssertionError: Decimal('90.000') == Decimal('90.000') : Une sortie non déclarée ne doit pas être reprise automatiquement dans un registre indépendant.

======================================================================
FAIL: test_R19_original_fichiste_preserved (review_probes.StockReview.test_R19_original_fichiste_preserved)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/workspace/scratch/cd623cc88cfb/revue_transmission_20261024/review_probes.py", line 48, in test_R19_original_fichiste_preserved
    self.assertEqual(p.historique[0]['fichiste'],self.fichiste.username,'L’historique doit garder l’auteur de la déclaration remplacée.')
AssertionError: 'second-fichiste' != 'fichiste'
- second-fichiste
+ fichiste
 : L’historique doit garder l’auteur de la déclaration remplacée.

----------------------------------------------------------------------
Ran 8 tests in 1.220s

FAILED (failures=7)
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...

```
