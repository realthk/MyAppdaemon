from datetime import datetime, timedelta
import datetime as dt
import time
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

BASE_URL = "https://github.com/sportstimes/f1/raw/master/db/"
GOOGLE_APPLICATION_CREDENTIALS="/conf/google_ha_service_account.json"
LANG = "hu"
LOCALE = "hu_HU"
TZ = "Europe/Budapest"

MINUTES_BEFORE_RACE = 5
SOMEONE_AT_HOME = 'input_boolean.someone_at_home'
TURN_TV_ON_SCRIPT = 'script.switch_tv_to_f1'

class Race:
    def __init__(self, name, translatedName, location, translatedLocation, qualifying, race, countRaces, counter):
        self.name = name
        self.translatedName = translatedName
        self.location = location
        self.translatedLocation = translatedLocation
        self.qualifying = qualifying
        self.race = race
        self.countRaces = countRaces
        self.currentCount = counter
        self.timerQual = 0
        self.timerRace = 0

class f1_reminder(hass.Hass):

    EVENT_TYPE_QUAL = 1
    EVENT_TYPE_RACE = 2

    def initialize(self):
        self.UTC = tz.gettz('UTC')
        self.localTZ = tz.gettz(TZ)
        self.day_name = ['hétfőn', 'kedden', 'szerdán', 'csütörtökön', 'pénteken', 'szombaton', 'vasárnap']
        self.month_name = [
            'január', 'február', 'március', 'április', 'május', 'június', 'július',
            'augusztus', 'szeptember', 'október', 'november', 'december'
        ]
        self.qual_names = ['időmérő', 'edzés', 'kvalifikáció', 'időmérő edzés']
        self.race_names = ['verseny', 'futam', 'grand prix', 'nagydíj', 'rendezvény']
        self.vowels = ['a', 'á', 'e', 'é', 'i', 'í', 'o', 'ö', 'ő', 'u', 'ú', 'ü', 'ű']
        self.races = []
        credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS)
        self.translate_client = translate.Client(credentials=credentials)

        self.load_events(None)

        self.set_textvalue("input_text.next_f1_race", self.next_event_text())

        self.listen_event(self.check_next_event, "event_f1_announcement")

        onceDT = dt.time(0, 1, 0)
        self.run_daily(self.load_events, onceDT)

    def announce(self, text):
        self.fire_event("tts_announce", message=text)

    def add_event_listener(self, event, event_type):
        handle = None
        if event_type==self.EVENT_TYPE_QUAL:
            when = event.qualifying
        else:
            when = event.race
        if when > datetime.now().astimezone(self.localTZ):
            handle = self.run_at(self.event_listener, when, event=event, event_type=event_type)
        return handle

    def event_listener(self, kwargs):
        if kwargs is not None and 'event' in kwargs and 'event_type' in kwargs:
            event = kwargs.get("event")
            text = event.translatedName + " forma 1 "
            if kwargs.get("event_type")==self.EVENT_TYPE_QUAL:
                text += random.choice(self.qual_names)
            else:
                text += random.choice(self.race_names)
            text = self.nice_text(text, event.translatedLocation)

            str = random.choice(['Rövidesen', 'Mindjárt', 'Éppen', 'Hamarosan', 'Nem sokára']) + ' ' + \
                  random.choice(['indul', 'kezdődik', 'rajtol', 'elstartol'])

            if event.currentCount==1:
                str += " idén az első"
            elif event.currentCount==event.countRaces:
                str += " idén az utolsó"
            elif event.currentCount==event.countRaces-1:
                str += " idén az utolsó előtti"

            str += (' ' + text)

            if self.get_state(SOMEONE_AT_HOME)=="on":
                str += ', ezért ' + \
                   random.choice([\
                        'most',
                        'hogy le ne maradj róla,',
                        'hogy kedveskedjek,',
                        'figyelmességből'
                        'a kedvedért'
                        ]) + ' ' + \
                   'bekapcsolom a TV-t'

                self.announce(str)

                self.turn_on(TURN_TV_ON_SCRIPT)
            else:
                str += ', de senki nincs itthon, ezért nem kapcsolom be a TV-t'

            self.log(str, level="INFO")
            self.call_service("logbook/log", message=str, name="f1_reminder")

    def load_events(self, kwargs):
        start_time = time.time()
        URL = BASE_URL + str(datetime.now().year) + ".json"
        response = requests.get(URL)
        if not response or not len(response.content):
            self.log(f"Cannot get F1 race calendar from '{URL}'! (ERROR: " + str(response.status_code) + ")", level="ERROR")
            return False

        new = changed = 0
        j = json.loads(response.content)
        if len(j['races']):
            oldRaces = deepcopy(self.races)
            for race in self.races:
                if race.qualifying > datetime.now().astimezone(self.localTZ) and race.timerQual:
                    self.cancel_timer(race.timerQual)
                if race.race > datetime.now().astimezone(self.localTZ) and race.timerRace:
                    self.cancel_timer(race.timerRace)
            self.races = []

            counter = 0
            for event in j['races']:
                counter += 1
                translatedName = self.translate_client.translate(event['name'].lower().replace("grand prix", ""), LANG)['translatedText']
                translatedLocation = self.translate_client.translate("from the " + event['location'], LANG)['translatedText'].replace("a ", "")
                qualDate = datetime.strptime(event['sessions']['qualifying'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=self.UTC).astimezone(self.localTZ)
                raceDate = datetime.strptime(event['sessions']['race'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=self.UTC).astimezone(self.localTZ)
                race = Race(event['name'], translatedName, event['location'], translatedLocation, qualDate, raceDate - timedelta(minutes = MINUTES_BEFORE_RACE), len(j['races']), counter)
                self.races.append(race)
                msg = race.name + " "
                for old in oldRaces:
                    if old.name == race.name:
                        if old.qualifying!=race.qualifying or old.race!=race.race:
                            changed+=1
                            msg += "has changed date (qualifying: " + race.qualifying.astimezone(self.localTZ).strftime("%Y.%m.%d %H:%M:%S")
                            msg += ", race: " + raceDate.astimezone(self.localTZ).strftime("%Y.%m.%d %H:%M:%S") + ")"
                        else:
                            msg += "unchanged on " + raceDate.astimezone(self.localTZ).strftime("%Y.%m.%d %H:%M:%S")
                        break
                else:
                    new+=1
                    if race.race > datetime.now().astimezone(self.localTZ):
                        msg += "will be"
                    else:
                        msg += "was"
                    msg += " on " + raceDate.astimezone(self.localTZ).strftime("%Y.%m.%d %H:%M:%S")
                self.log(msg, level="INFO")

            runtime = round((time.time() - start_time) * 1000)
            if new or changed:
                self.log(f"Loaded {new} race, changed {changed} in {runtime} ms.", level="INFO")

            for race in self.races:
                race.timerQual = self.add_event_listener(race, self.EVENT_TYPE_QUAL)
                race.timerRace = self.add_event_listener(race, self.EVENT_TYPE_RACE)

            return True
        else:
            self.log("F1 race calendar is empty!", level="WARNING")
            return False

    def check_next_event(self, event, data, args):
        text =  self.next_event_text()
        self.announce(text)

    def next_event_text(self):
        text = ""
        if len(self.races):
            for event in self.races:
                if event.race > datetime.now().astimezone(self.localTZ):
                    text = "A következő "
                    text += self.nice_text(event.translatedName + " " + random.choice(self.race_names), event.translatedLocation)
                    text += ", " + self.nice_date(event.race)
                    if event.qualifying > datetime.now().astimezone(self.localTZ) and self.calendardays_diff(event.qualifying, datetime.now().astimezone(self.localTZ)) < 3:
                        text += ", az edzés pedig " + self.nice_date(event.qualifying)
                    text += " lesz."
                    break
            else:
                text = random.choice([
                    'Idén nincsen már több verseny',
                    'Erre az évre már nincsen több futam a naptárban',
                    ])
        else:
            text = "Üres a versenynaptár"

        return text

    def nice_text(self, text, location):
        start = "a"
        if (text[0] in self.vowels):
            start = "az"
        text = start + " " + text
        if (location > ""):
            text += " " + location
        return text

    def calendardays_diff(self, date1, date2):
        A = date1.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        B = date2.now().astimezone(self.localTZ).replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        return (A - B).days

    def nice_date(self, date):
        text = ""
        days  = self.calendardays_diff(date, datetime.now().astimezone(self.localTZ))
        if days == 0:
            text += "ma"
        elif days == 1:
            text += "holnap"
        elif days == 2:
            text += "holnapután"
        else:
            weekdiff = date.isocalendar()[1] - datetime.now().astimezone(self.localTZ).isocalendar()[1]
            if weekdiff==1 or weekdiff==2:
                text += "jövő "
                if weekdiff==2:
                    text += " utáni "
                text += self.day_name[date.isocalendar()[2]-1]
            else:
                text += self.month_name[date.month-1] + " " + str(date.day)

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
