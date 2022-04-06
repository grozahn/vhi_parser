# Gtk stuff
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gio, Gtk

import os
from typing import Tuple
from vhi import mktree


class ErrorDialog(Gtk.MessageDialog):
    r"""
    Wrapper around MessageDialog to make dialog window with error message
    """

    def __init__(self, parent: Gtk.Widget,
                 text: str, secondary_text: str):

        Gtk.MessageDialog.__init__(self,
                                   transient_for=parent,
                                   flags=0,
                                   message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.CANCEL,
                                   text=text)
        self.format_secondary_text(secondary_text)
        self.run()

    def __del__(self):
        self.destroy()


class ExceptionDialog:
    r"""
    Creates ErrorDialog with message from Exception
    """

    def __new__(cls, parent: Gtk.Widget, error: Exception) -> None:
        ErrorDialog(parent, error.__class__.__name__, str(error))
        raise error


class SaveDialog(Gtk.FileChooserDialog):
    r"""
    Wrapper around FileChooserDialog to select file saving location
    """

    FILTERS = {
        "Text CSV":         "*.csv",
        "SQLite database":  "*.sqlite",
        "All files":        "*"
    }

    def __init__(self, parent: Gtk.Window, title="Select saving location"):
        Gtk.FileChooserDialog.__init__(self, title=title, parent=parent,
                                       action=Gtk.FileChooserAction.SAVE)

        self.set_default_size(800, 400)
        self.set_local_only(True)
        #  self.set_do_overwrite_confirmation(True)

        self.append_mode = False

        self.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            "Save",
            Gtk.ResponseType.OK
        )

        # Apppend to file CheckButton
        self.append_mode_chkbtn = Gtk.CheckButton(label="Append to file")
        self.append_mode_chkbtn.connect("toggled",
                                        self._on_append_mode_chkbtn_toggled)
        #  self.append_mode_chkbtn.set_label()

        # Adding append-mode-chkbtn to content area
        content_area = self.get_content_area()
        content_area.pack_end(self.append_mode_chkbtn, False, False, 2)
        content_area.show_all()

        # Add file filters
        self._add_filters()

    def _on_append_mode_chkbtn_toggled(self, chkbtn: Gtk.CheckButton) -> None:
        self.append_mode = chkbtn.get_active()

    def _add_filters(self) -> None:
        for name, pattern in self.FILTERS.items():
            filt = Gtk.FileFilter()
            filt.set_name(name)
            filt.add_pattern(pattern)

            self.add_filter(filt)

    def select(self) -> Tuple[str, bool]:
        # Create and set initial dumping directory
        mktree("dumps")
        self.set_current_folder(os.path.abspath("dumps"))

        fp = None
        if self.run() == Gtk.ResponseType.OK:
            fp = self.get_filename()
        self.destroy()
        return (fp, self.append_mode)


class ParserWindow(Gtk.Window):
    r"""
    Main application window

    Places GtkGrid (main-grid) as child
    """

    # Window title
    TITLE = "VHI Parser"

    def __init__(self):
        Gtk.Window.__init__(self)

        self.set_title(self.TITLE)

        # For testing purpose
        # self.set_resizable(True)
        # self.set_default_size(400, 300)

        # "destroy" signal handler
        self.connect("destroy", self._on_destroy)

        # To change application theme
        self._settings = Gtk.Settings.get_default()

        # Import GUI mockup made with Glade
        builder = Gtk.Builder()
        builder.add_from_file("ui/ParserWindow.ui")
        builder.connect_signals(self)

        # Main widgets container
        self.main_grid = builder.get_object("main-grid")

        # Vertical box with canvas and toolbar
        self.plt_vbox = builder.get_object("plt-vbox")

        # Dark theme switch
        self.use_dark_theme_switch = builder.get_object(
            "use-dark-theme-switch")

        # Settings stack
        self.settings_stack = builder.get_object("settings-stack")

        # Settings ListBox
        self.listbox1 = builder.get_object("listbox1")

        # * Province selection Combo
        self.province_combo = builder.get_object("province-combo")

        # * Year ranges Combos
        self.year1_combo = builder.get_object("year1-combo")
        self.year2_combo = builder.get_object("year2-combo")

        # * CheckButtons group
        self.show_extremums_chkbtn = builder.get_object(
            "show-extremums-chkbtn")

        self.show_vhi_ranges_chkbtn = builder.get_object(
            "show-vhi-ranges-chkbtn")

        # * Stack
        # self.stack1 = builder.get_object("stack1")

        # ** Plot button
        self.plot_btn = builder.get_object("plot-btn")

        # ** Spinner
        # self.spinner1 = builder.get_object("spinner1")

        # Save to database button
        self.save_btn = builder.get_object("save-btn")

        # * Canvas clear button
        self.clear_canvas_btn = builder.get_object("clear-canvas-btn")

        # * Show drought years CheckButton
        self.show_drought_years_chkbtn = builder.get_object(
            "show-drought-years-chkbtn")

    def _on_destroy(self, widget: Gtk.Widget) -> None:
        Gtk.main_quit()

    def show(self) -> None:
        self.add(self.main_grid)
        self.show_all()
