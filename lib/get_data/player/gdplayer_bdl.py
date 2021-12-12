# author: Peter Wu
# desc: Gets player statistics from balldontlie API
# https://www.balldontlie.io/#stats
# ----------------------------------------------------------------------------
from lib.get_data.player.gdplayer import GDPlayer
from requests import get
from datetime import datetime
import pandas as pd
import warnings


class GDPlayerBDL (GDPlayer):

    player_endpoint = 'https://www.balldontlie.io/api/v1/players'
    stats_endpoint = 'https://www.balldontlie.io/api/v1/stats'
    stats_available = ['ast', 'blk', 'dreb', 'fg3_pct', 'fg3a',
                       'fg3m', 'fg_pct', 'fga', 'fgm', 'ft_pct',
                       'fta', 'ftm', 'min', 'oreb', 'pf',
                       'pts', 'reb', 'stl', 'turnover']

    @classmethod
    def get_stats(cls, name, team, stat_list: list, start_date: str, end_date: str = None) -> pd.DataFrame:
        """Queries player information from balldontlie service between start_date and end_date (inclusive)

        :param name: Player first and last name
        :param team: Abbreviated city name, eg. Toronto Raptors = TOR
        :param stat_list: List of stats to query
        :param start_date: String yyyy-mm-dd
        :param end_date: String yyyy-mm-dd
        :return: Dataframe with dates of games as index and stat categories as columns
        """

        # Checks if the requested stat categories are available from API
        for item in stat_list:
            if item not in cls.stats_available:
                raise ValueError(item + " is not an available stat from balldontlie API")

        # Ignores capitalization for team string
        team = team.upper()
        ids = cls._get_ids(name, team)

        dfs = []

        # Queries player data
        for player in ids:
            data = cls._get_data(player, start_date, end_date=end_date)
            dfs.append(cls._format_data(data, stat_list))

        df = pd.concat(dfs)

        return df

    # Helper methods----------------------------------------------------------
    @classmethod
    def _get_ids(cls, name, team):
        # This function tries to find balldontlie's player id given a player full name and team
        # It's expected there won't be players with the same name playing on the same team
        query_url = cls.player_endpoint + '?search=' + name

        # TODO try
        response = get(query_url)
        content = response.json()

        ids = []

        # First we look for a player with the same name and team
        for player in content['data']:
            if player['team']['abbreviation'] == team:
                ids.append(player['id'])

        # Try again with loosened criteria if the exact name doesn't return a match
        if not ids:
            query_url = cls.player_endpoint + '?search=' + name.split(' ')[-1]

            # TODO try
            response = get(query_url)
            content = response.json()

            # Look for a player with the same last name, same first initial and same team
            for player in content['data']:
                if player['team']['abbreviation'] == team and player['first_name'][0] == name[0]:
                    ids.append(player['id'])

        # If still nothing then ¯\_(ツ)_/¯
        if not ids:
            warnings.warn('No data found for player - ' + name)
        elif len(ids) > 1:
            warnings.warn('Multiple players found for criteria')

        return ids

    @classmethod
    def _get_data(cls, player_id, start_date, end_date=None):
        # Queries balldontlie with arguments and returns response content

        # Create query url
        query_url = cls.stats_endpoint + '?player_ids[]=' + str(player_id) + '&start_date=' + start_date
        if end_date:
            query_url += '&end_date=' + end_date
        query_url += '&per_page[]=82'

        # TODO try
        response = get(query_url)

        return response.json()

    @staticmethod
    def _format_data(json_struct, stat_list):
        # Formats stats structure in a json dict into a dataframe

        data = [[datetime.strptime(game['game']['date'].split('T')[0], '%Y-%m-%d')] + [game[cat] for cat in stat_list]
                for game in json_struct['data']]

        df = pd.DataFrame(data, columns=['date_'] + stat_list)
        df.set_index('date_', inplace=True)
        df.sort_index(inplace=True)

        return df






