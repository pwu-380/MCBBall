# author: Peter Wu
# desc: This class is used to access league data for Yahoo Fantasy Basketball
# See: https://developer.yahoo.com/oauth2/guide/flows_authcode/ for OAuth
# See: https://developer.yahoo.com/fantasysports/guide/ for API
# ----------------------------------------------------------------------------
from collections import namedtuple
from requests import get, post
from datetime import datetime
from lib.player import Player
import warnings
import webbrowser
import base64
import xmltodict
import time
import re


class YahooFantasy:

    base_url = 'https://api.login.yahoo.com/'
    league_endpoint = 'https://fantasysports.yahooapis.com/fantasy/v2/league/'
    fantasy_team_endpoint = 'https://fantasysports.yahooapis.com/fantasy/v2/team/'
    player_endpoint = 'https://fantasysports.yahooapis.com/fantasy/v2/player/'

    def __init__(self, client_id, client_secret, league_id):
        # TODO Docstring
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_code = None
        self.access_token = None
        self.refresh_token = None

        self._authorized = False
        self._authorization_time = None
        self._expiration_time = None

        self.auth_headers = None
        self.headers = None
        self.league_id = league_id
        self.teams = None
        self.teams_lookup = None
        self.MatchUp = namedtuple('MatchUp', ['week', 'week_start', 'week_end', 'opponent'])

    # All of the following deals with authentication processes----------------
    def get_auth_code(self):
        """Opens a browser instance so user can sign in to yahoo and get authentication code for
        league information access"""

        auth_url = f'oauth2/request_auth?client_id={self.client_id}&redirect_uri=oob&response_type=code&language=en-us'
        webbrowser.open(self.base_url + auth_url)

    def authorize(self, auth_code):
        """Authorizes application for querying league information
        :param auth_code: string gotten from get_auth_code"""

        self.auth_code = auth_code
        self._get_access_token()
        self._authorized = True

    def _get_access_token(self):
        # Refer to OAuth docs step 4
        encoded = base64.b64encode((self.client_id + ':' + self.client_secret).encode("utf-8"))

        self.auth_headers = {
            'Authorization': f'Basic {encoded.decode("utf-8")}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'redirect_uri': 'oob',
            'code': self.auth_code
        }

        self._authorization_time = time.time()

        # TODO try
        response = post(self.base_url + 'oauth2/get_token', headers=self.auth_headers, data=data)
        content = response.json()

        self.access_token = content['access_token']
        self.refresh_token = content['refresh_token']
        self._expiration_time = self._authorization_time + content['expires_in']

    def _refresh_access_token(self):
        # Refer to OAuth docs step 5
        data = {
            'grant_type': 'refresh_token',
            'redirect_uri': 'oob',
            'code': self.auth_code,
            'refresh_token': self.refresh_token
        }

        # Cannot refresh access token if class was not authorized first
        is_authorized = self._check_authorization()
        if is_authorized:

            self._authorization_time = time.time()

            # TODO try
            response = post(self.base_url + 'oauth2/get_token', headers=self.auth_headers, data=data)
            content = response.json()

            self.access_token = content['access_token']
            self._expiration_time = self._authorization_time + content['expires_in']

            self.headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        else:
            raise RuntimeError('No token to refresh')

    def _check_authorization(self):
        # For data access methods, need to check if class has been authorized to access data first
        if self._authorized:
            if time.time() >= self._expiration_time:
                warnings.warn('User authorization has expired')
                self._authorized = False
                self._authorization_time = None
                self._expiration_time = None
                return False
            else:
                return True
        else:
            warnings.warn('User has not authorized access to league')
            return False

    # Data query stuff--------------------------------------------------------
    # TODO refactor: make generic request class
    def get_teams_in_league(self):
        """Get all the fantasy teams' names and ids in the league.

        Ids are stored internally in class for the purposes of querying information about a team. The user will only
        need to provide names for any public method.

        :return: List of team names and ids"""

        self._refresh_access_token()

        if not self.teams:
            resource_url = self.league_endpoint + 'nba.l.' + str(self.league_id) + '/standings'

            # TODO try
            response = get(resource_url, headers=self.headers)
            content = xmltodict.parse(response.content)

            teams = {}
            # For the purposes of looking up the id of a user entered team name, we lowercase and remove
            # punctuation to make it less stringent
            teams_lookup = {}

            for team in content['fantasy_content']['league']['standings']['teams']['team']:
                teams[team['name']] = team['team_id']
                teams_lookup[self._process_str(team['name'])] = team['team_id']

            self.teams = teams
            self.teams_lookup = teams_lookup

        return self.teams

    def get_matchups(self, team):
        """Get list of week-to-week fantasy league opponents for team

        :param team: Fantasy team name
        :return: List of tuples providing each week's opponent, start date and end date"""

        self._refresh_access_token()

        if not self.teams:
            self.get_teams_in_league()

        # TODO try
        team_id = self.teams_lookup[self._process_str(team)]

        resource_url = self.fantasy_team_endpoint + 'nba.l.' + str(self.league_id) + '.t.' + str(team_id) + '/standings'

        # TODO try
        response = get(resource_url, headers=self.headers)
        content = xmltodict.parse(response.content)

        matchups = []

        for week in content['fantasy_content']['team']['matchups']['matchup']:
            # The reason we use datetime for dates here and str elsewhere is because I expect
            # to use inequality lookups to find matchup weeks, whereas other dates (e.g. season start)
            # might be transcribed from looking at a calendar or Google, etc
            matchups.append(self.MatchUp(week['week'],
                                         datetime.strptime(week['week_start'], '%Y-%m-%d'),
                                         datetime.strptime(week['week_end'], '%Y-%m-%d'),
                                         week['teams']['team'][1]['name']))
        return matchups

    def get_team_roster(self, team, exclude_unavailable=False):
        """Create Player objects associated with each member of a fantasy roster

        :param team: Fantasy team name
        :param exclude_unavailable: Don't return players with Injured or Out statues
        :return: List of Player objects inited with name, team and status"""

        if not self.teams:
            self.get_teams_in_league()
        else:
            self._refresh_access_token()

        # TODO try
        team_id = self.teams_lookup[self._process_str(team)]

        resource_url = self.fantasy_team_endpoint + 'nba.l.' + str(self.league_id) + '.t.' + \
                       str(team_id) + '/roster/players'

        # TODO try
        response = get(resource_url, headers=self.headers)
        content = xmltodict.parse(response.content)

        roster = []

        for c in content['fantasy_content']['team']['roster']['players']['player']:
            if 'status' in c:
                status = c['status']
            else:
                # No status key is returned by default so "no problem" is assigned to
                # players without status
                status = 'NP'

            # If flagged, "injured" or "out" players are excluded from list
            if not exclude_unavailable or (status != 'INJ' and status != 'O'):
                roster.append(Player(first_name=c['name']['first'], last_name=c['name']['last'],
                                     team=c['editorial_team_abbr'], status=status))
        return roster

    # Helper methods----------------------------------------------------------
    @staticmethod
    def _process_str(text):
        # Lowercase and remove punctuations from strings for matching purposes
        text = re.sub(r'[^\w]', '', text)
        text = text.lower()

        return text



