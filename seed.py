""" Autoloads database with QUANDL API data, risk profiles, profile allocations, fake user profiles and banking information """

import json, urllib, csv
import model
from model import User, UserBanking, RiskProfile, ProfileAllocation,Ticker, Price
from datetime import datetime

def load_risk_profs(session):
	filename = open("./seed_data/risk_profiles.csv")
	for line in filename:
		name = line.strip()
	 	new_risk_profile = RiskProfile(name=name)
		session.add(new_risk_profile)
	session.commit()

def load_prof_allocs(session):
	filename = open("./seed_data/profile_allocations.csv")
	for line in filename:
		data = line.strip().split(",")
		risk_profile_id = data[0]
		ticker_id = data[1]
		ticker_weighting = data[2]
	 	new_profile_allocation = ProfileAllocation(risk_profile_id=risk_profile_id, 
	 		ticker_id=ticker_id, ticker_weight_percent=ticker_weighting)
		session.add(new_profile_allocation)
	session.commit()

# ticker_list = ["NYSEARCA_VV", "NYSEARCA_VB", "NYSEARCA_VEU", 
# 	"NYSEARCA_BIV", "NYSEARCA_BSV", "NYSEARCA_VWO", "NYSEARCA_BND"]
ticker_list = ["VV", "VB", "VEU", "BIV", "BSV", "VWO", "BND"]
ticker_identifier_list = []
ticker_url_list = []

def find_ticker(ticker_list, file_name):
	"""Searches through csv file to find ticker and corresponding 
	ticker url identifier.
	"""
	filename = open(file_name)
	for line in filename:
		data = line.strip().split(",")
		for ticker in ticker_list:
			if ticker == data[0]:
				ticker_identifier_list.append(data[1])
	return ticker_identifier_list

def build_ticker_url(ticker_identifier_list):
	""" Queries the url using the desired ticker identifier and token"""
	for ticker_identifier in ticker_identifier_list:
		url = "https://www.quandl.com/api/v1/datasets/"
		token = open("quandl_tokens.txt").read()
		ticker_url = url + ticker_identifier + ".json?auth_token=" + token
		ticker_url_list.append(ticker_url)
	return ticker_url_list

def load_ticker_data(ticker_url_list, session):
	for ticker_url in ticker_url_list:	
		u = urllib.urlopen(ticker_url)
		data = u.read()
		newdata = json.loads(data)

		ticker_symbol = (newdata["code"].split("_"))[1]
		ticker_name = newdata["name"]

		# Create new instance of the Ticker class called new_ticker
		new_ticker = Ticker(symbol=ticker_symbol, name=ticker_name)
        # Add each instance to session
		session.add(new_ticker)
		session.commit()
		
		# Prices pulls a list of lists (consisting of date, open, high, 
			# low, close, volume. adjusted close)
		prices = newdata["data"]

		for price in prices:
			date = price[0]
			date_format = datetime.strptime(date, "%Y-%m-%d")
			date_format = date_format.date()
			close_price = price[4]
			new_ticker_price = Price(ticker_id=new_ticker.id, date=date_format, close_price=close_price)
			session.add(new_ticker_price)

    # commit after all instances are added
	session.commit()

def load_ticker_category(session):
	filename = open("./seed_data/ticker_categories.csv")
	ticker_id = 1
	for line in filename:
		category = line.strip()
		new_category = model.session.query(model.Ticker).filter_by(id=
			ticker_id).update({model.Ticker.category: category})
		ticker_id = ticker_id + 1 
	session.commit()

def calc_daily_change(session):
	"""
	This function calculates the percent change since 4/10/2007 and saves
	that value to the new_change column in the database.

	All values are being benchmarked against 4/10/2007, which is the latest
	inception date for all of the funds for apples-to-apples since-inception
	comparison.
	"""

	ticker_id = 0
	for i in range(len(ticker_list)):
		ticker_id = ticker_id + 1
		ticker = model.session.query(model.Price).filter_by(ticker_id=
			ticker_id).all()

		new_index = 0
		old_close_price = model.session.query(model.Price).filter_by(date=
				"2007-04-10", ticker_id=ticker_id).first().close_price
		old_date = datetime.strptime("2007-04-10", "%Y-%m-%d").date()

		while ticker[new_index].date > old_date:
			new_close_price = ticker[new_index].close_price
			difference = round((new_close_price - old_close_price)/
				old_close_price, 4)
			new_change_id = ticker[new_index].id
			new_change = model.session.query(model.Price).filter_by(id=
				new_change_id).update({model.Price.percent_change: difference}) 
			new_index = new_index + 1
		session.commit()

def main(session):
	# load_ticker_data(build_ticker_url(find_ticker(ticker_list, "seed_data/ETFs-GOOG.csv")), session)
	# load_ticker_category(session)
	# load_risk_profs(session)
	# load_prof_allocs(session)
	# calc_daily_change(session)

if __name__ == "__main__":
    session = model.session
    main(session)
	