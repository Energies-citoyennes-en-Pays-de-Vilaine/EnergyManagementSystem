from credentials.db_credentials import db_credentials
from database.EMS_db_creator import execute_queries
from database.ELFE_db_types import *

def create_tables(credentials):
	tables_queries = [
		ELFE_BallonECS                      .get_create_table_str(ELFE_database_names["ELFE_BallonECS"                      ]),
		ELFE_ChauffageNonAsservi            .get_create_table_str(ELFE_database_names["ELFE_ChauffageNonAsservi"            ]),
		ELFE_EquipementPilote               .get_create_table_str(ELFE_database_names["ELFE_EquipementPilote"               ]),
		ELFE_VehiculeElectriqueGenerique    .get_create_table_str(ELFE_database_names["ELFE_VehiculeElectriqueGenerique"    ]),
		ELFE_Utilisateur					.get_create_table_str(ELFE_database_names["ELFE_Utilisateur"					]),		
		ELFE_Cohorte						.get_create_table_str(ELFE_database_names["cohorte_utilisateurs"				]),
		ELFE_Jour_HPHC						.get_create_table_str(ELFE_database_names["ELFE_Jour_HPHC"						]),
		# ELFE_BallonECSHeuresCreuses         .get_create_table_str(ELFE_database_names["ELFE_BallonECSHeuresCreuses"         ]),
		# ELFE_ChauffageAsservi               .get_create_table_str(ELFE_database_names["ELFE_ChauffageAsservi"               ]),
		# ELFE_ChauffageAsserviModeleThermique.get_create_table_str(ELFE_database_names["ELFE_ChauffageAsserviModeleThermique"]),
		# ELFE_MachineGenerique               .get_create_table_str(ELFE_database_names["ELFE_MachineGenerique"               ]),
		# ELFE_MachineGeneriqueCycle          .get_create_table_str(ELFE_database_names["ELFE_MachineGeneriqueCycle"          ]),
	]
	execute_queries(credentials, tables_queries)

if __name__ == "__main__":
	create_tables(db_credentials["ELFE"])