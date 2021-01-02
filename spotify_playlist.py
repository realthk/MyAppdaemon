import pytz
import random
import appdaemon.plugins.hass.hassapi as hass
import time
from datetime import datetime

# For "rest_command/restart_spotify_connect" to work, has to create this command in configuration.yaml
# (HA client usually disappears from Spotify Connect list after some time, and gets back after restart)
"""
rest_command:
  restart_spotify_connect:
    url: http://supervisor/addons/a0d7b954_spotify/restart
    method: POST
    headers:
      authorization: !secret api_bearer_token
      Content-Type: "application/json"
"""
# And in secrets.yaml
# api_bearer_token: "Bearer xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# where token is provided by Remote API proxy installed from  https://developers.home-assistant.io/


SPOTIFY = 'media_player.spotify_realthk'
SOURCE_BRIX = "HomeAssistant"
SOURCE_BEDROOM = "Bedroom Speaker"
AVR_LIVINGROOM  = 'media_player.pioneer_avr'
AVR_BEDROOM     = 'media_player.pioneer_avr_zone2'
BEDROOM_SPEAKER = 'media_player.bedroom'
ALARM_FIRED_FLAG = 'input_boolean.spotify_alarm_fired'
SOMEONE_WOKE_UP_FLAG = 'input_boolean.someone_woke_up_after_alarm'
SPOTIFY_SWITCHED_FLAG = 'input_boolean.spotify_music_switched_to_living_room'
RETRIES = 5
SONGRETRIES = 3
SPEAKER = 'media_player.living_room_display'
TTS_SERVICE = 'tts/google_cloud_say'
TTS_LANGUAGE = 'hu-HU'

