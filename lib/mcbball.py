# author: Peter Wu
# desc: This class orchestrates simulating period stat lines based on sample data
# ----------------------------------------------------------------------------
from lib.get_data.player.gdplayer_bdl import GDPlayerBDL
from lib.get_data.schedule.gdschedule_bdl import GDScheduleBDL
from lib.player import Player
from typing import List
import pandas as pd


class MCBBall:

    def __init__(self):
        # TODO theoretically the data source would be configured through config
        self.gdp = GDPlayerBDL()
        self.gds = GDScheduleBDL()

    def generate_stat_totals(self, roster: List[Player], sim_start: str, sim_end: str, stat_list: List[str],
                             stat_start: str, num_runs, bootstrap=False) -> pd.DataFrame:
        """Simulates the total category stats for a time range between sim_start and sim_end, for a roster of
        players, for num_runs number of simulations

        :param roster: list of inited Player objects (first name, last name, team inited)
        :param sim_start: (yyyy-mm-dd) start date of the simulated period
        :param sim_end: (yyyy-mm-dd) end date of the simulated period
        :param stat_list: list of actual player stats to query as strings (has to be available from stats resource)
        :param stat_start: (yyyy-mm-dd) cutoff date for querying actual stats - older stats may be less predictive
        :param num_runs: How many times the period is simulated
        :param bootstrap: Flag indicates whether to use bootstrap sampling or assume guassian for stat line simulation
        :return: Dataframe where columns are stat_list of categories and rows are simulated category totals generated
        by the roster for the period
        """

        # Initiate all Players with sample actual stats
        roster = self._initiate_player_stats(roster, stat_list, stat_start)

        # Get distinct teams from player list
        teams = [player.team for player in roster]
        teams = list(set(teams))

        # Get number of games for every team in simulated period
        num_games = self._count_games(teams, sim_start, sim_end)

        # For each run, get the simulated stat totals for the defined period
        runs = []
        for i in range(num_runs):
            statlines = []
            # Get individual statlines for each player for the period
            for player in roster:
                statlines.extend(player.generate_statline_all(num_games=num_games[player.team], bootstrap=bootstrap))

            df = pd.DataFrame(statlines)
            # This is to track the total number of games played by the team in the period
            df['games'] = 1
            # Sum all the statlines together to get the period total
            runs.append(df.sum().tolist())

        # Convert list of simulated stat totals
        totals = pd.DataFrame(runs, columns=stat_list + ['games'])

        return totals

    # Helper methods----------------------------------------------------------
    def _initiate_player_stats(self, roster: List[Player], stat_list: List[str], stat_start: str) -> List[Player]:
        # Initiate all Player objects in a list with stats queried from a player stats resource
        for player in roster:
            stats = self.gdp.get_stats(name="{} {}".format(player.first_name, player.last_name),
                                       team=player.team,
                                       stat_list=stat_list,
                                       start_date=stat_start)
            player.set_stats(stats=stats)

        return roster

    def _count_games(self, teams: List[str], start_date, end_date):
        # Returns the number of games a team plays in a period by querying the schedule resource
        num_games = {}
        for team in teams:
            num_games[team] = self.gds.get_num_games(team, start_date, end_date)

        return num_games
