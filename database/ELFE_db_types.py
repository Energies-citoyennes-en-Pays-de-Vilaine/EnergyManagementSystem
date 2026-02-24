from database.annotations import DBAnnotation, serializableThroughDatabase, PrimaryAutoInt
from dataclasses import dataclass
from utils.time.period import Period
from typing import List
from datetime import datetime

ELFE_database_names = {
	"ELFE_BallonECS"                       : "equipement_pilote_ballon_ecs",
	"ELFE_BallonECSHeuresCreuses"          : "equipement_pilote_ballon_ecs_heures_creuses",
	"ELFE_ChauffageAsservi"                : "equipement_pilote_chauffage_asservi",
	"ELFE_ChauffageAsserviModeleThermique" : "chauffage_asservi_modele_thermique",
	"ELFE_ChauffageNonAsservi"             : "equipement_pilote_chauffage_non_asservi",
	"ELFE_EquipementPilote"                : "equipement_pilote_ou_mesure",
	"ELFE_MachineGenerique"                : "equipement_pilote_machine_generique",
	"ELFE_MachineGeneriqueCycle"           : "equipement_pilote_machine_generique_cycle",
	"ELFE_VehiculeElectriqueGenerique"     : "equipement_pilote_vehicule_electrique_generique",
}

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_EquipementPilote():
	Id                                  : PrimaryAutoInt
	equipement_pilote_specifique_id     : int
	equipement_pilote_ou_mesure_type_id : int
	equipement_pilote_ou_mesure_mode_id : int
	etat_controle_id                    : int
	etat_commande_id                    : int
	nom_humain                          : str
	description                         : str
	typologie_installation_domotique_id : int
	ems_consigne_marche                 : bool
	timestamp_derniere_mise_en_marche   : int
	timestamp_derniere_programmation    : int
	utilisateur                         : str

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_ChauffageAsserviModeleThermique():
	Id 	        : PrimaryAutoInt
	nom         : str
	description : str


@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_Chauffage():
	prog_semaine_periode_1_confort_actif       : bool
	prog_semaine_periode_1_confort_heure_debut : int
	prog_semaine_periode_1_confort_heure_fin   : int
	prog_semaine_periode_2_confort_actif       : bool
	prog_semaine_periode_2_confort_heure_debut : int
	prog_semaine_periode_2_confort_heure_fin   : int
	prog_weekend_periode_1_confort_actif       : bool
	prog_weekend_periode_1_confort_heure_debut : int
	prog_weekend_periode_1_confort_heure_fin   : int
	prog_weekend_periode_2_confort_actif       : bool
	prog_weekend_periode_2_confort_heure_debut : int
	prog_weekend_periode_2_confort_heure_fin   : int
	def get_periods (self, midnight_date : datetime) -> List[Period]:
		periods : List[Period] = []
		if midnight_date.weekday() >= 5:
			if self.prog_weekend_periode_1_confort_actif == True:
				periods.append(Period(int(midnight_date.timestamp()) + self.prog_weekend_periode_1_confort_heure_debut, int(midnight_date.timestamp()) + self.prog_weekend_periode_1_confort_heure_fin))
			if self.prog_weekend_periode_2_confort_actif == True:
				periods.append(Period(int(midnight_date.timestamp()) + self.prog_weekend_periode_2_confort_heure_debut, int(midnight_date.timestamp()) + self.prog_weekend_periode_2_confort_heure_fin))
		else:
			if self.prog_semaine_periode_1_confort_actif == True:
				periods.append(Period(int(midnight_date.timestamp()) + self.prog_semaine_periode_1_confort_heure_debut, int(midnight_date.timestamp()) + self.prog_semaine_periode_1_confort_heure_fin))
			if self.prog_semaine_periode_2_confort_actif == True:
				periods.append(Period(int(midnight_date.timestamp()) + self.prog_semaine_periode_2_confort_heure_debut, int(midnight_date.timestamp()) + self.prog_semaine_periode_2_confort_heure_fin))
		return periods
