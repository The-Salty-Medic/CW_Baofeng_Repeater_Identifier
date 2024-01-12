# Written and envisioned by Aaron Hope, 360-460-1874, hope.aaron.c@gmail.com, WRXJ407
# Pico Clone :  VCC-GND YD-RP2040
# Language :  CircuitPython via Thonny

import board, digitalio, analogio, time, neopixel_write, pwmio, busio, adafruit_ssd1306, displayio

print("\nThe model of this board is :  " + board.board_id)           

# begin constant parameters
CW_Word_Per_Minute = 20 # sets pace for all subsequent tone output
paris_to_dit = 50
minute_to_second = 60
Dit_time = minute_to_second / (CW_Word_Per_Minute * paris_to_dit)
Dah_time = Dit_time * 3
Tone_Gap_Time = Dit_time # between individual tones
Character_Gap_time = Dah_time # between characters
Space_time = Dit_time * 7 # between
Audio_Confirmation_Delay = 0.1 # debounce audio and add to audio confirmation count when appropriate
Polite_CW_Delay = 120 # waiting for a pause in the conversation, up to 2 minute, applies to short delay
Max_Long_Delay = 900 # maximum long delay of 15 minutes for GMRS compliance, set to 600 for Ham
Min_Long_Delay = Max_Long_Delay - Polite_CW_Delay  # so we can transmit between the two timelines.
Audio_Input_Threshold = 20000 # When radio is on, usually rests at zero, audio is usually 50k+
Your_FCC_Call_Sign = "Your Call Sign Here" # put your information here

# mutable parameters
System_Status = 0 # tracking this as we go for visual display
Display_Status = 0 # set to follow the system status for display
Reception_Flag = 0 # hearing test flashbacks
Transmission_Flag = 0 # used to track transmission politeness
Current_Audio_Level = 0 # to be modified over time
Polite_CW_Timer = 0 # iteratively managed
Long_CW_Timer = 0 # iteratively managed

# onboard USR button setup
USRkey = digitalio.DigitalInOut(board.BUTTON)
USRkey.direction = digitalio.Direction.INPUT
USRkey.pull = digitalio.Pull.UP

# onboard neopixel setup
np = digitalio.DigitalInOut(board.NEOPIXEL)
np.direction = digitalio.Direction.OUTPUT
neopixel_off = bytearray([0, 0, 0])
neopixel_green = bytearray([75, 0, 0])
neopixel_red = bytearray([0, 75, 0])
neopixel_blue = bytearray([0, 0, 75])
neopixel_white = bytearray([255, 255, 255])
# defaulting off
neopixel_write.neopixel_write(np, neopixel_off)

# onboard led setup
led = pwmio.PWMOut(board.LED, frequency = 5000)
# defaulting off
led.duty_cycle = 0

# audio input setup
# only works when both audio input and audio output are plugged in and the radio is on.
Audio_Input = analogio.AnalogIn(board.A3) # pin labelled as 29

# This works really well
# Audio_Input = digitalio.DigitalInOut(board.GP29) # yields true/false metric
# Audio_Input.direction = digitalio.Direction.INPUT

# PTT output setup
# Any output setting has low / activating voltage
PTT_Output = digitalio.DigitalInOut(board.GP26)
PTT_Output.direction = digitalio.Direction.OUTPUT
PTT_Output.value = False

# audio output setup
Audio_Output = pwmio.PWMOut(board.GP4, variable_frequency = True)
Audio_Volume = 2 ** 9 # 32760 is max duty cycle
Audio_Output.duty_cycle = 0 # for now
Audio_Output.frequency = 800

# ssd1306 display setup
i2c_interface = busio.I2C(board.GP1, board.GP0)
tiny_display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c_interface)
tiny_display.fill(0) # blanks the screen
tiny_display.text("Top Line", 0, 0, 1)
tiny_display.text("Second Line", 0, 16, 1)
tiny_display.text("Third Line", 0, 28, 1)
tiny_display.text("Fourth Line", 0, 40, 1)
tiny_display.text("Fifth Line", 0, 52, 1)
tiny_display.show()

