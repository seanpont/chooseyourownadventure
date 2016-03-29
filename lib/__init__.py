import datetime

def format_datetime(dt):
  if isinstance(dt, datetime.datetime):
    return dt.strftime("%Y-%m-%d %H:%M:%S")
  else:
    return None
