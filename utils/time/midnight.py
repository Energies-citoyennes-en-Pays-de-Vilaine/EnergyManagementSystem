from datetime import datetime, timedelta, timezone

def get_midnight_date(timestamp : int) -> datetime:
	#TODO_ELFE this have to be relocated in a specific time module
	date : datetime = datetime.fromtimestamp(timestamp, timezone.utc)
	midnight : datetime = date - timedelta(0, date.second + date.hour * 3600 + date.minute * 60)
	return midnight

def get_midnight_timestamp(timestamp : int) -> int:
	date : datetime = datetime.fromtimestamp(timestamp, timezone.utc)
	midnight : datetime = date - timedelta(0, date.second + date.hour * 3600 + date.minute * 60)
	return int(midnight.timestamp())