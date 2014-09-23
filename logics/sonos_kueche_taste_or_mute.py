from time import sleep

#trigger current_state for this sonos speaker to get the latest play-state
#this is necessary to prevent a wrong button state. This happens, if the button was pressed too frequently.
sleep(0.2)

if sh.Kueche.mute:
    sh.Kueche.mute(False)
else:
    sh.Kueche.mute(True)
