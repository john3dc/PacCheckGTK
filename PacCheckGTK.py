#!/usr/bin/python3
import gi
import subprocess
import threading
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib
import pty
import os
import re

class PacCheckWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="PacCheck")
        self.set_default_size(900, 600)

        # HeaderBar
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        self.set_titlebar(header_bar)

        # Gtk.Box Haupt
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(vbox)

        # Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_duration(1000)
        self.stack.connect("notify::visible-child-name", self.on_stack_switch_page)
        vbox.pack_start(self.stack, True, True, 0)      
          
        # StackSwitcher
        stack_switcher = Gtk.StackSwitcher()
        stack_switcher.set_stack(self.stack)
        header_bar.set_custom_title(stack_switcher)


        # button
        self.button_refresh = Gtk.Button.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        self.button_refresh.set_tooltip_text("Update Database")
        self.button_refresh.connect("clicked", self.on_button_refresh)
        header_bar.pack_end(self.button_refresh)
        
        self.button_add = Gtk.Button.new_from_icon_name("list-add", Gtk.IconSize.BUTTON)
        self.button_add.set_tooltip_text("Add Packages")
        self.button_add.connect("clicked", self.on_button_add)
        header_bar.pack_start(self.button_add)
        
        self.button_remove = Gtk.Button.new_from_icon_name("list-remove", Gtk.IconSize.BUTTON)
        self.button_remove.set_tooltip_text("Remove Packages")
        self.button_remove.connect("clicked", self.on_button_remove)
        header_bar.pack_start(self.button_remove)
        
        self.button_update= Gtk.Button.new_from_icon_name("software-update-available-symbolic", Gtk.IconSize.BUTTON)
        self.button_update.set_tooltip_text("Update all Packages")
        self.button_update.connect("clicked", self.on_button_update)
        header_bar.pack_start(self.button_update)
        
        
        # Ansichten erstellen und Komponenten speichern
        self.list_store1, self.label1, self.text_view1, self.tree_view1 = self.create_view("Browse")
        self.list_store2, self.label2, self.text_view2, self.tree_view2 = self.create_view("Installed")
        self.list_store3, self.label3, self.text_view3, self.tree_view3 = self.create_view("Updates")

        # Connect the on_selection_changed signal to the callback function
        self.tree_view1.get_selection().connect("changed", self.on_selection_changed)
        self.tree_view2.get_selection().connect("changed", self.on_selection_changed)
        self.tree_view3.get_selection().connect("changed", self.on_selection_changed)

        # Startup List Packages
        self.load_packages()
        self.load_inst_packages()
        self.load_upd_packages()
        
        
        
    # Funktion zum Erstellen der Ansichten
    def create_view(self, title):
        vbox_main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        tree_view = Gtk.TreeView()
        self.setup_treeview_for_multiselect(tree_view)
        tree_view.set_headers_visible(False)
        tree_view_scroll = Gtk.ScrolledWindow()
        tree_view_scroll.add(tree_view)
        tree_view_scroll.set_size_request(280, -1)
        list_store = Gtk.ListStore(str)
        column_text = Gtk.TreeViewColumn("Text", Gtk.CellRendererText(), text=0)
        tree_view.append_column(column_text)
        tree_view.set_model(list_store)
                   
        label = Gtk.Label()
        label.set_text("")
        label.set_xalign(0.0)
        
        text_view = Gtk.TextView()
        text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        #text_view.set_editable(False)
        text_view.set_can_focus(False)
        vbox_text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox_text_bkg = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox_text.pack_start(label, False, True, 0)
        vbox_text.pack_start(text_view, True, True, 0)
        
        text_view_scroll = Gtk.ScrolledWindow()
        text_view_scroll.add(vbox_text)
        
        vbox_text_bkg.pack_start(text_view_scroll, True, True, 0)
        
        vbox_main.pack_start(tree_view_scroll, False, True, 0)
        vbox_main.pack_start(vbox_text_bkg, True, True, 0)
        
        
        
        self.stack.add_titled(vbox_main, title, title)
        
        self.add_css_style(vbox_text_bkg, "box {background-color: white; padding:20px;}")
        self.add_css_style(text_view, "textview {font-family: 'Source Code Pro', monospace;font-size: 14px;}")
        self.add_css_style(tree_view, "treeview {font-family: 'Source Code Pro', monospace;font-size: 15px;padding-left:10px;}")
        self.add_css_style(label, "label {font-family: 'Source Code Pro', monospace;font-size: 18px;}")
        
        return list_store, label, text_view, tree_view
    
    def setup_treeview_for_multiselect(self, tree_view):
        selection = tree_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.MULTIPLE)
    
    def on_button_add(self, button):
        model, paths = self.tree_view1.get_selection().get_selected_rows()
        result_str = ""
        if not paths:
                print("Keine Zeile ausgewählt.")
                return()
        for path in paths:
            iter_ = model.get_iter(path)
            selected_string = model.get_value(iter_, 0)
            result_str = result_str + str(selected_string) + ' '
        pacman_window = PacmanWindow("pkexec pacman -S " + result_str.strip(), "Install Packages")
        pacman_window.set_transient_for(self)
        pacman_window.set_modal(True)
        pacman_window.show_all()
        pacman_window.connect("destroy", self.on_pacman_window_closed)
    
    def on_button_remove(self, button):
        model, paths = self.tree_view2.get_selection().get_selected_rows()
        result_str = ""
        if not paths:
                print("Keine Zeile ausgewählt.")
                return()
        for path in paths:
            iter_ = model.get_iter(path)
            selected_string = model.get_value(iter_, 0)
            result_str = result_str + str(selected_string) + ' '
        pacman_window = PacmanWindow("pkexec pacman -R " + result_str.strip(), "Remove Packages")
        pacman_window.set_transient_for(self)
        pacman_window.set_modal(True)
        pacman_window.show_all()
        pacman_window.connect("destroy", self.on_pacman_window_closed)
        
    def on_button_refresh(self, button):
        pacman_window = PacmanWindow("pkexec pacman -Syy", "Update Database")
        pacman_window.set_transient_for(self)
        pacman_window.set_modal(True)
        pacman_window.show_all()
        pacman_window.connect("destroy", self.on_pacman_window_closed)

    # Package Update
    def on_button_update(self, button):
        pacman_window = PacmanWindow("pkexec pacman -Syu", "Update Packages")
        pacman_window.set_transient_for(self)
        pacman_window.set_modal(True)
        pacman_window.show_all()
        pacman_window.connect("destroy", self.on_pacman_window_closed)


    # Pacman_Window_Handle        
    def on_pacman_window_closed(self, widget):
        self.load_packages()
        self.load_inst_packages()
        self.load_upd_packages()


    # Clear Stear (Browse,Installed or Update)
    def clear_view(self, tree_view, list_store, text_view, label):
        tree_view.set_model(None)
        list_store.clear()
        tree_view.set_model(list_store)
        text_view.get_buffer().delete(text_view.get_buffer().get_start_iter(), text_view.get_buffer().get_end_iter())
        label.set_text("")
    
    
    # List browse packages 
    def load_packages(self):
        thread = threading.Thread(target=self._load_packages_thread)
        thread.daemon = True  
        thread.start()

    def _load_packages_thread(self):
        try:
            output = subprocess.check_output(["pacman", "-Qq"], text=True)
            packages = output.strip().split('\n')
            output2 = subprocess.check_output(["pacman", "-Slq"], text=True)
            packages2 = output2.strip().split('\n')
            unique_packages = sorted(list(set(packages).symmetric_difference(set(packages2))))
            GLib.idle_add(self._update_list_store1, unique_packages)
        except subprocess.CalledProcessError as e:
            print(f"Error executing pacman -Qq: {e}")

    def _update_list_store1(self, unique_packages):
        self.clear_view(self.tree_view1, self.list_store1, self.text_view1, self.label1)
        for package in unique_packages:
            self.list_store1.append([package])
        if self.stack.get_visible_child_name() == "Browse":
            self.tree_view1.get_selection().select_path(Gtk.TreePath.new_first())
    
     
    # List installed packages
    def load_inst_packages(self):
        thread = threading.Thread(target=self._load_inst_packages_thread)
        thread.daemon = True  
        thread.start()

    def _load_inst_packages_thread(self):
        try:
            output = subprocess.check_output(["pacman", "-Qq"], text=True)
            packages = output.strip().split('\n')
            GLib.idle_add(self._update_list_store2, packages)
        except subprocess.CalledProcessError as e:
            print(f"Error executing pacman -Qq: {e}")

    def _update_list_store2(self, packages):
        self.clear_view(self.tree_view2, self.list_store2, self.text_view2, self.label2)
        for package in packages:
            self.list_store2.append([package])
        if self.stack.get_visible_child_name() == "Installed":
            self.tree_view2.get_selection().select_path(Gtk.TreePath.new_first())
    
    # List updates packages
    def load_upd_packages(self):
        thread = threading.Thread(target=self._load_upd_packages_thread)
        thread.daemon = True  
        thread.start()

    def _load_upd_packages_thread(self):
        try:
            output = subprocess.check_output(["pacman", "-Quq"], text=True)
            packages = output.strip().split('\n')
            GLib.idle_add(self._update_list_store3, packages)
        except subprocess.CalledProcessError as e:
            self.clear_view(self.tree_view3, self.list_store3, self.text_view3, self.label3)
            #print(f"Error executing pacman -Qq: {e}")

    def _update_list_store3(self, packages):
        self.clear_view(self.tree_view3, self.list_store3, self.text_view3, self.label3)
        for package in packages:
            self.list_store3.append([package])
        if self.stack.get_visible_child_name() == "Updates":
            self.tree_view3.get_selection().select_path(Gtk.TreePath.new_first())
    
    # Add css style                
    def add_css_style(self, widget, style):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(style)
        context = widget.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    
    # Stackswitch
    def on_stack_switch_page(self, stack, param):
        if stack.get_visible_child_name() == "Browse":
            self.button_add.show()
            self.button_remove.hide()
            self.button_update.hide()
            if not self.tree_view1.get_selection().count_selected_rows() > 0:
                self.tree_view1.get_selection().select_path(Gtk.TreePath.new_first())
        elif stack.get_visible_child_name() == "Installed":
            self.button_add.hide()
            self.button_remove.show()
            self.button_update.hide()
            if not self.tree_view2.get_selection().count_selected_rows() > 0:
                self.tree_view2.get_selection().select_path(Gtk.TreePath.new_first())
        elif stack.get_visible_child_name() == "Updates":
            self.button_add.hide()
            self.button_remove.hide()
            self.button_update.show()
            if not self.tree_view3.get_selection().count_selected_rows() > 0:
                self.tree_view3.get_selection().select_path(Gtk.TreePath.new_first())
    
    # Selected package info
    def on_selection_changed(self, selection):
        model, pathlist = selection.get_selected_rows()
        for path in pathlist:
            treeiter = model.get_iter(path)
            package_name = model.get_value(treeiter,0)
            self.run_and_update_pacman_Si(package_name)

    def run_and_update_pacman_Si(self, package_name):
        def _run_pacman_Si_thread():
            try:
                package = package_name
                output = subprocess.check_output(["pacman", "-Si", package], text=True)
                if self.stack.get_visible_child_name() == "Updates":
                    package = subprocess.check_output(["pacman", "-Qu", package], text=True)
                GLib.idle_add(self.update_text_view, output, package)
            except subprocess.CalledProcessError as e:
                print(f"Error executing pacman -Si: {e}")

        threading.Thread(target=_run_pacman_Si_thread, daemon=True).start()

    def update_text_view(self, result, package_name):
        if self.stack.get_visible_child_name() == "Browse":
            buffer = self.text_view1.get_buffer()
            self.label1.set_text(package_name)
        if self.stack.get_visible_child_name() == "Installed":
            buffer = self.text_view2.get_buffer()
            self.label2.set_text(package_name)
        if self.stack.get_visible_child_name() == "Updates":
            buffer = self.text_view3.get_buffer()
            self.label3.set_text(package_name)
            
        tag_table = buffer.get_tag_table()
        tag_indent = tag_table.lookup("indent")
        if tag_indent is None:
            tag_indent = Gtk.TextTag(name="indent")
            tag_indent.set_property("indent", -215)
            tag_indent.set_property("wrap-mode", Gtk.WrapMode.WORD)
            tag_table.add(tag_indent)
        buffer.delete(buffer.get_start_iter(), buffer.get_end_iter())
        buffer.insert_with_tags_by_name(buffer.get_end_iter(), result, "indent")

