import re
import requests
import lxml.html

from urllib.parse import urlencode
from typing import Tuple, List, NamedTuple, Callable, Optional

from .error import ParsingError


class WeekRecord(NamedTuple):
    """
    NamedTuple for representation of weekly VHI records
    """

    province: int
    year: int
    week: int
    data: List[float]

    def __str__(self):
        return "{},{},{},{}".format(*self[:3],
                                    ",".join([str(i) for i in self.data]))


def cached(fn):
    def wrapper(self, province, years):
        key = hash((fn.__name__, province, years))

        recs = self.cache.get(key)
        if not recs:
            recs = fn(self, province, years)
            self.cache[key] = recs
        return recs
    return wrapper


class Parser():
    """
    Parser for VHI Data from star.nesdis.noaa.gov
    """

    BASE_URI = "https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH"

    # Endpoint to web page with selectors for provinces and years range
    BROWSER_URN = BASE_URI + "/vh_browseByCountry_province.php"

    # Endpoint to raw vhi data represented in similar to csv format
    RAW_DATA_URN = BASE_URI + "/get_TS_admin.php"

    # Hardcoded country query param
    COUNTRY_ID = "UKR"  # Ukraine

    # Types of VHI Data
    TYPE_MEAN = "Mean"
    TYPE_PAREA = "VHI_Parea"

    def __init__(self):
        # For storing provinces parsed from selectors on web page
        self.provinces: List[str] = []

        # Same for years range
        self.years: List[str] = []

        self.headers = {
            # Just for mimic to browser
            "User-Agent": "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:87.0) "
            "Gecko/20100101 Firefox/87.0",
            "Connection": "keep-alive"
        }

        self.cache = {}

    def parse_selectors(self) -> None:
        """
        Parses province and selectors from web page

        Stores result to provinces and years members
        """

        resp = requests.get(self.BROWSER_URN + f"?country={self.COUNTRY_ID}",
                            headers=self.headers)

        dom_root = lxml.html.fromstring(resp.text)

        self.provinces.extend(dom_root.xpath(
            "//select[@id='Province']/option/text()"))

        # Skipping first 'cause it's Combobox name
        self.years.extend(dom_root.xpath(
            "//select[@id='Year1']/option/text()")[1:])

    def _get_raw_vhi_data(self, province: str, years: Tuple[int, int],
                          vhi_type: str) -> Tuple[int, Optional[str]]:

        """
        Retrieves raw VHI records and strips down <pre> html tag
        Returns string with rows separated by \n.
        Each row has columns separated by commas

        :param province: province name, which was parsed from web page
        :param years: years range (from, to)
        :vhi_type: type of VHI records to get (Mean or Percentage of Area)
        :rtype: str
        """

        province_id = int(province[:province.find(":")])

        query = urlencode({
            "country":    self.COUNTRY_ID,
            "provinceID": province_id,
            "year1":      years[0],
            "year2":      years[1],
            "type":       vhi_type
        })

        resp = requests.get("%s?%s" % (self.RAW_DATA_URN, query),
                            headers=self.headers)

        # Get inner text of "pre" tag
        return (province_id,
                re.search(r"<pre>((?:.|\n|\r)*?)</pre>", resp.text)[0][5:-7])

    def _parse_vhi(self, vhi_data: Tuple[int, str],
                   filter: Callable) -> List[WeekRecord]:

        """
        Parses VHI records from raw data.

        :param vhi_data: result of _get_raw_vhi_data() method
        :param filter: function to filter data in row
        :returns: list of WeekRecord objects
        :rtype: List[WeekRecord]
        """

        ret = []
        for ln in vhi_data[1].replace(" ", "").split("\n"):
            record_ln = ln[:-1].split(",")

            data = filter(list(map(float, record_ln[2:])))
            if data:
                ret.append(WeekRecord(vhi_data[0],
                           int(record_ln[0]), int(record_ln[1]), data))

        return ret

    @cached
    def parse_mean(self, province: str,
                   years: Tuple[int, int]) -> List[WeekRecord]:

        """
        Parses Mean records by passing filter lambda.

        Filter function ignores negative values and leaves only last column
        """

        try:
            return self._parse_vhi(
                self._get_raw_vhi_data(province, years, self.TYPE_MEAN),

                lambda dat: [dat[-1]] if dat[-1] != -1.0 else None)
        except Exception as e:
            raise ParsingError(e)

    @cached
    def parse_parea(self, province: str,
                    years: Tuple[int, int]) -> List[WeekRecord]:

        """
        Parses Percentage of Area records by passing filter.

        Filter function just ignores negative values
        """

        try:
            return self._parse_vhi(
                self._get_raw_vhi_data(province, years, self.TYPE_PAREA),

                lambda dat: dat if dat[0] != -1.0 else None)
        except Exception as e:
            raise ParsingError(e)
