from datetime import datetime, timedelta
import datetime as dt
import calendar
import locale
import requests
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from copy import deepcopy
from dateutil import tz
import json
import pytz
import random
import appdaemon.plugins.hass.hassapi as hass

GOOGLE_APPLICATION_CREDENTIALS="/conf/google_ha_service_account.json"
LANG = "hu"
LOCALE = "hu_HU.utf8"
TZ = "Europe/Budapest"

MINUTES_BEFORE_RACE = 5
SOMEONE_AT_HOME = 'input_boolean.someone_at_home'
TURN_TV_ON_SCRIPT = 'script.switch_tv_to_f1'

class Race:  
    def __init__(self, name, translatedName, location, translatedLocation, qualifying, race):  
        self.name = name  
        self.translatedName = translatedName  
        self.location = location  
        self.translatedLocation = translatedLocation  
        self.qualifying = qualifying  
        self.race = race  
        self.timerQual = 0
        self.timerRace = 0

class f1_reminder(hass.Hass):
    def initialize(self):
        self.UTC = tz.gettz('UTC')
        self.localTZ = tz.gettz(TZ)
        self.day_name = ['hétfőn', 'kedden', 'szerdán', 'csütörtökön', 'pénteken', 'szombaton', 'vasárnap']        
        self.baseURL = "https://github.com/sportstimes/f1/raw/master/db/"
        self.vowels = ['a', 'á', 'e', 'é', 'i', 'í', 'o', 'ö', 'ő', 'u', 'ú', 'ü', 'ű']
        self.races = []
        credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
        self.translate_client = translate.Client(credentials=credentials)

        self.load_events()

        self.listen_event(self.announce_next_event, "event_f1_announcement")

        onceDT = dt.time(0, 1, 0)
        self.run_daily(self.load_events, onceDT)                

    def announce(self, text):
        self.fire_event("tts_announce", message=text)        

    def add_event_listener(self, when, event_description, location):
        text = self.nice_text(event_description, location)
        handle = None
        if when > datetime.now().astimezone(self.localTZ):
            handle = self.run_at(self.event_listener, when, message=text)
        return handle

    def event_listener(self, kwargs):
        if kwargs is not None and 'message' in kwargs:
            text = kwargs.get("message")
            str = random.choice(['Rövidesen', 'Mindjárt', 'Éppen']) + ' ' + \
                  random.choice(['indul', 'kezdődik', 'rajtol']) + ' ' + text

            if self.get_state(SOMEONE_AT_HOME)=="on":
                str += ', ezért ' + \
                   random.choice([\
                        'most',
                        'hogy le ne maradj róla,',
                        'hogy kedveskedjek,',
                        'figyelmességből'
                        ]) + ' ' + \
                   'bekapcsolom a TV-t'

                self.announce(str)

                self.turn_on(TURN_TV_ON_SCRIPT)
            else:
                str += ', de senki nincs itthon, ezért nem kapcsolom be a TV-t'

            self.log(str, level="INFO")
            self.call_service("logbook/log", message=str, name="f1_reminder")                    


    def load_events(self):
        URL = self.baseURL + str(datetime.now().year) + ".json"
        r = requests.get(URL)
        new = changed = 0
        if len(r.content):
            j = json.loads(r.content)
            if len(j['races']):
                oldRaces = deepcopy(self.races)
                for race in self.races:
                    if race.qualifying > datetime.now().astimezone(self.localTZ) and race.timerQual:
                        self.cancel_timer(race.timerQual)
                    if race.race > datetime.now().astimezone(self.localTZ) and race.timerRace:
                        self.cancel_timer(race.timerRace)
                self.races = []

                for event in j['races']:
                    translatedName = self.translate_client.translate(event['name'], LANG)['translatedText']
                    translatedLocation = self.translate_client.translate("from the " + event['location'], LANG)['translatedText'].replace("a ", "")
                    qualDate = datetime.strptime(event['sessions']['qualifying'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=self.UTC).astimezone(self.localTZ)
                    raceDate = datetime.strptime(event['sessions']['race'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=self.UTC).astimezone(self.localTZ)
                    race = Race(event['name'], translatedName, event['location'], translatedLocation, qualDate, raceDate - timedelta(minutes = MINUTES_BEFORE_RACE))
                    self.races.append(race)
                    found = False
                    msg = race.name + " "
                    for old in oldRaces:
                        if old.name == race.name:
                            found = True
                            if old.qualifying!=race.qualifying or old.race!=race.race:
                                changed+=1
                                msg += "has changed date (qual: " + race.qualifying.astimezone(self.localTZ).isoformat() + ", race: " + race.race.astimezone(self.localTZ).isoformat() + ")"
                            else:
                                msg += "unchanged."
                    if not found:
                        new+=1
                        msg += "is new on " + race.race.astimezone(self.localTZ).isoformat()
                    self.log(msg, level="INFO")
                if new>0:
                    self.log(f"Loaded {new} race, changed {changed}.", level="INFO")

                for race in self.races:
                    text = race.translatedName + " forma 1 " + random.choice(\
                        ['időmérő', 'edzés', 'kvalifikáció', 'időmérő edzés'])
                    race.timerQual = self.add_event_listener(race.qualifying, text, race.translatedLocation)

                    text = race.translatedName + " forma 1 "+random.choice(\
                        ['verseny', 'futam', 'grand prix', 'nagydíj'])
                    race.timerRace = self.add_event_listener(race.race, text, race.translatedLocation)
                    if race.timerQual or race.timerRace:
                        self.log(race.name +" timer set.", level="INFO")
            else:
                self.log("F1 race calendar is empty!", level="WARNING")
        else:
            self.log("Cannot get F1 race calendar!", level="ERROR")

    def check_next_event(self):
        if len(self.races):
            found = False
            for event in self.races:
                if event.race > datetime.now().astimezone(self.localTZ):
                    found = True
                    self.announce_event(event)
                    break

            if not found:
                self.announce(random.choice([
                    'Idén nincsen már több verseny',
                    'Erre az évre már nincsen több futam a naptárban',
                    ]))                
                
        else:
            self.announce("Üres a versenynaptár")                
    
    def announce_next_event(self, event):
        text = "A következő "
        text += self.nice_text(event.translatedName, event.translatedLocation)
        text += ", " + self.nice_date(event.race)
        self.announce(text)

    def nice_text(self, text, location):
        start = "a"
        if (text[0] in self.vowels):
            start = "az"
        text = start + " " + text
        text += " forma 1 "+random.choice(['verseny', 'futam', 'grand prix', 'nagydíj', 'rendezvény'])
        if (location > ""):
            text += " " + location
        return text

    def nice_date(self, date):
        text = ""
        diff = date - datetime.now().astimezone(self.localTZ)
        if diff.days == 0:
            text += "ma"
        elif diff.days == 1:
            text += "holnap"
        elif diff.days == 2:
            text += "holnapután"
        else:
            weekdiff = date.isocalendar()[1] - datetime.now().astimezone(self.localTZ).isocalendar()[1]
            locale.setlocale(locale.LC_ALL, LOCALE)
            if weekdiff==1 or weekdiff==2:
                text += "jövő "
                if weekdiff==2:
                    text += " utáni "
                text += self.day_name[date.isocalendar()[2]-1]
            else:
                text += calendar.month_name[date.month] + " " + str(date.day)    

        hour = date.hour
        daypart = ""
        if hour < 6:
            daypart = "hajnalban"
        elif hour < 9:
            daypart = "reggel"
        elif hour < 12:
            daypart = "délelőtt"
        elif hour < 19:
            daypart = "délután"
            hour -= 12
        elif hour < 22:
            daypart = "este"
            hour -= 12
        else:
            daypart = "éjjel"
            hour -= 12
        text += " " + daypart + " " + str(hour) + "-kor"
        return text       
