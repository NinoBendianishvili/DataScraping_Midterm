from typing import Optional, Dict, Union
from enum import Enum
import re # Import re for cleaning vote strings

class Party(Enum):
    DEMOCRATIC = "Democratic"
    REPUBLICAN = "Republican"
    OTHER = "Other"

class StateData:
    """
    Holds information specific to a US State: name, electoral votes, population.
    """
    def __init__(self,
                 state_name: str,
                 electoral_votes: Optional[int] = None,
                 total_population: Optional[int] = None):
        """ Initializes state-level data. """
        if not state_name or not isinstance(state_name, str):
            raise ValueError("State name must be a non-empty string.")
        self.state_name: str = state_name

        if electoral_votes is not None and not isinstance(electoral_votes, int):
            raise TypeError(f"Electoral votes must be an integer, got {type(electoral_votes)}.")
        self.electoral_votes: Optional[int] = electoral_votes

        if total_population is not None and not isinstance(total_population, int):
            raise TypeError(f"Total population must be an integer, got {type(total_population)}.")
        self.total_population: Optional[int] = total_population

    def __repr__(self) -> str:
        """ Developer-friendly representation. """
        return (f"StateData(name='{self.state_name}', "
                f"EV={self.electoral_votes}, Pop={self.total_population})")

class YearData:
    """
    Holds information specific to a single election year: year, candidates, national votes.
    Note: dem_votes, rep_votes, total_votes here refer to NATIONAL totals.
    """
    def __init__(self,
                 year: int,
                 dem_leader: Optional[str] = None,
                 rep_leader: Optional[str] = None,
                 dem_votes: Optional[int] = None, # National Popular Votes
                 rep_votes: Optional[int] = None, # National Popular Votes
                 total_votes: Optional[int] = None, # Potentially national total
                 winner_image_url: Optional[str] = None): # URL of winner's image
        """ Initializes year-specific data. """
        if not isinstance(year, int):
             raise TypeError(f"Election year must be an integer, got {type(year)}.")
        self.year: int = year

        if dem_leader is not None and not isinstance(dem_leader, str):
            raise TypeError(f"Democratic leader must be a string, got {type(dem_leader)}.")
        self.dem_leader: Optional[str] = dem_leader

        if rep_leader is not None and not isinstance(rep_leader, str):
            raise TypeError(f"Republican leader must be a string, got {type(rep_leader)}.")
        self.rep_leader: Optional[str] = rep_leader

        if winner_image_url is not None and not isinstance(winner_image_url, str):
            raise TypeError(f"Winner image URL must be a string, got {type(winner_image_url)}.")
        self.winner_image_url: Optional[str] = winner_image_url

        # Check and store votes (now handles strings with commas)
        self.dem_votes: Optional[int] = self._check_votes(dem_votes, "Democratic National")
        self.rep_votes: Optional[int] = self._check_votes(rep_votes, "Republican National")
        self.total_votes: Optional[int] = self._check_votes(total_votes, "Total National") # Usually derived or None

    def _check_votes(self, votes: Optional[Union[int, str]], vote_type: str) -> Optional[int]:
        """ Check: votes should be an integer >= 0 (or None), handles comma strings."""
        if votes is None:
            return None

        original_votes = votes # Keep for logging

        if isinstance(votes, str):
            # Clean the string: remove commas, whitespace
            cleaned_votes = re.sub(r'[,\s]', '', votes)
            if cleaned_votes.isdigit():
                try:
                    votes = int(cleaned_votes)
                except ValueError:
                     print(f"Warning ({self.year}): Could not convert cleaned string '{cleaned_votes}' to integer for {vote_type} votes. Original: '{original_votes}'. Storing 'None'.")
                     return None
            else:
                 # Handle cases like 'N/A' or other non-numeric strings if necessary
                 print(f"Warning ({self.year}): Non-numeric string value '{original_votes}' for {vote_type} votes. Storing 'None'.")
                 return None
        elif isinstance(votes, float):
             if votes.is_integer() and votes >= 0:
                 votes = int(votes)
             else:
                 print(f"Warning ({self.year}): Non-integer float value '{original_votes}' for {vote_type} votes. Storing 'None'.")
                 return None
        elif not isinstance(votes, int):
             print(f"Warning ({self.year}): Expected integer or parseable string for {vote_type} votes, got {type(original_votes)} '{original_votes}'. Storing 'None'.")
             return None

        # Final check after potential conversion
        if votes < 0:
            print(f"Warning ({self.year}): {vote_type} votes '{votes}' is negative (Original: '{original_votes}'). Storing 'None'.")
            return None

        return votes


    def __repr__(self) -> str:
        """ Developer-friendly representation. """
        return (f"YearData(year={self.year}, "
                f"DEM='{self.dem_leader}', REP='{self.rep_leader}', "
                f"DEM_Nat_Votes={self.dem_votes}, REP_Nat_Votes={self.rep_votes}, "
                f"TotalNatVotes={self.total_votes}, "
                f"WinnerImageURL={self.winner_image_url})")

class ElectionResult:
    """
    Connects state information, year information (incl. national leaders/votes),
    and the state-level percentage results for a specific election.
    """
    def __init__(self,
                 state_info: StateData,
                 year_info: YearData,
                 dem_percentage: Optional[float] = None, # State-level %
                 rep_percentage: Optional[float] = None, # State-level %
                 winner: Optional[Party] = None):       # State-level winner
        """ Initializes the election result link. """
        if not isinstance(state_info, StateData):
            raise TypeError(f"state_info must be an instance of StateData, got {type(state_info)}.")
        self.state_info: StateData = state_info

        if not isinstance(year_info, YearData):
            raise TypeError(f"year_info must be an instance of YearData, got {type(year_info)}.")
        self.year_info: YearData = year_info

        self.dem_percentage: Optional[float] = self._check_percentage(dem_percentage, "Democratic (State)")
        self.rep_percentage: Optional[float] = self._check_percentage(rep_percentage, "Republican (State)")
        self.winner: Optional[Party] = winner # Assumes winner is validated elsewhere if needed

    def _check_percentage(self, percent: Optional[float], party_name: str) -> Optional[float]:
        """ Helper check: percentages should be numbers between 0 and 100. """
        if percent is not None:
            if not isinstance(percent, (int, float)):
                raise TypeError(f"{party_name} percentage must be a number, got {type(percent)}.")
            if not (0 <= percent <= 100):
                raise ValueError(f"{party_name} percentage must be between 0 and 100, got {percent}.")
        return percent

    def __repr__(self) -> str:
        """ Developer-friendly representation showing the link. """
        state_name = self.state_info.state_name if self.state_info else 'N/A'
        year = self.year_info.year if self.year_info else 'N/A'
        return (f"ElectionResult(State='{state_name}', Year={year}, "
                f"DEM%={self.dem_percentage}, REP%={self.rep_percentage}, "
                f"StateWinner={self.winner.value if self.winner else 'N/A'})")

    # Properties to access underlying data easily
    @property
    def state_name(self) -> str:
        return self.state_info.state_name

    @property
    def year(self) -> int:
        return self.year_info.year