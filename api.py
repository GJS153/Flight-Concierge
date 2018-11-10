# -*- coding: utf-8 -*-
from datetime import timedelta 
from flask import Flask, request, jsonify
from uber_rides.session import Session
from uber_rides.client import UberRidesClient
import datetime
import re
import requests
import string
import json
import os

app = Flask(__name__)

#def check_if_flight_exists(the_airline_code, the_airport_code, the_departure_date, the_flight_number):

def getLyftEstimates(user_latitude, user_longitude, airport_latitude, airport_longitude):
    print("getlyftEstimates")
    estimates = []
    lyft_categories_needed = ["lyft_line", "lyft", "lyft_plus"]

    lyft_api = 'https://api.lyft.com/v1/cost'
    parameters = {
        'start_lat': user_latitude,
        'start_lng': user_longitude,
        'end_lat': airport_latitude,
        'end_lng': airport_longitude,
        'key': "NDX5SMbUychA"
    }

    options = requests.get(lyft_api, params=parameters).json()

    for i in range (len(options['cost_estimates'])):
        lyftType = options['cost_estimates'][i]['ride_type']
        if(lyftType.lower().strip() in lyft_categories_needed):
            tempDict = {}
            tempDict["category"] = lyftType.lower().strip()
            tempDict['distance'] = options['cost_estimates'][i]['estimated_distance_miles']
            tempDict['duration'] = options['cost_estimates'][i]['estimated_duration_seconds']
            tempDict['price_estimate'] = '$' + str(int(int(options['cost_estimates'][i]['estimated_cost_cents_min'])/100)) + '-$' + str(int(int(options['cost_estimates'][i]['estimated_cost_cents_max'])/100))
            #low_price': options['cost_estimates'][i]['estimated_cost_cents_min'],
            #'high_price': options['cost_estimates'][i]['estimated_cost_cents_max'],
            if(tempDict):
                estimates.append(tempDict)

    return estimates

# example output
# {
#     'lyft_line': {
#         'distance': 5.63, 
#         'duration': 752, 
#         'price_estimate': '$10-12', 
#         'low_price': 1000, 
#         'high_price': 1200
#         }, 
#     'lyft': {
#         'distance': 5.63, 
#         'duration': 752, 
#         'price_estimate': '$12-15', 
#         'low_price': 1200, 
#         'high_price': 1500
#         }, 
#     'lyft_plus': {
#         'distance': 5.63, 
#         'duration': 752, 
#         'price_estimate': '$21-24', 
#         'low_price': 2100, 
#         'high_price': 2400
#         }, 
#     'lyft_premier': {
#         'distance': 5.63, 
#         'duration': 752, 
#         'price_estimate': '$28-32', 
#         'low_price': 2800, 
#         'high_price': 3200
#         }, 
#     'lyft_lux': {
#         'distance': 5.63, 
#         'duration': 752, 
#         'price_estimate': '$36-40', 
#         'low_price': 3600, 
#         'high_price': 4000
#         }, 
#     'lyft_luxsuv': {
#         'distance': 5.63, 
#         'duration': 752, 
#         'price_estimate': '$45-50', 
#         'low_price': 4500, 
#         'high_price': 5000
#         }
# }

def getDrivingEstimate(user_latitude, user_longitude, airport_latitude, airport_longitude, arrival_time = None):
    print("getDrivingEstimate")
    google_map_api = 'https://maps.googleapis.com/maps/api/distancematrix/json'

    parameters = {
        'mode': 'driving',
        'origins': str(user_latitude) + ',' + str(user_longitude),
        'destinations': str(airport_latitude) + ',' + str(airport_longitude),
        'units': 'metric',
        'arrival_time': arrival_time,
        'key': 'AIzaSyBjDYYCA4Vo7Lv4x8usZQoTp9kjnc2v7xY'
    }

    driving_estimate = requests.get(google_map_api, params=parameters).json()

    estimate = {
        #'distance' : driving_estimate['rows'][0]['elements'][0]['distance']['value'],
        "duration" : driving_estimate['rows'][0]['elements'][0]['duration']['value']
    }

    return estimate

# example output
# {
#     'distance': 8645, 
#     'duration': 687
# }

