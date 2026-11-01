"""Classeur de données et de critères, sans recalcul des états ni formules Excel."""
from io import BytesIO

from django.http import HttpResponse


TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def exporter_excel(nom, entetes, lignes, criteres):
    from openpyxl import Workbook
    from openpyxl.cell import WriteOnlyCell
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    classeur = Workbook(write_only=True)

    def feuille(titre, colonnes, donnees):
        page = classeur.create_sheet(titre)
        page.freeze_panes = "A2"

        def cellule(valeur, titre=False):
            if isinstance(valeur, str):
                valeur = ILLEGAL_CHARACTERS_RE.sub("", valeur)
            c = WriteOnlyCell(page, value=valeur)
            if isinstance(valeur, str):
                # Les noms, téléphones et critères restent du texte, y compris
                # lorsqu'ils commencent par =, +, - ou @.
                c.data_type = "s"
            if titre:
                c.font = Font(bold=True)
            return c

        page.append([cellule(v, titre=True) for v in colonnes])
        nombre = 1
        for ligne in donnees:
            page.append([cellule(v) for v in ligne])
            nombre += 1
        page.auto_filter.ref = f"A1:{get_column_letter(len(colonnes))}{nombre}"

    feuille("Données", entetes, lignes)
    feuille("Critères", ["Critère", "Valeur"], criteres)
    contenu = BytesIO()
    classeur.save(contenu)
    reponse = HttpResponse(contenu.getvalue(), content_type=TYPE_XLSX)
    reponse["Content-Disposition"] = f'attachment; filename="{nom}.xlsx"'
    return reponse
