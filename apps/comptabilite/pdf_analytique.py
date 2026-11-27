"""Génération des états analytiques PDF natifs, sans recalcul comptable.

Les données sont fournies par le même moteur que les écrans et exports CSV/XLSX.
Le module ne lit ni n'écrit directement en base.
"""
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.utils.text import slugify


def _polices():
    """Utilise les polices Vera embarquées par ReportLab pour les accents français."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if "ERP-Vera" in pdfmetrics.getRegisteredFontNames():
        return "ERP-Vera", "ERP-Vera-Bold"

    import reportlab

    dossier = Path(reportlab.__file__).resolve().parent / "fonts"
    fichiers = {
        "ERP-Vera": dossier / "Vera.ttf",
        "ERP-Vera-Bold": dossier / "VeraBd.ttf",
        "ERP-Vera-Italic": dossier / "VeraIt.ttf",
        "ERP-Vera-BoldItalic": dossier / "VeraBI.ttf",
    }
    if all(chemin.is_file() for chemin in fichiers.values()):
        for nom, chemin in fichiers.items():
            pdfmetrics.registerFont(TTFont(nom, str(chemin)))
        pdfmetrics.registerFontFamily(
            "ERP-Vera",
            normal="ERP-Vera",
            bold="ERP-Vera-Bold",
            italic="ERP-Vera-Italic",
            boldItalic="ERP-Vera-BoldItalic",
        )
        return "ERP-Vera", "ERP-Vera-Bold"
    return "Helvetica", "Helvetica-Bold"


def _valeur(valeur):
    if valeur is None:
        return ""
    if isinstance(valeur, bool):
        return "Oui" if valeur else "Non"
    if isinstance(valeur, (datetime, date)):
        return valeur.strftime("%d/%m/%Y")
    if isinstance(valeur, Decimal):
        return format(valeur, ",.2f").replace(",", " ").replace(".", ",")
    if isinstance(valeur, float):
        return format(Decimal(str(valeur)), ",.2f").replace(",", " ").replace(".", ",")
    texte = str(valeur)
    return "".join(caractere for caractere in texte if caractere in "\n\t" or ord(caractere) >= 32)


def generer_pdf(nom, titre, debut, fin, entetes, lignes, note=""):
    """Produit un PDF multipage A4 paysage (A3 pour les journaux larges)."""
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A3, A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

    police, police_grasse = _polices()
    entetes = list(entetes) or ["Donnée"]
    lignes = list(lignes)
    largeur_page = landscape(A3 if len(entetes) > 8 else A4)
    sortie = BytesIO()
    periode = f"Du {debut:%d/%m/%Y} au {fin:%d/%m/%Y}"
    nom_sain = slugify(nom) or "analytique"

    document = SimpleDocTemplate(
        sortie,
        pagesize=largeur_page,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=17 * mm,
        bottomMargin=16 * mm,
        title=titre,
        author="ERP Transport Afrique Centrale",
    )
    styles = {
        "titre": ParagraphStyle(
            "ERPTitre", fontName=police_grasse, fontSize=14, leading=18,
            textColor=colors.HexColor("#1A3263"), spaceAfter=3 * mm,
        ),
        "sous_titre": ParagraphStyle(
            "ERPPeriode", fontName=police, fontSize=8, leading=10,
            textColor=colors.HexColor("#475569"), spaceAfter=2 * mm,
        ),
        "note": ParagraphStyle(
            "ERPNote", fontName=police, fontSize=7.5, leading=9,
            textColor=colors.HexColor("#475569"), spaceAfter=3 * mm,
        ),
        "cellule": ParagraphStyle(
            "ERPCellule", fontName=police, fontSize=7, leading=8.5,
            alignment=TA_LEFT, splitLongWords=True,
        ),
        "entete": ParagraphStyle(
            "ERPEntete", fontName=police_grasse, fontSize=7, leading=8.5,
            textColor=colors.white, alignment=TA_LEFT, splitLongWords=True,
        ),
    }

    def paragraphe(valeur, style):
        texte = escape(_valeur(valeur)).replace("\n", "<br/>") or "&nbsp;"
        return Paragraph(texte, style)

    donnees = [[paragraphe(valeur, styles["entete"]) for valeur in entetes]]
    for ligne in lignes:
        valeurs = list(ligne[:len(entetes)])
        valeurs.extend([""] * (len(entetes) - len(valeurs)))
        donnees.append([paragraphe(valeur, styles["cellule"]) for valeur in valeurs])
    if not lignes:
        donnees.append([paragraphe("Aucune donnée sur la période.", styles["cellule"])]
                       + [paragraphe("", styles["cellule"]) for _ in entetes[1:]])

    nombre_colonnes = len(entetes)
    largeur_disponible = document.width
    if nombre_colonnes == 1:
        largeurs = [largeur_disponible]
    else:
        premiere = largeur_disponible * (0.28 if nombre_colonnes <= 7 else 0.20)
        reste = (largeur_disponible - premiere) / (nombre_colonnes - 1)
        largeurs = [premiere] + [reste] * (nombre_colonnes - 1)

    tableau = LongTable(
        donnees,
        colWidths=largeurs,
        repeatRows=1,
        splitByRow=1,
        hAlign="LEFT",
    )
    tableau.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D6DEE8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6FA")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    contenu = [
        Paragraph(escape(titre), styles["titre"]),
        Paragraph(escape(periode), styles["sous_titre"]),
    ]
    if note:
        contenu.append(Paragraph(escape(_valeur(note)), styles["note"]))
    contenu.extend([Spacer(1, 2 * mm), tableau])

    def pied_page(canvas, doc):
        canvas.saveState()
        canvas.setTitle(titre)
        canvas.setAuthor("ERP Transport Afrique Centrale")
        canvas.setSubject(f"{titre} — {periode}")
        canvas.setFont(police, 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(doc.leftMargin, 7 * mm, f"{titre} — {periode}")
        canvas.drawRightString(largeur_page[0] - doc.rightMargin, 7 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(contenu, onFirstPage=pied_page, onLaterPages=pied_page)
    reponse = HttpResponse(sortie.getvalue(), content_type="application/pdf")
    reponse["Content-Disposition"] = f'attachment; filename="{nom_sain}.pdf"'
    reponse["X-Content-Type-Options"] = "nosniff"
    return reponse
