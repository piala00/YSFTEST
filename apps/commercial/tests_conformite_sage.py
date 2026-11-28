"""Conformité du sens des mouvements de stock au tableau officiel Sage 100 V12.20 (Objets Métiers).

Source : skill `sage100-ecrans-etats-v12`, fichier MOUVEMENTS_ET_SIGNES_V12.csv (manuel M02, p. 459-460).
On compare les lignes à quantité saisie positive : document saisi directement (sans document d'origine).
"""
import csv
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

from .models import Document

TABLE = Path(settings.BASE_DIR) / ".claude/skills/sage100-ecrans-etats-v12/references/MOUVEMENTS_ET_SIGNES_V12.csv"
D = Document
CORRESPONDANCE = {
    ("VENTE", "Devis"): D.DEVIS, ("VENTE", "Bon de commande"): D.COMMANDE,
    ("VENTE", "Préparation de livraison"): D.PREPARATION, ("VENTE", "Bon de livraison"): D.LIVRAISON,
    ("VENTE", "Facture"): D.FACTURE, ("VENTE", "Bon de retour"): D.RETOUR,
    ("VENTE", "Bon d’avoir financier"): D.AVOIR_FINANCIER, ("VENTE", "Facture de retour"): D.FACTURE_RETOUR,
    ("VENTE", "Facture d’avoir"): D.AVOIR,
    ("ACHAT", "Préparation de commande"): D.ACHAT_PREPARATION, ("ACHAT", "Bon de commande"): D.ACHAT_COMMANDE,
    ("ACHAT", "Bon de livraison"): D.ACHAT_RECEPTION, ("ACHAT", "Facture"): D.ACHAT_FACTURE,
    ("ACHAT", "Bon de retour"): D.ACHAT_RETOUR, ("ACHAT", "Bon d’avoir financier"): D.ACHAT_AVOIR_FINANCIER,
    ("ACHAT", "Facture de retour"): D.ACHAT_FACTURE_RETOUR, ("ACHAT", "Facture d’avoir"): D.ACHAT_AVOIR,
    ("STOCK", "Mouvement d’entrée"): D.STOCK_ENTREE, ("STOCK", "Mouvement de sortie"): D.STOCK_SORTIE,
}
# Écart connu, à traiter : Sage passe un mouvement « en montant » (correction de valeur du stock, sans quantité)
# pour les avoirs financiers d'achat ; l'ERP ne corrige pas encore la valeur du stock sur ces pièces.
ECARTS_CONNUS = {"SORTIE_MONTANT"}


class SensDesMouvementsTests(SimpleTestCase):
    def test_sens_des_mouvements_de_quantite(self):
        with TABLE.open(encoding="utf-8") as f:
            lignes = [l for l in csv.DictReader(f, delimiter=";") if l["qte_interface_signe"] == "POSITIF"]
        verifiees = 0
        for ligne in lignes:
            type_document = CORRESPONDANCE.get((ligne["domaine"], ligne["document"]))
            if type_document is None:
                continue                                    # dépréciation, virement : traités ailleurs
            mouvement = ligne["mouvement_documente"]
            doc = Document(type_document=type_document)
            with self.subTest(source=ligne["id"], document=ligne["document"], domaine=ligne["domaine"]):
                if mouvement == "AUCUN" or mouvement in ECARTS_CONNUS:
                    self.assertFalse(doc.mouvemente_stock)
                elif mouvement == "ENTREE_QUANTITE":
                    self.assertTrue(doc.mouvemente_stock)
                    self.assertIn(type_document, Document.TYPES_ENTREE)
                elif mouvement == "SORTIE_QUANTITE":
                    self.assertTrue(doc.mouvemente_stock)
                    self.assertIn(type_document, Document.TYPES_SORTIE)
                verifiees += 1
        self.assertGreaterEqual(verifiees, 19)
