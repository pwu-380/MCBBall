# author: Peter Wu
# desc: Gets team schedule from balldontlie API
# https://www.balldontlie.io/#games
# ----------------------------------------------------------------------------
from lib.get_data.schedule.gdschedule import GDSchedule
from requests import get


class GDScheduleBDL(GDSchedule):

    teams_endpoint = 'https://www.balldontlie.io/api/v1/teams'
    games_endpoint = 'https://www.balldontlie.io/api/v1/games'
    teams_abb = None
    ids = None

    @classmethod
    def __init__(cls):
        """Queries schedule information from balldontlie service"""
        cls.ids = cls._get_ids()
        cls.teams_abb = list(cls.ids.keys())

    @classmethod
    def _get_ids(cls):
        # Gets ids corresponding to each team used by resource

        # TODO try
        response = get(cls.teams_endpoint)
        content = response.json()

        ids = {}
        for team in content['data']:
            ids[team['abbreviation']] = team['id']

        return ids

    @classmethod
    def get_schedule(cls, team, start_date: str, end_date: str):
        """Gets game schedule between start_date and end_date (inclusive) for team

        :param team: Abbreviated city name, eg. Toronto Raptors = TOR
        :param start_date: String yyyy-mm-dd
        :param end_date: String yyyy-mm-dd
        :return: List of tuples giving the opposing team and game date"""

        team = team.upper()
        resource_url = cls.games_endpoint + '?team_ids[]=' + str(cls.ids[team]) + \
                       '&start_date=' + start_date + '&end_date=' + end_date

        # TODO try
        response = get(resource_url)
        content = response.json()

        schedule = []

        for game in content['data']:
            if game['home_team']['abbreviation'] == team:
                opp = game['visitor_team']['abbreviation']
            else:
                opp = game['home_team']['abbreviation']

            schedule.append((opp, game['date'].split('T')[0]))

        return schedule

    @classmethod
    def get_num_games(cls, team, start_date: str, end_date: str):
        """Gets number of games between start_date and end_date (inclusive) for team

        :param team: Abbreviated city name, eg. Toronto Raptors = TOR
        :param start_date: String yyyy-mm-dd
        :param end_date: String yyyy-mm-dd
        :return: int"""

        schedule = cls.get_schedule(team, start_date, end_date)

        return len(schedule)
