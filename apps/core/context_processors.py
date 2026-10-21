from .models import Exercice, Societe


def societe(request):
    if not request.user.is_authenticated:
        return {}
    return {"societe": Societe.get(), "exercice_courant": Exercice.courant()}