def getTimeAtAirport(waiting_time, the_departure_time, the_departure_date):
    print("getTimeAtAirport")
    datetime_object = datetime.datetime.strptime(the_departure_date+' '+the_departure_time, '%m/%d/%Y %I:%M:%S%p')
    waiting_time += 30
    time_at_the_airport = datetime_object - datetime.timedelta(minutes=waiting_time)
    return time_at_the_airport

def getTransitEstimate(user_latitude, user_longitude, airport_latitude, airport_longitude, arrival_time = None):
    google_map_api = 'https://maps.googleapis.com/maps/api/distancematrix/json'

    parameters = {
        'mode': 'transit',
        'origins': str(user_latitude) + ',' + str(user_longitude),
        'destinations': str(airport_latitude) + ',' + str(airport_longitude),
        'units': 'metric',
        'arrival_time': arrival_time,
        'key': 'AIzaSyBjDYYCA4Vo7Lv4x8usZQoTp9kjnc2v7xY'
    }

    transit_data = requests.get(google_map_api, params=parameters).json()

    estimate = {
        #'distance': transit_data['rows'][0]['elements'][0]['distance']['value'],
        'duration': transit_data['rows'][0]['elements'][0]['duration']['value'],
        #'price': transit_data['rows'][0]['elements'][0]['fare']['value'],
        'price': transit_data['rows'][0]['elements'][0]['fare']['text']
    }

    return estimate

# example output
# {
#     'distance': 8128, 
#     'duration': 2026, 
#     'price': 1.25, 
#     'price_string': '$1.25'
# }


def getUberEstimates(user_latitude, user_longitude, airport_latitude, airport_longitude):
    print("getUberEstimates")
    estimates = []
    uber_categories_needed = ["uberxl", "uberpool", "uberx"]

    uber_api = 'https://api.uber.com/v1.2/estimates/price'
    parameters = {
        'start_latitude': user_latitude,
        'start_longitude': user_longitude,
        'end_latitude': airport_latitude,
        'end_longitude': airport_longitude,
        'server_token': "OPm8xhBUV9GJS8unpi_14G8tbK38fqfCRSNTGVzW"
    }

    options = requests.get(uber_api, params=parameters).json()

    for i in range (len(options['prices'])):
        uberCategory = options['prices'][i]['display_name'].lower().strip()
        if(uberCategory in uber_categories_needed):
            temp_price_estimate = options['prices'][i]['estimate'].replace('-', '-$')
            tempDict = {}
            tempDict["category"] = uberCategory
            tempDict['distance'] = options['prices'][i]['distance']
            tempDict['duration'] = options['prices'][i]['duration']
            tempDict['price_estimate'] = temp_price_estimate
            #'low_price': options['prices'][i]['low_estimate'],
            #'high_price': options['prices'][i]['high_estimate'],
            if(tempDict):
                estimates.append(tempDict)

    return estimates

# example output
# {
#     'Select': {
#         'distance': 6.34, 
#         'duration': 1380, 
#         'price_estimate': '$34-42', 
#         'low_price': 34.0, 
#         'high_price': 42.0
#          }, 
#     'UberXL': {
#         'distance': 6.34, 
#         'duration': 1380, 
#         'price_estimate': '$23-29', 
#         'low_price': 23.0, 
#         'high_price': 29.0
#         }, 
#     'Black': {
#         'distance': 6.34, 
#         'duration': 1380, 
#         'price_estimate': '$43-54', 
#         'low_price': 43.0, 
#         'high_price': 54.0
#         }, 
#     'Black SUV': {
#         'distance': 6.34, 
#         'duration': 1380, 
#         'price_estimate': '$56-69', 
#         'low_price': 56.0, 
#         'high_price': 69.0
#         }, 
#     'Assist': {
#         'distance': 6.34, 
#         'duration': 1380, 
#         'price_estimate': '$16-20', 
#         'low_price': 16.0, 
#         'high_price': 20.0
#         }, 
#     'WAV': {
#         'distance': 6.34, 
#         'duration': 1380, 
#         'price_estimate': '$16-20', 
#         'low_price': 16.0, 
#         'high_price': 20.0
#         }, 
#     'UberPool': {
#         'distance': 6.34, 
#         'duration': 1380, 
#         'price_estimate': '$10-14', 
#         'low_price': 10.0, 
#         'high_price': 15.0
#         }, 
#     'UberX': {
#         'distance': 6.34, 
#         'duration': 1380, 
#         'price_estimate': '$16-20', 
#         'low_price': 16.0, 
#         'high_price': 20.0
#         }, 
#     'Taxi': {
#         'distance': 6.34, 
#         'duration': 1380, 
#         'price_estimate': 'Metered', 
#         'low_price': None, 
#         'high_price': None
#         }
# }

