import sys
import webbrowser
from socket import error as socker_error
from urllib2 import URLError
from PySide import QtGui, QtCore
from furl.furl import furl
from jinja2 import FileSystemLoader
from jinja2.environment import Environment
from time import time
from bf3 import BF3Server, browse_server, get_regions
from iso_country_codes import COUNTRY
from pinger import do_one


class MainWindow(QtGui.QDialog):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle('Battlefield 3 Server Browser')
        self.setWindowFlags(QtGui.QStyle.SP_TitleBarMinButton)
        QtGui.QStatusBar
        # Main Vertical Box Layout
        vbox = QtGui.QVBoxLayout()

        # Maps List
        self.map_check_box, map_widget = self.make_layout(2, BF3Server.map_code.values(), 'MAPS')

        # Mode List
        self.mode_check_box, mode_widget = self.make_layout(2, BF3Server.game_mode.values(), 'MODE')

        # Game Size List
        self.game_size_check_box, game_size_widget = self.make_layout(6, BF3Server.game_size.values(), 'GAME SIZE')

        # Free Slots List
        self.free_slots_check_box, free_slots_widget = self.make_layout(5, BF3Server.free_slots.values(), 'FREE SLOTS')

        # Preset List
        self.preset_check_box, preset_widget = self.make_layout(3, BF3Server.preset.values(), 'PRESET')

        # Base Game and Expansion Packs List
        self.game_check_box, game_widget = self.make_layout(3, BF3Server.game.values(), 'GAME')

        # Text box for server name search query
        self.server_name_search_box = QtGui.QLineEdit()
        self.server_name_search_box.setPlaceholderText("Server Name Filter")

        self.countries = []

        # Lets make the buttons
        browse_button = QtGui.QPushButton('Browse')
        default_button = QtGui.QPushButton('Default')
        regions_button = QtGui.QPushButton('Select Regions')
        # QHBoxLayout for the buttons
        button_hbox = QtGui.QHBoxLayout()
        # Adding the buttons to the layout. addStretch() adds blank space between the buttons.
        button_hbox.addWidget(default_button)
        button_hbox.addStretch(True)
        button_hbox.addWidget(regions_button)
        button_hbox.addWidget(browse_button)

        # QVBoxLayout for adding various small widgets to the left.
        vbox_left = QtGui.QVBoxLayout()
        vbox_left.addWidget(mode_widget)
        vbox_left.addWidget(game_size_widget)
        vbox_left.addWidget(free_slots_widget)
        vbox_left.addWidget(preset_widget)
        vbox_left.addWidget(game_widget)

        # QVBoxLayout fir adding map name checkboxes and other widgets.
        vbox_right = QtGui.QVBoxLayout()
        vbox_right.addWidget(map_widget)
        vbox_right.addWidget(self.server_name_search_box)

        # QHBoxLayout for making two main columns. vbox_left is added to the left and map_widget to the right.
        hbox = QtGui.QHBoxLayout()
        hbox.addLayout(vbox_left)
        hbox.addLayout(vbox_right)

        # Label to show the selected regions/countries.
        self.region_label = QtGui.QLabel("Region: None")
        self.region_label.setWordWrap(True)

        # Finally adding the hbox containing almost all checkboxes to the main vbox.
        # Buttons are added to the bottom of the vbox.
        vbox.addLayout(hbox)
        vbox.addWidget(self.region_label)
        vbox.addLayout(button_hbox)

        browse_button.clicked.connect(self.fetch_data)
        default_button.clicked.connect(self.set_default)
        regions_button.clicked.connect(self.callRegionWindow)

        self.setLayout(vbox)
        self.set_default()

    def make_layout(self, col, label_list, group_box_label):
        """
        Makes a QGridLayout of checkboxes based on the following parameters.
        :param col: Number of columns the grid should have.
        :param label_list: List of string values to use as label for the checkboxes.
        :param group_box_label: Label (string) to use for group box enclosing the grid.
        :return check_box_list: List of QCheckBox objects.
        :return group_box: QGroupBox object enclosing the grid of checkboxes.
        """
        check_box_list = []
        if len(label_list) < col:
            col = len(label_list)
        grid_layout = QtGui.QGridLayout()
        for i in range((len(label_list) / col) + 1):
            for j in range(col):
                index = (i * col) + j
                if index > len(label_list) - 1:
                    continue
                check_box_list.append(QtGui.QCheckBox(label_list[index]))
                grid_layout.addWidget(check_box_list[-1], i, j)
        group_box = QtGui.QGroupBox(group_box_label)
        group_box.setLayout(grid_layout)
        return check_box_list, group_box

    def set_default(self):
        """ Checks the default options as on Battlelog. """
        self.clear_all_checkboxes()
        map(lambda x: x.toggle(), self.game_check_box)
        self.preset_check_box[0].toggle()
        self.server_name_search_box.clear()

    def clear_all_checkboxes(self):
        """ Clears all the checkboxes. """
        check_box_listception = (self.map_check_box, self.mode_check_box, self.game_size_check_box,
                                 self.free_slots_check_box, self.preset_check_box, self.game_check_box)
        for check_box_list in check_box_listception:
            for check_box in check_box_list:
                if check_box.isChecked():
                    check_box.toggle()

    def fetch_data(self):
        """
        Fetches the data from Battlelog and shows the result to the user.
        Here self.build_url() is called for every QCheckBox list we have.
        Checks whether the application has admin privilege by sending one ping.
        """
        try:
            do_one("battlelog.battlefield.com")
        except socker_error:
            error_msg = "Cannot ping the servers since the application doesn't have admin privilege."
            QtGui.QMessageBox.warning(self, "Socket Error", error_msg)
            return
        start_time = time()
        self.base_url = furl("http://battlelog.battlefield.com/bf3/servers/")
        self.base_url.add({'filtered': '1'})
        self.build_url(self.map_check_box, BF3Server.map_code, 'maps')
        self.build_url(self.mode_check_box, BF3Server.game_mode, 'gamemodes')
        self.build_url(self.game_size_check_box, BF3Server.game_size, 'gameSize')
        self.build_url(self.free_slots_check_box, BF3Server.free_slots, 'slots')
        self.build_url(self.preset_check_box, BF3Server.preset, 'gamepresets')
        self.build_url(self.game_check_box, BF3Server.game, 'gameexpansions')
        if self.countries:
            self.base_url.add({'useLocation': '1'})
            self.base_url.add({'country': '|'.join(self.countries)})
        print self.base_url
        print self.countries
        try:
            server_list = browse_server(url=str(self.base_url))
        except URLError:
            error_msg = "Unable to retrieve server data from the Battlelog. Please check your network connection."
            QtGui.QMessageBox.warning(self, "Network Error", error_msg)
            return
        time_elapsed = round(time() - start_time, 2)
        template_env = Environment()
        template_env.loader = FileSystemLoader('.')
        template_args = dict(servers=enumerate(server_list), bf3=BF3Server, time_elapsed=time_elapsed)
        output = template_env.get_template('layout.html').render(**template_args).encode('utf8')
        open('output_temp.html', 'w').write(output)
        webbrowser.open('output_temp.html')

    def build_url(self, check_box_list, bf3_data_list, param_name):
        """
        Checks every QCheckBox object in check_box_list for whether it is checked
        and builds URL query according to that.
        Doesn't returns anything. Just modifies the self.base_url
        """
        for checkbox in check_box_list:
            if checkbox.isChecked():
                map_name = [x for x, y in bf3_data_list.iteritems() if y == checkbox.text()]
                self.base_url.add({param_name: map_name})

    def callRegionWindow(self):
        """
        Invokes the Region Selection dialog.
        """
        try:
            country_codes = get_regions()
        except URLError:
            error_message = "Unable to retrieve region data from the Battlelog. Please check your network connection."
            QtGui.QMessageBox.warning(self, "Network Error", error_message)
            return
        dialog = RegionWindow(country_codes)
        if dialog.exec_():
            checked_countries = []
            for region in dialog.cc_check_boxes:
                for check_box in region:
                    if check_box.isChecked():
                        checked_countries.append(check_box.text())
            if len(checked_countries):
                region_label_text = "Regions: " + ', '.join(checked_countries)
                self.region_label.setText(region_label_text)
                self.countries = [y.lower() for x in checked_countries for y, z in COUNTRY.iteritems() if z == x.upper()]
            else:
                self.region_label.setText("Region: None")


