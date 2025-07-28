
from lxml import html, etree
from slugify import slugify
from src.fileio import FileIO
from src.network import NetworkDefaults
from curl_cffi import requests as curlrequests
import cchardet
import datetime
import glob
import html as html2
import importlib
import io
import json
import os
import re
import requests
import src.threader
import string
import sys
import time
import urllib
import csv
import traceback
import locale
locale.setlocale( locale.LC_ALL, '' )

import pyap
import usaddress

def parseAddress(address_string):
	components = {}
	components["Street"] = ""
	components["City"] = ""
	components["State"] = ""
	components["Zip_Code"] = ""
	components["Country"] = ""

	address_parser = pyap.parse(address_string, country='US')
	if len(address_parser):
		parsed_address = address_parser[0]
		city = parsed_address.city
		state = parsed_address.region1
		postal_code = parsed_address.postal_code
		country = parsed_address.country_id
		print(city)
		street = re.findall(f"^(.+?).{city}", address_string)[0]

		components["Street"] = street
		components["City"] = city
		components["State"] = state
		components["Zip_Code"] = postal_code
		components["Country"] = country
	else:
		try:
			address_parser = usaddress.tag(address_string)
			if len(address_parser):
				parsed_address = address_parser[0]
				city = parsed_address["PlaceName"]
				state = parsed_address["StateName"]
				postal_code = parsed_address["ZipCode"]
				country = "United States"
				street = re.findall(f"^(.+? .+?)[, ]+{city}", address_string)[0]

				components["Street"] = street
				components["City"] = city
				components["State"] = state
				components["Zip_Code"] = postal_code
				components["Country"] = country
		except:
			pass

	return components

def get_domain(url):
	if not url:
		return ""
	if not "://" in url:
		url = "https://"+url
	parsed_url = urllib.parse.urlparse(url)
	domain = parsed_url.netloc.replace("www.", "")
	return domain

def parse_csv_string(csv_string):
    csv_file = io.StringIO(csv_string, newline='')
    data = []
    
    reader = csv.DictReader(csv_file)
    for row in reader:
        data.append(row)
    
    return data

