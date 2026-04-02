
import typing
from typing import Union, List

class DBAnnotation():
	is_db_primary    : bool
	is_db_nullable   : bool
	is_db_list       : bool
	db_element_count : int
	def __init__(self) -> None:
		self.is_db_primary  = False
		self.is_db_nullable = False
		self.is_db_list     = False
		db_element_count    = 0


def create_DB_Annotation(*, is_primary = False, is_nullable = False, is_db_list = False, db_element_count = 0):
	class toReturn(DBAnnotation):
		pass
	toReturn.is_db_nullable   = is_nullable
	toReturn.is_db_primary    = is_primary
	toReturn.is_db_list       = is_db_list
	toReturn.db_element_count = db_element_count 
	return toReturn
class PrimaryAutoInt(int):
	pass

def serializableThroughDatabase(clas):
	def get_create_table_str(name, schema:str = ""):
		args = []
		annotations = clas.__annotations__
		for key in annotations.keys():
			base_type = annotations[key]
			dbannotation = DBAnnotation()
			if type(base_type) == typing._UnionGenericAlias:
				dbannotation = base_type.__args__[1]
				base_type = base_type.__args__[0]
			if not dbannotation.is_db_list:
				if (base_type == PrimaryAutoInt):
					args.append(f"{key} SERIAL PRIMARY KEY")
				elif (base_type == int):
					args.append(f"{key} INTEGER {'PRIMARY KEY' if dbannotation.is_db_primary else ''} {'NOT NULL' if not dbannotation.is_db_nullable else ''}")
				elif (base_type == bool):
					args.append(f"{key} BOOLEAN {'NOT NULL' if not dbannotation.is_db_nullable else ''}")
				elif (base_type == str):
					args.append(f"{key} TEXT    {'PRIMARY KEY' if dbannotation.is_db_primary else ''} {'NOT NULL' if not dbannotation.is_db_nullable else ''}")
				elif (base_type == float):
					args.append(f"{key} REAL    {'PRIMARY KEY' if dbannotation.is_db_primary else ''} {'NOT NULL' if not dbannotation.is_db_nullable else ''}")
				else:
					print(annotations[key])
			else:
				for i in range(dbannotation.db_element_count):
					if (base_type == int):
						args.append(f"{key}_{i} INTEGER {'NOT NULL' if not dbannotation.is_db_nullable else ''}")
					elif (base_type == bool):
						args.append(f"{key}_{i} BOOLEAN {'NOT NULL' if not dbannotation.is_db_nullable else ''}")
					elif (base_type == str):
						args.append(f"{key}_{i} TEXT    {'NOT NULL' if not dbannotation.is_db_nullable else ''}")
					elif(base_type == float):
						args.append(f"{key}_{i} REAL    {'NOT NULL' if not dbannotation.is_db_nullable else ''}")
					else:
						print(annotations[key])
			
		return (f" CREATE TABLE IF NOT EXISTS {schema+("." if schema != "" else "")}{name} ({', '.join(args)});")

	def get_append_in_table_str(self, name):
		args = []
		values = []
		annotations = clas.__annotations__
		primary_key = None
		for key in annotations.keys():
			base_type = annotations[key]
			dbannotation = DBAnnotation()
			if type(base_type) == typing._UnionGenericAlias:
				dbannotation = base_type.__args__[1]
				base_type = base_type.__args__[0]
			if dbannotation.is_db_primary:
				primary_key = key
			if (base_type == PrimaryAutoInt):
				primary_key = key
				continue
			
			if (self.__getattribute__(key) is None):
				if (dbannotation.is_db_nullable):
					continue
				else:
					raise Exception(f"try to serialize not nullable with none ({key})")
			if not dbannotation.is_db_list:
				if (base_type == int):
					args.append(f"{key}")
					values.append(self.__getattribute__(key))
				elif (base_type == float):
					args.append(f"{key}")
					values.append(self.__getattribute__(key))
				elif (base_type == str):
					args.append(f"{key}")
					values.append(self.__getattribute__(key))
				elif (base_type == bool):
					args.append(f"{key}")
					values.append('1' if self.__getattribute__(key) == True else '0')
				else:
					print(annotations[key])
			else:
				for i in range(dbannotation.db_element_count):
					if (base_type == int):
						args.append(f"{key}_{i}")
						values.append(self.__getattribute__(key)[i])
					elif (base_type == float):
						args.append(f"{key}_{i}")
						values.append(self.__getattribute__(key)[i])
					elif (base_type == str):
						args.append(f"{key}_{i}")
						values.append(self.__getattribute__(key)[i])
					elif (base_type == bool):
						args.append(f"{key}_{i}")
						values.append('1' if self.__getattribute__(key)[i] == True else '0')
					else:
						print(annotations[key])
		if primary_key is None:
			print("warning, no primary key registered")
			return (f"INSERT INTO {name} ({', '.join(args)}) VALUES ({', '.join(['%s' for s in args])});", values)
		return (f"INSERT INTO {name} ({', '.join(args)}) VALUES ({', '.join(['%s' for s in args])}) RETURNING {primary_key};", values)

	def get_update_in_table_str(self, name):
		args = []
		values = []
		annotations = clas.__annotations__
		primary_key   = ""
		primary_value = -1
		for key in annotations.keys():
			base_type = annotations[key]
			dbannotation = DBAnnotation()
			if type(base_type) == typing._UnionGenericAlias:
				dbannotation = base_type.__args__[1]
				base_type = base_type.__args__[0]
			if (base_type == PrimaryAutoInt or dbannotation.is_db_primary):
				primary_key = key
				primary_value = self.__getattribute__(key)
				continue
			if (self.__getattribute__(key) is None):
				if (dbannotation.is_db_nullable):
					continue
				else:
					raise Exception(f"try to serialize not nullable with none ({key})")
			if not dbannotation.is_db_list:
				if (base_type == int):
					args.append(f"{key}")
					values.append(self.__getattribute__(key))
				elif (base_type == float):
					args.append(f"{key}")
					values.append(self.__getattribute__(key))
				elif (base_type == str):
					args.append(f"{key}")
					values.append(self.__getattribute__(key))
				elif (base_type == bool):
					args.append(f"{key}")
					values.append('1' if self.__getattribute__(key) == True else '0')
				else:
					print(annotations[key])
			else:
				for i in range(dbannotation.db_element_count):
					if (base_type == int):
						args.append(f"{key}_{i}")
						values.append(self.__getattribute__(key)[i])
					elif (base_type == int):
						args.append(f"{key}")
						values.append(self.__getattribute__(key))
					elif (base_type == str):
						args.append(f"{key}_{i}")
						values.append(self.__getattribute__(key)[i])
					elif (base_type == bool):
						args.append(f"{key}_{i}")
						values.append('1' if self.__getattribute__(key)[i] == True else '0')
					else:
						print(annotations[key])

		return (f"UPDATE {name} SET {', '.join([s + '=%s' for s in args])} WHERE {primary_key} = %s;", values + [primary_value])

	def get_create_or_update_in_table_str(self, name:str, schema:str = ""):
		args = []
		values = []
		annotations = clas.__annotations__
		primary_key   = ""
		primary_value = -1
		for key in annotations.keys():
			base_type = annotations[key]
			dbannotation = DBAnnotation()
			if type(base_type) == typing._UnionGenericAlias:
				dbannotation = base_type.__args__[1]
				base_type = base_type.__args__[0]
			if (base_type == PrimaryAutoInt or dbannotation.is_db_primary):
				primary_key = key
				primary_value = self.__getattribute__(key)
				continue
			if (self.__getattribute__(key) is None):
				if (dbannotation.is_db_nullable):
					continue
				else:
					raise Exception(f"try to serialize not nullable with none ({key})")
			if not dbannotation.is_db_list:
				if (base_type == int):
					args.append(f"{key}")
					values.append(self.__getattribute__(key))
				elif (base_type == float):
					args.append(f"{key}")
					values.append(self.__getattribute__(key))
				elif (base_type == str):
					args.append(f"{key}")
					values.append(self.__getattribute__(key))
				elif (base_type == bool):
					args.append(f"{key}")
					values.append('1' if self.__getattribute__(key) == True else '0')
				else:
					print(annotations[key])
			else:
				for i in range(dbannotation.db_element_count):
					if (base_type == int):
						args.append(f"{key}_{i}")
						values.append(self.__getattribute__(key)[i])
					elif (base_type == float):
						args.append(f"{key}")
						values.append(self.__getattribute__(key))
					elif (base_type == str):
						args.append(f"{key}_{i}")
						values.append(self.__getattribute__(key)[i])
					elif (base_type == bool):
						args.append(f"{key}_{i}")
						values.append('1' if self.__getattribute__(key)[i] == True else '0')
					else:
						print(annotations[key])
		return (f"INSERT INTO {schema+("." if schema != "" else "")}{name} ({', '.join([primary_key] + args)}) VALUES ({', '.join(['%s' for s in [primary_key] + args])}) ON CONFLICT ({primary_key}) DO UPDATE SET {', '.join([s + '=%s' for s in args])};", [primary_value] + values + values)


	def create_from_select_output(output):
		obj = {}
		annotations = clas.__annotations__
		j = 0
		for i in range(len(list(annotations.keys()))):
			key = list(annotations.keys())[i]

			base_type = annotations[key]
			dbannotation = DBAnnotation()
			if type(base_type) == typing._UnionGenericAlias:
				dbannotation = base_type.__args__[1]
				base_type = base_type.__args__[0]
			if not dbannotation.is_db_list:
				if (base_type == int):
					obj[list(annotations.keys())[i]] = int(output[j])
				elif (base_type == bool):
					obj[list(annotations.keys())[i]] = bool(output[j])
				elif (base_type == float):
					obj[list(annotations.keys())[i]] = float(output[j])
				else:
					obj[list(annotations.keys())[i]] = output[j]
				j = j + 1
			else:
				obj[list(annotations.keys())[i]] = [0] * dbannotation.db_element_count
				for k in range(dbannotation.db_element_count):
					if (base_type == int):
						obj[list(annotations.keys())[i]][k] = int(output[j])
					elif (base_type == float):
						obj[list(annotations.keys())[i]] = float(output[j])
					elif (base_type == bool):
						obj[list(annotations.keys())[i]][k] = bool(output[j])
					else:
						obj[list(annotations.keys())[i]][k] = output[j]
					j = j + 1
		return clas(**obj)
	
	clas.get_update_in_table_str = get_update_in_table_str
	clas.get_append_in_table_str = get_append_in_table_str
	clas.get_create_table_str    = get_create_table_str
	clas.get_create_or_update_in_table_str = get_create_or_update_in_table_str
	clas.create_from_select_output = create_from_select_output
	return clas