from copy import deepcopy
from librosa import load as librosa_load
from math import ceil
from mingus.core import keys as minguskeys
from mingus.core import notes as mingusnotes
from moviepy.editor import *
from operator import itemgetter
from os import getcwd, listdir, remove
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
from random import randint, shuffle
from scipy.io import wavfile
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from shutil import copy
from time import sleep, time
from webdriver_manager.chrome import ChromeDriverManager
import dawdreamer as daw
import py_midicsv as pm
import traceback
import undetected_chromedriver as uc

class MeditationGenerator:

    def __init__(self, BPM, TOTAL_BARS, SAMPLE_RATE=44100, BUFFER_SIZE=512):
        
        self.SAMPLE_RATE = SAMPLE_RATE
        self.BUFFER_SIZE = BUFFER_SIZE
        self.ENGINE = daw.RenderEngine(SAMPLE_RATE, BUFFER_SIZE)

        self.DIRECTORY = getcwd()
        self.CONJOINER = '\\'
        self.CHORD_PROGRESSIONS_PATH = self.DIRECTORY+self.CONJOINER+'Chord Progressions\\'
        self.WORKSPACE_PATH = self.DIRECTORY+self.CONJOINER+'Workspace\\'
        self.BPM = BPM
        self.TEMPO = int(60000000/BPM)
        self.TOTAL_BARS = TOTAL_BARS
        self.LENGTH = 0
        self.CONTENT = []
        self.PRE_CONTENT = []
        
        self.VITAL_PLUGIN = self.DIRECTORY+self.CONJOINER+'Plugins'+self.CONJOINER+'Vital'+self.CONJOINER+'Vital.dll'
        self.VITAL_PLUGIN_STATES = self.DIRECTORY+self.CONJOINER+'Plugins'+self.CONJOINER+'Vital'+self.CONJOINER+'States'+self.CONJOINER
        
        self.PROFILE_PATH = self.DIRECTORY+self.CONJOINER+'Chrome'
        self.AMBIENCE_FOLDER = self.DIRECTORY+self.CONJOINER+'Sound FX'+self.CONJOINER+'Ambience'+self.CONJOINER
        self.SHORT_FX_FOLDER = self.DIRECTORY+self.CONJOINER+'Sound FX'+self.CONJOINER+'Short FX'+self.CONJOINER
        self.FINAL_FILE = self.WORKSPACE_PATH+'finalWav.wav'

        options = webdriver.ChromeOptions()
        options.add_argument(r"--user-data-dir="+self.PROFILE_PATH)
        options.add_argument(r'--profile-directory=Profile 1')
        self.driver = uc.Chrome(ChromeDriverManager().install(), options=options)
        prefs = {
            "behavior": "allow",
            "downloadPath": self.WORKSPACE_PATH
        }
        self.driver.execute_cdp_cmd("Page.setDownloadBehavior", prefs)
        
        self.driver.get('http://google.com')
        sleep(3)
        self.driver.execute_script('''window.open("","_blank");''')
        sleep(3)
        self.window_after = self.driver.window_handles[1]
        self.driver.switch_to.window(self.window_after)
        sleep(3)
        self.driver.get('http://bing.com')
        self.window_before = self.driver.window_handles[0]
        self.driver.switch_to.window(self.window_before)
        self.action = ActionChains(self.driver)

    def convertAudioFile(self, file_path, duration=None):

        sig, rate = librosa_load(file_path, duration=duration, mono=False, sr=self.SAMPLE_RATE)
        assert(rate == self.SAMPLE_RATE)
        return sig
    
    def chooseRandomFile(self, filePath):
        
        listOfFiles = listdir(filePath)
        file = filePath+self.CONJOINER+listOfFiles[randint(0,len(listOfFiles)-1)]
        return file
    
    def onLength(self, number):
        return int(number*(10**self.LENGTH))

    def midiToContent(self, midiFile):
        
        textfile = self.WORKSPACE_PATH+'temporary.txt'
        notEightBars = False

        with open(textfile, "w") as f:
            f.writelines(pm.midi_to_csv(midiFile))
        textFileLines = open(textfile).readlines()
        remove(textfile)
    
        preContent = []
        postContent = []
        content = []
        counter = 0

        while(counter < len(textFileLines)):
            temporary = (textFileLines[counter].strip()).split(', ')

            if temporary[2] != 'Note_on_c':
                textFileLines[counter] = temporary
                preContent.append(textFileLines[counter])
            else:
                break
        
            counter+=1
        
        lengthChecked = False
        while(counter < len(textFileLines)):
            
            textFileLines[counter] = (textFileLines[counter].strip()).split(', ')

            if textFileLines[counter][2] == 'Note_off_c' and lengthChecked == False:
                self.LENGTH = len(textFileLines[counter][1])
                lengthChecked = True

            if 'Tempo' in textFileLines[counter]:
                textFileLines[counter][3] = self.TEMPO

            if 'Note_' in textFileLines[counter][2]:
                content.append(textFileLines[counter])

            if 'End_track' in textFileLines[counter]:
                
                if int(textFileLines[counter][1]) != self.onLength(3.0720):
                    notEightBars = True

                postContent.append(textFileLines[counter])
                postContent.append((textFileLines[counter+1].strip()).split(', '))
                break
                
            counter+=1

        return preContent, content, postContent, notEightBars

    def contentToMidi(self, content, midiFile, filename='temporary', length=6.1440):

        completeContent = deepcopy(self.PRE_CONTENT)
        completeContent.extend(content)
        completeContent.extend(self.makePostContent(self.onLength(length)))

        tempText = self.WORKSPACE_PATH+filename+'.txt'
 
        with open(tempText, "w") as f:
            
            for line in range(len(completeContent)):

                if line == (len(completeContent)-2):
                    completeContent[line][1] = self.onLength(length)
                
                lineString = ''.join(str(x)+', ' for x in completeContent[line])
                lineString = lineString[:lineString.rfind(',')]

                if 'End_of_file' not in completeContent[line]:    
                    f.write(lineString+'\n')
                else:
                    f.write(lineString)
        
        midi_object = pm.csv_to_midi(tempText)
        open(midiFile, 'w').close()
        with open(midiFile, "wb") as output_file:
            midi_writer = pm.FileWriter(output_file)
            midi_writer.write(midi_object)
    
        remove(tempText)
        return midiFile

    def makePostContent(self, length):
        return [['2', str(length), 'End_track'], ['0', '0', 'End_of_file']]

    def setGlobalVariables(self, chordMIDI):

        preContent, content, postContent, notEightBars = self.midiToContent(chordMIDI)
        
        if notEightBars == True:
            fourBarContent = content
            entered = False
            fourBarContent.append(['empty', 'empty'])
            for line in range(len(fourBarContent)):
                if fourBarContent[line][1] == str(self.onLength(1.5360)) and fourBarContent[line][2] == 'Note_off_c':
                    entered = True
                    continue
                if entered == True:
                    fourBarContent = fourBarContent[:line]
                    break
        
            extendedfourBarContent = deepcopy(fourBarContent)
            for line in range(len(extendedfourBarContent)):
                extendedfourBarContent[line][1] = str(int(extendedfourBarContent[line][1]) + self.onLength(1.5360))
            fourBarContent.extend(extendedfourBarContent)
            content = fourBarContent
        
        for line in content:
            line[1] = str(int(line[1])*2)
        
        self.CONTENT = deepcopy(content)
        self.PRE_CONTENT = deepcopy(preContent)

        self.contentToMidi(content, chordMIDI, 'chord')

    def addSilenceMIDI(self, name, silenceBars=2):

        silenceContent = deepcopy(self.CONTENT)

        for line in silenceContent:
            line[5] = str(randint(70, 80))
            if line[2] == 'Note_off_c':
                if silenceBars==3:
                    line[1] = str(int(line[1])-int((self.onLength(0.7680)*3)/4))
                elif silenceBars==2:
                    line[1] = str(int(line[1])-int(self.onLength(0.7680)/2))
                elif silenceBars==1:
                    line[1] = str(int(line[1])-int((self.onLength(0.7680)*1)/4))
        
        self.contentToMidi(silenceContent, self.WORKSPACE_PATH+name+'.mid', 'silence')

        return self.WORKSPACE_PATH+name+'.mid'
    
    def strumMIDI(self, name, strumType='exponential', strumStrength=2, reverse=True, angle=2):
        
        strumContent = deepcopy(self.CONTENT)
        streak = 0

        for line in range(len(strumContent)):
            if strumContent[line][2] == 'Note_on_c':
                streak+=1
            else:
                if streak > 0:
                    temporary = []
                    for counter in range(streak):
                        temporary.append(strumContent[line-(counter+1)])
                    temporary = sorted(temporary, key=itemgetter(4))
                    if reverse == True:
                        temporary.reverse()

                    for counter in range(streak):
                        strumContent[line-(counter+1)] = temporary[counter]

                    if strumType=='linear':
                        strengthValue = int(self.onLength(1.5360/(strumStrength*2)))
                    else:
                        strengthValue = int(self.onLength(1.5360/(strumStrength)))
                    timeIncrement = 0
                    timeIncrementAdd = strengthValue*(angle**(-streak))
                    velocity = 0
                    velocityAdd = int((70-50)/streak)
                    constant = streak

                    while(streak != 0): 
                        strumContent[line-(streak)][1] = str(int(strumContent[line-(streak)][1])+timeIncrement)
                        strumContent[line-(streak)][5] = str(70-velocity)
                        if strumType == 'exponential':
                            timeIncrementAdd*=angle
                            timeIncrement = int(timeIncrementAdd)
                        elif strumType == 'linear':
                            timeIncrement+=int(strengthValue/constant)
                        velocity+=velocityAdd
                        streak-=1
        
        self.contentToMidi(strumContent, self.WORKSPACE_PATH+name+'.mid', 'strum')

        return self.WORKSPACE_PATH+name+'.mid'

    def combineMIDI(self, midiFiles, name, totalLength):

        shuffle(midiFiles)
        length = 0
        allContents = []
        for midiFile in midiFiles:
            returnValues = self.midiToContent(midiFile)
            for line in returnValues[1]:
                line[1] = str(int(line[1])+length)
            length = length + self.onLength(totalLength/len(midiFiles))
            allContents.extend(returnValues[1])
            
        filename = self.WORKSPACE_PATH+name+'.mid' 
        self.contentToMidi(allContents, filename, name, totalLength)

        return filename
    
    def makeMelody(self, foundationMIDI, chordMIDI, howOftenMelodicNotePlaysInBars, totalLength=98.3040): #i'm aware it's a horrific variable name but idk how else to put it without making things confusing

        key = chordMIDI[chordMIDI.rfind(self.CONJOINER)+1:]
        key = key[:key.rfind(' ')].strip()
        if key=='A#':
            key="Bb"
        elif key=="B#":
            key='C'
        elif key=="b#":
            key='c'
        elif key=="D#":
            key='Eb'
        elif key=="E#":
            key='F'
        elif key=="e#":
            key='f'
        elif key=="G#":
            key='Ab'
        elif key=="cb":
            key='b'
        elif key=="db":
            key='c#'
        elif key=="Fb":
            key='E'
        elif key=="fb":
            key='e'
        elif key=="gb":
            key='f#'
        notes = minguskeys.get_notes(key)
        notes = deepcopy(notes)

        if key.isupper():
            del notes[3]
            del notes[5]
        else:
            del notes[1]
            del notes[4]

        returnValues = self.midiToContent(foundationMIDI)
        content = returnValues[1]
        
        segments = [0]
        oneBar = self.onLength(0.3840)
        constantOcc = howOftenMelodicNotePlaysInBars

        while(len(segments) <= (self.onLength(totalLength)/(oneBar*constantOcc))):
            segments.append(oneBar*howOftenMelodicNotePlaysInBars)
            howOftenMelodicNotePlaysInBars+=constantOcc
        
        desiredStamp = []
        for melodyTime in range(1, len(segments)):
            
            start = int(((segments[melodyTime]-segments[melodyTime-1])*randint(1, 31))/32)
            
            x = segments[melodyTime-1]+start
            y = int(x+(segments[melodyTime]-x)+self.onLength(0.240))

            desiredStamp.append([x, y])
        
        for stampLine in desiredStamp:

            noteStartTime = stampLine[0]
            noteEndTime = stampLine[1]

            note = notes[randint(0, len(notes)-1)]
            note = str(mingusnotes.note_to_int(note)+60)
            velocity = str(randint(60, 70))

            noteStart = ['2', str(noteStartTime), 'Note_on_c', '0', note, velocity]
            noteEnd = ['2', str(noteEndTime), 'Note_off_c', '0', note, velocity]

            for contentLine in range(len(content)):
                if int(content[contentLine][1]) > noteStartTime:
                    content.insert(contentLine, noteStart)
                    break
                    
            for contentLine in range(len(content)):
                if int(content[contentLine][1]) >= noteEndTime:
                    content.insert(contentLine, noteEnd)
                    break

        filename = self.WORKSPACE_PATH+'with_melody.mid'
        return self.contentToMidi(content, filename, length=totalLength)

    def makeTrack(self, midi):

        self.ENGINE.set_bpm(float(self.BPM))
        serenity = self.ENGINE.make_plugin_processor("serenity", self.VITAL_PLUGIN)
        serenity.load_state(self.chooseRandomFile(self.VITAL_PLUGIN_STATES))
        serenity.load_midi(midi, beats=True)

        graph = [
            (serenity, [])
        ]
        
        self.ENGINE.load_graph(graph)
        self.ENGINE.render(1024, beats=True)
        wavfile.write(self.FINAL_FILE, self.SAMPLE_RATE, (self.ENGINE.get_audio()).transpose())

        return self.FINAL_FILE

    def presetToState(self):

        vital = self.ENGINE.make_plugin_processor("plugin", self.VITAL_PLUGIN)
        for file in listdir(self.VITAL_PLUGIN_STATES):
            vital.open_editor()
            vital.save_state(self.VITAL_PLUGIN_STATES+str(time()))
        for file in listdir(self.VITAL_PLUGIN_STATES):
            if '.vital' in file:
                remove(self.VITAL_PLUGIN_STATES+file)
    
    def addSoundFX(self, baseFile):

        mainSegment = AudioSegment.from_file(baseFile)
        mainSegment = mainSegment + 2
        mainSegment.export(baseFile, format="wav")
        return baseFile
    
    def cutSilence(self, file):
        
        trim_leading_silence: AudioSegment = lambda x: x[detect_leading_silence(x) :]
        trim_trailing_silence: AudioSegment = lambda x: trim_leading_silence(x.reverse()).reverse()
        strip_silence: AudioSegment = lambda x: trim_trailing_silence(trim_leading_silence(x))
        unstrippedAudioSegment = AudioSegment.from_file(file)
        audioSegment = strip_silence(unstrippedAudioSegment)
        audioSegment.export(file)
    
    def specificFile(self, file):
        x = ''
        while file not in x:
            x = self.chooseRandomFile(self.CHORD_PROGRESSIONS_PATH)
        return x

    def makeVideo(self, audioFile):
        
        try:
            remove(self.WORKSPACE_PATH+'finalVideo.mp4')
        except FileNotFoundError:
            pass
        usedStockVideos = open(self.DIRECTORY+self.CONJOINER+'usedStock.txt', 'r').readlines()

        for line in range(len(usedStockVideos)):
            usedStockVideos[line] = usedStockVideos[line].strip()

        self.driver.get('https://www.pexels.com/search/videos/nature/?orientation=landscape&size=large')
        leave = False
        while(leave == False):
            elements = WebDriverWait(self.driver, 20).until(EC.presence_of_all_elements_located((By.XPATH, '//a[@title="Download"]')))
            counter = 0
            while(counter < len(elements) and leave == False):
                link = elements[counter].get_attribute('href')
                if link not in usedStockVideos:
                    self.driver.get(link)
                    open(self.DIRECTORY+self.CONJOINER+'usedStock.txt', 'a').write(link+'\n')
                    leave = True
                counter+=1
            self.action.send_keys(Keys.CONTROL, Keys.END).perform()
            self.action.send_keys(Keys.PAGE_UP).perform()
            sleep(1)
        
        noCrDownload = 0
        while(1):
            constant = noCrDownload
            files = listdir(self.WORKSPACE_PATH)
            for file in files:
                if '.crdownload' in file:
                    constant=+1
            if constant == noCrDownload:
                break
            else:
                sleep(5)
            
        for file in listdir(self.WORKSPACE_PATH):
            if '.mp4' in file:
                if file != 'finalVideo.mp4':
                    chosenFile = file
                    
        videoClip = VideoFileClip(self.WORKSPACE_PATH+chosenFile)
        audioClip = AudioFileClip(audioFile)
        amountOfClips = ceil(audioClip.duration/videoClip.duration)
        allClips = []
        while(amountOfClips != 0):
            allClips.append(videoClip)
            amountOfClips-=1
        finalClip = concatenate_videoclips(allClips)
        finalClip = finalClip.subclip(0, audioClip.duration)
        finalClip = finalClip.with_audio(audioClip)
        finalClip.write_videofile(self.WORKSPACE_PATH+'finalVideo.mp4', threads=12)
        videoClip.close()
        audioClip.close()
        finalClip.close()

        try:
            remove(self.WORKSPACE_PATH+chosenFile)
        except:
            print(traceback.format_exc())
        
        return self.WORKSPACE_PATH+'finalVideo.mp4'
    
    def randomSleep(self):
        sleep(randint(2,5))