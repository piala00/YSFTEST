# Migration additive : coordonnées locales seulement, aucune pièce financière modifiée.
import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import re
import unicodedata


def telephone_normalise(valeur):
    texte = (valeur or "").strip()
    if not texte or re.search(r"[^0-9+\s().-]", texte):
        return ""
    texte = re.sub(r"[\s().-]", "", texte)
    if texte.startswith("00"):
        texte = "+" + texte[2:]
    international = texte.startswith("+")
    chiffres = texte[1:] if international else texte
    if not re.fullmatch(r"[0-9]{7,15}", chiffres):
        return ""
    if international:
        return "+" + chiffres
    if len(chiffres) == 12 and chiffres.startswith("237"):
        return "+" + chiffres
    if len(chiffres) == 9 and chiffres[0] in "26":
        return "+237" + chiffres
    # Ne pas attribuer arbitrairement un autre pays aux numéros ambigus.
    return chiffres


def nom_normalise(valeur):
    nom = "".join(c for c in unicodedata.normalize("NFKD", valeur or "").casefold()
                  if not unicodedata.combining(c))
    return " ".join("".join(c if c.isalnum() else " " for c in nom).split())[:240]


def reprendre(apps, schema_editor):
    alias = schema_editor.connection.alias
    Personne = apps.get_model("transport", "PersonneGuichet")
    for modele, nom, telephone, piece, auteur in (
        ("Billet", "voyageur", "telephone", "piece_identite", "vendu_par_id"),
        ("Colis", "expediteur", "tel_expediteur", None, "cree_par_id"),
        ("Colis", "destinataire", "tel_destinataire", None, "cree_par_id"),
    ):
        Modele = apps.get_model("transport", modele)
        champs = [nom, telephone, auteur] + ([piece] if piece else [])
        for ligne in Modele.objects.using(alias).filter(site_origine="").order_by("cree_le", "pk").values(*champs).iterator(chunk_size=500):
            tel, n = telephone_normalise(ligne[telephone]), nom_normalise(ligne[nom])
            if not tel or not n:
                continue
            cni = (ligne[piece] or "").strip() if piece else ""
            qs = Personne.objects.using(alias).filter(telephone_normalise=tel, nom_normalise=n)
            if (not cni and qs.exists()) or qs.filter(piece_identite=cni).exists():
                continue
            Personne.objects.using(alias).create(nom=ligne[nom].strip(), telephone=ligne[telephone].strip(),
                telephone_normalise=tel, nom_normalise=n, piece_identite=cni,
                cree_par_id=ligne[auteur], modifie_par_id=ligne[auteur])


class Migration(migrations.Migration):
    dependencies = [
        ("transport", "0016_agences_points_de_vente"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="PersonneGuichet",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("nom", models.CharField(max_length=120)),
                ("telephone", models.CharField(max_length=30)),
                ("telephone_normalise", models.CharField(db_index=True, max_length=20)),
                ("nom_normalise", models.CharField(db_index=True, max_length=240)),
                ("piece_identite", models.CharField(blank=True, max_length=40)),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
                ("modifie_le", models.DateTimeField(auto_now=True)),
                ("cree_par", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                related_name="+", to=settings.AUTH_USER_MODEL)),
                ("modifie_par", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                   related_name="+", to=settings.AUTH_USER_MODEL)),
            ], options={"ordering": ["nom", "id"], "verbose_name": "Coordonnées du guichet"},
        ),
        migrations.CreateModel(
            name="SaisieGuichet",
            fields=[
                ("cle", models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ("genre", models.CharField(max_length=10)),
                ("empreinte", models.CharField(max_length=64)),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
                ("utilisateur", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                   related_name="+", to=settings.AUTH_USER_MODEL)),
                ("billet", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                                related_name="+", to="transport.billet")),
                ("colis", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT,
                                               related_name="+", to="transport.colis")),
            ],
        ),
        migrations.RunPython(reprendre, migrations.RunPython.noop),
    ]