# indexible AlphaNumeric list
Standard_AlphaNumeric_List = [
      "A",
      "B",
      "C",
      "D",
      "E",
      "F",
      "G",
      "H",
      "I",
      "J",
      "K",
      "L",
      "M",
      "N",
      "O",
      "P",
      "Q",
      "R",
      "S",
      "T",
      "U",
      "V",
      "W",
      "X",
      "Y",
      "Z",
      "1",
      "2",
      "3",
      "4",
      "5",
      "6",
      "7",
      "8",
      "9",
      "0",
      "/",
      " "
]

# indexible dit dah list
CW_AlphaNumeric_List = [
      ".-",     # A
      "-...",   # B
      "-.-.",   # C
      "-..",    # D
      ".",      # E
      "..-.",   # F
      "--.",    # G
      "....",   # H
      "..",     # I
      ".---",   # J
      "-.-",    # K
      ".-..",   # L
      "--",     # M
      "-.",     # N
      "---",    # O
      ".--.",   # P
      "--.-",   # Q
      ".-.",    # R
      "...",    # S
      "-",      # T
      "..-",    # U
      "...-",   # V
      ".--",    # W
      "-..-",   # X
      "-.--",   # Y
      "--..",   # Z
      ".----",  # 1
      "..---",  # 2
      "...--",  # 3
      "....-",  # 4
      ".....",  # 5
      "-....",  # 6
      "--...",  # 7
      "---..",  # 8
      "----.",  # 9
      "-----",  # 0
      "-..-.",  # forward slash
      " "       # space character
]

# string to list
Encoded_FCC_Call_Sign = []
for letter in Your_FCC_Call_Sign:
    Encoded_FCC_Call_Sign.append(letter)
    
print("\nYou entered the following callsign:")
print(Encoded_FCC_Call_Sign) # before

for i in range(len(Standard_AlphaNumeric_List) ):
    # pick a letter to replace
    replace_this = Standard_AlphaNumeric_List[i]
    # with dit dah or space
    with_that = CW_AlphaNumeric_List[i]
    # then swap all instances of each character
    for j in range(len(Encoded_FCC_Call_Sign) ):
        # within each element of the list of characters
        Encoded_FCC_Call_Sign[j] = Encoded_FCC_Call_Sign[j].replace(replace_this, with_that)

print("\n In CW, your callsign translates as:")
print(Encoded_FCC_Call_Sign) # and after

# while True:
#     if USRkey.value == False:
#         neopixel_write.neopixel_write(np, neopixel_blue)
#         time.sleep(0.25)
#         neopixel_write.neopixel_write(np, neopixel_red)
#         time.sleep(0.25)
#         neopixel_write.neopixel_write(np, neopixel_green)
#         time.sleep(0.25)
#         neopixel_write.neopixel_write(np, neopixel_white)
#         time.sleep(0.25)
#         neopixel_write.neopixel_write(np, neopixel_off)
#     else:
#         neopixel_write.neopixel_write(np, neopixel_off)
#         led.duty_cycle = 2 ** 15
#         time.sleep(0.5)
#         PTT_Output.value = True
#         led.duty_cycle = 2 ** 11
#         time.sleep(0.5)
#         PTT_Output.value = False

