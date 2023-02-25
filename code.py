# Open Source Licensing
# SPDX-FileCopyrightText: 2021 Jake Grim for Wake Hydro LLC
# SPDX-License-Identifier: MIT
#
# Wake Hydro is an open-source project and utilizes open-source resources. Parts of the
# projects listed below have been utilized in the development of Wake Hydro. It is important
# to note that I could only have brought this idea to life with the incredible resources
# provided by Adafruit Industries, LLC. They are a fantastic company; I highly recommend
# buying products from https://adafruit.com. I greatly appreciate the contribution these developers
# have made to the open-source community and acknowledge their code has been integrated into
# the Wake Hydro project. Please let me know if you notice any code I forgot to credit.

# Lastly, I hope that my talents benefit humanity.
# I pray that my heart shines goodness upon the world.

# With great love,

# Jake M. Grim

# P.S. I am well aware that I code like a caveman, and many would refer to my work
# as "spaghetti code." Coding is not my talent, but it works. Over time I plan to
# clean up the code as this is just an MVP. I am open to recommendations for improving
# the code and appreciate any support.


# External Resources / Developers / Projects / Links:

# Encoder:
# SPDX-FileCopyrightText: 2021 John Furcean
# SPDX-License-Identifier: MIT
# Link: https://docs.circuitpython.org/projects/seesaw/en/latest/examples.html

# RTC:
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Link: https://docs.circuitpython.org/projects/ds3231/en/stable/examples.html

# Scale:
# SPDX-FileCopyrightText: 2021, 2022 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT
# Link: https://github.com/CedarGroveStudios/CircuitPython_NAU7802

# Display:
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
# Link: https://github.com/adafruit/Adafruit_CircuitPython_HT16K33
# Link: https://learn.adafruit.com/adafruit-led-backpack/changing-i2c-address?view=all#circuitpython-and-python-usage-197dcbfa-4ccf-4b98-a152-3982411df681

# Sounds:
# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
# SPDX-License-Identifier: MIT
# Link: https://learn.adafruit.com/circuitpython-essentials/circuitpython-pwm

# I2C:
# SPDX-FileCopyrightText: 2017 Limor Fried for Adafruit Industries
# SPDX-License-Identifier: MIT
# Link: https://learn.adafruit.com/scanning-i2c-addresses/circuitpython

##########################################################################################################################################################
##########################################################################################################################################################


import board
import time
import busio
import supervisor
import microcontroller
import adafruit_ds3231
import pwmio
from digitalio import DigitalInOut, Direction, Pull
from cedargrove_nau7802 import NAU7802
from rainbowio import colorwheel
from adafruit_seesaw import seesaw, rotaryio, digitalio, neopixel
from adafruit_ht16k33.segments import BigSeg7x4

i2c = busio.I2C(board.SCL1, board.SDA1) #set up i2c for STEMMA connector on QT Py RP2040

#My variables
#############################################################################
sleepTime = 0
clockTimeMinutes = 0
snoozeTime = 1
setClock = 0
setAlarm = 0
setSnooze = 0
setTare = 0
setSleep = 0
alarmState = 0
setAlarmHour = False
setClockHour = False
h = 0
m = 0
colonDot = True
alarmDot = False
clockMenu = 0
clockMenuMode = 0

rainbowColor = 0

# With NAU7802 and Strain Gauge Load Cell - 4 Wires - 10Kg - 80mm long:
# 1 gram = 450 units
# 1 cup of water = 108000 untis
# 1/4 cup of water is 27,000
# 1 tablespoon of water is about 6.7k units

taredValue = 0
drinkMin = 27000 #min wight of liquid (1/4 cup of water)
drinkVariance = 5000 #Tolerance for weight of empty drink. High value  = less sensitive scale. 5k seems like a safe rang. If container is set near the edge of the scale, it is sometimes off by about 3k units
minDrinkContainerWeight = 10000 #min weight of drink container (Should be greater than drinkVariance) 10K = 22.2g
avgValue = 0

#digital outputs
piezoPin = board.A3
gnd_pin0 = DigitalInOut(board.A0)
gnd_pin0.direction = Direction.OUTPUT
gnd_pin0.value = False
gnd_pin1 = DigitalInOut(board.A1)
gnd_pin1.direction = Direction.OUTPUT
gnd_pin1.value = False
gnd_pin2 = DigitalInOut(board.A2)
gnd_pin2.direction = Direction.OUTPUT
gnd_pin2.value = False

#non-voltage memory
#0:4 is Scale Tare
#5:6 is snooze time 0-30
#7:8 is 24 hour time 0-1
#9:10 is display brightness 0-20
#11:12 Led rainbow 0-1
#13:15 LED color 1 - 256
#16:17 LED brightness 0-20


