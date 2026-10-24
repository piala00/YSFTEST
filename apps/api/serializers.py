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
    valeur_stock = serializers.DecimalField(max_digits=18, decimal_places=0, read_only=True)

    class Meta:
        model = Article
        fields = ["id", "reference", "designation", "nature", "famille", "unite", "prix_achat", "prix_vente",
                  "taux_tva", "suivi_stock", "stock", "cmup", "valeur_stock", "stock_minimum", "en_alerte", "actif"]
        read_only_fields = ["stock", "cmup"]


class LigneDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneDocument
        fields = ["id", "article", "designation", "quantite", "prix_unitaire", "remise", "taux_tva",
                  "montant_ht", "montant_tva"]
        read_only_fields = ["montant_ht", "montant_tva"]


class DocumentSerializer(serializers.ModelSerializer):
    lignes = LigneDocumentSerializer(many=True)
    tiers_nom = serializers.CharField(source="tiers.nom", read_only=True, default="")
    depot_nom = serializers.CharField(source="depot.intitule", read_only=True, default="")
    type_libelle = serializers.CharField(source="get_type_document_display", read_only=True)
    reste_a_payer = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = Document
        fields = ["id", "type_document", "type_libelle", "numero", "date", "date_echeance", "tiers", "tiers_nom", "payeur",
                  "depot", "depot_nom", "depot_destination",
                  "reference_externe", "statut", "notes", "total_ht", "total_tva", "total_ttc", "reste_a_payer", "lignes",
                  "cree_par", "cree_le", "valide_par", "valide_le"]
        read_only_fields = ["numero", "statut", "total_ht", "total_tva", "total_ttc", "cree_par", "cree_le", "valide_par", "valide_le"]

    def validate(self, attrs):
        from django.core.exceptions import ValidationError as DjangoValidationError

        doc = Document(**{k: attrs.get(k, getattr(self.instance, k, None))
                          for k in ("type_document", "tiers", "depot", "depot_destination")})
        try:
            doc.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)
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


class ImputationSerializer(serializers.Serializer):
    facture = serializers.IntegerField(source="document_id")
    numero = serializers.CharField(source="document.numero")
    montant = serializers.DecimalField(max_digits=18, decimal_places=2)


class ReglementSerializer(serializers.ModelSerializer):
    tiers_nom = serializers.CharField(source="tiers.nom", read_only=True)
    factures = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, required=False,
        queryset=Document.objects.filter(type_document__in=(Document.FACTURE, Document.ACHAT_FACTURE)))
    imputations = ImputationSerializer(many=True, read_only=True)
    en_attente_de_rattachement = serializers.DecimalField(max_digits=18, decimal_places=2, read_only=True)

    class Meta:
        model = Reglement
        fields = ["id", "numero", "date", "tiers", "tiers_nom", "mode", "journal", "montant", "facture", "factures", "commande",
                  "agence_encaissement", "reference", "libelle", "cree_par", "imputations", "en_attente_de_rattachement"]
        read_only_fields = ["numero", "cree_par"]

    def create(self, validated_data):
        from django.core.exceptions import ValidationError as ErreurModele
        from rest_framework.exceptions import ValidationError

        factures = validated_data.pop("factures", None) or None
        try:
            return Reglement(**validated_data).enregistrer(factures)
        except ErreurModele as exc:                     # ex. reçu de créance sans facture
            raise ValidationError(exc.message_dict if hasattr(exc, "error_dict") else exc.messages)


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