@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_ChauffageAsservi(ELFE_Chauffage):
	Id                                         : int
	equipement_pilote_ou_mesure_id             : int
	temperature_eco                            : int
	temperature_confort                        : int
	prog_semaine_periode_1_confort_actif       : bool
	prog_semaine_periode_1_confort_heure_debut : int
	prog_semaine_periode_1_confort_heure_fin   : int
	prog_semaine_periode_2_confort_actif       : bool
	prog_semaine_periode_2_confort_heure_debut : int
	prog_semaine_periode_2_confort_heure_fin   : int
	prog_weekend_periode_1_confort_actif       : bool
	prog_weekend_periode_1_confort_heure_debut : int
	prog_weekend_periode_1_confort_heure_fin   : int
	prog_weekend_periode_2_confort_actif       : bool
	prog_weekend_periode_2_confort_heure_debut : int
	prog_weekend_periode_2_confort_heure_fin   : int
	delta_temp_maximale_temp_demandee          : int
	puissance                                  : int
	modele_thermique_id                        : int
	mesures_puissance_elec_id                  : int
	mesure_temperature_id                      : int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_ChauffageNonAsservi(ELFE_Chauffage):
	Id                                         : PrimaryAutoInt
	equipement_pilote_ou_mesure_id             : int
	prog_semaine_periode_1_confort_actif       : bool
	prog_semaine_periode_1_confort_heure_debut : int
	prog_semaine_periode_1_confort_heure_fin   : int
	prog_semaine_periode_2_confort_actif       : bool
	prog_semaine_periode_2_confort_heure_debut : int
	prog_semaine_periode_2_confort_heure_fin   : int
	prog_weekend_periode_1_confort_actif       : bool
	prog_weekend_periode_1_confort_heure_debut : int
	prog_weekend_periode_1_confort_heure_fin   : int
	prog_weekend_periode_2_confort_actif       : bool
	prog_weekend_periode_2_confort_heure_debut : int
	prog_weekend_periode_2_confort_heure_fin   : int
	puissance_moyenne_eco                      : int
	puissance_moyenne_confort                  : int
	pourcentage_eco_force                      : int
	mesures_puissance_elec_id                  : int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_MachineGenerique():
	Id                                           : PrimaryAutoInt
	equipement_pilote_ou_mesure_id               : int
	timestamp_de_fin_souhaite                    : int
	delai_attente_maximale_apres_fin             : int
	cycle_equipement_pilote_machine_generique_id : int
	mesures_puissance_elec_id                    : int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_VehiculeElectriqueGenerique():
	Id                                           : PrimaryAutoInt
	equipement_pilote_ou_mesure_id               : int
	pourcentage_charge_restant                   : int
	pourcentage_charge_finale_minimale_souhaitee : int
	duree_de_charge_estime                       : int
	timestamp_dispo_souhaitee                    : int
	puissance_de_charge                          : int
	capacite_de_batterie                         : int
	mesures_puissance_elec_id                    : int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_MachineGeneriqueCycle():
	Id                                     : PrimaryAutoInt
	equipement_pilote_machine_generique_id : int
	duree_cycle                            : int
	nom                                    : str
	description                            : str
	timestamp_dernier_declenchement        : int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_BallonECS():
	Id                                : PrimaryAutoInt
	equipement_pilote_ou_mesure_id    : int
	volume_ballon                     : int
	puissance_chauffe                 : int
	mesures_puissance_elec_id         : int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_BallonECSHeuresCreuses():
	Id                              : PrimaryAutoInt
	equipement_pilote_ballon_ecs_id : int
	nom                             : str
	description                     : str
	actif                           : bool
	debut                           : int
	fin                             : int

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_EquipementType:
	Id : PrimaryAutoInt
	nom : str
	nom_humain : str
	description : str

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_EtatControleType:
	Id : PrimaryAutoInt
	nom : str
	nom_humain : str
	description : str

@serializableThroughDatabase
@dataclass(init=True, repr=True)
class ELFE_EtatCommandeType:
	Id : PrimaryAutoInt
	nom : str
	nom_humain : str
	description : str