if int.from_bytes(microcontroller.nvm[7:8], "big") == 1 or int.from_bytes(microcontroller.nvm[7:8], "big") == 0:
    HourTime24 = int.from_bytes(microcontroller.nvm[7:8], "big")  #1 is 24 hour time and 0 is 12 hour time
else:
    HourTime24 = 0

if int.from_bytes(microcontroller.nvm[11:12], "big") == 1 or int.from_bytes(microcontroller.nvm[11:12], "big") == 0:
    rainbow = int.from_bytes(microcontroller.nvm[11:12], "big")  #1 is 24 hour time and 0 is 12 hour time
else:
    rainbow = 0




#############################################################################

#display
########################################################################
display = BigSeg7x4(i2c) #without ribon
#display = BigSeg7x4(board.I2C()) #with ribon

if int.from_bytes(microcontroller.nvm[9:10], "big") / 20 <= 1 and int.from_bytes(microcontroller.nvm[9:10], "big") / 20 >= 0:
    display.brightness = int.from_bytes(microcontroller.nvm[9:10], "big") / 20 #replace with nvm value
else:
    display.brightness = 0.1


display.print("LOAD")
display.blink_rate = 3
########################################################################

#rtc
########################################################################
rtc = adafruit_ds3231.DS3231(i2c)
# Lookup table for names of days (nicer printing).
days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

# pylint: disable-msg=using-constant-test
if False:  # change to True if you want to set the time!
    #                     year, mon, date, hour, min, sec, wday, yday, isdst
    t = time.struct_time((2018, 1, 31, 14, 56, 58, 0, -1, -1))
    #rtc.alarm1 = (time.struct_time((2017,1,9,12,0,0,0,0,-1)), "daily")
    # you must set year, mon, date, hour, min, sec and weekday
    # yearday is not supported, isdst can be set but we don't
    print("Setting time to:", t)  # uncomment for debugging
    rtc.datetime = t
    print()



#set up alarm
########################################################################
t = rtc.alarm1[0]
h = t.tm_hour
m = t.tm_min
alarmTimeHour = t.tm_hour
alarmTimeMin = t.tm_min
alarmTime = h*60 + m
rtc.alarm1_status = False
rtc.alarm2_status = False
########################################################################


########################################################################
#setting alarm 2 (snooze)
def set_alarm_2():
    rtc.alarm2_status = False #this turns off the alarm on rtc
    t = rtc.datetime
    h = t.tm_hour
    m = t.tm_min
    clockTimeMinutes = h*60 + m
    snoozeTime = int.from_bytes(microcontroller.nvm[5:6], "big")
    nextAlarm = clockTimeMinutes + snoozeTime

    #keep clock between 0 and 1440
    #############################################################################
    if nextAlarm >1439:
        nextAlarm = nextAlarm - 1440

    print("Now nextAlarm is: {}".format(nextAlarm))

    h = nextAlarm // 60
    m = nextAlarm % 60

    print("Setting h to:", h)
    print("Setting m to:", m)

    t = (time.struct_time((2017, 1, 9, h, m, 0, 0, 0, -1)), "daily")
    # you must set year, mon, date, hour, min, sec and weekday
    # yearday is not supported, isdst can be set but we don't
    print("Setting time to:", t)  # uncomment for debugging
    rtc.alarm2 = t
    print()
########################################################################













# pylint: enable-msg=using-constant-test
########################################################################

#set up scale
#############################################################################
# Instantiate 24-bit load sensor ADC; two channels, default gain of 128
nau7802 = NAU7802(i2c, address=0x2A, active_channels=2)

# Enable NAU7802 digital and analog power
enabled = nau7802.enable(True)
nau7802.channel = 1

def read_raw_value(samples=500):
    """Read and average consecutive raw sample values. Return average raw value."""
    sample_sum = 0
    sample_count = samples
    while sample_count > 0:
        if nau7802.available:
            sample_sum = sample_sum + nau7802.read()
            sample_count -= 1
    return int(sample_sum / samples)

#############################################################################


def read_avgValue():
    #print("alarmState == 1")
    tarScale = int.from_bytes(microcontroller.nvm[0:4], "big")
    i = 0
    sumValue = 0
    #take 10 sample average of scale
    while i < 10:
        i += 1
        taredValue = read_raw_value(10) - tarScale################################################################## needs to be a - not + ########################################################################################
        sumValue = sumValue + taredValue
        avgValue = sumValue / i
        #time.sleep(0.1) #takes 1 second to get avg scale value
    #print("channel 1 average value: %7.0f" % (avgValue))
    return int(avgValue)




#############################################################################