class spotify_playlist(hass.Hass):
    AVRused = True

    def initialize(self):
        self.vowels = ['a', 'á', 'e', 'é', 'i', 'í', 'o', 'ö', 'ő', 'u', 'ú', 'ü', 'ű']
        self.morning_list = {
            "Birds in the forest":              "spotify:user:spotify:playlist:37i9dQZF1DWVEt8B7a1H1M",
            "Wake up and smell coffee":         "spotify:user:spotify:playlist:37i9dQZF1DXcxacyAXkQDu",
            "Have a great day ":                "spotify:user:spotify:playlist:37i9dQZF1DX7KNKjOK0o75",
            "Morning motivation":               "spotify:user:spotify:playlist:37i9dQZF1DXc5e2bJhV6pu",
            "Wake up happy":                    "spotify:user:spotify:playlist:37i9dQZF1DX0UrRvztWcAU",
            "Tastebreakers":                    "spotify:user:spotify:playlist:37i9dQZF1EiR27oyeR6BZz",
            "Mellow morning":                   "spotify:user:spotify:playlist:37i9dQZF1DWWzVPEmatsUB",
            "Mood booster":                     "spotify:user:spotify:playlist:37i9dQZF1DX3rxVfibe1L0",
            "Confidence boost":                 "spotify:user:spotify:playlist:37i9dQZF1DX4fpCWaHOned",
            "Monday motivation":                "spotify:user:spotify:playlist:37i9dQZF1DX1OY2Lp0bIPp",
            "John Lennon":                      "spotify:artist:4x1nvY2FN8jxqAFA0DA02H",
            "80s hits":                         "spotify:user:spotify:playlist:37i9dQZF1DXb57FjYWz00c",
            "Easy 80s":                         "spotify:user:spotify:playlist:37i9dQZF1DX6l1fwN15uV5",
            "All out 80s":                      "spotify:user:spotify:playlist:37i9dQZF1DX4UtSsGT1Sbe",
            "80s Miami cocaine":                "spotify:user:119372264:playlist:2f09qLyyLKgRnH2s9547fj",
            "Beatles radio":                    "spotify:user:spotify:playlist:37i9dQZF1E4BV5Wf9ansml",
            "Get home happy":                   "spotify:user:spotify:playlist:37i9dQZF1DXeby79pVadGa",
            "Feelin good":                      "spotify:user:spotify:playlist:37i9dQZF1DX9XIFQuFvzM4",
            "Positive vibes":                   "spotify:user:spotify:playlist:37i9dQZF1DWUAZoWydCivZ",
            "Happy pop hits":                   "spotify:user:spotify:playlist:37i9dQZF1DWVlYsZJXqdym",
            "Feel good friday":                 "spotify:user:spotify:playlist:37i9dQZF1DX1g0iEXLFycr",
            "Easy 90s":                         "spotify:user:spotify:playlist:37i9dQZF1DWV8xrpik0esU",
            "Happy folk":                       "spotify:user:spotify:playlist:37i9dQZF1DWSkMjlBZAZ07",
            "Easy 60s":                         "spotify:user:spotify:playlist:37i9dQZF1DWZWYUuTGjjhE",
            "Easy 70s":                         "spotify:user:spotify:playlist:37i9dQZF1DWSWNiyXQAvbl",
            "Just smile":                       "spotify:user:spotify:playlist:37i9dQZF1DWVu0D7Y8cYcs",
            "Friday funday":                    "spotify:user:spotify:playlist:37i9dQZF1DX2Psgy8H1wu7",
            "Arab mood booster":                "spotify:user:spotify:playlist:37i9dQZF1DWYBAUZiPMirH",
            "Morning bossa n jazz":             "spotify:user:borwornm:playlist:38mZ38uR8itU9ZJR3WJJtf",
            "All out of 60s":                   "spotify:user:spotify:playlist:37i9dQZF1DXaKIA8E7WcJj",
            "Alternative 60s":                  "spotify:user:spotify:playlist:37i9dQZF1DX5qNE4zrflL7",
            "60s, 70s, 80s classic rock":       "spotify:user:4wruv3fyqtjrp8sc4r66sfezh:playlist:5FuRHPeSD72GhmRY4RhM7X",
            "60s allerbeste":                   "spotify:user:spotify:playlist:37i9dQZF1DX0ZEgBnamJNd",
            "60s smash hits":                   "spotify:user:myplay.com:playlist:31LVuXlRYRVq4Z6krWGedS",
            "60s and  70s played on oldies":    "spotify:user:willsagraves:playlist:1rBmDe5HGnRfMATuqJZrps",
            "Oldies 80s 70s 60s best songs":    "spotify:user:sanik007:playlist:1TNg7JCxifAjwrnQARimex",
            "Rock and roll 50s 60s":            "spotify:user:21f72cob23id3qkhxyiuxdyja:playlist:0pRQRASH4cCPJlCQNYAdKK",
            "Happy days":                       "spotify:user:spotify:playlist:37i9dQZF1DX84kJlLdo9vT",
            "Classic oldies":                   "spotify:user:spotify:playlist:37i9dQZF1DX56bqlsMxJYR",
            "Classic 60s":                      "spotify:user:legacysweden:playlist:5n6Qo8WNYc5oVBmGbO2iYG",
            "Top 1000 oldies hits":             "spotify:user:diestro:playlist:0ldz31wyL6VPUfcJHwWmQR",
            "Best of 60s, 70s, 80s and 90s":    "spotify:user:1163571455:playlist:04UMVlWWVJJQEJzZvsnKy7",
            "60s/70s acoustic rock":            "spotify:user:aidan.a.zufolo:playlist:3DfUINo8a3K4yogzaL6Dej",
            "Oldies 60s best of":               "spotify:user:22d2joumnedmpekg352dt57ti:playlist:37UmKX8PkFmwHZGH9pefTs",
            "60s dance party":                  "spotify:user:drssb:playlist:3AtyPNtuJTmOjXRimFGa5x",
            "Greatest 60s hits ever":           "spotify:user:playlistmeukfeatured:playlist:0TJY4WN5dmKpbSZf77VAJe",
            "All out of 60s, 70s, 80s, 90s":    "spotify:user:leobosss02:playlist:3mciKnAAmxjOgfkSf27lHH",
            "Vietnam war era music":            "spotify:user:fe9tt9ixsnby6ps13wvnq4pxj:playlist:0EAjSsXy7GhxXtmYtwv1Bs",
            "Classic 50s, 60s":                 "spotify:user:rebeccaszulga:playlist:5QtBHTc3XN6W9Ey8h122Vl",
            "The sixties":                      "spotify:user:12179810579:playlist:0b2CO1VoiRQiVvaShqk8pJ",
            "60s songs":                        "spotify:user:listanauta:playlist:4dFKQEBMgsW2RlLBhTz1Pk",
            "60s, 70s, 80s hits":               "spotify:user:mayagal1707:playlist:7bGL2eYs5LYqjVhX41G5ov",
            "Best 60s to 70s":                  "spotify:user:sergiolohn:playlist:5Jkqe7oQ3mSWhDhkJrt2HG",
            "Top 60s classic hits":             "spotify:user:1276640268:playlist:2oxMpeZNUjt7HfOklaTQAP",
            "All out of 50s, 60s, 70s and 80s": "spotify:user:cameron.greenwood108:playlist:44aLSiKMThIYqDg6Eh5OSl",
            "Happy 60s songs only":             "spotify:user:22myddujetdgtwujrqflhg5ei:playlist:44kmQC1wJrCUtFQ5hJoRFS",
            "60s-80s- happy songs":             "spotify:user:121917471:playlist:12kNJT8B3hzCuVtZDeBD1H",
            "Upbeat 50s 60s":                   "spotify:user:alecn87:playlist:6kn52dQK8YwytJHZRK0cVi",
            "All out of 60s, 70s, 89s":         "spotify:user:umaon5y2ux93ku4tkiiq2hbso:playlist:566k6DtCQHhjuFKjj0CZTX",
            "Top 60s, 70s and 80s":             "spotify:user:rubyspixart:playlist:3x1j88XfNcvgI35k20OyOf",
            "Early 60s":                        "spotify:user:brendenfar.17:playlist:0KU1eeB1eEFGFz3QWi72q8",
            "Old classics":                     "spotify:user:gabrielleanth:playlist:0wimXO9OGdQugkjly1lNOw",
            "Best of the 50s, 60s and 70s":     "spotify:user:alina.altkind:playlist:05UW3vZYVqIizQEjlXjiat",
            "No milk today: 60s favourites":    "spotify:user:1166942447:playlist:3KCwBSpyzmjyXvs5ljzLLN",
            "60s, 70s, 80s popular music":      "spotify:user:mattalizer:playlist:7xCOF8dQ4X2HfYsctRYG0u",
            "Oldies but goldies 60s-90s":       "spotify:user:vblinder-gb:playlist:0LK1Kzo7crWa2KKtnSwTNe",
            "60s, 70s FM radio classics":       "spotify:user:12142787119:playlist:0irIEzA2bbcoVjoZdfxqXz",
            "60s pop songs":                    "spotify:user:listanauta:playlist:3QvsJIKP9A1G39WwvN6dlt",
            "Flashback 60s, 70s, 80s":          "spotify:user:rodrigofiusson:playlist:7H7bJdBbUpfYBgEcvwjJyk",
            "Throwback top hits":               "spotify:user:pukvanes3101:playlist:1VDWA3ZQcC8hDJ4Lh3E31b",
            "Summer 70s":                       "spotify:user:153x:playlist:2MrIKOlicQYzgn0gzVJcaf",
            "Hits of the 60s, 70s, 80s":        "spotify:user:kellychr004:playlist:7tRjF74dZ8cu8Xbiir3YtX",
            "Best of 60s, 70s, 80s":            "spotify:user:1279575975:playlist:1FyP82XDJBYIbltvnT6lFi",
            "British 60s, 70s":                 "spotify:user:timberford:playlist:7CMNLmmFcVyAPw8bDUB2L0",
            "Mindig péntek Hangfoglaló":        "spotify:playlist:0eIirD06V3j9glcf1jumya",
            "Soft morning":                     "spotify:playlist:37i9dQZF1DXb5Mq0JeBbIw",
        }

        self.sleep_list = {
            "Dreamy vibes": 	                    "spotify:user:spotify:playlist:37i9dQZF1DWSiZVO2J6WeI",
            "Acoustic calm": 	                    "spotify:user:spotify:playlist:37i9dQZF1DXaImRpG7HXqp",
            "Deep sleep": 	                        "spotify:user:spotify:playlist:37i9dQZF1DWYcDQ1hSjOpY",
            "Sleep": 	                            "spotify:user:spotify:playlist:37i9dQZF1DWZd79rJ6a7lp",
            "Peaceful meditation": 	                "spotify:user:spotify:playlist:37i9dQZF1DWZqd5JICZI0u",
            "Meditate to the sounds of nature": 	"spotify:user:spotify:playlist:37i9dQZF1DX1tuUiirhaT3",
            "Stress relief": 	                    "spotify:user:spotify:playlist:37i9dQZF1DWXe9gFZP0gtP",
            "Peaceful piano": 	                    "spotify:user:spotify:playlist:37i9dQZF1DX4sWSpwq3LiO",
            "Songs for sleeping": 	                "spotify:user:spotify:playlist:37i9dQZF1DWStLt4f1zJ6I",
            "Floating through space": 	            "spotify:user:spotify:playlist:37i9dQZF1DX1n9whBbBKoL",
            "Lava lamp": 	                        "spotify:user:spotify:playlist:37i9dQZF1DWWtqHeytOZ8f",
            "Sleep tight": 	                        "spotify:user:spotify:playlist:37i9dQZF1DWSUFOo47GEsI",
            "Binaural beats 'sleep'": 	            "spotify:user:spotify:playlist:37i9dQZF1DX8h3zQNo57xG",
            "Yoga & meditation": 	                "spotify:user:spotify:playlist:37i9dQZF1DX9uKNf5jGX6m",
            "Peaceful retreat": 	                "spotify:user:spotify:playlist:37i9dQZF1DX1T2fEo0ROQ2",
            "Meditation/sleep": 	                "spotify:user:chrisspatola:playlist:5717SM3tpAkXtxXwt19ibS",
            "Deep meditation 50": 	                "spotify:user:1294538383:playlist:2AuzXlM5ma5VEUdW2xllCO",
            "Binaural beats 'meditation'": 	        "spotify:user:spotify:playlist:37i9dQZF1DX5Tgh3tlyc3X",
            "Meditation: frequencies, vibrations": 	"spotify:user:nowrocky:playlist:1Jbt5d9e88pwdteS3IrX9C",
            "Meditation before sleep": 	             "spotify:user:meditationrelaxclub:playlist:3w9WbtHK9BuaulCK7OxyXp",
            "Meditation playlist for deep sleep": 	"spotify:user:1234273080:playlist:09v8l7XFODUhBWI7XZWjQn",
            "Sleep meditation": 	                "spotify:user:1295166195:playlist:0I8mg2ngPlMpDMvNuYcpJx",
            "Meditation sleep radio": 	            "spotify:user:22n3h22ajrjsuhctyogbkhkcy:playlist:5zCeQu2CtcT4mGZsv2RH1R",
            "Chakras and meditation": 	            "spotify:user:1217888767:playlist:5qvKvocJf26jFZFKcd9Wxb",
            "Buddhist mediation songs": 	        "spotify:user:1159774715:playlist:3c4AduB9UOrxkfdW0Nh2hA",
            "Yoga music, spa relaxation, meditation": 	"spotify:user:rfawz6ogwn1s1sy1tkx5joff7:playlist:5xMfrf3XPlxRuuWaqSiXQe",
            "Calm meditation": 	                    "spotify:user:gunner.sinclair:playlist:5HqAfu7bOFiTlkKLiR6tww",
            "Chines meditation music": 	            "spotify:user:zenmusicgarden:playlist:3RpFqqjrJSPSws8YvuH0qc",
            "Deep sleep mediation, 423-852 Hz": 	"spotify:user:paribuddha:playlist:0RiQ7bd0aBvjKzCPYkzf6X",
            "Budist meditation": 	                "spotify:user:215qrkjtdxsviadsgpcrdcwfi:playlist:0k0JsqCjreOWsvQFTDUDog",
            "Mindfulness & meditation": 	        "spotify:user:%2Aruby%2A:playlist:43j9sAZenNQcQ5A4ITyJ82",
            "Spiritual healing meditation": 	    "spotify:user:marc2629:playlist:5LgM7kyPF4ahHfrKFJxpv9",
            "Zen sleep + meditation": 	            "spotify:user:kaylynbell:playlist:1fhvOcfwrRWjAfjs9tqgkm",
            "Transcental mneditation: journey through outer space": 	"spotify:user:rainyday75:playlist:2wRDJSS0nowmVk5v1wMOw8",
            "Yoga and meditation":          	    "spotify:user:niners3434:playlist:3S9a0U2ljqpu8nWdE9uxcU",
            "Sleeping-meditation": 	                "spotify:user:1212746454:playlist:17UCwTVPiBsBG1NQSHa5iE",
            "Crystal meditation": 	                "spotify:user:kkwofficial:playlist:7qIRuIm3H0N20Dn2YLKJxR",
            "Zen meditation music": 	            "spotify:user:zenmeditationplanet:playlist:5JaAKGr0HLHl8wKSDJRjQ3",
            "Lucid dreaming": 	                    "spotify:user:1217592163:playlist:77758KbLZnBhujE3C7Y8O4",
            "Spa, meditation, relaxation music": 	"spotify:user:astrowanderer00:playlist:4XgMq3qJbUofkeNIBKrwIb",
            "Fresh meditation": 	                "spotify:user:meditacao.e:playlist:1pDTasmINC345zHBCIIRDi",
            "Ambient sleeping pill": 	            "spotify:user:stereoscenic:playlist:40cwXRImcYfwTkOhVND8wI",
            "Dreamscape": 	                        "spotify:user:dreamwalker24:playlist:1u6zQrXd14Dv2b3Gu2DhaM",
            "Celtic meditation": 	                "spotify:user:gabi_sash:playlist:2vuaxpgeutNeo107Cr8as4",
            "Sensual tantrix erotic meditation": 	"spotify:user:1214662664:playlist:3nV57nDBkbkLwdUy0Bnmvw",
            "Instrumental study":                   "spotify:playlist:37i9dQZF1DX9sIqqvKsjG8",
            "Organic experimental":                 "spotify:playlist:37i9dQZF1DX4ALYsOGumV8",
        }

        self.sexy_list = {
            "Lo-fi beats": 	                        "spotify:user:spotify:playlist:37i9dQZF1DWWQRwui0ExPn",
            "Chill hits": 	                        "spotify:user:spotify:playlist:37i9dQZF1DX4WYpdgoIcn6",
            "Lounge - soft house": 	                "spotify:user:spotify:playlist:37i9dQZF1DX82pCGH5USnM",
            "Deep House Relax":                     "spotify:user:spotify:playlist:37i9dQZF1DX2TRYkJECvfC",
            "Indian Chill": 	                    "spotify:user:spotify:playlist:37i9dQZF1DX3AQIJcCkXwU",
            "Chill Out Music": 	                    "spotify:user:spotify:playlist:37i9dQZF1DX32oVqaQE8BM",
            "Ibiza Sunset": 	                    "spotify:user:spotify:playlist:37i9dQZF1DX9FIMhEujaK6",
            "Lo-fi / chillhop beats":               "spotify:playlist:6Sh0iYBCG7lu42mwfGf4EG",
            "Lo-Fi house":                          "spotify:playlist:37i9dQZF1DXbXD9pMSZomS",
            "Lo Fo Chill Beats & Coffee":           "spotify:album:42Rk1C4NeDILBbTlxi4fJD",
            "Lo-Fi Hip Hop Chill Wave Radio":       "spotify:album:2EmIIHbojdSlOj8ulSFlBX",
            "Lo-Fi for Ghosts":                     "spotify:playlist:6Nlu15pOVXSGtPONEV2zds",
            "Adderall":                             "spotify:playlist:4nO5GSNhdidHJKKj0pW9pZ",
        }

        self.evening_chill_list = {
            "Tom Waits radio": 	                    "spotify:user:spotify:playlist:37i9dQZF1E4ExaIyMjSY4l",
            "Elvis Presley Radio": 	                "spotify:user:spotify:playlist:37i9dQZF1E4DCb8LyxJ4rN",
            "Passenger Radio": 	                    "spotify:user:spotify:playlist:37i9dQZF1E4ySsLtCRzFVe",
            "Relax & unwind": 	                    "spotify:user:spotify:playlist:37i9dQZF1DWU0ScTcjJBdj",
            "Evening acoustic": 	                "spotify:user:spotify:playlist:37i9dQZF1DXcWBRiUaG3o5",
            "Late Night vibes": 	                "spotify:user:spotify:playlist:37i9dQZF1DXdQvOLqzNHSW",
            "70s Road trip": 	                    "spotify:user:spotify:playlist:37i9dQZF1DWWiDhnQ2IIru",
            "Dark & Stormy": 	                    "spotify:user:spotify:playlist:37i9dQZF1DX2pSTOxoPbx9",
            "Calm Down": 	                        "spotify:user:spotify:playlist:37i9dQZF1DX5bjCEbRU4SJ",
            "John Lennon legend": 	                "spotify:user:eduardo.mckagan:playlist:7nCdbNAqqVHwz7P1Hq429l",
            "Classic acoustic": 	                "spotify:user:spotify:playlist:37i9dQZF1DX504r1DvyvxG",
            "Paul McCartney radio": 	            "spotify:user:spotify:playlist:37i9dQZF1E4AbilptT03rX",
            "The Beatles radio": 	                "spotify:user:spotify:playlist:37i9dQZF1E4BV5Wf9ansml",
            "Pink Floyd radio": 	                "spotify:user:spotify:playlist:37i9dQZF1E4qrJkevzHBMH",
            "70s rock anthems": 	                "spotify:user:spotify:playlist:37i9dQZF1DWWwzidNQX6jx",
            "Easy": 	                            "spotify:user:spotify:playlist:37i9dQZF1DX2czWA9hqErK",
            "Feeling acoustically good": 	        "spotify:user:spotify:playlist:37i9dQZF1DWXRvPx3nttRN",
            "Your favourite coffeehouse": 	        "spotify:user:spotify:playlist:37i9dQZF1DX6ziVCJnEm59",
            "Deep dark indie": 	                    "spotify:user:spotify:playlist:37i9dQZF1DWTtTyjgd08yp",
            "Country coffeehouse": 	                "spotify:user:spotify:playlist:37i9dQZF1DWYiR2Uqcon0X",
            "Bossa nova covers": 	                "spotify:user:spotify:playlist:37i9dQZF1DXardnHdSkglX",
            "Bossa nova lounge": 	                "spotify:user:daniosul:playlist:5FXXASlWpsxNvjf8tAOZBy",
            "Bossa nova covers en ingles": 	        "spotify:user:12182229421:playlist:3bgCwGaijwNd5WEavuo5J5",
            "Relaxing Bossa lounge": 	            "spotify:user:1249117231:playlist:4vouIEnT76VjVFQL6Bxziu",
            "Relax Bossa nova": 	                "spotify:user:laherradurash:playlist:6DQeFjE6Q6lOzsKPp3bgZi",
            "Bossa nove pop hits": 	                "spotify:user:pgrisolle:playlist:7fZrByN90G1dY8YJju3SZR",
            "Pink floyd radio 2": 	                "spotify:user:alejandrom87:playlist:5FIoA1txL0YfzPl2rBObAQ",
            "Coffee table jazz": 	                "spotify:user:spotify:playlist:37i9dQZF1DWVqfgj8NZEp1",
            "Late night jazz": 	                    "spotify:user:spotify:playlist:37i9dQZF1DX4wta20PHgwo",
            "Italian cooking music": 	            "spotify:user:616212:playlist:3WPuV7Q2Uy8nUthfZywVFa",
            "60s top tracks": 	                    "spotify:user:soundrop:playlist:7gTCSvWv9XwcqIPvGaBX3w",
            "Country's greatest hits: 60s": 	    "spotify:user:spotify:playlist:37i9dQZF1DX7CGYgLhqwu5",
            "Sad 50s, 60s songs": 	                "spotify:user:spuddboys:playlist:7fvS4B2j9EyweiVP3N4gv9",
            "Country music classics": 	            "spotify:user:listanauta:playlist:0QFaFgDQQiKBob7VIZIilG",
            "50s 60s country": 	                    "spotify:user:1220976776:playlist:324xDT9sg1idZRiRFFXoRG",
            "Easy listening 60s and 70s": 	        "spotify:user:martinkoss:playlist:5q4VozjtNEBgK7mFQXExra",
            "Romanticas en ingles": 	            "spotify:user:rodolfomorales21:playlist:6HacwaAhYpkhaHzezUSiFY",
            "Easy 60s, 70s, 80s, 90s, 00s": 	    "spotify:user:natffarch:playlist:5an6YawEyRtANv8SIPCz07",
            "Best rock ballads ever of the 60s, 70s, 80s and 90s": 	"spotify:user:workingonadream:playlist:0boMvditdYOewVRFyOF3L3",
            "Radio magica 88.3 FM": 	            "spotify:user:12141642855:playlist:5qchMwemq43CWhGJrepzLr",
            "Soft rock songs - power ballads": 	    "spotify:user:casperius:playlist:05k7PplHIBP9j1u1Lv7RRi",
            "Folk music at the gaslight cafe": 	    "spotify:user:spotify:playlist:37i9dQZF1DXdUnte9bTlLT",
            "60s 70s funk dance": 	                "spotify:user:gailandsingh:playlist:3tgQzrORMUlzpfklsJlLxU",
            "60s, 70s acoustics": 	                "spotify:user:heathhooper3:playlist:31w6jfdJYKtHvRDQrU6SUN",
            "Mersey beat 60s": 	                    "spotify:user:bigboy1959:playlist:0qAD0RMKz9HhUNJVjRCl2v",
            "60s easy listening": 	                "spotify:user:11148921698:playlist:70gXl4SBibgv68ZuY5y9fA",
            "Slow 50s, 60s": 	                    "spotify:user:1232436009:playlist:3UTnPPDUSb7WLL6I7itVoi",
            "60s number 1s": 	                    "spotify:user:11126168622:playlist:6UfjmORs8gyb0qfMbpFFX4",
            "Country 60s": 	                        "spotify:user:andreas1965-71:playlist:675pFT0ROYpeezhwA2pB8S",
            "Classic 60s, 70s folk": 	            "spotify:user:mackbb64:playlist:3KcIFFSYoC7BlSI6eWXulV",
            "British pop & rock mix (sok Morissey)":"spotify:user:12132996215:playlist:5hsM3IXICFcMO8jy5LwcbK",
            "Best rock ballads": 	                "spotify:user:demetris.tzanakis:playlist:5X2trnktsYANDYo2jZzDDv",
            "Old time honky tonk": 	                "spotify:user:wendib72:playlist:1Rh5edJt7QfYtgN1mKUgDP",
            "Springtime 60s": 	                    "spotify:user:michajones008:playlist:3FVTKM8XZuqU8SCBaF6Q0w",
            "60s, 70s, 80s best easy classics": 	"spotify:user:osman978:playlist:3pbx1VC4VKdEevSMxKFPuG",
            "Instrumental hits of 50s, 60s": 	    "spotify:user:1288629929:playlist:4fK6W44dYSlV8WPNdrXuel",
            "Country's greatest hits: 50s": 	    "spotify:user:spotify:playlist:37i9dQZF1DWWnpcjfCqaW0",
            "Lo-fi / chillhop beats":               "spotify:playlist:6Sh0iYBCG7lu42mwfGf4EG",
            "Lo-Fi Hip Hop Chill Wave Radio":       "spotify:album:2EmIIHbojdSlOj8ulSFlBX",
            "Lo-Fi Cafe":                           "spotify:playlist:37i9dQZF1DX9RwfGbeGQwP",
            "Lo Fi Instrumentals":                  "spotify:playlist:6fuPMGNaQ1jyUuo3i1iSLq",
            "Pet Methany Radio":                    "spotify:playlist:37i9dQZF1E4kiDL64xUfTi",
            "Pet Methany Group":                    "spotify:artist:4uBSazM6snEc9wCG3jMlYt",
            "This is Pet Metheny":                  "spotify:playlist:37i9dQZF1DZ06evO20WiVk",
            "Lush + Atmospheric":                   "spotify:playlist:37i9dQZF1DX79Y9Kr2M2tM",
            "The stress buster":                    "spotify:playlist:37i9dQZF1DWUvQoIOFMFUT",
            "Rainy day":                            "spotify:playlist:37i9dQZF1DXbvABJXBIyiY",
            "Sad indie":                            "spotify:playlist:37i9dQZF1DWVV27DiNWxkR",
            "Your coffee break":                    "spotify:playlist:37i9dQZF1DWYqdkUCLfYzP",
            "Café con leche":                       "spotify:playlist:37i9dQZF1DXa3NnZWk6Z3T",
            "Coping with loss":                     "spotify:playlist:37i9dQZF1DWVxpHBekDUXK",
            "Front porch":                          "spotify:playlist:37i9dQZF1DXa2PsvJSPnPf",

        }

        self.listen_event(self.start_morning_playlist,  "event_start_morning_playlist")
        self.listen_event(self.start_sleep_playlist,    "event_start_sleep_playlist")
        self.listen_event(self.start_sexy_playlist,     "event_start_sexy_playlist")
        self.listen_event(self.start_chill_playlist,    "event_start_chill_playlist")


    def start_morning_playlist(self, event, data, args):
        self.AVRused = True
        if int(self.get_state("sensor.num_in_master_bed")) > 0:
            avr = AVR_BEDROOM
        else:
            avr = AVR_LIVINGROOM
        self.turn_off("switch.terasz_hangszoro")

        self.run_in(self.setSpotifyShuffle, 10)
        self.run_in(self.setAVRParams, 6, avr=avr, volume="0.4")
        if self.start_selectedList(self.morning_list, avr, self.get_state("input_number.spotify_normal_volume")):
            self.turn_on(ALARM_FIRED_FLAG)

    def start_sleep_playlist(self, event, data, args):
        self.AVRused = True
        avr = AVR_BEDROOM
        self.turn_off("switch.terasz_hangszoro")
        self.run_in(self.setSpotifyShuffle, 10)
        self.run_in(self.setAVRParams, 6, avr=avr, volume="0.19")
        self.start_selectedList(self.sleep_list, avr, self.get_state("input_number.spotify_night_volume"))

    def start_sexy_playlist(self, event, data, args):
        self.AVRused = True
        avr = AVR_BEDROOM
        self.turn_off("switch.terasz_hangszoro")
        self.run_in(self.setSpotifyShuffle, 10)
        self.run_in(self.setAVRParams, 6, avr=avr, volume="0.41")
        self.start_selectedList(self.sexy_list, avr, self.get_state("input_number.spotify_night_volume"))

    def start_chill_playlist(self, event, data, args):
        self.AVRused = True
        self.test_running_playlist()
        avr = AVR_LIVINGROOM
        self.run_in(self.setAVRParams, 6, avr=avr, volume="0.42")
        self.run_in(self.setSpotifyShuffle, 10)
        self.start_selectedList(self.evening_chill_list, avr, self.get_state("input_number.spotify_normal_volume"))


    def start_selectedList(self, selectedList, avr, volume_level):
        self.call_service("rest_command/restart_spotify_connect")
        self.turn_off(ALARM_FIRED_FLAG)
        self.turn_off(SPOTIFY_SWITCHED_FLAG)
        if self.AVRused:
            self.turn_on(avr)
        success = False
        songTries = 0
        errorCode = 0
        while not success and songTries < SONGRETRIES:
            songTries += 1
            tries = 0
            listName, listUrl = random.choice(list(selectedList.items()))
            if (self.AVRused):
                spotify_source = SOURCE_BRIX
            else:
                spotify_source = SOURCE_BEDROOM

            while not success and tries < RETRIES:
                tries += 1
                try:
                    self.call_service("media_player/select_source", entity_id=SPOTIFY, source=spotify_source)
                except:
                    str = f"Exception during Spotify select source to '{spotify_source}'"
                    self.log(str)
                    self.call_service("logbook/log", message=str, name="spotify_playlist")
                    errorCode = 1
                    time.sleep(.3)
                    continue

                time.sleep(0.8)
                current_spotify_source = self.get_state(SPOTIFY, attribute="source")
                if current_spotify_source != spotify_source:
                    str = f"Spotify current source is '{current_spotify_source}' instead of '{spotify_source}'!"
                    self.log(str)
                    self.call_service("logbook/log", message=str, name="spotify_playlist")
                    time.sleep(.3)
                    continue
                else:
                    str = f"OK, Spotify current source is '{current_spotify_source}'"
                    self.log(str)
                    self.call_service("logbook/log", message=str, name="spotify_playlist")

                try:
                    self.call_service("media_player/shuffle_set", entity_id=SPOTIFY, shuffle="true")
                except:
                    str = f"Cannot set media player to shuffle exception"
                    self.log(str)
                    self.call_service("logbook/log", message=str, name="shuffle_set")
                    errorCode = 2
                    time.sleep(.3)
                    continue

                time.sleep(0.5)
                #if self.get_state(SPOTIFY, attribute="shuffle")!=True:
                #    str = f"Spotify set to shuffle did not work!"
                #    self.log(str)
                 #   self.call_service("logbook/log", message=str, name="spotify_playlist")


                try:
                    self.call_service("media_player/play_media", entity_id=SPOTIFY, media_content_id=listUrl, media_content_type="playlist")
                except:
                    str = f"Cannot start Spotify playlist '{listName}' url: {listUrl}"
                    self.log(str)
                    self.call_service("logbook/log", message=str, name="spotify_playlist")
                    errorCode = 2
                    time.sleep(.3)
                    continue

                time.sleep(.3)

                str = f"Started Spotify playlist '{listName}' url: {listUrl}"
                self.log(str)
                self.call_service("logbook/log", message=str, name="spotify_playlist")

                try:
                    self.call_service("media_player/volume_set", entity_id=SPOTIFY, volume_level=volume_level)
                except:
                    str = f"Exception during Spotify volume set"
                    self.log(str)
                    self.call_service("logbook/log", message=str, name="spotify_playlist")
                    errorCode = 3
                    time.sleep(.3)
                    continue

                success = True

            if not success:
                str = f"Cannot start Spotify playlist '{listName}' url: {listUrl} in {RETRIES} tries"
                self.log(str)
                self.call_service("logbook/log", message=str, name="spotify_playlist")
                self.call_service("persistent_notification/create", message=str, title="Spotify playlist error")

        if success:
            return True
        else:
            str = f"Cannot start any Spotify playlist in {SONGRETRIES} tries"
            self.log(str)
            self.call_service("logbook/log", message=str, name="spotify_playlist")
            self.call_service("persistent_notification/create", message=str, title="Spotify playlist error")
            if errorCode == 1:
                str = f"Ajjaj, a Spotify nem találja a lejátszót!"
            else:
                str = f"Ajjaj, Spotify hiba történt!"
            self.fire_event("tts_announce", message=str)
            return False

    def setSpotifyShuffle(self, kwargs):
        try:
            self.call_service("media_player/shuffle_set", entity_id=SPOTIFY, shuffle="True")
        except:
            str = f"Exception during Spotify shuffle set"
            self.log(str)
            self.call_service("logbook/log", message=str, name="spotify_playlist")

    def setAVRParams(self, kwargs):
        if kwargs is not None and 'volume' in kwargs:
            self.call_service("media_player/volume_set", entity_id=kwargs.get("avr"), volume_level=kwargs.get("volume"))
            time.sleep(.4)
            self.call_service("media_player/select_source", entity_id=kwargs.get("avr"), source=self.get_state("input_text.pioneer_spotify"))
        if kwargs is not None and 'dim' in kwargs:
            time.sleep(.4)
            self.call_service("media_player/pioneer_dim_display", entity_id=kwargs.get("avr"), dim_display=kwargs.get("dim"))

    def setAVRSpeaker(self, kwargs):
        if kwargs is not None and 'speaker' in kwargs:
            self.call_service("media_player/pioneer_select_speaker", entity_id=AVR, speaker=kwargs.get("speaker"))

    def test_running_playlist(self):
        if self.get_state("media_player.spotify") == "playing":
            artist = self.nice_text(self.get_state("media_player.spotify", attribute = "media_artist"))
            song = self.nice_text(self.get_state("media_player.spotify", attribute = "media_title"))
            if random.randint(1, 100) <= 60:
                nags = [
                    f"Pedig én tökre szeretem {artist} számait.",
                    "Ejnye, de finnyás ízlése van valakinek!",
                    "Van, akinek semmi sem tetszik.",
                    f"Kár, {song} dal pont az egyik kedvencem vót.",
                    f"Pedig egy gyors közvéleménykutatásom szerint nagyon népszerű szám {song}.",
                    f"Micsoda világ, ahol már {song} sem tetszik valakinek.",
                    f"Pedig Rúzsa Magdinak is az egyik kedvenc száma {song}.",
                    f"Mérges lesz a gazda, mert neki egyik kedvence {artist}.",
                    f"Hát jó. Majd ha nagyobb leszel, talán értékeled még {artist} művészetét.",
                ]
                text = random.choice(nags)
                self.fire_event("tts_announce", message=text)

    def nice_text(self, text):
        start = "a"
        if (text[0] in self.vowels):
            start = "az"
        text = start + " " + text
        return text





