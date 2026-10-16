"""
Modèles de réponse de l'API (response_model des routes, cf. app/api/v1/router.py).
"""
from pydantic import BaseModel, Field


class ExampleKPIValue(BaseModel):
    valeur: int = Field(..., description="Nombre de lignes sur la période")
    montant_total: float = Field(..., description="Somme de `amount` sur la période")


class ExampleKPIResponse(BaseModel):
    data: ExampleKPIValue
