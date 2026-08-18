from typing import Dict

poids = {
    "ACI_1"     : {"ACI": 0.01, "ACCHC": 1, "ACCHP": 5, "IMPHC": 10, "IMPHP": 50},
    "default"   : {"ACI": 0.01, "ACCHC": 1, "ACCHP": 5, "IMPHC": 10, "IMPHP": 50},
}

def get_poids(cohorte_id: str) -> Dict[str, int]:
    cohorte = "default"
    if cohorte_id in poids.keys():
        cohorte = cohorte_id
    return poids[cohorte]

