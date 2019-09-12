#Amir Alaj & Kristi Luu; 
#This program uses a web API from 'https://www.nps.gov/subjects/developer/index.htm' and creates a GUI that
#allows the user to look up what national parks are in specific states and allows them to save the description
#of selected parks into a txt file, that txt file is saved to a directory of the users choice.
import urllib.request as ur
import requests
import json
import tkinter as tk
import tkinter.messagebox as tkmb
import time
import threading
import queue
import tkinter.filedialog
import os

class MainWin(tk.Tk):
    def __init__(self):
        '''
        The constructor creates the listbox of all 50 states, and the 'ok' button has
        the callback function which calls check selections
        '''
        super().__init__()
        with open('states_hash.json', 'r') as fh:
            self.stateDict = json.load(fh)
        self.masterDict = {}
        self.title("US National Parks")
        self.stateKeys = [key for key in xself.stateDict]
        self.frame = tk.Frame(self)
        self.frame.grid()
        boxTitle = tk.Label(self.frame, text = "Choose up to 3 States").grid(row = 0)
        S = tk.Scrollbar(self.frame)
        self.LB = tk.Listbox(self.frame, selectmode = "multiple", width = 35, height = 10, yscrollcommand = S.set)
        self.LB.grid(row = 1, padx=20)
        S.grid(row = 1, column = 1, rowspan = 10,  sticky = 'ns')
        S.config(command=self.LB.yview)
        self.LB.insert(tk.END, *self.stateDict.values())
        tk.Button(self.frame, text = "Ok", command = self.checkSelection).grid(row = 12, padx=20)
        self.resultLabel = tk.Label(self.frame, text = "")
        self.resultLabel.grid(row = 13, column = 0)
        self.labelString = "Result: "
        
    def checkSelection(self):
        '''
        Checks the amount of selections that the user has chosen, if they have the appropriate amount
        then the selections are processed through threads, all data created from the processed threads 
        are then used to print to the listbox and call the DisplayWindow
        '''
        selections = self.LB.curselection()
        if len(selections) < 1 or len(selections) > 3:
            tkmb.showerror("Error", "The you chose " + str(len(selections)) + " states, you can only choose between 1 or 3 states")
        else:
            self.q = queue.Queue()
            self.resultLabel['text'] += self.labelString
            for i in range(len(selections)):
                t = threading.Thread(target = self.getData, args = (selections[i], ))
                t.start()
            for i in range(len(selections)):
                self.resultLabel['text'] += self.q.get() 
                #without this self.q.get(), there's no pop so you get no data
                self.update_idletasks() #no update = GUI will wait until everyone's finished and when display data is updated, it'll update
                # you want it to create a new thread to update the window, and anything new will show up later
                # ask GUI to update itself, never update it yourself (as user)
            display = DisplayWindow(self, self.masterDict, self.stateDict)
            # self.wait_window(display)
            
    def getData(self, index):
        '''
        The function the threads are passed into where the web API is opened and the contents are saved 
        into a large dictionary, also the information to be displayed to the list box is put into a queue
        '''
        page = requests.get("https://developer.nps.gov/api/v1/parks?stateCode="+str(self.stateKeys[index])+"&api_key=CvW6ufDA3jkAx1LkbuZ42GFpj1DYkS8cj6Gr0KZR")
        infoDict = page.json()
        self.masterDict[self.stateKeys[index]] = infoDict
        self.q.put(str(self.stateDict[self.stateKeys[index]]) + ": " + str(infoDict['total']) + " ")
        
class DisplayWindow(tk.Toplevel):
    def __init__(self, master, masterDict, stateDict):
        '''
        In this constructor another list box is made with each park from the previously 
        selected states, the user is to select at least one park from the listbox. The 'ok'
        button contains the callback function which calls the saveDescription function.
        '''
        super().__init__(master)
        self.master = master
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.masterDict = masterDict
        self.stateDict = stateDict
        self.frame = tk.Frame(self)
        self.frame.grid()
        boxTitle = tk.Label(self.frame, text = "Select parks to save to file").grid(row = 0)
        S = tk.Scrollbar(self.frame)
        self.LB = tk.Listbox(self.frame, selectmode = "multiple", width = 75, height = 10, yscrollcommand = S.set)        
        self.LB.grid(row = 1)
        S.grid(row = 1, column = 1, rowspan = 10,  sticky = 'ns')
        S.config(command=self.LB.yview)   
        for stateCode in self.masterDict:
            for i in range(len(self.masterDict[stateCode]['data'])):
                self.LB.insert(tk.END, str(self.stateDict[stateCode] + ": " + self.masterDict[stateCode]['data'][i]['fullName']))
        tk.Button(self.frame, text = "Ok", command = self.saveDescription).grid(row = 12, padx=20)
        self.grab_set()
        self.focus_set()
        
    def _close(self):
        '''
        When the textbox is done or force quit the DisplayWindow is 
        destroyed and the label from selections is cleared.
        Clears dictionary so new values aren't appended.
        '''  
        self.master.masterDict = {}
        self.master.resultLabel['text'] = ""
        self.destroy()
                
    def saveDescription(self):
        '''
        Checks to see if the user has chosen at least one park, if so the data is gathered from
        the masterDict dictionary and the descriptions of the selected park are ready to be
        written to a txt file. The program asks the user to select a directory of their choice.
        '''
        selections = self.LB.curselection()
        if len(selections) == 0:
            tkmb.showerror("Invalid, must choose to save at least one description")
        else:
            parkDescriptions = []   
            for index in selections:
                total = 0
                for stateKey in self.masterDict:
                    total += (int(self.masterDict[stateKey]['total']) )
                    if index <= (total - 1):
                        location = index - (total - int(self.masterDict[stateKey]['total']))
                        parkDescriptions.append(self.masterDict[stateKey]['data'][location]['fullName'] + ", " + self.stateDict[stateKey] + '\n'
                                                + self.masterDict[stateKey]['data'][location]['description'] + '\n')
                        break
            directory = tk.filedialog.askdirectory(initialdir = os.getcwd())
            os.chdir(directory)
            if os.path.isfile("parks.txt"):
                tkmb.showwarning("Warning", "This file already exists, its contents will be overwritten")
            with open("parks.txt", 'w') as outFile:
                for description in parkDescriptions:
                    outFile.write(description)
                    outFile.write('\n')
            self._close()
        
app = MainWin()
app.mainloop()
