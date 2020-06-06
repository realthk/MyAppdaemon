import pytz
import appdaemon.plugins.hass.hassapi as hass
import datetime

NOTIFY_SERVICE = 'notify/pushbullet'
MY_PERSON = 'person.henrik'

class away_notify(hass.Hass):

    def initialize(self):
        self.listen_event(self.away_notify,  "away_notify")        

    def away_notify(self, event, data, args):
        if data is not None and 'message' in data:
            message = data.get("message")
            if self.get_state(MY_PERSON)!="home":
                self.call_service(NOTIFY_SERVICE, message=message + " (" + datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S") + ")")
                self.log("'" + message + "' sent.", level="INFO", log="diag_log")
            else:
                self.log("'" + message + "' NOT sent.", level="INFO", log="diag_log")


