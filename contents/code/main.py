#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt, QFileSystemWatcher, QObject, SIGNAL
from PyQt4.QtGui import QGraphicsLinearLayout, QButtonGroup
from PyKDE4.plasma import Plasma
from PyKDE4 import plasmascript

from re import split

class PlasmaFreq(plasmascript.Applet):
    def __init__(self, parent, args=None):
        # Init for plasma applet
        plasmascript.Applet.__init__(self, parent)

    def listGovernors(self):
        # Lists governors aka power modes available in current system.
        path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors" # This is the file that usually contain available governor
        governorsFile = open(path, 'r') # Open the file
        self.watcher.addPath(path)
        availableGovernors = governorsFile.read()
        governorsList = split(" +", availableGovernors) # Splitting the string to list, space is the separator
        governorsList.remove("\n") # Remove newline item from list, added by split
        return governorsList # Returns a well-fromed list containing available governors

    def listFrequencies(self):
        # Lists processor core frequencies available for scaling
        path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies"
        frequenciesFile = open(path, 'r') # This is the file that usually contain available frequencies
        self.watcher.addPath(path)
        availableFrequencies = frequenciesFile.read()
        frequenciesList = split(" +", availableFrequencies) # Splitting the string to list, space is the separator
        frequenciesList.remove("\n") # Remove newline item from list, added by split
        return frequenciesList # Returns a well-fromed list containing available frequencies

    def currentGovernor(self):
        # Returns a string containing the current governor
        path = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        governorFile = open(path, 'r')
        self.watcher.addPath(path)
        currentGovernor = governorFile.read()
        currentGovernor = currentGovernor.rstrip() # Removes newline from string, since we don't need a list for this.
        return currentGovernor

    def file_changed(self, path):
        print "Something changed!"

    def init(self):

        # Setting some Plasma-specific settings
        self.setHasConfigurationInterface(False) # We dont have a configuration interface, yet.
        self.theme = Plasma.Svg(self)
        self.setBackgroundHints(Plasma.Applet.DefaultBackground
        self.layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
        self.applet.setLayout(self.layout)

        # Adding a nice-looking GroupBox for RadioButtons
        self.setGovernorBox = Plasma.GroupBox(self.applet)
        self.setGovernorBox.setText("Mode selection")
        self.setGovernorBox.setLayout(QGraphicsLinearLayout(Qt.Vertical,self.setGovernorBox))
        self.layout.addItem(self.setGovernorBox)
        self.governorGroup = QButtonGroup(self.applet) # Creating a abstract ButtonGroup in order to link RadioButtons together

        # Creating a QFileSystemWatcher to watch changes in current frequency and governor
        self.watcher = QFileSystemWatcher(self)
        QObject.connect(self.watcher,SIGNAL("fileChanged(const QString&)"), self.file_changed)

        # Initializing some variables and setting variables to them.
        self.availableFrequencies = self.listFrequencies()
        self.availableGovernors = self.listGovernors()
        self.currentGovernor = self.currentGovernor()
        self.radioButton = {}
        # This contains texts and tooltips for RadioButtons
        self.governorTextsDict = {'conservative' : ['Conservative', 'Similiar to On Demand, but CPU clock speed switches gradually through all its available frequencies based on system load '],
                          'ondemand' : ['On Demand', 'Dynamically switches between the CPU available clock speeds based on system load '],
                          'userspace' : ['User Defined', 'Lets user to manually configure clock speeds'],
                          'powersave' : ['Powersave', 'Runs the CPU at minimum clock speeds'],
                          'performance' : ['Performance','Runs the CPU at maximum clock speeds']}

        for x in self.availableGovernors:
            # Makes a RadioButton for each governor available.
            self.radioButton[x] = Plasma.RadioButton(self.applet) # The object is added to dict and "paired" with name of the governor
            # Define that what governor x is and set a human readable text for radioButton
            self.radioButton[x].setText(self.governorTextsDict[x][0]) # Sets the text for radioButton from governorTextsDict above
            self.radioButton[x].setToolTip(self.governorTextsDict[x][1])
            self.governorGroup.addButton(self.radioButton[x].nativeWidget()) # Adds RadioButton's native widget to abstract governorGroup
            self.setGovernorBox.layout().addItem(self.radioButton[x]) # Adds radioButton to setGovernorBox layout
            if x == self.currentGovernor:
                self.radioButton[x].setChecked(True) # Checks if x is current governor and should we have a tick on RadioButton


def CreateApplet(parent):
    # Telling to Plasma that what class contains the applet
    return PlasmaFreq(parent)

# She came to me with a serpent's kiss
# as the Eye of the Sun rose on her lips,
# moonlight catches silver tears I cry.
# So we lay in a black embrace
# and the Seed is sown in a holy place
# and I watched and I waited for the dawn.
