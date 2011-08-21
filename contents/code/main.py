#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt, QFileSystemWatcher, QObject, SIGNAL
from PyQt4.QtGui import QGraphicsLinearLayout, QButtonGroup, QSizePolicy
from PyKDE4.plasma import Plasma
from PyKDE4.kdecore import KAuth
from PyKDE4.kdeui import KPasswordDialog
from PyKDE4 import plasmascript

from re import split
from subprocess import call
from os import devnull

class PlasmaFreq(plasmascript.Applet):
    def __init__(self, parent, args=None):
        # Init for plasma applet
        plasmascript.Applet.__init__(self, parent)

    def listGovernors(self):
        # Lists governors aka power modes available in current system.
        self.listGovPath = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors"
        governorsFile = open(self.listGovPath, 'r') # Open the file
        availableGovernors = governorsFile.read()
        governorsList = split(" +", availableGovernors) # Splitting the string to list, space is the separator
        governorsList.remove("\n") # Remove newline item from list, added by split
        governorsFile.close()
        return governorsList

    def listFrequencies(self):
        # Lists processor core frequencies available for scaling
        self.listFreqPath = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_available_frequencies"
        frequenciesFile = open(self.listFreqPath, 'r')
        availableFrequencies = frequenciesFile.read()
        frequenciesList = split(" +", availableFrequencies)
        frequenciesList.remove("\n")
        frequenciesFile.close()
        return frequenciesList

    def currentFrequency(self):
        # Returns a string containing the current governor
        self.curFreqPath = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"
        frequencyFile = open(self.curFreqPath, 'r')
        if self.curFreqPath not in self.watcher.files():
            self.watcher.addPath(self.curFreqPath)
        currentFrequency = frequencyFile.read()
        currentFrequency = currentFrequency.rstrip() # Removes newline from string, since we don't need a list for this.
        frequencyFile.close()
        return currentFrequency

    def currentGovernor(self):
        self.curGovPath = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
        governorFile = open(self.curGovPath, 'r')
        if self.curGovPath not in self.watcher.files(): # Not adding file to watcher in case of it exicsts already
            self.watcher.addPath(self.curGovPath)
        currentGovernor = governorFile.read()
        currentGovernor = currentGovernor.rstrip() # Removes newline from string, since we don't need a list for this.
        governorFile.close()
        return currentGovernor

    def file_changed(self, path):
        if path == self.curGovPath: # When scaling governor has changed, this is true
            self.currentGovernorStr = self.currentGovernor()
            self.radioButton[self.currentGovernorStr].setChecked(True) # Check radioButton that represents the new governor

        if path == self.curFreqPath:
            self.currentFrequencyStr = self.currentFrequency()

    def applyChanges(self):
        # We basically run a for-loop to try out that which radioButton is checked. Better ways warmly welcome.
        for x in self.availableGovernors:
            if self.radioButton[x].isChecked() == True: # radioButton for x governor is checked
                governor = '"%s"' % x # Adding quotes to governor name
                # Insert some variables to command. We should use KAuth instead of kdesudo but I have no idea how to use KAuth in python
                cmd = "kdesudo -d -i %s --comment '<b>PlasmaFreq</b> need administrative priviledges. Please enter your password.' -c 'echo %s > %s'" % (self.icon, governor, self.curGovPath)
                # Run the command. shell=True would be a security vulnerability (shell injection) if the cmd parameter would have something from user input
                fnull = open(devnull, 'w') # Open /dev/null for stdout/stderr redirection
                call(cmd, shell=True, stdout = fnull, stderr = fnull)
                fnull.close()


    def init(self):

        # Setting some Plasma-specific settings
        self.setHasConfigurationInterface(False) # We dont have a configuration interface, yet.
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        self.theme = Plasma.Svg(self)
        self.setBackgroundHints(Plasma.Applet.DefaultBackground)
        self.layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
        self.applet.setLayout(self.layout)
        self.icon = self.package().path() + "plasmafreq.svg" # Finding a path for our apps icon

        # Adding a nice-looking GroupBox for RadioButtons
        self.setGovernorBox = Plasma.GroupBox(self.applet)
        self.setGovernorBox.setText("Mode selection")
        self.setGovernorBox.setLayout(QGraphicsLinearLayout(Qt.Vertical,self.setGovernorBox))
        self.layout.addItem(self.setGovernorBox)
        self.governorGroup = QButtonGroup(self.applet) # Creating a abstract ButtonGroup in order to link RadioButtons together

        # Creating a QFileSystemWatcher to watch changes in current frequency and governor
        self.watcher = QFileSystemWatcher(self)
        QObject.connect(self.watcher,SIGNAL("fileChanged(const QString&)"), self.file_changed)

#        # Initializing some variables and setting variables to them.
        self.availableFrequencies = self.listFrequencies()
        self.availableGovernors = self.listGovernors()
        self.currentGovernorStr = self.currentGovernor()
        self.currentFrequencyStr = self.currentFrequency()
        self.radioButton = {}
        # This contains texts and tooltips for RadioButtons
        self.governorTextsDict = {'conservative' : ['Conservative', 'Similiar to On Demand, but CPU clock speed switches gradually through all its available frequencies based on system load '],
                          'ondemand' : ['On Demand', 'Dynamically switches between the CPU available clock speeds based on system load '],
                          'userspace' : ['User Defined', 'Lets user to manually configure clock speeds'],
                          'powersave' : ['Powersave', 'Runs the CPU at minimum clock speeds'],
                          'performance' : ['Performance','Runs the CPU at maximum clock speeds']}

        for x in self.availableGovernors:
            # Makes a RadioButton for each governor available.
            self.radioButton[x] = Plasma.RadioButton(self.applet)
            self.radioButton[x].setText(self.governorTextsDict[x][0]) # Sets the text for radioButton from governorTextsDict above
            self.radioButton[x].setToolTip(self.governorTextsDict[x][1])
            self.governorGroup.addButton(self.radioButton[x].nativeWidget()) # We need to add radioButton's native widget
            self.setGovernorBox.layout().addItem(self.radioButton[x])
            if x == self.currentGovernorStr:
                self.radioButton[x].setChecked(True) # Checks if x is current governor and should we have a tick on RadioButton

        # Add a button for applying changes
        self.applyButton = Plasma.PushButton(self.applet)
        self.applyButton.setText("Apply")
        self.applyButton.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum))
        self.layout.addItem(self.applyButton)
        QObject.connect(self.applyButton, SIGNAL("clicked()"), self.applyChanges)


def CreateApplet(parent):
    # Telling to Plasma that what class contains the applet
    return PlasmaFreq(parent)

# She came to me with a serpent's kiss
# as the Eye of the Sun rose on her lips,
# moonlight catches silver tears I cry.
# So we lay in a black embrace
# and the Seed is sown in a holy place
# and I watched and I waited for the dawn.
