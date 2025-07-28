
import json
import os
from src.threader import Threader, ThreadSafeCallstack

def milesToIncrement(miles):
	lat_to_miles = 69
	lng_to_miles = 54.6
	search_grid_inc = (miles / lng_to_miles)
	return search_grid_inc

class Geo :

	cacher = None
	net = None

	def getCacher(self):
		return self.cacher

	def setCacher(self, cacher):
		self.cacher = cacher

	def getNetwork(self):
		return self.net

	def setNetwork(self, net):
		self.net = net

	def getGrid(self, bbox, miles = None, increment = .5) :
		if miles:
			increment = milesToIncrement(miles)
		sections = []
		lat_lng_x = 1
		lat = [bbox[0], bbox[0] + increment]
		while (lat[0] < bbox[2]) :
			lng = [bbox[1], bbox[1] + increment]
			while (lng[0] < bbox[3]) :
				lat_lng_x += 1
				if lat[0] < bbox[0]:
					lat[0] = bbox[0]
				if lat[1] > bbox[2]:
					lat[1] = bbox[2]
				if lng[0] < bbox[1]:
					lng[0] = bbox[2]
				if lng[1] > bbox[3]:
					lng[1] = bbox[3]
				section = [lat[0], lng[0], lat[1], lng[1]]
				sections.append(section)
				lng[0] += increment
				lng[1] += increment
			lat[0] += increment
			lat[1] += increment
		return sections

	def getZipcodeFromLatLng(self, coord):
		url = f'https://us-reverse-geo.api.smartystreets.com/lookup?key=21102174564513388&latitude={coord[0]}&longitude={coord[1]}&agent=smartystreets+(sdk:javascript@1.11.1)&country=US&candidates=1'
		headers = {
			'Content-Type': 'text/plain; charset=utf-8',
			'Referer': 'https://www.smartystreets.com/'
		}
		res = self.net.request(method="get", url=url, headers=headers, cache=True, use_curl=True, must_be_json=True)
		if "results" in res.json():
			if res.json()["results"]:
				return res.json()["results"][0]["address"]["zipcode"]
			else:
				return False

	def getUSGrid(self, miles = None, increment = .5):
		coords = []
		bbox = [26.141779, -126.802163, 49.349896, -62.078617]
		coords1 = self.getGrid(bbox, miles=miles, increment=increment)
		bbox = [51.354343952290705, -170.20473039615877, 71.69632408574896, -139.79457590969784]
		coords2 = self.getGrid(bbox, miles=miles, increment=increment)
		bbox = [12.316293132629621, -172.24997191169268, 26.251950585719722, -148.036106128398]
		coords3 = self.getGrid(bbox, miles=miles, increment=increment)
		bbox = [17.435156809973098, -67.86061026243665, 19.005637065738426, -64.18568367134458]
		coords4 = self.getGrid(bbox, miles=miles, increment=increment)
		return coords1 + coords2 + coords3 + coords4

	def getTestGrid(self, miles = None, increment = .5):
		coords = []
		bbox = [35.991424390262566, -90.86148002259685, 49.349896, -62.078617]
		coords1 = self.getGrid(bbox, miles=miles, increment=increment)
		return coords1

	def getGridExtended(self, miles = None, increment = .5):
		coords = self.getGrid(miles=miles, increment=increment)
		Threader.runThreads(self.getZipcodeFromLatLng, coords, 20)
		for coord in coords:
			coord.append(self.getZipcodeFromLatLng(coord))
		return coords

	def getUSGridExtended(self, miles = None, increment = .5):
		coords = self.getUSGrid(miles=miles, increment=increment)
		Threader.runThreads(self.getZipcodeFromLatLng, coords, 20)
		for coord in coords:
			coord.append(self.getZipcodeFromLatLng(coord))
		return coords

	def getTestGridExtended(self, miles = None, increment = .5):
		coords = self.getTestGrid(miles=miles, increment=increment)
		Threader.runThreads(self.getZipcodeFromLatLng, coords, 20)
		for coord in coords:
			coord.append(self.getZipcodeFromLatLng(coord))
		return coords

	def __init__(self, cacher=None, net=None):
		self.setCacher(cacher)
		self.setNetwork(net)