def getTsaEstimates(the_airport_code, the_tsa_pre_check):
    print("getTsaEstimates")
    #Assume waiting line in TSA is 2 minutes, unless users have done tsa pre check
    totalWaitingTime = 2
    if(the_tsa_pre_check):
        totalWaitingTime = 1

    try:
        #Cal TSA API for retrieving TSA waiting time
        url = 'https://apps.tsa.dhs.gov/MyTSAWebService/GetConfirmedWaitTimes.ashx?ap='+the_airport_code
        response = requests.post(url)

        #Convert unicode to string
        response = response.text.encode('utf8')

        #Average waiting time per person in TSA
        waitingTimePerPerson = 3

        #Current number of people in TSA waiting line
        peopleInTsa = int(re.search('<travelerCount>(.*)</travelerCount>', response).group(1))

        totalWaitingTime += (peopleInTsa * waitingTimePerPerson)

    except:
        pass

    return totalWaitingTime;

def getWaitingTimeBeforeTsa(the_baggage_check_in, the_online_check_in):
    print("getWaitingTimeBeforeTsa")
    waitingTime = 0
    if the_baggage_check_in:
        waitingTime += 5
    if not the_online_check_in:
        waitingTime += 5

    return waitingTime

def updateDrivingAndTransit(theDrivingEstimateDict, the_time_at_airport):
    print("updateDrivingAndTransit")
    departure_time_from_home = the_time_at_airport - datetime.timedelta(seconds=(theDrivingEstimateDict["duration"]+(15*60)))
    theDrivingEstimateDict["departure_time_from_home"] = departure_time_from_home.strftime('%m/%d/%Y - %I:%M%p')
    theDrivingEstimateDict["time_at_the_airport"] = the_time_at_airport.strftime('%m/%d/%Y - %I:%M%p')
    return theDrivingEstimateDict

def updateRideSharing(rideSharingEstimateList, time_at_airport):
    print("updateRideSharing")
    for eachRideSharing in rideSharingEstimateList:
        departure_time_from_home = time_at_airport - datetime.timedelta(seconds=eachRideSharing["duration"])
        eachRideSharing["departure_time_from_home"] = departure_time_from_home.strftime('%m/%d/%Y - %I:%M%p')
        eachRideSharing["time_at_the_airport"] = time_at_airport.strftime('%m/%d/%Y - %I:%M%p')

    return rideSharingEstimateList

def getCoordinates(address):
    print("getCoordinates")
    geo_coding_api = 'https://maps.googleapis.com/maps/api/geocode/json'
    parameters = {
        'address': address,
        'key': "AIzaSyBjDYYCA4Vo7Lv4x8usZQoTp9kjnc2v7xY"
    }
    latitude_longitude = requests.get(geo_coding_api, params=parameters).json()
    latitude = latitude_longitude['results'][0]['geometry']['location']['lat']
    longitude = latitude_longitude['results'][0]['geometry']['location']['lng']

    return latitude, longitude

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError

def get_error_message(the_return_json_to_frontend, error_msg):
    print("get_error_message")
    the_return_json_to_frontend["success"] = 0
    the_return_json_to_frontend["error_message"] = error_msg
    return json.dumps(the_return_json_to_frontend)
        

