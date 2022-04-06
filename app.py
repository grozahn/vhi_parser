#!/usr/bin/env python3

# Gtk stuff
import gi
gi.require_versions({'Gtk': '3.0', 'GLib': '2.0', 'Gio': '2.0'})
from gi.repository import GLib, Gio, Gtk

from widgets import ParserWindow, SaveDialog, ErrorDialog, ExceptionDialog

import os
import datetime
from threading import Thread

# VHI stuff
from vhi import (
    Parser, WeekRecord,
    MeanFrame, PareaFrame, Plotter,
    Storage,
    SavingError,
    mktree,
    gtk_rgb_to_hex
)


class ParserApp(ParserWindow):
    def __init__(self):
        ParserWindow.__init__(self)

        # Parser, Storage and Plotter instances
        self.parser = Parser()
        self.storage = Storage(self.parser)
        self.plt = Plotter()

        # Connect extra signals
        self.connect("show", self._on_window_show)

        self.use_dark_theme_switch.connect("state-set",
                                           self._on_use_dark_theme_state_set)

        self.plot_btn.connect("clicked", self._on_plot_btn_clicked)
        self.save_btn.connect("clicked", self._on_save_btn_clicked)
        self.clear_canvas_btn.connect("clicked",
                                      self._on_clear_canvas_btn_clicked)

        # Setup widgets
        # - Set canvas size
        self.plt.canvas.set_size_request(600, 500)

        # - Add canvas to plt_vbox
        self.plt_vbox.pack_start(self.plt.canvas, True, True, 0)

        # - Add toolbar to plt_vbox
        self.toolbar = self.plt.get_toolbar(self.plt_vbox)
        self.toolbar.set_valign(Gtk.Align.END)

        self.plt_vbox.pack_start(self.toolbar, False, False, 0)

    # For testing purpose only
    def _delay(self, seconds: float):
        from time import time

        start = time()
        while time() != start + seconds:
            pass

    def _on_window_show(self, win):
        def init_job(self):
            self.listbox1.set_sensitive(False)
            self._fill_combos()
            self.listbox1.set_sensitive(True)

        Thread(target=init_job, args=(self, )).start()

    def _on_plot_btn_clicked(self, btn):
        # Taking settings from GUI
        province = self.province_combo.get_active_text()
        years = (int(self.year1_combo.get_active_text()),
                 int(self.year2_combo.get_active_text()))

        # Get CheckButtons state
        show_extremums = self.show_extremums_chkbtn.get_active()
        show_ranges = self.show_vhi_ranges_chkbtn.get_active()
        show_drought_years = self.show_drought_years_chkbtn.get_active()

        # Plotting itself

        # Set limits for X axis
        self.plt.ax.set_xlim(datetime.date.fromisocalendar(years[0]-1, 1, 1),
                             datetime.date.fromisocalendar(years[1]+1, 1, 1))

        # Get VHI Mean/Parea data
        self.mean_records = self.parser.parse_mean(province, years)

        # Plot Mean data
        mdf = MeanFrame(self.mean_records)
        self.plt.plot(mdf["Mean"], show_ranges=show_ranges, label=province)

        if show_extremums:
            extr = MeanFrame.get_extremums(mdf)
            self.plt.plot(extr[0], marker='o', show_ranges=show_ranges)
            self.plt.plot(extr[1], marker='o', show_ranges=show_ranges)

        if show_drought_years:
            self.parea_records = self.parser.parse_parea(province, years)

            # For calculating drought years
            pdf = PareaFrame(self.parea_records)

            # Plot drought years
            drought = PareaFrame.get_drought_years(pdf, mdf)
            self.plt.plot(drought["Mean"], show_ranges=show_ranges,
                          label=province + ": Помірні посухи",
                          color="orange")

            # Plot extreme drought years
            extreme_drought = PareaFrame.get_extreme_drought_years(pdf, mdf)
            self.plt.plot(extreme_drought["Mean"], show_ranges=show_ranges,
                          label=province + ": Екстримальні посухи",
                          color="red")

    def _on_save_btn_clicked(self, btn):
        fp, append = SaveDialog(self).select()
        if not fp:
            ErrorDialog(self, "Failed to save data",
                        "Output file was not selected")

        try:
            self.storage.save_to(fp, append)
        except SavingError as e:
            ExceptionDialog(self, e)

    def _on_clear_canvas_btn_clicked(self, btn):
        self.plt.clear()
        self.plt.refresh()

    # Callback for dark mode switch
    def _on_use_dark_theme_state_set(self, switch, state: bool):
        self._settings.set_property("gtk-application-prefer-dark-theme", state)

        # Get toolbar background and foreground colors after theme switching
        style = self.toolbar.get_style_context()

        # FIXME: "get_background_color()" is deprecated
        bgcolor = style.get_background_color(Gtk.StateFlags.NORMAL)
        fgcolor = style.get_color(Gtk.StateFlags.NORMAL)

        # Set retrieved colors for Plotter
        self.plt.switch_colors(gtk_rgb_to_hex(bgcolor.to_string()),
                               gtk_rgb_to_hex(fgcolor.to_string()))

        self.plt.refresh()

    def _fill_combos(self):
        r"""
        Fills Comboboxes with data such as Province and available years range
        """

        # Get available provinces and years
        self.parser.parse_selectors()

        # Fill Province selection Combo
        for prov in self.parser.provinces:
            self.province_combo.append_text(prov)
        self.province_combo.set_active(0)

        # Fill years range combos
        for year in self.parser.years:
            self.year1_combo.append_text(year)
            self.year2_combo.append_text(year)

        # Set active items
        self.year1_combo.set_active(0)
        self.year2_combo.set_active(len(self.parser.years) - 1)

    def run(self):
        self.show()
        Gtk.main()


if __name__ == "__main__":
    app = ParserApp()
    app.run()
