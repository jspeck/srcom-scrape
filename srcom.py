#!/usr/bin/env python2
# Python 2.7
# gets speedrun.com leaderboard and writes to csv

import requests
import datetime
import sys
from UnicodeWriter import UnicodeWriter

class srcom_leaderboard:
    def __init__(self, game_name=None, game_abbrev=None):
        self.runs = []
        self.runs.append(['version', 'category', 'runner', 'time', 'video', 'comment'])
        if game_name is None and game_abbrev is None:
            sys.exit()
        self.game_name = game_name
        self.game_abbrev = game_abbrev
        self.platforms = self.get_platforms()
        self.game_id = self.get_game_id(self.game_name, self.game_abbrev)
        self.category_dict = self.get_category_dict()
        self.scrape_leaderboard()

    def get_platforms(self):
        ret = {}
        r = requests.get("http://www.speedrun.com/api/v1/platforms?max=200")
        for platform in r.json()['data']:
            ret[platform['id']] = platform['name']
        return ret

    def get_game_id(self, game_name=None, game_abbrev=None):
        if game_name is None and game_abbrev is None:
            sys.exit()

        if game_abbrev is None:
            r = requests.get("http://www.speedrun.com/api/v1/games?name=" + game_name.replace(" ", "%20")).json()
        else:
            r = requests.get("http://www.speedrun.com/api/v1/games?abbreviation=" + game_abbrev).json()
        for data in r['data']:
            if game_abbrev is not None:
                if game_abbrev == data['abbreviation']:
                    self.game_name = data['names']['international']
                    return data['id']
            elif game_name == data['names']['international']:
                self.game_abbrev = data['abbreviation']
                return data['id']
        sys.exit()

    def get_category_dict(self):
        ret = {}
        r = requests.get("http://www.speedrun.com/api/v1/games/" + self.game_id + "/categories")
        for category in r.json()['data']:
            if category['type'] == 'per-game':
                ret[category['name']] = category['id']
        return ret

    def seconds_to_hms(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%d:%02d:%02d" % (h, m, s)

    def scrape_leaderboard(self):
        for catname, catid in self.category_dict.iteritems():
            players = {}
            url = "http://wwww.speedrun.com/api/v1/leaderboards/" + self.game_id + "/category/" + catid + "?embed=players"
            print url
            r = requests.get(url).json()
            for player in r['data']['players']['data']:
                if player['rel'] == 'user':
                    players[player['id']] = player['names']['international']
            for run in r['data']['runs']:
                run_element = []
                if run['place'] != 0:
                    if run['run']['system']['emulated'] == True:
                        run_element.append("emu")
                    else:
                        run_element.append( self.platforms[run['run']['system']['platform']] )
                    run_element.append(catname)
                    if run['run']['players'][0]['rel'] == 'user':
                        run_element.append(players[run['run']['players'][0]['id']])
                    else:
                        run_element.append(run['run']['players'][0]['name'])
                    run_element.append(self.seconds_to_hms(run['run']['times']['realtime_t']))
                    if run['run']['videos'] is not None:
                        if 'links' in run['run']['videos']: 
                            run_element.append(run['run']['videos']['links'][0]['uri'])
                    else:
                        run_element.append("")

                    if run['run']['comment'] is None:
                        run_element.append("")
                    else:
                        run_element.append(run['run']['comment'])
                    self.runs.append(run_element)

    def write_csv(self):
        outfile = 'srcom_' + self.game_abbrev + "_" + str(datetime.datetime.now().strftime("%Y_%m_%d")) + '.csv'
        with open(outfile, 'wb') as f:
            writer = UnicodeWriter(f)
            writer.writerows(self.runs)

def main(argv):
    if len(argv) == 0:
        print "-a       game name abbreviation"
        print "else     Game Name"
        sys.exit()
    else:
        if argv[0] == "-a":
            lb = srcom_leaderboard( game_abbrev = argv[1] )
        else:
            lb = srcom_leaderboard(" ".join(argv))
    lb.write_csv()

if __name__ == "__main__":
    main(sys.argv[1:])