@app.route('/get_result', methods=['GET', 'POST'])
def get_the_result():
    return_json_to_frontend = {
        "success":1,
        "error_message": ""
    }

    try:
        jsonDict = request.get_json()
    except:
        return get_error_message(return_json_to_frontend, "Cannot parse the json")


    if(jsonDict):
    	print(jsonDict)
  
    print("value")

    #Get IATA airline code
    try:
        airline_code = jsonDict['airline_code']
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: airline_code")

    #Get the IATA departure airport code
    try:
        airport_code = jsonDict['airport_code']
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: airport_code")

    #Get the departure airport name
    '''
    try:
        airport_name = jsonDict['airport_name']
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: airport_name")
	'''

    #Get departure date
    try:
        departure_date = jsonDict['departure_date']
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: departure_date") 

    #Get departure time zone
    '''
    try:
        departure_time_zone = jsonDict['departure_time_zone']
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: departure_time_zone")
	'''

    #Get departure time
    try:
        departure_time = jsonDict['departure_time']
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: departure_time")

    #Get flight number
    try:
        flight_number = jsonDict['flight_number']
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: flight_number")    

    #Get user current latitude
    try:
        user_current_latitude = float(jsonDict['user_latitude'])
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: user_latitude") 

    #Get user current latitude
    try:
        user_current_longitude = float(jsonDict['user_longitude'])
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: user_longitude") 

    #Check if the user will check in online or not
    try:
        online_check_in = int(jsonDict['online_check_in'])
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: online_check_in")

    #Check if the user will do baggage check in or not
    try:
        baggage_check_in = int(jsonDict['baggage_check_in'])
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: baggage_check_in")

    #Check if the user will do TSA pre-checking or not
    try:
        tsa_pre_check = int(jsonDict['tsa_pre_check'])
    except:
        return get_error_message(return_json_to_frontend, "Missing json key of: tsa_pre_check")

    #Get the flight departure time
    '''
    flight_exists = check_if_flight_exists(airline_code, airport_code, departure_date, flight_number)
    if(not flight_exists):
        return get_error_message(return_json_to_frontend, "Flight does not exist")
    '''

    try:
	    #Get the airport coordinates
	    airport_latitude, airport_longitude = getCoordinates(airport_code+" airport")
	    
            print(airport_latitude, airport_longitude)
	    #Estimate the Uber cost and trip duration
	    uberEstimateList = getUberEstimates(user_current_latitude, user_current_longitude, airport_latitude, airport_longitude)
	    for x in uberEstimateList:
            	print(x)
	    #Estimate the Lyft cost and trip duration
	    lyftEstimateList = getLyftEstimates(user_current_latitude, user_current_longitude, airport_latitude, airport_longitude)
            for x in lyftEstimateList:
                print(x)
	    #Estimate personal driving duration
	    drivingEstimateDict = getDrivingEstimate(user_current_latitude, user_current_longitude, airport_latitude, airport_longitude)
	    print(drivingEstimateDict)
	    #Estimate public transportation duration and cost
	    try:
		publicTransportationDict = getTransitEstimate(user_current_latitude, user_current_longitude, airport_latitude, airport_longitude)
            	print(publicTransportationDict)
	    except:
		pass
	    #Get TSA Wait Time
	    tsa_waiting_time_in_minute = getTsaEstimates(airport_code, tsa_pre_check)

	    #Waiting time before TSA
	    waiting_time_before_tsa_in_minute = getWaitingTimeBeforeTsa(baggage_check_in, online_check_in)

	    #Get time to be at airport
	    time_at_airport = getTimeAtAirport(tsa_waiting_time_in_minute+waiting_time_before_tsa_in_minute, departure_time, departure_date)

	    #Update Uber, Lyft, driving, and public transportation with a required arrival time at the airport
	    uberEstimateList = updateRideSharing(uberEstimateList, time_at_airport)
	    lyftEstimateList = updateRideSharing(lyftEstimateList, time_at_airport)
	    drivingEstimateDict = updateDrivingAndTransit(drivingEstimateDict, time_at_airport)
	    #publicTransportationDict = updateDrivingAndTransit(publicTransportationDict, time_at_airport)

	    return_json_to_frontend["uber"] = uberEstimateList
	    return_json_to_frontend["lyft"] = lyftEstimateList
	    return_json_to_frontend["driving"] = drivingEstimateDict
	    #return_json_to_frontend["transit"] = publicTransportationDict
		
	    print(return_json_to_frontend)
	    return json.dumps(return_json_to_frontend)

    except Exception, e:
	print(str(e))
        return json.dumps({})

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 80, debug=True)