class Scraper : 

	def print(self, data):
		if type(data) == str:
			print(data)
		if type(data) == dict or type(data) == list:
			print(json.dumps(data, indent=4))

	default_headers = {
		"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
		"accept-language": "en-US,en;q=0.9,da;q=0.8",
		"cache-control": "no-cache",
		"pragma": "no-cache",
		"upgrade-insecure-requests": "1",
		"Referer": "https://manatee.realforeclose.com/index.cfm?resetcfcobjs=1",
		"Referrer-Policy": "strict-origin-when-cross-origin"
	}
	default_headers_ajax = {
		"accept": "application/json, text/javascript, */*; q=0.01",
		"accept-language": "en-US,en;q=0.9,da;q=0.8",
		"cache-control": "no-cache",
		"content-type": "application/x-www-form-urlencoded; charset=UTF-8",
		"pragma": "no-cache",
		"x-requested-with": "XMLHttpRequest",
		"Referer": "https://broward.realforeclose.com/index.cfm?zaction=AUCTION&Zmethod=PREVIEW&AUCTIONDATE=03/01/2024",
		"Referrer-Policy": "strict-origin-when-cross-origin"
	}

	def getGenericResDoc(self, *args, **kargs):
		if not kargs.get("headers"):
			kargs["headers"] = NetworkDefaults.html_headers
		if not kargs.get("cache"):
			kargs["cache"] = False
		if not kargs.get("use_curl"):
			kargs["use_curl"] = True
		res = self.man.net.request(**kargs)
		content1 = b"""<meta charset="utf-8" />"""
		doc = html.fromstring(content1+res.content)
		return res, doc

	def getGenericResDocResi(self, *args, **kargs):
		if not kargs.get("headers"):
			kargs["headers"] = NetworkDefaults.html_headers
		if not kargs.get("cache"):
			kargs["cache"] = False
		if not kargs.get("use_curl"):
			kargs["use_curl"] = True
		res = self.man.netresi.request(**kargs)
		content1 = b"""<meta charset="utf-8" />"""
		doc = html.fromstring(content1+res.content)
		return res, doc

	def getGenericResDocSession(self, *args, **kargs):
		if not "session" in dir(self):
			self.session = curlrequests.Session()
		if not kargs.get("headers"):
			kargs["headers"] = NetworkDefaults.html_headers
		res = self.session.request(**kargs)
		content1 = b"""<meta charset="utf-8" />"""
		doc = html.fromstring(content1+res.content)
		return res, doc

	def loginToCounty(self, county):
		url = "https://manatee.realforeclose.com/index.cfm"
		headers = {
			"accept": "application/json, text/javascript, */*; q=0.01",
			"accept-language": "en-US,en;q=0.9,da;q=0.8",
			"cache-control": "no-cache",
			"content-type": "application/x-www-form-urlencoded; charset=UTF-8",
			"cookie": "no-cache",
			"x-requested-with": "XMLHttpRequest",
			"Referer": "https://manatee.realforeclose.com/index.cfm?resetcfcobjs=1",
			"Referrer-Policy": "strict-origin-when-cross-origin"
		}
		data = "ZACTION=AJAX&ZMETHOD=LOGIN&func=SWITCH&VENDOR={}".format(county)
		method = "post"
		res, doc = self.getGenericResDoc(method=method, url=url, data=data, headers=headers)
		return res.json()["URL"]

	def generate_monthly_dates(self):
	    start_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d')
	    end_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d')

	    dates_list = []

	    current_date = start_date
	    while current_date <= end_date:
	        dates_list.append(current_date.strftime('%Y-%m-01'))
	        year = current_date.year + (current_date.month + 1) // 12
	        month = (current_date.month + 1) % 12 or 12
	        current_date = current_date.replace(year=year, month=month)
	        
	    return dates_list

	def getCalendarAuctionDates(self, county_domain, date):
		self.checkRunning()
		url = "https://{}/index.cfm?zaction=user&zmethod=calendar&selCalDate=%7Bts%20%27{}%2000%3A00%3A00%27%7D".format(county_domain, date)
		method = "get"
		res, doc = self.getGenericResDoc(method=method, url=url, headers=self.default_headers)

		auctions = doc.xpath('//*[contains(@class, "CALBOX") and @dayid]')
		for auction in auctions:
			self.checkRunning()
			auction_date = auction.get('dayid')
			auction_date_ts = datetime.datetime.strptime(auction_date, "%m/%d/%Y").date()
			auction_date_formatted = auction_date_ts.strftime("%Y-%m-%d")
			if not self.start_date <= auction_date_formatted <= self.end_date:
				continue
			self.man.cmdOutputLine("[AUCTION] {}".format(auction_date_formatted))

			auction_url = "https://{}/index.cfm?zaction=AUCTION&Zmethod=PREVIEW&AUCTIONDATE={}".format(county_domain, auction_date)
			timestamp = round(time.time() * 1000)

			res, doc = self.getGenericResDocSession(method="GET", url=auction_url, headers=self.default_headers)

			headers = self.default_headers
			headers["Referer"] = auction_url

			for page in range(1, 10):
				self.checkRunning()
				print(page)
				PageDir = 0
				if page > 1:
					PageDir = 1
				ajax_url = "https://{}/index.cfm?zaction=AUCTION&Zmethod=UPDATE&FNC=LOAD&AREA=C&PageDir={}&doR=1&tx={}&bypassPage=0&test=1&_=1712501554902".format(county_domain, PageDir, timestamp)
				res, doc = self.getGenericResDocSession(method="GET", url=ajax_url, headers=headers)

				text = res.json()["retHTML"]
				text = text.replace(r"@A", r'<div class="')
				text = text.replace(r"@B", r'</div>')
				text = text.replace(r"@C", r'class="')
				text = text.replace(r"@D", r'<div>')
				text = text.replace(r"@E", r'AUCTION')
				text = text.replace(r"@F", r'</td><td')
				text = text.replace(r"@G", r'</td></tr>')
				text = text.replace(r"@H", r'<tr><td ')
				text = text.replace(r"@I", r'table')
				text = text.replace(r"@J", r'p_back="NextCheck=')
				text = text.replace(r"@K", r'style="Display:none"')
				text = text.replace(r"@L", r'/index.cfm?zaction=auction&zmethod=details&AID=')
				content1 = """<meta charset="utf-8" />"""
				doc = html.fromstring(content1+text)

				aids = []
				auction_rows = doc.xpath('//*[@class="AUCTION_ITEM PREVIEW"]')
				for auction_row in auction_rows:
					aid = auction_row.get('aid').strip()
					aids.append(aid)

				aids_str = ",".join(aids)
				update_url = "https://{}/index.cfm?zaction=AUCTION&ZMETHOD=UPDATE&FNC=UPDATE&ref={}&tx={}&_=1712503375705".format(county_domain, aids_str, timestamp)
				headers["Referer"] = auction_url
				res, doc2 = self.getGenericResDocSession(method="GET", url=update_url, headers=headers)

				auctions_updated = {}
				aitems = res.json()["ADATA"]["AITEM"]
				for aitem in aitems:
					auctions_updated[aitem["AID"]] = aitem

				auction_rows_len = len(auction_rows)
				print(auction_rows_len)
				auction_rows = doc.xpath('//*[@class="AUCTION_ITEM PREVIEW"]')
				for auction_row in auction_rows:
					self.checkRunning()
					aid = auction_row.get('aid').strip()

					fields = {}
					fields["County"] = county_domain
					labels = auction_row.xpath('.//*[contains(@class, "AD_LBL")]')
					for label in labels:
						title = label.text_content().strip().strip(":")
						if not title:
							title = "Property Location"
						value = label.xpath('./following-sibling::*')[0].text_content().strip()
						if title == "Parcel ID":
							fields["Parcel Url"] = ""
							try:
								fields["Parcel Url"] = label.xpath('./following-sibling::*/a')[0].get('href')
							except:
								pass
						fields[title] = value
						if title == "Property Location":
							fields["P.L. City"] = ""
							fields["P.L. State"] = ""
							fields["P.L. Zip"] = ""

					if aid in auctions_updated and auctions_updated[aid]["D"]:
						fields["Auction Sold"] = auctions_updated[aid]["B"]
						fields["Amount"] = auctions_updated[aid]["D"]
						fields["Sold To"] = auctions_updated[aid]["ST"]

						if False and fields.get("Parcel Url"):
							if re.findall(r"[0-9-]{2,}[A-Z0-9\.\s-]{5,}", fields["Parcel Url"]):
								if not "parcel_urls" in dir(self):
									self.parcel_urls = {}
								parcel_domain = get_domain(fields["Parcel Url"])
								if not parcel_domain in self.parcel_urls:
									self.parcel_urls[parcel_domain] = []
								if len(self.parcel_urls[parcel_domain]) < 10:
									self.parcel_urls[parcel_domain].append(fields["Parcel Url"])
									FileIO.saveJson("parcel_urls.json", self.parcel_urls)

						try:
							if True and fields.get("Parcel Url"):
								if re.findall(r"[0-9-]{2,}[A-Z0-9\.\s-]{5,}", fields["Parcel Url"]):

									print()
									print(fields["Parcel Url"])
									self.man.cmdOutputLine("[AUCTION] {} {}".format(auction_date_formatted, fields["Parcel Url"]), overwrite=True)

									headers = self.default_headers.copy()
									if "publicaccess.vcgov.org" in fields["Parcel Url"]:
										headers = {
											"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
											"accept-language": "en-US,en;q=0.9,da;q=0.8",
											"cache-control": "no-cache",
											"pragma": "no-cache",
											"upgrade-insecure-requests": "1",
											"cookie": "_ga=GA1.1.342405762.1713361329; acceptedNewDisclaimer=true; _ga_NVHWYL61Z3=GS1.1.1714962177.5.1.1714962454.0.0.0; ADRUM=s=1714962511326&r=https%3A%2F%2Fvcpa.vcgov.org%2Fparcel%2Fsummary%2F%3F-1796796341"
										}
										fields["Parcel Url"] = "https://vcpa.vcgov.org/parcel/summary/?altkey={}".format(fields["Parcel ID"])
									res, doc3 = self.getGenericResDoc(method="get", url=fields["Parcel Url"], headers=headers, verify=False)
									time.sleep(.2)
									content = res.content
									content = content.replace(b'<?xml version="1.0" encoding="utf-16"?>', b'')
									content = re.sub(b"<\/?(?:br|BR) ?\/?>", b"\n", content)

									doc3 = html.fromstring(content)
									if not "parcel_xpaths" in dir(self):
										self.parcel_xpaths = FileIO.loadJson("parcel_xpaths.json")

									parcel_domain = get_domain(fields["Parcel Url"])
									if "ocpafl" in parcel_domain:

										url = "https://ocpa-mainsite-afd-standard.azurefd.net/api/PRC/GetPRCGeneralInfo?pid={}".format(fields["Parcel ID"])
										res, doc3 = self.getGenericResDoc(method="get", url=url, headers=headers, verify=False)
										fields["Owner(s)"] = res.json().get("ownerName")
										fields["Mailing Address"] = "{} {}, {} {}".format(
											res.json().get("mailAddress"),
											res.json().get("mailCity"),
											res.json().get("mailState"),
											res.json().get("mailZip")
										)

									elif "hcpafl" in parcel_domain:

										url = "https://gis.hcpafl.org/CommonServices/property/search//ParcelData?pin={}".format(fields["Parcel ID"])
										res, doc3 = self.getGenericResDoc(method="get", url=url, headers=headers, verify=False)
										fields["Owner(s)"] = res.json()["owner"]
										fields["Mailing Address"] = "{} {}, {} {}".format(
											(res.json()["mailingAddress"]["addr1"]+" "+res.json()["mailingAddress"]["addr2"]).strip(),
											res.json()["mailingAddress"]["city"],
											res.json()["mailingAddress"]["state"],
											res.json()["mailingAddress"]["zip"]
										)

									elif "miamidade" in parcel_domain:

										url = "https://www.miamidade.gov/Apps/PA/PApublicServiceProxy/PaServicesProxy.ashx?Operation=GetPropertySearchByFolio&clientAppName=PropertySearch&folioNumber={}".format(fields["Parcel ID"].replace("-", ""))
										print(url)
										res, doc3 = self.getGenericResDoc(method="get", url=url, headers=headers, verify=False)
										try:
											fields["Owner(s)"] = res.json()["OwnerInfos"][0]["Name"]
										except:
											pass
										fields["Mailing Address"] = "{} {}, {} {}".format(
											(res.json()["MailingAddress"]["Address1"]+" "+res.json()["MailingAddress"]["Address2"]).strip(),
											res.json()["MailingAddress"]["City"],
											res.json()["MailingAddress"]["State"],
											res.json()["MailingAddress"]["ZipCode"]
										)

									elif "paslc" in parcel_domain:

										url = "https://www.paslc.gov/recordcarddata/api/re/PropertyIndex/{}".format(fields["Parcel ID"])
										print(url)
										res, doc3 = self.getGenericResDoc(method="get", url=url, headers=headers, verify=False)
										url = "https://www.paslc.gov/recordcarddata/api/re/baserecordcard/{}".format(res.json()["AccountNumber"])
										print(url)
										res, doc3 = self.getGenericResDoc(method="get", url=url, headers=headers, verify=False)
										fields["Owner(s)"] = res.json()[0].get("Owner1")
										fields["Mailing Address"] = "{} {}, {} {}".format(
											(res.json()[0]["Street1"]+" "+res.json()[0]["Street2"]).strip(),
											res.json()[0]["City"],
											res.json()[0]["State"],
											res.json()[0]["Zip"]
										)


									elif parcel_domain in self.parcel_xpaths:

										if "citruspa.org1" in parcel_domain:
											FileIO.saveRaw("somefile.html", res.text)

										try:
											if "owners" in self.parcel_xpaths[parcel_domain]:
												fields["Owner(s)"] = doc3.xpath(self.parcel_xpaths[parcel_domain]["owners"])[0].text_content().strip()
												fields["Owner(s)"] = '\n'.join([line.strip() for line in fields["Owner(s)"].splitlines()])
												fields["Owner(s)"] = fields["Owner(s)"].strip()
												print(fields["Owner(s)"])
										except:
											pass

										try:
											if "mail" in self.parcel_xpaths[parcel_domain]:
												text = "\n".join([el.text_content().strip() for el in doc3.xpath(self.parcel_xpaths[parcel_domain]["mail"])])
												if "vcpa.vcgov.org" in parcel_domain:
													text = "\n".join(text.split("\n")[:-1])
												els = doc3.xpath(self.parcel_xpaths[parcel_domain]["mail"])
												fields["Mailing Address"] = text
												fields["Mailing Address"] = '\n'.join([line.strip() for line in fields["Mailing Address"].splitlines()])
												fields["Mailing Address"] = fields["Mailing Address"].strip()
										except Exception as ex:
											print(traceback.format_exc())
											pass

									if fields.get("Mailing Address"):
										fields = {**fields, **self.parseAddress(fields["Mailing Address"])}
						except Exception as ex:
							print(traceback.format_exc())
							pass

						if "foreclose" in fields.get("County").lower():
							if fields.get("Final Judgment Amount") and fields.get("Amount"):
								final_judgement_amount = fields.get("Final Judgment Amount").replace("$","").replace(",","")
								amount = fields.get("Amount").replace("$","").replace(",","")
								fields["Projected overage"] = locale.currency(float(amount) - float(final_judgement_amount), grouping=True)
								print(fields["Projected overage"])

						elif "taxdeed" in fields.get("County").lower():
							if fields.get("Opening Bid") and fields.get("Amount"):
								opening_bid = fields.get("Opening Bid").replace("$","").replace(",","")
								amount = fields.get("Amount").replace("$","").replace(",","")
								fields["Projected overage"] = locale.currency(float(amount) - float(opening_bid), grouping=True)
								print(fields["Projected overage"])

						if fields.get("Property Location"):
							city_statezip = fields.get("Property Location").split(", ")
							fields["P.L. City"] = city_statezip[0]
							if len(city_statezip) > 1:
								state_zip = city_statezip[1].split("- ")
								if len(state_zip) == 1:
									fields["P.L. State"] = ""
									fields["P.L. Zip"] = state_zip[0]
								elif len(state_zip) > 1:
									fields["P.L. State"] = state_zip[0]
									fields["P.L. Zip"] = state_zip[1]
							del fields["Property Location"]

						self.sheet.append(fields)
				if auction_rows_len < 10:
					break

	def getResults(self, domain):
		self.man.cmdOutputLine("[LOGIN]")

		timestamp = round(time.time() * 1000)
		start_date_ts = datetime.datetime.strptime(self.start_date, "%Y-%m-%d").date()
		start_date_formatted = start_date_ts.strftime("%m/%d/%Y")
		end_date_ts = datetime.datetime.strptime(self.end_date, "%Y-%m-%d").date()
		end_date_formatted = end_date_ts.strftime("%m/%d/%Y")

		url = "https://{}/index.cfm?Zaction=admin&Zmethod=REPORT&report_id=37".format(domain)
		res, doc = self.getGenericResDocSession(method="GET", url=url, headers=self.default_headers)
		try:
			repid = re.findall(r"var ReportID = '(.+?)';", res.text)[0]
		except:
			self.man.cmdOutputLine("{} is currently offline".format(domain))
			return

		url = "https://{}/index.cfm?&start_date={}&end_date={}&Case_Number=&Certificate_Number=&Bidder=&Parcel=&SoldTO=NULL&Is_user=2&auctType=NULL&zaction=AJAX&zmethod=COM&process=REPVIEW&FUNC=FilterData&SHOWJSON=false&REPID={}&_=1712569118625".format(domain, start_date_formatted, end_date_formatted, repid)
		res, doc = self.getGenericResDocSession(method="GET", url=url, headers=self.default_headers)

		url = "https://{}/index.cfm?Zaction=admin&Zmethod=REPORTCSV&Report_id=18&repid={}".format(domain, repid)
		res, doc = self.getGenericResDocSession(method="GET", url=url, headers=self.default_headers)

		self.sheet += parse_csv_string(res.text)

	def doLoginToSite(self, domain):
		self.man.cmdOutputLine("[LOGIN]")

		url = "https://{}/index.cfm".format(domain)
		res, doc = self.getGenericResDocSession(method="GET", url=url, headers=self.default_headers)

		data = "ZACTION=AJAX&ZMETHOD=LOGIN&func=LOGIN&USERNAME=Billycmiller&USERPASS=Vapassword2024!"
		res, doc = self.getGenericResDocSession(method="POST", url=url, data=data, headers=self.default_headers_ajax)
		self.acceptNotices(domain)

	def acceptNotices(self, domain):
		url = "https://{}/index.cfm".format(domain)
		res, doc = self.getGenericResDocSession(method="GET", url=url, headers=self.default_headers)

		time.sleep(.2)
		self.checkRunning()

		notices = doc.xpath('//*[@id="NOTICEMSG"]')
		for notice in notices:
			nid = notice.get('nid')
			self.man.cmdOutputLine("[NOTICE] #{}".format(nid))

			data = "zaction=AJAX&zmethod=COM&process=NOTICE&func=ACCEPT&showjson=false&NID={}".format(nid)
			res, doc = self.getGenericResDocSession(method="POST", url=url, data=data, headers=self.default_headers_ajax)
			self.acceptNotices(domain)
			break

	def checkRunning(self):
		if not self.man.is_started:
			exit()

	def parseAddress(self, address_string):
		url = "https://us-street.api.smarty.com/street-address?key=21102174564513388&agent=smarty+(website:demo%2Fsingle-address%40latest)&match=enhanced&candidates=5&geocode=true&license=us-rooftop-geocoding-cloud&street={}".format(urllib.parse.quote(address_string))
		headers = {
			"accept": "application/json, text/plain, */*",
			"accept-language": "en-US,en;q=0.9,da;q=0.8",
			"cache-control": "no-cache",
			"pragma": "no-cache",
			"Referer": "https://www.smarty.com/",
			"Referrer-Policy": "strict-origin-when-cross-origin"
		}
		res, doc = self.getGenericResDocResi(method="get", url=url, headers=headers)
		fields = {}
		fields["delivery_line_1"] = res.json()[0].get("delivery_line_1")
		fields["city_name"] = res.json()[0]["components"]["city_name"]
		fields["state"] = res.json()[0]["components"]["state_abbreviation"]
		fields["zipcode"] = res.json()[0]["components"]["zipcode"]
		fields["plus4_code"] = res.json()[0]["components"]["plus4_code"]
		return fields

	def doExportAuctions(self):

		self.sheet_fn = "realtaxdeed-auctions-{}-{}.xlsx".format(self.start_date, self.end_date)
		self.sheet_fn = os.path.join(self.man.getResultsDir(), self.sheet_fn)
		FileIO.saveRaw(self.sheet_fn, "")
		self.sheet = []
		self.checkRunning()

		for county in self.counties:
			self.checkRunning()
			county_url = self.loginToCounty(county)
			county_domain = urllib.parse.urlparse(county_url).netloc
			self.man.cmdOutputLine("[JUMPTO] {}".format(county_domain))

			monthly_dates = self.generate_monthly_dates()
			for monthly_date in monthly_dates:
				self.checkRunning()
				self.man.cmdOutputLine("[CALENDAR] {}".format(monthly_date))

				self.getCalendarAuctionDates(county_domain, monthly_date)
		
		self.man.excel.writeAllXlsx(self.sheet_fn, {"Auctions": self.sheet})

	def doExportResults(self):

		self.sheet_fn = "realtaxdeed-results-{}-{}.xlsx".format(self.start_date, self.end_date)
		self.sheet_fn = os.path.join(self.man.getResultsDir(), self.sheet_fn)
		FileIO.saveRaw(self.sheet_fn, "")
		self.sheet = []
		self.checkRunning()

		for county in self.counties:
			self.checkRunning()
			county_url = self.loginToCounty(county)
			county_domain = urllib.parse.urlparse(county_url).netloc
			self.man.cmdOutputLine("[JUMPTO] {}".format(county_domain))

			self.doLoginToSite(county_domain)
			self.getResults(county_domain)
		
		self.man.excel.writeAllXlsx(self.sheet_fn, {"Results": self.sheet})
			
	def __init__(self, man, counties, start_date, end_date):
		self.man = man
		self.counties = counties
		self.start_date = start_date
		self.end_date = end_date