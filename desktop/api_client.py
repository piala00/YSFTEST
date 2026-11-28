"""Client HTTP de l'API REST de l'ERP (authentification par jeton)."""
import requests


class ApiError(Exception):
    pass


class ErpApi:
    def __init__(self, base_url, token=None, timeout=20):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()

    # --- Bas niveau ------------------------------------------------------
    def _headers(self):
        return {"Authorization": f"Token {self.token}"} if self.token else {}

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}/api/{path.lstrip('/')}"
        try:
            response = self.session.request(method, url, headers=self._headers(), timeout=self.timeout, **kwargs)
        except requests.RequestException as exc:
            raise ApiError(f"Serveur injoignable : {exc}") from exc
        if response.status_code == 401:
            raise ApiError("Session expirée ou identifiants invalides.")
        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text[:300]
            raise ApiError(self._format_erreur(detail))
        return response.json() if response.content else None

    @staticmethod
    def _format_erreur(detail):
        if isinstance(detail, dict):
            parties = []
            for cle, valeur in detail.items():
                valeur = " ".join(map(str, valeur)) if isinstance(valeur, list) else str(valeur)
                parties.append(valeur if cle in ("detail", "non_field_errors") else f"{cle} : {valeur}")
            return "\n".join(parties)
        if isinstance(detail, list):
            return "\n".join(map(str, detail))
        return str(detail)

    def get(self, path, **params):
        return self._request("GET", path, params={k: v for k, v in params.items() if v not in (None, "")})

    def post(self, path, data=None):
        return self._request("POST", path, json=data or {})

    def lister(self, path, **params):
        """Récupère toutes les pages d'une liste paginée."""
        data = self.get(path, **params)
        if isinstance(data, list):
            return data
        resultats = list(data["results"])
        while data.get("next"):
            page = int(data["next"].split("page=")[1].split("&")[0])
            data = self.get(path, page=page, **params)
            resultats.extend(data["results"])
        return resultats

    # --- Authentification ----------------------------------------------
    def connecter(self, utilisateur, mot_de_passe):
        try:
            response = self.session.post(f"{self.base_url}/api/token/",
                                         data={"username": utilisateur, "password": mot_de_passe}, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ApiError(f"Serveur injoignable : {exc}") from exc
        if response.status_code != 200:
            raise ApiError("Identifiants incorrects.")
        self.token = response.json()["token"]
        return self.token

    # --- Métier ----------------------------------------------------------
    def tiers(self, type_tiers, q=""):
        return self.lister("tiers/", type=type_tiers, q=q)

    def articles(self, q=""):
        return self.lister("articles/", q=q)

    def documents(self, domaine, type_document="", q=""):
        return self.lister("documents/", domaine=domaine, type=type_document, q=q)

    def document(self, pk):
        return self.get(f"documents/{pk}/")

    def creer_document(self, data):
        return self.post("documents/", data)

    def valider_document(self, pk):
        return self.post(f"documents/{pk}/valider/")

    def transformer_document(self, pk, type_cible):
        return self.post(f"documents/{pk}/transformer/", {"type_cible": type_cible})

    def journaux(self):
        return self.get("journaux/")

    def creer_reglement(self, data):
        return self.post("reglements/", data)

    def dashboard(self):
        return self.get("reporting/dashboard/")

    def balance(self, du=None, au=None, compte_debut="", compte_fin=""):
        return self.get("reporting/balance/", du=du, au=au, compte_debut=compte_debut, compte_fin=compte_fin)

    def bilan(self, au=None):
        return self.get("reporting/bilan/", au=au)

    def compte_resultat(self, du=None, au=None):
        return self.get("reporting/compte-resultat/", du=du, au=au)

    def balance_agee(self, type_tiers="CLIENT"):
        return self.get("reporting/balance-agee/", type=type_tiers)

    def navigation(self, module):
        return self.get("navigation/", module=module)