def set_display():
    #print("setting display")
    #This Runs the clock
    ########################################################################
    t = rtc.datetime
    #print(t)     # uncomment for debugging
    #print("The time is {}:{:02}:{:02}".format(t.tm_hour, t.tm_min, t.tm_sec))

    if HourTime24 == 0:
        if t.tm_hour>12:                #converts 24hour time to 12hour time
            hour12 = t.tm_hour - 12     #
        else:                           #
            hour12 = t.tm_hour          #
        if t.tm_hour==0:                #coverts hour 0 to 12(am)
            hour12 = 12                 #
        if t.tm_hour>11:                #controls PM dot
            hourPmDot = True               #
        else:                           #
            hourPmDot = False              #
    else:
        hour12 = t.tm_hour
        hourPmDot = False

    clocktime = ("{:2}{:02}".format(hour12, t.tm_min,))
    display.print(clocktime)
    #print("setting display pt2")
    display.colons[0]= colonDot
    display.bottom_left_dot = hourPmDot
    display.top_left_dot = alarmDot
    ########################################################################



def set_display_alarm():
    #This Runs the clock
    ########################################################################
    print("rtc     ", rtc.alarm1[0])
    t = rtc.alarm1[0]
    b = rtc.datetime
    print("t     ", b)
    print("t     ", b.tm_hour)
    # print(t)     # uncomment for debugging
    print("The alarmtime is {}:{:02}:{:02}".format(t.tm_hour, t.tm_min, t.tm_sec))
    if HourTime24 == 0:
        if t.tm_hour>12:                #converts 24hour time to 12hour time
            hour12 = t.tm_hour - 12     #
        else:                           #
            hour12 = t.tm_hour          #
        if t.tm_hour==0:                #coverts hour 0 to 12(am)
            hour12 = 12                 #
        if t.tm_hour>11:                #controls PM dot
            hourPmDot = True               #
        else:                           #
            hourPmDot = False              #
    else:
        hour12 = t.tm_hour
        hourPmDot = False
    clocktime = ("{:2}{:02}".format(hour12, t.tm_min,))
    display.print(clocktime)
    display.colons[0]= colonDot
    display.bottom_left_dot = hourPmDot
    display.top_left_dot = True
    ########################################################################




#display flash

def display_flash():
    # display.fill(1)
#     time.sleep(.5)
#     display.fill(0)
#     time.sleep(.5)
#     display.fill(1)
#     time.sleep(.5)
#     display.fill(0)
#     time.sleep(.5)
    loadSpeed = 0.07
    display.fill(0)
    time.sleep(loadSpeed)
    display.set_digit_raw(2, 0b00000001)
    time.sleep(loadSpeed)
    display.set_digit_raw(3, 0b00000001)
    time.sleep(loadSpeed)
    display.set_digit_raw(3, 0b00000011)
    time.sleep(loadSpeed)
    display.set_digit_raw(3, 0b00000111)
    time.sleep(loadSpeed)
    display.set_digit_raw(3, 0b00001111)
    time.sleep(loadSpeed)
    display.set_digit_raw(2, 0b00001001)
    time.sleep(loadSpeed)
    display.set_digit_raw(1, 0b00001000)
    time.sleep(loadSpeed)
    display.set_digit_raw(0, 0b00001000)
    time.sleep(loadSpeed)
    display.set_digit_raw(0, 0b00011000)
    time.sleep(loadSpeed)
    display.set_digit_raw(0, 0b00111000)
    time.sleep(loadSpeed)
    display.set_digit_raw(0, 0b00111001)
    time.sleep(loadSpeed)
    display.set_digit_raw(1, 0b00001001)
    time.sleep(loadSpeed)
    display.fill(0)


#setup encoder
#############################################################################
seesaw = seesaw.Seesaw(i2c, 0x36)
seesaw_product = (seesaw.get_version() >> 16) & 0xFFFF
print("Found product {}".format(seesaw_product))
if seesaw_product != 4991:
    print("Wrong firmware loaded?  Expected 4991")
seesaw.pin_mode(24, seesaw.INPUT_PULLUP)
button = digitalio.DigitalIO(seesaw, 24)
button_held = False
encoder = rotaryio.IncrementalEncoder(seesaw)
last_position = None


pixel = neopixel.NeoPixel(seesaw, 6, 1)
if int.from_bytes(microcontroller.nvm[16:17], "big") / 20 <= 1 and int.from_bytes(microcontroller.nvm[16:17], "big") / 20 >= 0:
    pixel.brightness = int.from_bytes(microcontroller.nvm[16:17], "big") / 20 #replace with nvm value
else:
    pixel.brightness = 0.1


if int.from_bytes(microcontroller.nvm[13:15], "big") <= 256 and int.from_bytes(microcontroller.nvm[13:15], "big") >= 0:
    color = int.from_bytes(microcontroller.nvm[13:15], "big")
else:
    color = 0.1

