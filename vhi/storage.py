import os
import sqlite3
import multiprocessing as mp

from typing import List, Iterable, Optional
from time import strftime

from .error import SavingError
from .parser import Parser, WeekRecord
from .util import gen_columns_labels, mktree


class Storage:
    r"""
    Class with methods for storing parsed data

    Able to dump data to csv files and sqlite3 database
    """

    def __init__(self, parser: Parser):
        r"""
        :param fp: file path to .sqlite database file
        :param parser: Parser instance
        """

        self.conn = None
        self.cur = None

        self.parser = parser
        self.records_cache = {}

        # self._create_tables()

    def __del__(self) -> None:
        self.cur.close()
        self.conn.close()

    def _sql_get_error() -> None: ...

    def _create_tables(self) -> None:
        week_record_tbl = r"""
DROP TABLE IF EXISTS "WeekRecord";
CREATE TABLE "WeekRecord" (
    "province_id"	INTEGER NOT NULL,
    "type"	TEXT,
    "year"	INTEGER,
    "week"	INTEGER,
    "data"	TEXT,
    FOREIGN KEY("province_id") REFERENCES "Provinces"("province_id")
);"""

        provinces_tbl = r"""
DROP TABLE IF EXISTS "Provinces";
CREATE TABLE "Provinces" (
    "province_id"	INTEGER PRIMARY KEY AUTOINCREMENT,
    "name"	TEXT
);"""

        self.cur.execute(week_record_tbl)
        self.cur.execute(provinces_tbl)

        self.conn.commit()

    def _insert_multi(self, tbl: str, values: List[str]) -> None:
        query = r"INSERT INTO {tbl} VALUES {values_list};".format(
            tbl=tbl, values_list=",".join(values))

        self.cur.execute(query)
        self.conn.commit()

    def _insert_provinces(self) -> None:
        self._insert_multi(
            "Provinces",

            ['(NULL, "{name}")'.format(
                name=prov[:prov.find(":")]) for prov in self.parser.provinces]
        )

    def insert_records(self) -> None:
        r"""
        Insert VHI records to database

        :param records: List of WeekRecord with Mean/Parea VHI data
        """
        self._insert_multi(
            "WeekRecords",

            ['({province_id}, "{type}", {year}, {week}, "{data}")'.format(
                province_id=rec.province,
                type="Mean" if len(rec.data) == 1 else "Parea",
                year=rec.year,
                week=rec.week,
                data=",".join([str(i) for i in rec.data])
            ) for rec in records]
        )

    def dump_tocsv(self, fp: str) -> None:
        r"""
        Dump records to csv file

        :param fp: output file path
        """
        # Create folders if they are not exist
        location = fp[:fp.rfind(os.path.sep)]
        mktree(location)

        with open(fp, "a" if self.append_mode else "w", newline="\n") as csv:
            if not self.append_mode:
                csv.write(",".join(["province", "week", "year"] +
                                   gen_columns_labels()) + "\n")

            for rec_list in self.parser.cache.values():
                for rec in rec_list:
                    print(rec)
                    csv.write(str(rec) + "\n")

    def dump_todb(self, fp):
        r"""
        Dump records to sqlite3 database

        :param fp: path to sqlite3 database
        """
        self.conn = sqlite3.connect(fp, timeout=10)
        self.cur = self.conn.cursor()

        if not self.append_mode:
            self._create_tables()

        self._insert_provinces()
        self.insert_records()

    def save_to(self, fp: str, append: bool) -> None:
        """
        Save current records to file

        :param fp: file path
        """

        ext = os.path.splitext(fp)[1]

        self.append_mode = append

        if ext == '.csv':
            self.dump_tocsv(fp)
        elif ext == '.sqlite':
            self.dump_todb(fp)
