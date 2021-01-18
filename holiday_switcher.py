import datetime
import pytz
import appdaemon.plugins.hass.hassapi as hass
import holidays

HOLIDAY_MODE = 'input_boolean.holiday_mode'

class holiday_switcher(hass.Hass):
    def initialize(self):
        self.events = {
            '2020-12-22': 'Szabadság',
            '2020-12-23': 'Szabadság',
            '2020-12-28': 'Szabadság',
            '2020-12-29': 'Szabadság',
            '2020-12-30': 'Szabadság',
            '2020-12-31': 'Szabadság',
            '2021-01-01': 'Újév',
        }

        onceDT = datetime.time(0, 1, 0)
        self.run_daily(self.event_listener, onceDT)


    def event_listener(self, kwargs):
        str = ""
        holidayName = ""
        aHoliday = holidays.CountryHoliday('HU').get_list(datetime.datetime.now())
        if (len(aHoliday)>0):
            holidayName = aHoliday[0]

        if not holidayName:
            dateStr = datetime.datetime.now().strftime("%Y-%m-%d")
            for eventdate, eventname in self.events.items():
                if eventdate == dateStr:
                    holidayName = eventname
                    break

        if holidayName:
            if self.get_state(HOLIDAY_MODE)=="off":
                self.turn_on(HOLIDAY_MODE)
                str = "'" + holidayName + "' miatt bekapcsolva munkaszüneti nap üzemmód."
        else:
            if self.get_state(HOLIDAY_MODE)=="on":
                self.turn_off(HOLIDAY_MODE)
                str = "Lekapcsolva a munkaszüneti nap üzemmód."

        if str:
            self.call_service("persistent_notification/create", message=str, title="Munkaszüneti nap kapcsoló")
            self.call_service("logbook/log", message=str, name="holiday_switcher")