pixel.fill(colorwheel(color))


#encoder rainbow


def pixel_rainbow():
    global rainbowColor
    rainbowColor += 1
    if rainbowColor >= 256:
        rainbowColor = 0
    pixel.fill(colorwheel(rainbowColor))

#pixel = neopixel.NeoPixel(seesaw, 6, 1)
#pixel.brightness = int.from_bytes(microcontroller.nvm[16:17], "big") / 20 #replace with nvm value
#color = int.from_bytes(microcontroller.nvm[13:15], "big")
#pixel.fill(colorwheel(color))


##########################################################################################################################################################

#sounds
##########################################################################################################################################################
# Create piezo buzzer PWM output.
piezo = pwmio.PWMOut(piezoPin, duty_cycle=0, frequency=100, variable_frequency=True)

# Main loop will go through each tone in order up and down.
def beep_sound_up():
    for f in ( 523,  # C4
              554,  # D4
              587,  # E4
              622,  # F4
              659,  # G4
              698,  # A4
              740,  ): # B4
        piezo.frequency = f
        piezo.duty_cycle = 65535 // 10  # On 50%
        time.sleep(0.05)  # On for 1/4 second
        piezo.duty_cycle = 0  # Off
        #time.sleep(0.02)  # Pause between notes
    #time.sleep(0.5)

def beep_sound_down():
    for f in ( 740,  # C4
              698,  # D4
              659,  # E4
              622,  # F4
              587,  # G4
              554,  # A4
              523,  ): # B4
        piezo.frequency = f
        piezo.duty_cycle = 65535 // 10  # On 50%
        time.sleep(0.05)  # On for 1/4 second
        piezo.duty_cycle = 0  # Off
        #time.sleep(0.02)  # Pause between notes
    #time.sleep(0.5)

def alarm_sound():
    for f in ( 740,  # C4
              698,  # D4
              659,  # E4
              622,  # F4
              587,  # G4
              554,  # A4
              523,  ): # B4
        piezo.frequency = f
        piezo.duty_cycle = 65535 // 1
        time.sleep(0.05)  # On for 1/4 second
        piezo.duty_cycle = 0  # Off
        #time.sleep(0.02)  # Pause between notes
    time.sleep(0.5)
##########################################################################################################################################################
























