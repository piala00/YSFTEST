from rest_framework import serializers

from apps.commercial.models import Article, Document, LigneDocument, Reglement, Tiers
from apps.comptabilite.models import Compte, Ecriture, Journal, LigneEcriture


class TiersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tiers
        fields = ["id", "type_tiers", "code", "nom", "niu", "rccm", "adresse", "ville", "telephone", "email",
                  "delai_paiement", "plafond_credit", "assujetti_tva", "actif"]


class ArticleSerializer(serializers.ModelSerializer):
    famille = serializers.StringRelatedField()
    en_alerte = serializers.BooleanField(read_only=True)

    class Meta:
        model = Article
        fields = ["id", "reference", "designation", "nature", "famille", "unite", "prix_achat", "prix_vente",
                  "taux_tva", "suivi_stock", "stock", "stock_minimum", "en_alerte", "actif"]
        read_only_fields = ["stock"]


class LigneDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneDocument
        fields = ["id", "article", "designation", "quantite", "prix_unitaire", "remise", "taux_tva",
                  "montant_ht", "montant_tva"]
        read_only_fields = ["montant_ht", "montant_tva"]


class DocumentSerializer(serializers.ModelSerializer):
    lignes = LigneDocumentSerializer(many=True)
    tiers_nom = serializers.CharField(source="tiers.nom", read_only=True)
    type_libelle = serializers.CharField(source="get_type_document_display", read_only=True)
    reste_a_payer = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = Document
        fields = ["id", "type_document", "type_libelle", "numero", "date", "date_echeance", "tiers", "tiers_nom",
                  "reference_externe", "statut", "notes", "total_ht", "total_tva", "total_ttc", "reste_a_payer", "lignes"]
        read_only_fields = ["numero", "statut", "total_ht", "total_tva", "total_ttc"]

    def validate(self, attrs):
        Document(type_document=attrs.get("type_document", getattr(self.instance, "type_document", None)),
                 tiers=attrs.get("tiers", getattr(self.instance, "tiers", None))).clean()
        return attrs

    def create(self, validated_data):
        lignes = validated_data.pop("lignes")
        document = Document.objects.create(**validated_data)
        for ligne in lignes:
            LigneDocument.objects.create(document=document, **ligne)
        document.recalculer()
        return document

    def update(self, instance, validated_data):
        if not instance.modifiable:
            raise serializers.ValidationError("Document validé : modification impossible.")
        lignes = validated_data.pop("lignes", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if lignes is not None:
            instance.lignes.all().delete()
            for ligne in lignes:
                LigneDocument.objects.create(document=instance, **ligne)
        instance.recalculer()
        return instance


class ReglementSerializer(serializers.ModelSerializer):
    tiers_nom = serializers.CharField(source="tiers.nom", read_only=True)

    class Meta:
        model = Reglement
        fields = ["id", "numero", "date", "tiers", "tiers_nom", "mode", "journal", "montant", "reference", "libelle"]
        read_only_fields = ["numero"]

    def create(self, validated_data):
        return Reglement(**validated_data).enregistrer()


class CompteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Compte
        fields = ["id", "numero", "intitule", "lettrable", "actif"]


class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = ["id", "code", "intitule", "type_journal", "compte_tresorerie"]


class LigneEcritureSerializer(serializers.ModelSerializer):
    compte_numero = serializers.CharField(source="compte.numero", read_only=True)

    class Meta:
        model = LigneEcriture
        fields = ["id", "compte", "compte_numero", "tiers", "libelle", "debit", "credit", "lettrage"]


class EcritureSerializer(serializers.ModelSerializer):
    lignes = LigneEcritureSerializer(many=True, read_only=True)
    journal_code = serializers.CharField(source="journal.code", read_only=True)

    class Meta:
        model = Ecriture
        fields = ["id", "numero", "journal", "journal_code", "date", "libelle", "reference", "statut", "origine", "lignes"]