class PacmanWindow(Gtk.Window):
    def __init__(self, package_name, windowtitle):
        super().__init__(title=windowtitle)
        self.set_default_size(800, 400)
        self.connect("delete-event", self.on_delete_event)
        self.set_border_width(10)
        
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.output_textview = Gtk.TextView()
        self.output_textview.set_can_focus(False)
        self.output_textbuffer = self.output_textview.get_buffer()
        self.output_textview.set_can_focus(False)
        self.add_css_style(self.output_textview, "textview {font-family: 'Source Code Pro', monospace;}")

        self.input_entry = Gtk.Entry()
        self.input_entry.connect("activate", self.on_input_entry_activate)

        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.add(self.output_textview)

        self.vbox.pack_start(self.scrolled_window, False, True, 0)
        self.vbox.pack_start(self.input_entry, False, False, 0)
        self.add(self.vbox)

        self.spawn_pacman_process(package_name)

        self.button1 = Gtk.Button(label="Ok")
        self.button1.connect("clicked", self.install_close)
        self.vbox.pack_start(self.button1, False, False, 0)
        
        self.input_entry.grab_focus() 

    def spawn_pacman_process(self, package_name):
        master_fd, slave_fd = pty.openpty()

        self.pacman_process = subprocess.Popen(
            [package_name],
            stdout=slave_fd,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1,
            preexec_fn=os.setsid,
            shell=True
        )

        self.pacman_output_channel = GLib.io_add_watch(master_fd, GLib.IO_IN, self.on_pacman_output)
        GLib.timeout_add(100, self.check_process_status)

    def on_pacman_output(self, source, condition):
        if condition == GLib.IO_IN:
            output = os.read(source, 1024).decode('utf-8')
            filtered_output = self.filter_pacman_escape_sequences(output)
            end_iter = self.output_textbuffer.get_end_iter()
            self.output_textbuffer.insert(end_iter, filtered_output)
            mark = self.output_textbuffer.create_mark(None, end_iter, False)
            if self.output_textview and self.output_textview.get_window(Gtk.TextWindowType.TEXT):
                self.output_textview.scroll_to_mark(mark, 0.0, False, 0.0, 1.0)
            return True

    def filter_pacman_escape_sequences(self, text):
        pacman_escape_pattern = r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'
        return re.sub(pacman_escape_pattern, '', text)

    def on_input_entry_activate(self, widget):
        input_text = self.input_entry.get_text()
        self.input_entry.set_text("")
        self.pacman_process.stdin.write(input_text + "\n")
        self.pacman_process.stdin.flush()

    def check_process_status(self):
        if self.pacman_process.poll() is not None:
            self.input_entry.set_visible(not self.input_entry.get_visible())
            self.resize(self.get_size()[0], self.get_size()[1] - 34)
            self.button1.set_label("Close")
            return False  
        return True  

    def on_delete_event(self, widget, event):
        if self.pacman_process.poll() is None:
            self.pacman_process.stdin.close()

    def install_close(self, widget=None):
        if self.button1.get_label() == "Close":
            if self.pacman_process.poll() is None:
                self.pacman_process.stdin.close()
            self.destroy()
        else:
            self.pacman_process.stdin.write("\n")
        self.pacman_process.stdin.flush()
        
        # Add css style                
    def add_css_style(self, widget, style):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(style)
        context = widget.get_style_context()
        context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

if __name__ == '__main__':
# Create an instance of StackWindow and run the Gtk main loop
    win = PacCheckWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    win.button_remove.hide()
win.button_update.hide()
Gtk.main()
