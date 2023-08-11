import time, serial

ser = serial.Serial('COM2', 9600, timeout=1)
txt = '압력: 235'
while True:
    
    ser.write(txt.encode())
    time.sleep(0.5)