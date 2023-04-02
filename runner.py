from MeditationGenerator import MeditationGenerator
from random import randint
from shutil import copy

#set instance
goodBPMs = [20, 24, 30, 32]
runner = MeditationGenerator(BPM=goodBPMs[randint(0, len(goodBPMs)-1)], TOTAL_BARS=256)

#set major variables
chosenChordMIDI = runner.chooseRandomFile(runner.CHORD_PROGRESSIONS_PATH)
newChordMIDI = runner.WORKSPACE_PATH+'chord.mid'
copy(chosenChordMIDI, newChordMIDI)
runner.setGlobalVariables(newChordMIDI)

#make stems
chordMIDISilence1 = runner.addSilenceMIDI('silence1', 2)
chordMIDISilence2 = runner.addSilenceMIDI('silence2', 1)
chordMIDIStrummed1 = runner.strumMIDI('strum1', 'exponential', 2, True, randint(2,4))
chordMIDIStrummed2 = runner.strumMIDI('strum2', 'linear', 1, True, randint(2,4))

#combine stems
foundationMIDI = runner.combineMIDI([chordMIDISilence1, chordMIDISilence2, chordMIDIStrummed1, chordMIDIStrummed2], 'foundation', 24.5760)
foundationMIDI = runner.combineMIDI([foundationMIDI, foundationMIDI, foundationMIDI, foundationMIDI], 'elongated_foundation', 98.3040)
finalMIDI = runner.makeMelody(foundationMIDI, chosenChordMIDI, randint(1,2), 98.3040)

#finalize and master audio
finalWav = runner.makeTrack(finalMIDI)
finalWav = runner.addSoundFX(finalWav)

#make video
runner.driver.switch_to.window(runner.window_before)
finalVideo = runner.makeVideo(finalWav)