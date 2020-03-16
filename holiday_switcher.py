import datetime
import pytz
import appdaemon.plugins.hass.hassapi as hass

HOLIDAY_MODE = 'input_boolean.holiday_mode'

class holiday_switcher(hass.Hass):
    def initialize(self):
        self.events = {
            '2019-06-10': 'Pünkösd hétfő',
            '2019-08-19': 'Gusztus 20',
            '2019-08-20': 'Gusztus 20',
            '2019-10-23': 'Október 23',
            '2019-11-01': 'Mindenszentek',
            '2019-12-24': 'Szenteste',
            '2019-12-25': 'Karácsony',
            '2019-12-26': 'Karácsony',
            '2019-12-27': 'Karácsony',
            '2019-12-30': 'Szilveszter',
            '2019-12-31': 'Szilveszter',
            '2020-01-01': 'Újév',
            '2020-04-10': 'Nagypéntek',
            '2020-04-13': 'Húsvét',
            '2020-05-01': 'Május 1',
            '2020-06-01': 'Pünkösd',
            '2020-08-20': 'Gusztus 20',
            '2020-08-21': 'Gusztus 20',
            '2020-10-23': 'Október 23',
            '2020-11-01': 'Mindenszentek',
            '2020-12-24': 'Szenteste',
            '2020-12-25': 'Karácsony',
            '2021-01-01': 'Újév',
        }

        onceDT = datetime.time(0, 1, 0)
        self.run_daily(self.event_listener, onceDT)


    def event_listener(self, kwargs):
        dateStr = datetime.datetime.now().strftime("%Y-%m-%d")
 
        str = ""
        holiday = False
        for eventdate, eventname in self.events.items():
            if eventdate == dateStr:
                holiday = True
                if self.get_state(HOLIDAY_MODE)=="off":
                    self.turn_on(HOLIDAY_MODE)
                    str = eventname + " miatt bekapcsolva munkaszüneti nap üzemmód."
                    break
        
        if not holiday and self.get_state(HOLIDAY_MODE)=="on":
            self.turn_off(HOLIDAY_MODE)
            str = "Lekapcsolva a munkaszüneti nap üzemmód."

        if str:
            self.call_service("persistent_notification/create", message=str, title="Munkaszüneti nap kapcsoló")
            self.call_service("logbook/log", message=str, name="holiday_switcher")
