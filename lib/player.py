# author: Peter Wu
# desc: Player class
# This is also the class used for generating synthetic stat lines
# ----------------------------------------------------------------------------
import pandas as pd
import random
import warnings


class Player:

    def __init__(self, first_name, last_name, team, status=None, player_id=None):
        """This class holds descriptive attributes of a player (e.g. name, team, status (as reported to the NBA),
        ids (as assigned by other resources)); can generate synthetic stat lines for the player if seeded with sample
        statistics."""

        self.first_name = first_name
        self.last_name = last_name
        self.team = team
        self.status = None
        self.player_id = None

        self.means = None
        self.stdevs = None
        self.stats = None
        self.stats_available = []

    def set_distribution(self, means: dict, stdevs: dict):
        """To generate synthetic stat lines (gaussian), we need at least the mean and standard deviations

        :param means: dict with entries of the form [category name: str]:[mean: float]
        :param stdevs: dict with entries of the form [category name: str]:[standard deviation: float]
        """

        # Need means and standard deviations for the all the same categories
        if means.keys() != stdevs.keys():
            raise ValueError("Keys don't match for stat means and standard deviation")

        self.stats = None
        self.stats_available = [x for x in means.keys()]
        self.means = means
        self.stdevs = stdevs

        return 0, 'Player statistics set'

    def set_stats(self, stats: pd.DataFrame):
        """To generate synthetic stats by bootstrap, actual stats is needed

        :param stats: Dataframe, each row is a stat line and columns are stat categories (index doesn't matter)
        """

        # Assume a statline of all 0s means player did not play
        stats = stats.loc[(stats != 0).any(axis=1)]

        self.stats = stats
        self.stats_available = [x for x in stats.columns]
        # Will also initialize the sample mean and standard deviations for gaussian generator
        means, stdevs = self._calculate_distribution(stats)
        self.means = means
        self.stdevs = stdevs

        return 0, 'Player statistics set'

    def generate_statline(self, stat_list, num_games=1, bootstrap=False) -> list:
        """Returns list of generated statlines for player

        :param stat_list: list of categories to generate stats for
        :param num_games: number of stat lines to generate
        :param bootstrap: Flag indicates whether to generate data by gaussian generator or bootstrap sampling
        :return: A list of dicts, with keys as category names"""

        # Check stat_list
        if ~set(self.stats_available).issuperset(set(stat_list)):
            raise ValueError('Item(s) in stat_list is not available for {} {}'.format(self.first_name, self.last_name))

        # Generate bootstrap sample or normal sample based on parameter
        statlines = []

        # Bootstrap sampling requires actual stats to be inited
        # Gaussian generator requires only a mean and standard deviation
        if self.means and self.stdevs:
            if not bootstrap:
                for i in range(num_games):
                    statlines.append(self._continuous(stat_list))
                return statlines

            elif self.stats is not None:
                for i in range(num_games):
                    statlines.append(self._bootstrap(stat_list))
                return statlines

            else:
                warnings.warn('No bootstrap values available for {} {}'.format(self.first_name, self.last_name))
                return []

        else:
            warnings.warn('No player statistics inited for {} {}'.format(self.first_name, self.last_name))
            return []

    def generate_statline_all(self, num_games=1, bootstrap=False) -> list:
        """Returns list of generated statlines for player for all stat categories available to class

        :param num_games: number of stat lines to generate
        :param bootstrap: Flag indicates whether to generate data by gaussian generator or bootstrap sampling
        :return: A list of dicts, with keys as category names"""

        statlines = []

        if not bootstrap:
            for i in range(num_games):
                statlines.append(self._continuous(self.stats_available))
        else:
            for i in range(num_games):
                statlines.append(self._bootstrap(self.stats_available))

        return statlines

    # Helper methods----------------------------------------------------------
    # Calculates sample mean and sample standard deviation from a set of sample stat lines
    def _calculate_distribution(self, df):
        means = {}
        stdevs = {}

        for cat in self.stats_available:
            means[cat] = df[cat].mean()
            stdevs[cat] = df[cat].std()

        return means, stdevs

    # Generates synthetic data in a continuous distribution, assuming normality and independence
    def _continuous(self, stat_list) -> dict:
        statline = {}

        for cat in stat_list:
            statline[cat] = random.gauss(mu=self.means[cat], sigma=self.stdevs[cat])

        return statline

    # Generates synthetic data by bootstrap sampling
    def _bootstrap(self, stat_list) -> dict:
        statline = self.stats[stat_list].sample().to_dict('records')[0]

        return statline

    # Report methods----------------------------------------------------------
    def __repr__(self):
        text = "Player(first_name={}, last_name={}, team={}, status={}, id={})".format(
            self.first_name, self.last_name, self.team, self.status, self.player_id)

        return text
