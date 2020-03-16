import datetime
import pytz
import random
import appdaemon.plugins.hass.hassapi as hass

#SPEAKER = 'media_player.arpi'
SPEAKER = 'media_player.living_room_display'
SOMEONE_AT_HOME = 'input_boolean.someone_at_home'
TURN_TV_ON_SCRIPT = 'script.switch_tv_to_f1'
#TTS_SERVICE = 'tts/google_say'
#TTS_LANGUAGE = 'hu'
#TTS_SERVICE = 'tts/mygooglecloudtts_say'
TTS_SERVICE = 'tts/google_cloud_say'
TTS_LANGUAGE = 'hu-HU'

DEBUG = False

class f1_reminder(hass.Hass):
    def initialize(self):
        # https://www.f1calendar.com/#!/timezone/Europe-Budapest
        self.events = {
#            'ausztrál':   ['2020-03-14 07:00', '2020-03-15 06:05', 'Melbörnből'],
#            'bahreini':   ['2020-03-21 16:00', '2020-03-22 16:05', 'ből'],
#            'vietnami':   ['2020-04-04 10:00', '2020-04-05 09:05', 'ból'],
#            'kínai':      ['2020-04-18 09:00', '2020-04-19 08:05', 'Sánghájból'],
            'holland':    ['2020-05-02 15:00', '2020-05-03 14:05', 'ból'],
            'spanyol':    ['2020-05-09 15:00', '2020-05-10 15:05', 'Katalunyából'],
            'monakói':    ['2020-05-23 15:00', '2020-05-24 15:05', 'Monte Carlóból'],
            'azeri':      ['2020-06-06 15:00', '2020-06-07 14:05', 'Bakuból'],
            'kanadai':    ['2020-06-13 20:00', '2020-06-14 20:05', 'Montreálból'],
            'francia':    ['2020-06-27 15:00', '2020-06-28 15:05', 'Paul Ricardból'],
            'osztrák':    ['2020-07-04 15:00', '2020-07-05 15:05', 'Spielbergből'],
            'brit':       ['2020-07-18 16:00', '2020-07-19 16:05', 'Silverstoneból'],
            'magyar':     ['2020-08-01 15:00', '2020-08-02 15:05', 'a hungaroringről'],
            'belga':      ['2020-08-29 15:00', '2020-08-30 15:05', 'Szpá-Frankorsampból'],
            'olasz':      ['2020-09-05 15:00', '2020-09-06 15:05', 'Monzából'],
            'szingapúri': ['2020-09-19 15:00', '2020-09-20 14:05', ''],
            'orosz':      ['2020-09-26 14:00', '2020-09-27 13:05', 'Szocsiból'],
            'japán':      ['2020-10-10 08:00', '2020-10-11 06:05', 'Szuzukából'],
            'amerikai':   ['2020-10-24 23:00', '2020-10-25 20:05', 'Ósztinból'],
            'mexikói':    ['2020-10-31 20:00', '2020-11-01 20:05', 'Mexikóvárosból'],
            'brazil':     ['2020-11-14 19:00', '2020-11-15 18:05', 'Szao Paulóból'],
            'abu dabii':  ['2020-11-28 14:00', '2020-11-29 14:05', 'Jasz Marinából'],
        }
        self.vowels = ['a', 'á', 'e', 'é', 'i', 'í', 'o', 'ö', 'ő', 'u', 'ú', 'ü', 'ű']
        self.dayname = [
            'hétfőn', 'kedden', 'szerdán', 'csütörtökön', 'pénteken', 'szombaton', 'vasárnap'
        ]
        self.monthname = [
            'január', 'február', 'március', 'április', 'május', 'június', 'július',
            'augusztus', 'szeptember', 'október', 'november', 'december'
        ]

        self.listen_event(self.next_event_check, "event_f1_announcement")

        for eventname, eventdata in self.events.items():
            text = f"{eventname} forma 1 " + random.choice(\
            ['időmérő', 'edzés', 'kvalifikáció', 'időmérő edzés'])
            self.add_event_listener(eventdata[0], text, eventdata[2])

            text = f"{eventname} forma 1 "+random.choice(\
                ['verseny', 'futam', 'grand prix', 'nagydíj'])
            self.add_event_listener(eventdata[1], text, eventdata[2])


    def add_event_listener(self, datestring, event_description, location):
        date = datestring.split(' ')[0].split('-')
        time = datestring.split(' ')[1].split(':')
        when = datetime.datetime(int(date[0]), int(date[1]), int(date[2]), \
                                 int(time[0]), int(time[1]), 0)

        text = self.nice_text(event_description, location)

        if when > datetime.datetime.now():
            self.run_at(self.event_listener, when, message=text)
            if DEBUG:
                self.log(when.isoformat()+" added", "INFO")
        else:
            if DEBUG:
                self.log(when.isoformat()+" is in the past", "INFO")


    def announce(self, text):
        self.fire_event("tts_announce", message=text)


    def nice_text(self, text, location):
        start = "a"
        if (text[0] in self.vowels):
            start = "az"
        text = start + " " + text
        if (location > ""):
            text += " " + location
        return text


    def nice_date(self, date):
        text = ""
        diff = date - datetime.datetime.now()
        if diff.days == 0:
            text += "ma"
        elif diff.days == 1:
            text += "holnap"
        elif diff.days == 2:
            text += "holnapután"
        else:
            weekdiff = date.isocalendar()[1] - datetime.datetime.now().isocalendar()[1]
            if weekdiff==1 or weekdiff==2:
                text += "jövő "
                if weekdiff==2:
                    text += " utáni "
                text += self.dayname[date.isocalendar()[2]-1]
            else:
                text += self.monthname[date.month-1] + " " + str(date.day)

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

                if SPEAKER>'':
                    self.announce(str)

                self.turn_on(TURN_TV_ON_SCRIPT)
            else:
                str += ', de senki nincs itthon, ezért nem kapcsolom be a TV-t'

            self.log(str)
            self.call_service("logbook/log", message=str, name="f1_reminder")

    def next_event_check(self, event, data, args):
        for eventname, eventdata in self.events.items():
            text = f"{eventname} forma 1 "+random.choice(\
                ['verseny', 'futam', 'grand prix', 'nagydíj'])
            hasResult = self.check_single_event(eventdata[1], text, eventdata[2])
            if hasResult:
                break

        if not hasResult:
            self.announce(random.choice([
                'Idén nincsen már több verseny',
                'Erre az évre már nincsen több futam a naptárban',
                ]))


    def check_single_event(self, datestring, event_description, location):
        date = datestring.split(' ')[0].split('-')
        time = datestring.split(' ')[1].split(':')
        when = datetime.datetime(int(date[0]), int(date[1]), int(date[2]), \
                                 int(time[0]), int(time[1]), 0)

        if when > datetime.datetime.now():
            text = "A következő "
            text += self.nice_text(event_description, location)
            text += ", " + self.nice_date(when)
            self.announce(text)
            return True
        else:
            return False
