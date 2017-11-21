#This script was written by Aaron Cohen on 11/20/2017
#Based on information from publicly available beacon decoding instructions found on ecamsat.org
# http://ecamsat.engr.scu.edu/beacon/EcAMSatBeaconDecoding.pdf
#Prompt user to paste beacon packet
packet = raw_input("Please post the entire 64 character beacon packet: ")
#WARNING: some terminals decode consecutive spaces as a single space
#Later there will be input validation but for now I'm lazy

#Parse packets into individual fields
busTime = packet[14:20] #6 bytes
SolarI = packet[20:24] #4 bytes
SolarT = packet[24:28] #4 bytes
Health0 = packet[28:30] #2 bytes
Health1 = packet[30:34] #4 bytes
Health2 = packet[34:38] #4 bytes
Health3 = packet[38:42] #4 bytes
PageNumber = packet[42:46] #4 bytes
CardTempM = packet[46:50] #4 bytes
WellNumber = packet[50:52] #2 bytes
TaosR = packet[52:56] #4 bytes
TaosG = packet[56:60] #4 bytes
TaosB = packet[60:64] #4 bytes

#Convert little endian to big endian function
def reverseEndian(byte,length):
    if length is 2:
        return bytes
    if length is 4:
        result = byte[2:4] + byte[0:2]
        return result
    if length is 6: 
        result = byte[4:6] + byte[2:4] + byte[0:2]
        return result

#Convert little endian to big endian... seriously who chose little endian?
busTime = reverseEndian(busTime,6)
SolarI = reverseEndian(SolarI,4)
SolarT = reverseEndian(SolarT,4)
Health1 = reverseEndian(Health1,4)
Health2 = reverseEndian(Health2,4)
Health3 = reverseEndian(Health3,4)
PageNumber = reverseEndian(PageNumber,4)
CardTempM = reverseEndian(CardTempM,4)
TaosR = reverseEndian(TaosR,4)
TaosG = reverseEndian(TaosG,4)
TaosB = reverseEndian(TaosB,4)

#Figure out which set of data this is
DataType = (int(WellNumber,16) % 4) + 1

print("Bus Time (seconds): " + str(int(busTime,16)))
#Convert Solar Panel Currents
if DataType is 1:
    SolarI = float(int(SolarI,16)) * 1.8678 + 3.41
if DataType is 2:
    SolarI = float(int(SolarI,16)) * 0.9542 - 1.07
if DataType is 3:
    SolarI = float(int(SolarI,16)) * 1.8785 - 0.41
if DataType is 4:
    SolarI = float(int(SolarI,16)) * 0.9562 - 1.04
print("Solar Panel " + str(DataType) + " current (mA): " + str(SolarI))
print("Solar Panel " + str(DataType) + " temperature (C): " + str(float(int(SolarT,16))/100)) 
if DataType is 1:
    #Convert Data
    powerPort = bin(int(Health0,16))
    Payload1T = (float(int(Health1,16)) * 0.0554) - 15.75
    BattV = (float(int(Health2,16)) * 0.0119) - 0.05
    PayloadHeaterI = (float(int(Health3,16)) * 3.2922) + 8.04
    #Print Data
    print("Bus Power Port Status: " + str(powerPort))
    print("Payload board temperature (C): " + str(Payload1T))
    print("Battery Voltage (V): " + str(BattV))
    print("Payload Heater Current (mA): " + str(PayloadHeaterI))
if DataType is 2:
    #Convert Data
    startupCounter = int(Health0,16)
    rads = int(Health1,16)
    CommV = (float(int(Health2,16)) * 0.0119) + 0.01
    PayloadI = (float(int(Health3,16)) * 3.4281) - 22.69
    #Print Data
    print("Spacecraft startup counter: " + str(startupCounter))
    print("Radiation counts per 30 seconds: " + str(rads))
    print("Comm Voltage (V): " + str(CommV))
    print("Payload Current (mA): " + str(PayloadI))
if DataType is 3:
    #Convert Data
    SCID = int(Health0,16)
    CommI = (float(int(Health1,16)) * 4.3330) + 16.27
    SensorV = (float(int(Health2,16)) * 0.0130) - 0.48
    BusPage = int(Health3,16)
    #Print Data
    print("Spacecraft to ground ID: " + str(SCID))
    print("Comm Current (mA): " + str(CommI))
    print("Sensor Voltage (V): " + str(SensorV))
    print("Bus Data Page: " + str(BusPage))
if DataType is 4:
    #Convert Data
    ExpPhase = bin(int(Health0,16))
    CommV = (float(int(Health1,16)) * 0.0119) + 0.01
    BusV = (float(int(Health2,16)) * 0.0059)
    WrapCount = int(Health3,16) 
    #Print Data
    print("Experiment phase: " + str(ExpPhase))
    print("Comm Voltage (V): " + str(CommV))
    print("Bus Voltage (V): " + str(BusV))
    print("Register File Wrap Count " + str(WrapCount))
print("Payload Page Number: " + str(int(PageNumber,16)))
CardTempM = float(int(CardTempM,16)) / 100
print("Median Card Temperature (C): " + str(CardTempM))
print("Well Number: " + str(int(WellNumber,16)))
print("TaosR (Hz): " + str(int(TaosR,16)))
print("TaosG (Hz): " + str(int(TaosG,16)))
print("TaosB (Hz): " + str(int(TaosB,16)))