####################################################################################################################################################################################################################################################################################################################
####################################################################################################################################################################################################################################################################################################################
while True:
    try:
        #print("running")
        a = read_avgValue()
        b = a / 100
        print(round(b))
        #print(avgValue)
        display.blink_rate = 0
        if rainbow == 1:
            pixel_rainbow()

        #print("alarm is                 ",rtc.alarm1)
        #set clock time and alarm time to minutes
        t = rtc.datetime
        clockTimeHour = t.tm_hour
        clockTimeMin = t.tm_min
        h = t.tm_hour
        m = t.tm_min
        clockTimeMinutes = h*60 + m


        #get encoder position and print clockTimeMinutes + alarm time
        #############################################################################
        position = encoder.position
        #print("Position: {}".format(position))
        #print(sleepTime)
        #print("clockTimeMinutes: {}".format(clockTimeMinutes))
        #print("alarmTime: {}".format(alarmTime))
        snoozeTime = int.from_bytes(microcontroller.nvm[5:6], "big")
        #print("snoozeTime: {}".format(snoozeTime))
        #print("Temp = {}".format(microcontroller.cpu.temperature))


        if rtc.alarm2_status:
            while not button.value:
                setSleep = True # This snoozes alarm 2. Alarm1 snoozes when the drink is empty
                print("Go Back To Bed")
                beep_sound_up()

        clockMenuItems = ["", "AL T", "CL T", "TARE", "SNO2", "24 H", " LED", "LED2" , "COLR", "FADE", "DONE"]
        #menu numbers     0    1        2        3      4        5      6       7        8       9       10

        #button is held for 2 sencods
        while not button.value and not setAlarm and not setClock and not alarmState > 1 and clockMenuMode ==0:
            if not button_held:
                sleepTime = 0
            #print(sleepTime)
            button_held = True
            #print("Button pressed")

            time.sleep(.1)
            sleepTime = sleepTime +1

            if sleepTime == 10:                         #after 1 second, go into clock menu
                clockMenu = 1
                clockMenuMode = 1
                print("Clock Menu")
                display.fill(0)
                beep_sound_up()
                display_flash()
                print(clockMenu)
                display.print(clockMenuItems[1])


        if button.value and button_held:
            print("button released")
            button_held = False
            sleepTime = 0

        while clockMenuMode == 1:
            position = encoder.position
            if position != last_position:
                print("spin")
                print(position)
                    # Change the clockMenu.
                if position > last_position:  # Advance forward through the clockMenu.
                    clockMenu += 1
                    print(clockMenu)
                    print(len(clockMenuItems))
                else:
                    clockMenu -= 1  # Advance backward through the clockMenu.
                    print(clockMenu)
                    print(len(clockMenuItems))

                if clockMenu < 1:
                    clockMenu = 1
                if clockMenu > len(clockMenuItems) - 1:
                    print("test")
                    clockMenu -= 1
            last_position = position
            display.print(clockMenuItems[clockMenu])

            if not button.value and not button_held:
                clockMenuMode = 2
                beep_sound_up()
                display_flash()


        while clockMenuMode == 2:

            while clockMenuItems[clockMenu] == "AL T":  #Update Snooze time
                print( str(clockMenuItems[clockMenu]) + " is now running")
                setAlarm = True # This runs the Set ALARM Time function
                seesaw.set_encoder_position(alarmTimeHour, encoder=0) #set encoder position to alarmTimeHour
                position = encoder.position
                setAlarmHour = True
                clockMenu = 0
                clockMenuMode = 0

                set_display_alarm()
                time.sleep(0.25)
                display[0] = " "
                display[1] = " "
                time.sleep(0.5)
                set_display_alarm()
                #time.sleep(0.5)
                #display[0] = " "
                #display[1] = " "
                #time.sleep(0.5)
                #set_display_alarm()

            while clockMenuItems[clockMenu] == "CL T": #Update Clock Time
                print( str(clockMenuItems[clockMenu]) + " is now running")
                print("Run Set Clock Time")
                setClock = True # This runs the Set Clock Time function
                seesaw.set_encoder_position(clockTimeHour, encoder=0)  #set encoder position to clockTimeMinutes
                position = encoder.position
                setClockHour = True
                clockMenu = 0
                clockMenuMode = 0

                set_display()
                time.sleep(0.25)
                display[0] = " "
                display[1] = " "
                time.sleep(0.5)
                set_display()
                #time.sleep(0.5)
                #display[0] = " "
                #display[1] = " "
                #time.sleep(0.5)
                #set_display()






            while clockMenuItems[clockMenu] == "TARE": #Tare Scale
                print( str(clockMenuItems[clockMenu]) + " is now running")
                setTare = True # This runs the Set TAR function
                clockMenu = 0
                clockMenuMode = 0

            while clockMenuItems[clockMenu] == "SNO2":  #Update Snooze time
                print( str(clockMenuItems[clockMenu]) + " is now running")
                setSnooze = True # This runs the Set SNOOZE function
                seesaw.set_encoder_position(snoozeTime, encoder=0)  #set encoder position to clockTimeMinutes
                position = encoder.position
                clockMenu = 0
                clockMenuMode = 0

            while clockMenuItems[clockMenu] == "24 H": #Switch to 24 Hour Time
                #print( str(clockMenuItems[clockMenu]) + " is now running")
                position = encoder.position
                if position != last_position:
                    print(position)
                    # ...change the brightness.
                    if position > last_position:  # Increase the brightness.
                        HourTime24 = position % 2
                    else:  # Decrease the brightness.
                       HourTime24 = position % 2
                    print(HourTime24)
                    microcontroller.nvm[7:8] = HourTime24.to_bytes(1, 'big')
                last_position = position
                if HourTime24 == 1:
                    display.print("  24")
                else:
                    display.print("  12")

                if not button.value:
                    clockMenu = 0
                    clockMenuMode = 0
                    beep_sound_down()


            while clockMenuItems[clockMenu] == " LED": #Adjust led display brightness
                #print( str(clockMenuItems[clockMenu]) + " is now running")
                display.print(" LED")
                position = encoder.position
                if position != last_position:
                    print(position)
                    # ...change the brightness.
                    if position > last_position:  # Increase the brightness.
                        display.brightness = min(1.0, display.brightness + 0.05)
                    else:  # Decrease the brightness.
                        display.brightness= max(0, display.brightness - 0.05)
                    print(display.brightness)
                    brightness20 = round(display.brightness * 20) #sets brightness20 to whole number between 0 and 20
                    microcontroller.nvm[9:10] = brightness20.to_bytes(1, 'big')
                last_position = position

                if not button.value:
                    clockMenu = 0
                    clockMenuMode = 0
                    beep_sound_down()


            while clockMenuItems[clockMenu] == "LED2": #Adjust neopixle brightness
                #print( str(clockMenuItems[clockMenu]) + " is now running")
                display.print("LED2")
                position = encoder.position
                if position != last_position:
                    print(position)
                    # ...change the brightness.
                    if position > last_position:  # Increase the brightness.
                        pixel.brightness = min(1.0, pixel.brightness + 0.05)
                    else:  # Decrease the brightness.
                        pixel.brightness = max(0, pixel.brightness - 0.05)
                    print(pixel.brightness)
                    brightness20 = round(pixel.brightness * 20) #sets brightness20 to whole number between 0 and 20
                    microcontroller.nvm[16:17] = brightness20.to_bytes(1, 'big')
                last_position = position

                if not button.value:
                    clockMenu = 0
                    clockMenuMode = 0
                    beep_sound_down()



            while clockMenuItems[clockMenu] == "COLR": #Adjust neopixle color
                #print( str(clockMenuItems[clockMenu]) + " is now running")
                display.print("COLR")
                position = encoder.position
                if position != last_position:
                    print(position)
                    # Change the LED color.
                    if position > last_position:  # Advance forward through the colorwheel.
                        color += 10
                    else:
                        color -= 10  # Advance backward through the colorwheel.
                    color = (color + 256) % 256  # wrap around to 0-256
                    pixel.fill(colorwheel(color))
                    #13:15 LED color 1 - 256
                    colorRound = round(color)
                    microcontroller.nvm[13:15] = colorRound.to_bytes(2, 'big')
                last_position = position

                if not button.value:
                    clockMenu = 0
                    clockMenuMode = 0
                    beep_sound_down()


            while clockMenuItems[clockMenu] == "FADE": #fade neopixle through color wheel
                #print( str(clockMenuItems[clockMenu]) + " is now running")
                position = encoder.position
                if position != last_position:
                    print(position)
                    # ...change the brightness.
                    if position > last_position:  # Increase the brightness.
                        rainbow = position % 2
                    else:  # Decrease the brightness.
                       rainbow = position % 2
                    print(rainbow)
                    microcontroller.nvm[11:12] = rainbow.to_bytes(1, 'big')
                last_position = position
                if rainbow == 1:
                    display.print("  ON")
                    pixel_rainbow()
                else:
                    display.print(" OFF")
                    pixel.fill(colorwheel(color))

                if not button.value:
                    clockMenu = 0
                    clockMenuMode = 0
                    beep_sound_down()


            while clockMenuItems[clockMenu] == "DONE": #End menu mode and go back to regular clock
                print( str(clockMenuItems[clockMenu]) + " is now running")
                clockMenu = 0
                clockMenuMode = 0

        #Leave Menu and go to selected funtion



    #If the encoder is not touched for X seconds or button is pressed, the following functions end
        #############################################################################
        if setClock or setAlarm or setSnooze:
            time.sleep(.1)
            sleepTime = sleepTime +1

            if not button.value and not setAlarmHour and not setClockHour or sleepTime > 100: #end setClock or setAlarm or setSnooze after 10 seconds or when the button is pressed
                sleepTime = 0
                setClock = False
                setAlarm = False
                setSnooze = False
                seesaw.set_encoder_position(0, encoder=0) #set encoder position to 0
                position = encoder.position
                beep_sound_down()
                display_flash()

        #############################################################################


        #When the encoder is rotated 360 degrees +-, it triggers set alarm time
        #############################################################################

        # if not setClock and not setAlarm and not setSnooze and clockMenuMode == 0:
    #         if abs(position) > 19:
    #             seesaw.set_encoder_position(alarmTime, encoder=0) #set encoder position to alarmTime
    #             position = encoder.position
    #             setAlarm = True

        if setAlarm and setAlarmHour:
            while not button.value:
                beep_sound_up()
                seesaw.set_encoder_position(alarmTimeMin, encoder=0) #set encoder position to alarmTimeHour
                position = encoder.position
                setAlarmHour = False

                time.sleep(0.25)
                display[2] = " "
                display[3] = " "
                time.sleep(0.5)
                set_display_alarm()
                #time.sleep(0.5)
                #display[2] = " "
                #display[3] = " "
                #time.sleep(0.5)
                #set_display_alarm()

        if setClock and setClockHour:
            while not button.value:
                beep_sound_up()
                seesaw.set_encoder_position(clockTimeMin, encoder=0) #set encoder position to alarmTimeHour
                position = encoder.position
                setClockHour = False


                time.sleep(0.25)
                display[2] = " "
                display[3] = " "
                time.sleep(0.5)
                set_display()
                #time.sleep(0.5)
                #display[2] = " "
                #display[3] = " "
                #time.sleep(0.5)
                #set_display()


        #when the encoder moves (sleepTime is reset to keep functions running)
        #############################################################################
        if position != last_position:
            sleepTime = 0
            last_position = position
            print("Position: {}".format(position))







            #update clock time
            #############################################################################
            if setClock:
                if setClockHour:
                    position = encoder.position
                    clockTimeHour = position
                    #keep alarm time positive and under 1440
                    #############################################################################
                    if clockTimeHour < 0:
                        clockTimeHour = 23
                        seesaw.set_encoder_position(clockTimeHour, encoder=0) #set encoder position to clockTimeHour
                        position = encoder.position
                    if clockTimeHour >23:
                        clockTimeHour = 0
                        seesaw.set_encoder_position(clockTimeHour, encoder=0) #set encoder position to clockTimeHour
                        position = encoder.position
                    print("Now clockTimeHour is: {}".format(clockTimeHour))




                if not setClockHour:
                    position = encoder.position
                    clockTimeMin = position
                    #keep alarm time positive and under 1440
                    #############################################################################
                    if clockTimeMin < 0:
                        clockTimeMin = 59
                        seesaw.set_encoder_position(clockTimeMin, encoder=0) #set encoder position to clockTimeMin
                        position = encoder.position
                    if clockTimeMin >59:
                        clockTimeMin = 0
                        seesaw.set_encoder_position(clockTimeMin, encoder=0) #set encoder position to clockTimeMin
                        position = encoder.position
                    print("Now clockTimeMin is: {}".format(clockTimeMin))

                print("Setting h to:", clockTimeHour)
                print("Setting m to:", clockTimeMin)
                t = time.struct_time((2018, 1, 31, clockTimeHour, clockTimeMin, 0, 0, -1, -1))
                # you must set year, mon, date, hour, min, sec and weekday
                # yearday is not supported, isdst can be set but we don't
                print("Setting time to:", t)  # uncomment for debugging
                rtc.datetime = t
                print()


            #update alarm time
            #############################################################################
            if setAlarm:
                if setAlarmHour:
                    position = encoder.position
                    alarmTimeHour = position
                    #keep alarm time positive and under 1440
                    #############################################################################
                    if alarmTimeHour < 0:
                        alarmTimeHour = 23
                        seesaw.set_encoder_position(alarmTimeHour, encoder=0) #set encoder position to alarmTimeHour
                        position = encoder.position
                    if alarmTimeHour >23:
                        alarmTimeHour = 0
                        seesaw.set_encoder_position(alarmTimeHour, encoder=0) #set encoder position to alarmTimeHour
                        position = encoder.position
                    print("Now alarmTimeHour is: {}".format(alarmTimeHour))




                if not setAlarmHour:
                    position = encoder.position
                    alarmTimeMin = position
                    #keep alarm time positive and under 1440
                    #############################################################################
                    if alarmTimeMin < 0:
                        alarmTimeMin = 59
                        seesaw.set_encoder_position(alarmTimeMin, encoder=0) #set encoder position to alarmTimeMin
                        position = encoder.position
                    if alarmTimeMin >59:
                        alarmTimeMin = 0
                        seesaw.set_encoder_position(alarmTimeMin, encoder=0) #set encoder position to alarmTimeMin
                        position = encoder.position
                    print("Now alarmTimeMin is: {}".format(alarmTimeMin))


                h = alarmTime // 60
                m = alarmTime % 60

                print("Setting h to:", alarmTimeHour)
                print("Setting m to:", alarmTimeMin)
                t = (time.struct_time((2017, 1, 9, alarmTimeHour, alarmTimeMin, 0, 0, 0, -1)), "daily")
                # you must set year, mon, date, hour, min, sec and weekday
                # yearday is not supported, isdst can be set but we don't
                print("                                 Setting alarm time to:", t)  # uncomment for debugging
                rtc.alarm1 = t
                print("lolololo" , rtc.alarm1 )
                print()
                set_display_alarm()



            #update snooze time
            #############################################################################
            if setSnooze:
                snoozeTime = position
                #keep snooze time 1-30 minutes
                #############################################################################
                if snoozeTime < 1:
                    snoozeTime = 1
                    seesaw.set_encoder_position(snoozeTime, encoder=0) #set encoder position to alarmTime
                    position = encoder.position
                if snoozeTime >30:
                    snoozeTime = 30
                    seesaw.set_encoder_position(snoozeTime, encoder=0) #set encoder position to alarmTime
                    position = encoder.position

                #store snooze time in a way that losing power will not lose snoozeTime value
                #############################################################################
                microcontroller.nvm[5:6] = snoozeTime.to_bytes(1, 'big')


                display.print("{:04}".format(snoozeTime))
                #############################################################################


                print("Now setSnooze is: {}".format(snoozeTime))



        #run Tare function
        #############################################################################
        if setTare:
            display.print("calc")
            time.sleep(1)
            setTareScale = abs(read_raw_value(500))
            microcontroller.nvm[0:4] = setTareScale.to_bytes(4, 'big')
            display_flash()
            beep_sound_down()
            setTare = False

        #This Runs the clock display
        ########################################################################
        if setAlarm == False and setSnooze == False:
            #print("########################################################################")
            set_display()
            #print("done setting display")
        ########################################################################




        #read scale
        #############################################################################
        #############################################################################
        if alarmState == 0:
            #print("alarmState == 0")
            tarScale = int.from_bytes(microcontroller.nvm[0:4], "big")
            taredValue = read_raw_value(10) - tarScale################################################################## needs to be a - not + ########################################################################################


           # print("channel 1 raw value: %7.0f" % (read_raw_value(10)))
           # print("channel 1 tar value: %7.0f" % (taredValue))
            alarmDot = False
            rtc.alarm1_status = False #this turns off the alarm on rtc
            rtc.alarm2_status = False #this turns off the alarm on rtc





        if alarmState > 0:
            #print("read avg")
            avgValue = read_avgValue()



        #############################################################################
        #############################################################################

        # alarmState:
        # 0 = waiting for full drink
        # 1 = full drink is on the scale
        # 2 = drink has been drunk, now in snooze mode

        if taredValue > drinkMin and alarmState == 0:
            #if the drink weighs enough the alarm is set
            alarmState = 1
            alarmDot = True
            beep_sound_up()



            #display_flash()
            display.fill(0)
            time.sleep(0.5)
            display.print("  al")
            time.sleep(1)
            display.print(" set")
            time.sleep(1)

            set_display_alarm()
            time.sleep(1)
            display.fill(0)

            #time.sleep(0.5)
            #set_display_alarm()
            #time.sleep(0.5)
            #display.fill(0)
            #time.sleep(0.5)
            #set_display_alarm()
            #time.sleep(0.5)
            #display.fill(0)
            #time.sleep(0.5)

            time.sleep(0.5)
            display.print("good")
            time.sleep(1)
            display.print("nite")
            time.sleep(1)



            set_display()

            avgValue = read_avgValue()
            print("if the drink weighs enough the alarm is set")
        #print("avg value")
        #print(avgValue)
        if avgValue < drinkVariance and alarmState == 1 and rtc.alarm1_status == False:
            print("a")
            #if the drink is removed before the alarm goes off, the alarm is shut off
            alarmState = 0
            beep_sound_down()
            print("channel 1 average value: %7.0f" % (avgValue))
            print("  #if the drink is removed before the alarm goes off, the alarm is shut off")


        if avgValue < drinkVariance and avgValue > -drinkVariance and alarmState == 1 and rtc.alarm1_status == True:
            #if the drink is on the scale and empty while the alarm is going off for the first time (alarmState == 2) go to snooze
            print("b")
            alarmState = 2
            rtc.alarm1_status = False #this turns off the alarm on rtc
            # fancy function that takes current time, adds snoozeTime and them sets tc.alarm2 to that time
            set_alarm_2()
            print("if the drink is on the scale and empty while the alarm is going off for the first time (alarmState == 1) go to snooze  ")
            time.sleep(3)



        if avgValue < -minDrinkContainerWeight and alarmState > 1:
            #if the drink is removed any time after the first alarm, the alarm is shut off
            print("c")
            rtc.alarm2_status = False #this turns off the alarm on rtc
            alarmState = 0
            beep_sound_down()

            print(" #if the drink is removed any time after the first alarm, the alarm is shut off ")


         #run sleep function aka snoozing
        #############################################################################
        if setSleep:
            setSleep = False
            if rtc.alarm2_status == True:
                rtc.alarm2_status = False #this turns off the alarm on rtc

                #fancy function that takes current time, adds snoozeTime and them sets rtc.alarm2 to that time
                set_alarm_2()
                print(" #run sleep function aka snoozing ")

        #This is alarm 1
        ########################################################################
        if alarmState == 1:
            print("d")
            if rtc.alarm1_status:
                print("wake up! 1")
                alarm_sound()
                #################################################################################### there will be a pause in sound for about 1 second
                #################################################################################### consider adding piezzo to high durning that time
                #rtc.alarm1_status = False #this turns off the alarm on rtc

                print(" #This is alarm 1 ")
        ########################################################################

            #This is alarm 2
        ########################################################################
        if alarmState == 2:
            if rtc.alarm2_status:
                print("wake up! 1")
                alarm_sound()
                #rtc.alarm1_status = False #this turns off the alarm on rtc

                print(" #This is alarm 2 ")
                #################################################################################### there will be a pause in sound for about 1 second
                #################################################################################### consider adding piezzo to high durning that time
        ########################################################################
        #print("alarm state== %7.0f" % (alarmState))
        #print("nodrink== %7.0f" % (taredValue))
        #print("rtc.alarm2_status== %7.0f" % (rtc.alarm2_status))
        #print("                                      rtc.alarm1_status== %7.0f" % (rtc.alarm1_status))
        #time
    except Exception as e:
        supervisor.reload()



# Write your code here :-)
