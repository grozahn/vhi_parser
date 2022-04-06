import datetime
import pandas as pd

# GTK3 Backend (Toolbar)
from matplotlib.backends.backend_gtk3 import (
    NavigationToolbar2GTK3 as NavigationToolbar)
# GTK3 Backend (Canvas)
from matplotlib.backends.backend_gtk3agg import (
    FigureCanvasGTK3Agg as FigureCanvas)

from matplotlib.figure import Figure

from typing import List, Optional
from .parser import WeekRecord
from .util import gen_columns_labels


class MeanFrame:
    def __new__(cls, records: List[WeekRecord]):
        return pd.DataFrame.from_records(
            data={
                "YW": [datetime.date.fromisocalendar(rec.year, rec.week, 1)
                       for rec in records],
                "Mean": [rec.data[0] for rec in records]
            },
            index="YW")

    @classmethod
    def get_extremums(cls, meandf: pd.DataFrame):
        return (meandf.loc[meandf.idxmin(), "Mean"],
                meandf.loc[meandf.idxmax(), "Mean"])


class PareaFrame:
    def __new__(cls, records: List[WeekRecord]):
        pareadf = pd.DataFrame.from_records(
            [rec.data[1:21] for rec in records],
            columns=gen_columns_labels()
        )

        pareadf["YW"] = [datetime.date.fromisocalendar(rec.year, rec.week, 1)
                         for rec in records]

        return pareadf.set_index("YW")

    @classmethod
    def get_drought_years(cls, pareadf: pd.DataFrame, meandf: pd.DataFrame):
        pareadf['percentage'] = (
            (pareadf > 0.1) & (pareadf < 1)).sum(1)

        pareadf = pareadf[pareadf['percentage'] >= 3]

        return pd.merge(meandf, pareadf, on=['YW'], how='inner')

    @classmethod
    def get_extreme_drought_years(cls, pareadf: pd.DataFrame,
                                  meandf: MeanFrame):

        pareadf["percentage"] = (pareadf <= 0.1).sum(1)
        pareadf = pareadf[pareadf["percentage"] >= 10]

        return pd.merge(meandf, pareadf, on=["YW"], how="inner")


class Plotter:
    r"""
    Provides plot canvas from matplotlib, which could be embedded into GTK3
    application.
    """

    # Background colors for different value ranges
    RANGES = {
        'red':    (0,  15),
        'orange': (15, 35),
        'yellow': (35, 60),
        'green':  (60, 100)
    }

    def __init__(self):
        self.fig = Figure()

        # Create an axis
        self.ax = self.fig.add_subplot(111)

        self.ax.grid(0)
        self.ax.margins(0)

        self.has_ranges = True
        self.canvas = FigureCanvas(self.fig)

    def clear(self):
        """ Clear canvas """

        self.ax.clear()
        self.has_ranges = True

    def refresh(self):
        """ Refresh canvas """

        self.canvas.draw()

    def switch_colors(self, bg: str, fg: str):
        """
        Used for coloring canvas to dark colors

        :param bg: fill background of canvas to passwd color
        :param fg: colorize ticks and labels to passed color
        """

        # Set canvas and axes background
        self.fig.set_facecolor(bg)
        self.ax.set_facecolor(bg)

        # Spines color
        for spine in self.ax.spines.values():
            spine.set_color(fg)

        # Ticks text color
        self.ax.tick_params(axis='x', colors=fg)
        self.ax.tick_params(axis='y', colors=fg)

        # Axis labels color
        self.ax.xaxis.label.set_color(fg)
        self.ax.yaxis.label.set_color(fg)

    def plot(self, series: pd.Series, marker: Optional[str] = '',
             label: Optional[str] = '',
             show_ranges: Optional[bool] = True, **kwargs):
        """ Plot series of data """

        self.ax.set_ylabel('Індекс VHI')

        # Set color ranges
        if show_ranges and self.has_ranges:
            self.has_ranges = False
            for k, v in self.RANGES.items():
                self.ax.axhspan(*v, facecolor=k, alpha=0.5)

        series.plot(marker=marker, label=label, ax=self.ax, **kwargs)
        if label:
            self.ax.legend(loc="upper right")

        # refresh canvas
        self.canvas.draw()

    def get_toolbar(self, win):
        """ Get toolbar widget object from matplotlib plotting GUI """

        return NavigationToolbar(self.canvas, win)
