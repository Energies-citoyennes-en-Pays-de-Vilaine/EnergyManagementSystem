#!/bin/bash
{
set -e
CONFIG_FILENAME="EMS_systemd_config.txt"
CONFIG_FOLDER="/etc/ems"
HAS_TO_INSTALL_ANACONDA=1
HAS_TO_UPDATE=1
HAS_TO_INSTALL_POSTGRES=1
HAS_TO_DROP_DATABASE=0
HAS_TO_CREATE_DATABASE=1
HAS_TO_CREATE_OUT_DATABASE=1
HAS_TO_GRANT_PERMISSIONS=1
HAS_TO_INSTALL_MILP=1
HAS_TO_CREATE_SERVICES=1
HAS_TO_INSTALL_PREDICTION_HISTORIZER=0

EMS_DB="ems_db"
EMS_USER="ems"
EMS_DB_CONFIG_FILENAME="db_credentials.py"

EMS_HISTO_PASS="0"
#if EMS_HISTO_PASS is exactly '0', then it will be changed
EMS_HISTO_USER="$EMS_USER"
EMS_HISTO_HOST="localhost"
EMS_HISTO_DB="$EMS_DB"

ELFE_OUT_PASS="pass"
ELFE_OUT_USER="testeu"
ELFE_OUT_HOST="localhost"
ELFE_OUT_DB="ems_sortie_test"
COMMAND_USER="testusr"
#next line comes from internal value from EMS, do not modify
EMS_RESULT_TABLE="result"

ELFE_DB="elfe_coordo"
ELFE_OPTIONS="-c search_path=$ELFE_DB,public"

EMSFOLDER="$(echo $PWD)"
# BASHRCPATH="$(echo $HOME)/.bashrc"
BASHRCPATH="/home/ens/.bashrc"
if [ "$EUID" -ne 0 ]
	then echo "please run installer as root"
	exit -1
fi

if [ "$HAS_TO_UPDATE" -ne 0 ]
	then
	echo "running apt update and upgrade for you"
	apt update
	apt upgrade -y
	apt autoremove -y
fi
echo "installing the environnement"

if [ "$HAS_TO_INSTALL_ANACONDA" -ne 0 ]
	then
	echo "installing the necessary packets for anaconda"
	# apt-get install -y libgl1-mesa-glx libegl1-mesa libxrandr2 libxrandr2 libxss1 libxcursor1 libxcomposite1 libasound2 libxi6 libxtst6
	echo "downloading anaconda installation script in /tmp"
	wget "https://repo.anaconda.com/archive/Anaconda3-2025.12-2-Linux-x86_64.sh" -O /tmp/anaconda_installer.sh
	chmod +x /tmp/anaconda_installer.sh
	/tmp/anaconda_installer.sh -b
	eval "$(~/anaconda3/bin/conda shell.bash hook)"
	conda init bash
	rm /tmp/anaconda_installer.sh
fi

if [ "$HAS_TO_INSTALL_MILP" -ne 0 ] || [ "$HAS_TO_INSTALL_ANACONDA" -ne 0 ]
	then
	echo "installing milp environnement"
	echo "sourcing $BASHRCPATH"
	source "$BASHRCPATH"
	conda env create -f "$EMSFOLDER/anaconda.yml"
fi

echo "sourcing bashrc at $BASHRCPATH"
echo "[WARNING] some bashrc files disable the non-interactive mode to use them, if the below section fails try there first $BASHRCPATH"
source $BASHRCPATH
echo "activating milp env"
conda activate milp

if [ "$HAS_TO_INSTALL_POSTGRES" -ne 0 ]
	then
	echo "installing postgresql"
	apt install -y postgresql
	echo "starting postgres"
	pg_ctlcluster 18 main start
fi

if [ "$HAS_TO_CREATE_OUT_DATABASE" -ne 0 ]
	then
	echo "creating output database"
	su - postgres -c "export PGPASSWORD=\"$ELFE_OUT_PASS\"; psql -h $ELFE_OUT_HOST -d postgres -U $ELFE_OUT_USER -c \"CREATE DATABASE $ELFE_OUT_DB WITH OWNER $ELFE_OUT_USER;\""
	if [ "$HAS_TO_GRANT_PERMISSIONS" -ne 0 ]
		then
		echo "granting database connection permissions to user $COMMAND_USER"
		su - postgres -c "export PGPASSWORD=\"$ELFE_OUT_PASS\"; psql -h $ELFE_OUT_HOST -d $ELFE_OUT_DB -U $ELFE_OUT_USER -c \"GRANT CONNECT ON DATABASE $ELFE_OUT_DB TO $COMMAND_USER;\""
		fi
fi

if [ "$HAS_TO_INSTALL_POSTGRES" -ne 0 ] || [ "$HAS_TO_CREATE_DATABASE" -ne 0 ]
	then
	#cleanup
	echo "creating database"
	if [ "$HAS_TO_DROP_DATABASE" -ne 0 ]
	then
		echo "dropping database"
		su - postgres -c "psql -c \"DROP DATABASE $EMS_DB;\""
		su - postgres -c "psql -c \"DROP USER $EMS_USER;\""
	fi

	POSTGRES_PASSWORD="$(LC_ALL=C tr -dc '[:alnum:]' < /dev/urandom | head -c20)"
	echo "setting encryption method for password as postgres-s default is really bad"
	su - postgres -c "psql -c \"SET password_encryption  = 'scram-sha-256';\"" >/dev/null
	echo "creating user for EMS ($EMS_USER)"
	su - postgres -c "psql -c \"CREATE USER $EMS_USER WITH ENCRYPTED PASSWORD '$POSTGRES_PASSWORD';\"">/dev/null
	echo "creating database for EMS ($EMS_DB)"
	su - postgres -c "psql -c \"CREATE DATABASE $EMS_DB WITH OWNER $EMS_USER;\"">/dev/null
	echo "copying the db_config file to ($EMS_DB_CONFIG_FILENAME) to populate it with the EMS password"
	cp "$EMSFOLDER/credentials/db_credentials_example.py" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	echo "setting up EMS config for EMS inner database"
	sed -i "s/myEMSSuperHost/localhost/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myEMSSuperDatabase/$EMS_DB/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myEMSSuperUser/$EMS_USER/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myEMSSuperPassword/$POSTGRES_PASSWORD/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"

	echo "setting up EMS config for EMS output database"
	sed -i "s/myOutSuperHost/$ELFE_OUT_HOST/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myOutSuperDatabase/$ELFE_OUT_DB/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myOutSuperUser/$ELFE_OUT_USER/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myOutSuperPassword/$ELFE_OUT_PASS/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	if [ "$HAS_TO_INSTALL_PREDICTION_HISTORIZER" -ne 0 ]
	then
		echo "setting up EMS config for EMS historizer database"
		if [ "$EMS_HISTO_PASS" = "0" ]
		then
			echo "using newly generated elfe password"
			EMS_HISTO_PASS="$POSTGRES_PASSWORD"
		fi
		sed -i "s/myHistoSuperHost/$EMS_HISTO_HOST/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
		sed -i "s/myHistoSuperDatabase/$EMS_HISTO_DB/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
		sed -i "s/myHistoSuperUser/$EMS_HISTO_USER/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
		sed -i "s/myHistoSuperPassword/$EMS_HISTO_PASS/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	fi
	echo "setting up EMS config for ELFE database"
	sed -i "s/myELFESuperHost/$ELFE_OUT_HOST/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myELFESuperDatabase/$ELFE_DB/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myELFESuperUser/$ELFE_OUT_USER/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myELFESuperPassword/$ELFE_OUT_PASS/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"
	sed -i "s/myELFESuperOptions/$ELFE_OPTIONS/g" "$EMSFOLDER/credentials/$EMS_DB_CONFIG_FILENAME"

	echo "creating tables for EMS inner database"
	python -m database.EMS_db_creator
	echo "creating tables for EMS output database"
	python -m database.EMS_OUT_db_creator
	if [ "$HAS_TO_INSTALL_PREDICTION_HISTORIZER" -ne 0 ]
	then
		echo "creating history database"
		python -m database.history_db_creator
	fi
	if [ "$HAS_TO_GRANT_PERMISSIONS" -ne 0 ]
		then
		echo "granting select permission to $COMMAND_USER on table $EMS_RESULT_TABLE"
		su - postgres -c "export PGPASSWORD=\"$ELFE_OUT_PASS\"; psql -h $ELFE_OUT_HOST -d $ELFE_OUT_DB -U $ELFE_OUT_USER -c \"GRANT SELECT ON TABLE $EMS_RESULT_TABLE TO $COMMAND_USER;\""
	fi
fi


echo "creating the config folder $CONFIG_FOLDER"
mkdir -p $CONFIG_FOLDER
echo "creating environnement config file for EMS services to launch"
echo "assumes this is where the EMS will live ($EMSFOLDER)"
echo "EMSFOLDER=\"$(echo $EMSFOLDER)\"">$CONFIG_FILENAME
echo "assumes the bashrc file is in there ($BASHRCPATH)"
echo "BASHRCPATH=\"$BASHRCPATH\"">>$CONFIG_FILENAME
echo "moving the config file to its location $CONFIG_FOLDER/$CONFIG_FILENAME"

mv $CONFIG_FILENAME $CONFIG_FOLDER/$CONFIG_FILENAME

if [ "$HAS_TO_CREATE_SERVICES" -ne 0 ]
	then
	echo "copying the services"
	for f in $(ls "$EMSFOLDER/services/systemd_files"); do
		cp "$EMSFOLDER/services/systemd_files/$f" "/etc/systemd/system"
	done
	echo "installing services"
	echo "installing ECS acquisition service"
	systemctl enable ECS_acquisition.timer
	systemctl start ECS_acquisition.timer

	echo "installing EMS launcher service"
	systemctl enable EMS_launcher.timer
	systemctl start EMS_launcher.timer

	echo "installing learning cleaner service"
	systemctl enable learning_cleaner.timer
	systemctl start learning_cleaner.timer

	echo "installing machine cycle learner service"
	systemctl enable machine_cycle_learner.timer
	systemctl start machine_cycle_learner.timer

	echo "installing power prediction service"
	systemctl enable power_prediction.timer
	systemctl start power_prediction.timer

	echo "installing user temp service"
	systemctl enable user_temp.timer
	systemctl start user_temp.timer

	echo "installing meteo concept service"
	systemctl enable Meteo_concept.timer
	systemctl start Meteo_concept.timer

	echo "installing zabbix prevision getter"
	systemctl enable prevision_getter.timer
	systemctl start prevision_getter.timer

	if [ "$HAS_TO_INSTALL_PREDICTION_HISTORIZER" -ne 0 ]
	then
		echo "installing the power prediction historizer service"
		systemctl enable prediction_historizer.service
		systemctl start prediction_historizer.service
	fi
fi
} 2>&1 | tee install.log