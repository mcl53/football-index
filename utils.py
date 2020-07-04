import datetime
from dateutil import relativedelta


def convert_date_to_str(date):
	year = date.year
	month = "{:02d}".format(date.month)
	day = "{:02d}".format(date.day)
	date_string = f"{year}{month}{day}"
	return date_string


def return_dates(months_prior=1):
	date = datetime.datetime.now()
	one_month_ago = date + relativedelta.relativedelta(months=-months_prior)
	delta = date - one_month_ago
	dates = []
	
	for i in range(1, delta.days + 1):
		this_date = one_month_ago + datetime.timedelta(days=i)
		this_date_string = convert_date_to_str(this_date)
		dates.append(this_date_string)
	
	return dates
