# author: Peter Wu
# desc: Abstract class for getting player statistics from some data source
# ----------------------------------------------------------------------------
from abc import ABC, abstractmethod
import pandas as pd


class GDPlayer(ABC):
    @property
    @abstractmethod
    def stats_available(self):
        # Class-level list indicating stat categories available from the data resource
        pass

    @classmethod
    @abstractmethod
    def get_stats(cls, name, team, stat_list: list, start_date: str, end_date: str) -> pd.DataFrame:
        # Gets player stat lines between start_data and end_date for team
        pass
