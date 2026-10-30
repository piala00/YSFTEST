"""Scénarios fictifs, journal GL traçable et plan de départs interagences pour la simulation existante."""
import datetime
import json
import math
from decimal import Decimal
from pathlib import Path
from django.core.management.base import CommandError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone


class SimulationMetierMixin:
    def configurer_metier(self, options):
        self.profil_complet = options.get('scenarios_complets', False)
        self.departs_jour = options.get('departs_jour', 0)
        if not 0 <= self.departs_jour <= 2000:
            raise CommandError('Départs par jour : 0 (aléatoire) à 2000 pour toutes les agences réunies.')
        if self.profil_complet and self.departs_jour == 1:
            raise CommandError('Deux départs au minimum pour tester une correspondance.')
        # Jusqu'à quatre portions de six heures par véhicule. Garder une place de planning pour la correspondance.
        options['vehicules'] = max(options['vehicules'], math.ceil((self.departs_jour + 1) / 4) - 5,
                                  4 if self.profil_complet else 1)
        self.scenarios, self.mesures, self.hypotheses = [], [], []

    def initialiser_metier(self):
        if not self.profil_complet:
            return
        from django.contrib.auth.models import Permission
        from .models import ArretLigne, Gare, Ligne, Vehicule
        from apps.partenaires.models import ContratPartenaire
        self.chef.user_permissions.add(*Permission.objects.filter(codename__in=[
            'autoriser_indemnite_colis', 'payer_indemnite_colis'], content_type__app_label='transport'))
        # Hypothèses fictives explicites, jamais une modification de contrats d'une société réelle.
        for i, c in enumerate(self.contrats):
            c.modele, c.taux_commission, c.montant_location = ContratPartenaire.COMMISSION, Decimal(15), Decimal(0)
            c.assiette_commission = ContratPartenaire.RECETTES if i % 2 == 0 else ContratPartenaire.MARGE
            c.notes = 'SIMULATION : hypothèse fictive, base des 15 % à confirmer pour le contrat réel.'
            c.save(update_fields=['modele', 'taux_commission', 'montant_location', 'assiette_commission', 'notes'])
        gamme = self.cars[0]['vehicule'].gamme
        self.ligne_transit = Ligne.objects.get(code='DLA-YDE' + ('-VIP' if gamme == 'VIP' else ''))
        self.ligne_suite = Ligne.objects.get(code='YDE-BTA' + ('-VIP' if gamme == 'VIP' else ''))
        # Les deux véhicules de scénario sont de même gamme ; le reste de la flotte reste mixte.
        if self.cars[1]['vehicule'].gamme != gamme:
            compatible = next(c for c in self.cars[2:] if c['vehicule'].gamme == gamme and not c.get('courrier'))
            k = self.cars.index(compatible)
            self.cars[1], self.cars[k] = self.cars[k], self.cars[1]
        self.arret = Gare.objects.create(code='SIM-ARRET', nom='Point intermédiaire Edéa (fictif)', ville='Edéa',
                                         type_gare=Gare.POINT_VENTE, rattachement=self.gares['DLA'])
        ArretLigne.objects.create(ligne=self.ligne_transit, gare=self.arret, ordre=1)
        self.secours = Vehicule.objects.create(immatriculation='SIM SECOURS', designation='Secours fictif', gamme=gamme,
                                               nombre_places=self.cars[0]['vehicule'].nombre_places)
        self._colis_scenarios = []

    def plan_journee(self, jour):
        if not self.profil_complet and not self.departs_jour:
            for c in self.cars:
                if self.r.random() > .72:
                    continue
                ligne = c['aller'] if (jour.day + self.cars.index(c)) % 2 else c['retour']
                yield c, ligne, self.r.choice([6, 7, 8, 10, 13, 15])
            return
        scenarios = self.profil_complet and jour == self.mois_jours[0]
        if self.departs_jour:
            candidats = [(c, c['aller'] if (jour.day + i + n) % 2 else c['retour'], 6*n)
                          for n in range(4) for i, c in enumerate(self.cars)]
            if scenarios:
                reserves = [(self.cars[0], self.ligne_transit, 0), (self.cars[1], self.ligne_suite, 6)]
                exclus = {(self.cars[0]['vehicule'].pk, 0), (self.cars[1]['vehicule'].pk, 0), (self.cars[1]['vehicule'].pk, 6)}
                candidats = [x for x in candidats if (x[0]['vehicule'].pk, x[2]) not in exclus]
            else:
                reserves = []
            nombre = self.departs_jour - len(reserves)
            plan = reserves + self.r.sample(candidats, nombre)
        else:
            plan = [(c, c['aller'] if (jour.day + i) % 2 else c['retour'], self.r.choice([6, 7, 8, 10, 13, 15]))
                    for i, c in enumerate(self.cars) if self.r.random() <= .72]
            if scenarios:
                plan = [x for x in plan if x[0] not in self.cars[:2]]
                plan += [(self.cars[0], self.ligne_transit, 0), (self.cars[1], self.ligne_suite, 6)]
        yield from sorted(plan, key=lambda x:(x[2], x[0]['vehicule'].pk))

    def reserve_scenarios(self, c, heure, jour):
        if not self.profil_complet or jour != self.mois_jours[0]:
            return 0
        return 2 if c is self.cars[0] and heure == 0 else 1 if c is self.cars[1] and heure == 6 else 0

    def assurer_especes(self, montant, jour):
        from .models_caisse import TransfertFonds, solde_tresorerie
        disponible = solde_tresorerie(self.ca.compte_tresorerie, jour)
        manque = Decimal(montant) - disponible
        if manque > 0:
            if solde_tresorerie(self.bq.compte_tresorerie, jour) < manque:
                raise CommandError('La trésorerie fictive est insuffisante ; aucun découvert silencieux n’est créé.')
            t = TransfertFonds(origine=self.bq, destination=self.ca, montant=manque, date_envoi=jour,
                              porteur='Approvisionnement espèces (simulation)')
            t.envoyer(self.chef)
            t.recevoir(self.chef, date=jour)
        return self.ca

    def tracer_scenario(self, module, cas, fonction):
        from apps.comptabilite.models import Ecriture, LigneEcriture
        avant = Ecriture.objects.aggregate(n=Max('pk'))['n'] or 0
        resultat = fonction()
        lignes = list(LigneEcriture.objects.filter(ecriture_id__gt=avant).select_related('compte','ecriture','vehicule','tiers'))
        self.scenarios.append({'date':str(timezone.localdate()), 'module':module, 'cas':cas,
            'objet':getattr(resultat, 'numero', None) or str(getattr(resultat, 'uid', '')),
            'debit':str(sum((l.debit for l in lignes), Decimal(0))),
            'credit':str(sum((l.credit for l in lignes), Decimal(0))),
            'ecritures':[{'source_gl_line_id':l.pk,'ecriture':l.ecriture.numero, 'statut':l.ecriture.statut,
                'compte':l.compte.numero,'debit':str(l.debit),'credit':str(l.credit),
                'vehicule':l.vehicule.immatriculation if l.vehicule_id else '', 'tiers':l.tiers.code if l.tiers_id else ''}
                for l in lignes]})
        return resultat

    def scenarios_avant_depart(self, jour, departs):
        if not self.profil_complet or jour != self.mois_jours[0]:
            self._depart_scenario = None
            return
        from .models import Billet, Colis
        from .models_suivi_colis import IncidentColis
        d1 = next(d for d,c,h in departs if c is self.cars[0] and h == 0)
        d2 = next(d for d,c,h in departs if c is self.cars[1] and h == 6)
        self._depart_scenario = d1.pk
        self._depart_suite_scenario = d2.pk
        self._colis_scenarios = []
        b = self.tracer_scenario('Billetterie', 'Transit / correspondance : un paiement pour deux portions', lambda:
            Billet(depart=d1, gare_arrivee=d2.ligne.gare_arrivee, voyageur='Correspondance (fictif)',
                   bagages='Sac fictif', prix_bagages=1500).vendre(self.agent))
        self.compteurs['billets'] += 1
        self.compteurs['bagages'] += 1
        self.tracer_scenario('Billetterie', 'Placement du billet déjà payé : aucun nouvel encaissement',
                             lambda: b.troncons.get(ordre=2).affecter(d2))
        self.tracer_scenario('Billetterie', 'Montée à un arrêt intermédiaire', lambda:
            Billet(depart=d1, gare_montee=self.arret, gare_arrivee=d1.ligne.gare_arrivee,
                   voyageur='Montée intermédiaire (fictif)', prix=2000).vendre(self.agent))
        self.compteurs['billets'] += 1
        for nature, retrouve, port in [(IncidentColis.PERDU,False,Colis.DU),(IncidentColis.ENDOMMAGE,False,Colis.PAYE),
                (IncidentColis.SANS_TRACE,False,Colis.DU),(IncidentColis.SANS_TRACE,True,Colis.DU)]:
            def creer():
                colis = Colis(gare_depart=d1.ligne.gare_depart, gare_arrivee=d1.ligne.gare_arrivee, prix=2500,
                    expediteur='Expéditeur fictif', destinataire='Destinataire fictif', port=port,
                    valeur_declaree=50000, description='Scénario '+nature,
                    contre_remboursement=10000 if retrouve else 0).enregistrer(self.agent)
                colis.charger(d1)
                return colis
            colis = self.tracer_scenario('Colis', 'Envoi '+nature+(' puis retrouvé' if retrouve else ''), creer)
            self.compteurs['colis'] += 1
            self._colis_scenarios.append((colis, nature, retrouve))
        self.scenarios_garage(jour, d1.vehicule)

    def scenarios_en_route(self, jour, depart):
        if not self.profil_complet or depart.pk != getattr(self,'_depart_scenario',None):
            return
        from .models_incidents import Incident, FraisIncident
        from .models_suivi_colis import IncidentColis
        declares = []
        for colis,nature,retrouve in self._colis_scenarios:
            incident = self.tracer_scenario('Colis', 'Signalement '+nature+' : aucun paiement automatique',
                lambda: IncidentColis.declarer(colis,nature,'Étape fictive','Constat fictif pendant l’acheminement',self.agent))
            declares.append((colis,incident,retrouve))
        self._colis_scenarios = declares
        i = self.tracer_scenario('Transport', 'Transvasement : répartition des produits, sans nouvelle vente', lambda:
            Incident.transborder(depart,40,self.secours,'Étape fictive','Panne (simulation)',self.chef))
        self.tracer_scenario('Garage', 'Dépannage du véhicule interrompu', lambda:
            FraisIncident(incident=i,nature=FraisIncident.DEPANNAGE,libelle='Remorquage fictif',montant=5000,
                          caisse=self.caisse_pour(5000,jour)).enregistrer())

    def scenarios_apres_arrivee(self, jour, depart):
        if not self.profil_complet or depart.pk != getattr(self,'_depart_scenario',None):
            return
        from apps.comptabilite.models import Compte
        from .models_suivi_colis import IncidentColis
        for colis, incident, retrouve in self._colis_scenarios:
            colis.refresh_from_db()
            if retrouve:
                self.tracer_scenario('Colis','Colis retrouvé : résolution sans écriture',lambda:incident.resoudre('Retrouvé, contrôle physique fictif',self.chef))
                self.tracer_scenario('Colis','Livraison : port dû et contre-remboursement distincts',lambda:
                    colis.livrer(colis.code_retrait,'Destinataire fictif, pièce DEMO',self.agent,date=jour))
                self.tracer_scenario('Colis','Reversement du contre-remboursement à l’expéditeur',lambda:
                    colis.reverser_contre_remboursement(self.agent,date=jour))
            elif incident.nature != IncidentColis.SANS_TRACE:
                montant = 10000 if incident.nature == IncidentColis.PERDU else 5000
                compte = Compte.objects.get_or_create(numero='6580000',defaults={'intitule':'Indemnités fictives — à valider'})[0]
                self.tracer_scenario('Colis','Autorisation explicite de l’indemnité fictive',lambda:
                    incident.autoriser(montant,compte,self.chef))
                self.tracer_scenario('Colis','Paiement de l’indemnité en espèces',lambda:
                    incident.payer(self.caisse_pour(montant,jour),self.chef))

    def scenarios_garage(self, jour, vehicule):
        from apps.garage.models_magasin import AchatMagasin, LigneAchatMagasin
        from apps.garage.models import OrdreReparation, LigneReparation
        def stock():
            a=AchatMagasin.objects.create(date=jour,paiement=AchatMagasin.ESPECES,caisse=self.caisse_pour(10000,jour),facture='SIM-STOCK')
            LigneAchatMagasin.objects.create(achat=a,article=self.articles['FILT'],quantite=2,prix_unitaire=5000)
            return a.valider(self.agent)
        self.tracer_scenario('Garage','Achat de pièces pour le stock : actif, sans charge véhicule',stock)
        def direct():
            a=AchatMagasin.objects.create(date=jour,paiement=AchatMagasin.ESPECES,caisse=self.caisse_pour(7000,jour),facture='SIM-DIRECT')
            LigneAchatMagasin.objects.create(achat=a,destination=LigneAchatMagasin.VEHICULE,vehicule=vehicule,
                designation='Pièce spécifique fictive',quantite=1,prix_unitaire=7000)
            return a.valider(self.agent)
        self.tracer_scenario('Garage','Achat directement consommé par un véhicule : une seule charge',direct)
        def reparation():
            o=OrdreReparation.objects.create(vehicule=vehicule,date_entree=jour,panne='Réparation interne fictive')
            LigneReparation.objects.create(ordre=o,nature=LigneReparation.MAGASIN,article=self.articles['FILT'],designation='Filtre',quantite=1)
            LigneReparation.objects.create(ordre=o,nature=LigneReparation.MAIN_OEUVRE_INTERNE,designation='Mécanicien salarié',prix_unitaire=5000)
            return o.cloturer(caisse=self.caisse_pour(0,jour),date=jour,utilisateur=self.agent)
        self.tracer_scenario('Garage','Réparation : stock vers charge véhicule ; main-d’œuvre interne sans double charge',reparation)
        def materiel():
            a=AchatMagasin.objects.create(date=jour,paiement=AchatMagasin.ESPECES,caisse=self.caisse_pour(20000,jour),facture='SIM-OUTIL')
            LigneAchatMagasin.objects.create(achat=a,destination=LigneAchatMagasin.IMMOBILISATION,
                designation='Outillage durable fictif',prix_unitaire=20000)
            return a.valider(self.agent)
        self.tracer_scenario('Garage','Matériel durable du garage : immobilisation, pas charge immédiate véhicule',materiel)

    def decomptes_metier(self, debut, fin):
        from apps.partenaires.models import ContratPartenaire, Decompte, DemandeRetrait, solde_partenaire
        for c in self.contrats:
            comparaisons={}
            ancienne=c.assiette_commission
            for base in (ContratPartenaire.RECETTES,ContratPartenaire.MARGE):
                c.assiette_commission=base
                e=Decompte.evaluer(c,debut,fin)
                comparaisons[base]={k:str(e[k]) for k in ('recettes','depenses','commission','montant_du')}
            c.assiette_commission=ancienne
            self.hypotheses.append({'periode':[str(debut),str(fin)],'contrat':c.numero,'vehicule':c.vehicule.immatriculation,
                'tiers':c.partenaire.code,'taux':'15','base_fictive_comptabilisee':ancienne,'comparaison_sans_ecriture':comparaisons,
                'avertissement':'Assiette réelle non confirmée. Marge signée, perte éventuelle à convenir. Aucun fixe ajouté.'})
            self.tracer_scenario('Partenaires','Arrêté du véhicule et crédit du compte tiers propriétaire',lambda:
                Decompte.calculer(c,debut,fin).approuver(self.chef,date=fin))
        for partenaire in {c.partenaire_id:c.partenaire for c in self.contrats}.values():
            disponible=solde_partenaire(partenaire,fin)
            if disponible<=0:
                continue
            montant=min(Decimal(100000),disponible)
            def retirer():
                r=DemandeRetrait(partenaire=partenaire,date=fin,montant=montant,
                    motif='Retrait mensuel fictif (dit salaire propriétaire), jamais une paie salariale').demander(self.agent)
                r.decider(True,self.chef)
                r.payer(self.caisse_pour(montant,fin),self.chef)
                return r
            self.tracer_scenario('Partenaires','Retrait mensuel en espèces : apurement du tiers, sans nouvelle charge',retirer)

    def ecrire_rapports_metier(self, chemin):
        if not self.profil_complet:
            return
        rapport={'fictif':True,'version':1,'avertissement':'15 % : assiette réelle à confirmer ; données, comptes et montants fictifs.',
                 'scenarios':self.scenarios,'comparaison_commission':self.hypotheses,'mesures_journalieres':self.mesures}
        cible=Path(chemin)
        cible.parent.mkdir(parents=True,exist_ok=True)
        cible.write_text(json.dumps(rapport,ensure_ascii=False,indent=2),encoding='utf-8')
        return rapport
