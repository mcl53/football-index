import datetime
from dateutil import relativedelta
from datetime import datetime, timedelta
import pytz
import secrets
from decimal import Decimal, ROUND_UP


def convert_date_to_str(date):
	year = date.year
	month = "{:02d}".format(date.month)
	day = "{:02d}".format(date.day)
	date_string = f"{year}{month}{day}"
	return date_string


def convert_datestr_to_timestamp(datestr):
	year = int(datestr[0:4])
	month = int(datestr[4:6])
	day = int(datestr[6:])

	date = datetime(year, month, day)
	tz = pytz.timezone(secrets.timezone)
	tz_aware_date = tz.localize(date, is_dst=None)
	ts = datetime.timestamp(tz_aware_date) + tz_aware_date.tzinfo._dst.seconds

	return ts


def return_dates(months_prior=0):
	date = datetime.now()

	if months_prior != 0:
		first_date = date + relativedelta.relativedelta(months=-months_prior)

	else:
		first_date = datetime(2019, 10, 22)

	delta = date - first_date
	dates = []

	for i in range(0, delta.days + 1):
		this_date = first_date + timedelta(days=i)
		this_date_string = convert_date_to_str(this_date)
		dates.append(this_date_string)

	return dates


def to_currency(value):
	return Decimal(value).quantize(Decimal(".01"), rounding=ROUND_UP)