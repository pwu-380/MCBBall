# author: Peter Wu
# desc: Abstract class for getting player statistics from some data source
# ----------------------------------------------------------------------------
from abc import ABC, abstractmethod


class GDSchedule(ABC):
    @property
    @abstractmethod
    def teams_abb(self):
        # Class-level list indicating team abbreviations for the data resource
        pass

    @classmethod
    @abstractmethod
    def get_schedule(cls, team, start_date, end_date):
        # Gets game schedule between start_data and end_date for team
        pass

    @classmethod
    @abstractmethod
    def get_num_games(cls, team, start_date, end_date):
        # Gets number of games between start_data and end_date for team
        pass