# Main Loop
while True:

    if System_Status == 0:
        # idle listening
        
        # resetting reception flag
        Reception_Flag = 0
        
        # setting display per system status
        tiny_display.fill(0) # blanks the screen
        tiny_display.text("System Status = 0", 0, 0, 1)
        tiny_display.text("System Idle", 0, 16, 1)
        tiny_display.text("Listening for Audio", 0, 28, 1)
        # tiny_display.text("Fourth Line", 0, 40, 1)
        # tiny_display.text("Fifth Line", 0, 52, 1)
        tiny_display.show()
        
        while System_Status == 0:
            
            # standard audio confirmation delay
            time.sleep(Audio_Confirmation_Delay)
            
            # assessing current audio level
            Current_Audio_Level = Audio_Input.value
            print("current audio level")
            print(Current_Audio_Level)
            print("reception flag")
            print(Reception_Flag)
            
            # if audio is high enough for a bit, the add points to the reception flag
            if (Current_Audio_Level >= Audio_Input_Threshold and Reception_Flag < 20):
                Reception_Flag += 1
            
            # if opposite, then reduce reception flag
            if (Current_Audio_Level < Audio_Input_Threshold and Reception_Flag > 0):
                Reception_Flag -= 1
                
            # if we have enough points, confirm audio reception by shifting system status
            if Reception_Flag >= 20:
                # audio input confirmed
                System_Status = 1
            
            # if someone hits the button, politely send
            if USRkey.value == False:
                System_Status = 1
            
    if System_Status == 1:
        # a short polite delay
        
        # resetting transmission flag
        Transmission_Flag = 0
        
        # setting display per system status
        tiny_display.fill(0) # blanks the screen
        tiny_display.text("System Status = 1", 0, 0, 1)
        tiny_display.text("Audio Input Confirmed.", 0, 16, 1)
        tiny_display.text("Now Waiting Politely", 0, 28, 1)
        tiny_display.text("to Send CW", 0, 40, 1)
        # tiny_display.text("Fifth Line", 0, 52, 1)
        tiny_display.show()
        
        while System_Status == 1:
                        
            # give it a short delay
            time.sleep(Audio_Confirmation_Delay)
            
            # register the audio level
            Current_Audio_Level = Audio_Input.value
            print("current audio level")
            print(Current_Audio_Level)
            print("polite cw timer")
            print(round(Polite_CW_Timer, 1) )
            print("transmission flag")
            print(Transmission_Flag)
            
            # waiting my turn as long as I can
            if Current_Audio_Level < Audio_Input_Threshold:
                Transmission_Flag += 1
            if Current_Audio_Level > Audio_Input_Threshold: 
                Transmission_Flag = 0
            
            # but keeping things accountable per FCC
            Polite_CW_Timer += Audio_Confirmation_Delay
                        
            # if it's quiet or too late, off we go to send audio
            if Transmission_Flag >= 20 or Polite_CW_Timer >= Polite_CW_Delay:
                System_Status = 2
            
    if System_Status == 2:
        # transmission of CW
        print("sending cw")
        
        # reset some timers
        Polite_CW_Timer = 0
        Long_CW_Timer = 0
        
        # turn off the big light
        neopixel_write.neopixel_write(np, neopixel_off)
        
        # setting display per system status
        tiny_display.fill(0) # blanks the screen
        tiny_display.text("System Status = 2", 0, 0, 1)
        tiny_display.text("Now Sending CW", 0, 16, 1)
        tiny_display.text("And Flashing CW", 0, 28, 1)
        # tiny_display.text("Fourth Line", 0, 40, 1)
        # tiny_display.text("Fifth Line", 0, 52, 1)
        tiny_display.show()
        
        # Open the PTT Relay
        PTT_Output.value = True
        
        # give bit, It does take the full 0.4 to make it happen without skipping anything.
        time.sleep(0.3)
        
        # for each character in the encoded call sign
        for i in range(len(Encoded_FCC_Call_Sign) ):
            
            # pause between characters
            # Character - Tone time because each tone incorporates a tone gap time already
            time.sleep(Character_Gap_time - Tone_Gap_Time)
            # total 2 units
            
            # for each sound in each character
            for j in Encoded_FCC_Call_Sign[i]:
                
                time.sleep(Tone_Gap_Time)
                # total 1 unit
                
                if j == ".":
                    # dit using neopixel for visual and audio output
                    neopixel_write.neopixel_write(np, neopixel_white)
                    Audio_Output.duty_cycle = Audio_Volume
                    time.sleep(Dit_time)
                    neopixel_write.neopixel_write(np, neopixel_off)
                    Audio_Output.duty_cycle = 0
