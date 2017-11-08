# Caching system is adapted from oauth1_twitter_caching.py
from requests_oauthlib import OAuth2Session
import json
import webbrowser
import csv
from datetime import datetime
from secret_data import app_key, client_secret

APP_KEY = app_key
CLIENT_SECRET = client_secret
AUTHORIZATION_BASE_URL = 'https://www.eventbrite.com/oauth/authorize'
TOKEN_URL = 'https://www.eventbrite.com/oauth/token'
REDIRECT_URI = 'https://www.programsinformationpeople.org/runestone/oauth'
REQUEST_URL = "https://www.eventbriteapi.com/v3/events/search/"
eventbrite_session = False

## CACHING SETUP
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
DEBUG = False
CACHE_FNAME = "cache_contents.json"
try:
    with open(CACHE_FNAME, 'r', encoding='utf-8-sig') as cache_file:
        cache_json = cache_file.read()
        CACHE_DICTION = json.loads(cache_json)
except:
    CACHE_DICTION = {}

def has_cache_expired(timestamp_str, expire_in_days):
    now = datetime.now()
    cache_timestamp = datetime.strptime(timestamp_str, DATETIME_FORMAT)
    delta = now - cache_timestamp
    delta_in_days = delta.days
    return delta_in_days > expire_in_days

def get_from_cache(identifier, dictionary):
    identifier = identifier.upper()
    if identifier in dictionary:
        data_assoc_dict = dictionary[identifier]
        if has_cache_expired(data_assoc_dict['timestamp'],data_assoc_dict["expire_in_days"]):
            if DEBUG:
                print("Cache has expired for {}".format(identifier))
            # also remove old copy from cache
            del dictionary[identifier]
            data = None
        else:
            data = dictionary[identifier]['values']
    else:
        data = None
    return data

def set_in_data_cache(identifier, data, expire_in_days):
    identifier = identifier.upper()
    CACHE_DICTION[identifier] = {
        'values': data,
        'timestamp': datetime.now().strftime(DATETIME_FORMAT),
        'expire_in_days': expire_in_days
    }

    with open(CACHE_FNAME, 'w', encoding='utf-8-sig') as cache_file:
        cache_json = json.dumps(CACHE_DICTION)
        cache_file.write(cache_json)

def create_request_identifier(url, params_diction):
    sorted_params = sorted(params_diction.items(),key=lambda x:x[0])
    params_str = "_".join([str(e) for l in sorted_params for e in l])
    total_ident = url + "?" + params_str
    return total_ident.upper()

def get_data_from_api(request_url, service_ident, params_diction, expire_in_days=7):
    ident = create_request_identifier(request_url, params_diction)
    data = get_from_cache(ident, CACHE_DICTION)
    if data:
        if DEBUG:
            print("Loading from data cache: {}... data".format(ident))
    else:
        if DEBUG:
            print("Fetching new data from {}".format(request_url))

        response = make_eventbrite_request(request_url, params_diction)
        data = response.json()
        set_in_data_cache(ident, data, expire_in_days)
    return data

def make_eventbrite_request(url, params=None):
    global eventbrite_session

    if not eventbrite_session:
        start_eventbrite_session()

    if not params:
        params = {}

    return eventbrite_session.get(url, params=params)

def start_eventbrite_session():
    global eventbrite_session

    try:
        token = get_saved_token()
    except FileNotFoundError:
        token = None

    if token:
        eventbrite_session = OAuth2Session(APP_KEY, token=token)

    else:
        eventbrite_session = OAuth2Session(APP_KEY, redirect_uri=REDIRECT_URI)
        authorization_url, state = eventbrite_session.authorization_url(AUTHORIZATION_BASE_URL)
        print('Opening browser to {} for authorization'.format(authorization_url))
        webbrowser.open(authorization_url)
        redirect_response = input('Paste the full redirect URL here: ')
        token = eventbrite_session.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET,
                                               authorization_response=redirect_response.strip())
        save_token(token)

def get_saved_token():
    with open('token.json', 'r') as f:
        token_json = f.read()
        token_dict = json.loads(token_json)

        return token_dict

def save_token(token_dict):
    with open('token.json', 'w') as f:
        token_json = json.dumps(token_dict)
        f.write(token_json)

class Event:
  def __init__(self, diction):
    self.name = diction['name']['text'].strip()
    self.url = diction['url']
    self.category = None if not diction['category'] else diction['category']['name']
    self.start_date_local = datetime.strptime(diction['start']['local'], '%Y-%m-%dT%H:%M:%S')
    self.end_date_local = datetime.strptime(diction['end']['local'], '%Y-%m-%dT%H:%M:%S')
    self.description = diction['description']['text'].strip()
    self.organizer_name = diction['organizer']['name']
    self.venue_name = diction['venue']['name']
    self.venue_address = diction['venue']['address']['localized_address_display']

def writeCSV(name, list_events):
    with open('{}.csv'.format(name), 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['NAME', 'CATEGORY', 'START DATE', 'END DATE',
                       'DESCRIPTION', 'ORGANIZER', 'VENUE', 'ADDRESS', 'URL'])
        for event in list_events:
            writer.writerow([event.name, event.category, event.start_date_local,
                             event.end_date_local, event.description, event.organizer_name,
                             event.venue_name, event.venue_address, event.url])

def create_event_list(url, params_diction):    
    params_diction['page'] = 1
    # get items from the first page
    eventbrite_result = get_data_from_api(url, "Eventbrite", params_diction)
    events = eventbrite_result['events']
    list_events = [Event(event) for event in events]
    ## get more items beyond page 1 (50 items are limited per page)
    total_pages = eventbrite_result['pagination']['page_count']
    for i in range(2, total_pages+1):
        params_diction['page'] = i
        eventbrite_result = get_data_from_api(url, "Eventbrite", params_diction)
        events = eventbrite_result['events']
        list_events += [Event(event) for event in events]
    return list_events

# main params
params_diction = {"sort_by": "date",                  
                  "start_date.keyword": "this_month",
                  "location.address": "Ann Arbor",
                  "location.within": "1mi",
                  "expand": "category,organizer,venue"}

#----- FREE EVENTS -----#
params_diction["price"]= "free"
list_events_free = create_event_list(REQUEST_URL, params_diction)
writeCSV('Eventbrite_Free_AnnArbor', list_events_free)

#----- PAID EVENTS -----#
params_diction["price"]= "paid"
list_events_paid = create_event_list(REQUEST_URL, params_diction)
writeCSV('Eventbrite_Paid_AnnArbor', list_events_paid)