class RegionWindow(MainWindow):

    def __init__(self, country_codes, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle('Region Selector')
        vbox = QtGui.QVBoxLayout()

        self.cc_check_boxes = []
        cc_group_boxes = []
        for region in country_codes.keys():
            country_codes_list = [COUNTRY[i.upper()].title() for i in country_codes[region]]
            check_boxes, group_box = self.make_layout(2, country_codes_list, BF3Server.regions[region])
            self.cc_check_boxes.append(check_boxes)
            cc_group_boxes.append(group_box)

        hbox = QtGui.QHBoxLayout()
        hbox_vbox_left = QtGui.QVBoxLayout()
        hbox_vbox_right = QtGui.QVBoxLayout()

        hbox_vbox_left.addWidget(cc_group_boxes[0])
        hbox_vbox_left.addWidget(cc_group_boxes[1])
        for i in cc_group_boxes[2:]:
            hbox_vbox_right.addWidget(i)

        hbox.addLayout(hbox_vbox_left)
        hbox.addLayout(hbox_vbox_right)
        vbox.addLayout(hbox)

        button_hbox = QtGui.QHBoxLayout()
        ok_button = QtGui.QPushButton("OK")
        cancel_button = QtGui.QPushButton("Cancel")
        button_hbox.addStretch(True)
        button_hbox.addWidget(ok_button)
        button_hbox.addWidget(cancel_button)
        vbox.addLayout(button_hbox)

        self.connect(ok_button, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("accept()"))
        self.connect(cancel_button, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("reject()"))

        self.setLayout(vbox)

app = QtGui.QApplication(sys.argv)
window = MainWindow()
window.show()
window.setFixedSize(window.size())
app.exec_()