#                     time.sleep(Tone_Gap_Time)
                    print("dit")
                
                if j == "-":
                    # dah using neopixel for visual and audio output
                    neopixel_write.neopixel_write(np, neopixel_white)
                    Audio_Output.duty_cycle = Audio_Volume
                    time.sleep(Dah_time)
                    neopixel_write.neopixel_write(np, neopixel_off)
                    Audio_Output.duty_cycle = 0
#                     time.sleep(Tone_Gap_Time)
                    print("dah")
                
                if j == " ":
                    # pause for the space
                    time.sleep(Space_time - ( Character_Gap_time + Tone_Gap_Time ) )
                    # total 4 units
                    print("space")
                
        # little pause after sending
        time.sleep(0.1)
        
        # Close the PTT Relay 
        PTT_Output.value = False
        
        # Now that we've completed the send, move to status 3
        System_Status = 3
        
    if System_Status == 3:
        # the long listen
        
        # reset reception flag
        Reception_Flag = 0
        
        # resetting long cw timer
        Long_CW_Timer = 0
        
        # setting display per system status
        tiny_display.fill(0) # blanks the screen
        tiny_display.text("System Status = 3", 0, 0, 1)
        tiny_display.text("Perform Long Listen", 0, 16, 1)
        tiny_display.text("for Further CW ID", 0, 28, 1)
        # tiny_display.text("Fourth Line", 0, 40, 1)
        # tiny_display.text("Fifth Line", 0, 52, 1)
        tiny_display.show()
        
        while System_Status == 3:
            
            # standard audio confirmation delay
            time.sleep(Audio_Confirmation_Delay)
            
            # building up long cw timer
            Long_CW_Timer += Audio_Confirmation_Delay
            
            # assessing current audio level
            Current_Audio_Level = Audio_Input.value
            print("current audio level")
            print(Current_Audio_Level)
            print("long cw timer")
            print(round(Long_CW_Timer, 1) )
            print("reception flag")
            print(Reception_Flag)

            
            # if audio is high enough for a bit, the add points to the reception flag
            if (Current_Audio_Level >= Audio_Input_Threshold):
                Reception_Flag += 1
            
            # if we get 2 full minutes of audio
            if Reception_Flag >= 120:
                # audio input confirmed prior to max delay
                System_Status = 4
            
            if Long_CW_Timer >= Max_Long_Delay:
                # audio failed ot confirm prior to max delay
                System_Status = 0
            
            # keep the long cw timer going
            
            # if someone hits the button, politely send
            if USRkey.value == False:
                System_Status = 1
            
    if System_Status == 4:
        # a longer polite delay
        
        # resetting transmission flag
        Transmission_Flag = 0
        
        # setting display per system status
        tiny_display.fill(0) # blanks the screen
        tiny_display.text("System Status = 4", 0, 0, 1)
        tiny_display.text("Audio Input Confirmed", 0, 16, 1)
        tiny_display.text("A Longer Polite Delay", 0, 28, 1)
        tiny_display.text("to Send CW", 0, 40, 1)
        # tiny_display.text("Fifth Line", 0, 52, 1)
        tiny_display.show()
        
        while System_Status == 4:
            
            # give it a short delay
            time.sleep(Audio_Confirmation_Delay)
            
            # building up long cw timer
            Long_CW_Timer += Audio_Confirmation_Delay
            
            # register the audio level
            Current_Audio_Level = Audio_Input.value
            print("current audio")
            print(Current_Audio_Level)
            print("long cw timer")
            print(round(Long_CW_Timer, 1) )
            print("transmission flag")
            print(Transmission_Flag)
            
            # waiting my turn as long as I can
            if Current_Audio_Level < Audio_Input_Threshold:
                Transmission_Flag += 1
            if Current_Audio_Level > Audio_Input_Threshold:
                Transmission_Flag = 0
            
            # if it's quiet and late enough, we send CW
            if Transmission_Flag >= 20 and Long_CW_Timer >= Min_Long_Delay:
                System_Status = 2
            
            # or if it has been long enough to force the send
            if Long_CW_Timer >= Max_Long_Delay:
                System_Status = 2
            
            # if someone hits the button, politely send
            if USRkey.value == False:
                System_Status = 1

