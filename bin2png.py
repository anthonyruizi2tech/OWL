import cv2
import numpy as np
import os
import ctypes
from dataclasses import dataclass
# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
DIR_PATH = "bin_files"

WIDTH = 1280
HEIGHT = 721

FPS = 30

# 14-bit grayscale packed into 16-bit words
BYTES_PER_PIXEL = 2

# Little-endian uint16
PIXEL_DTYPE = np.dtype('<u2')
# if deciding to use big-Endian change this line above to the one below 
# PIXEL_DTYPE = np.dtype('>u2') 


FRAME_SIZE = WIDTH * HEIGHT * BYTES_PER_PIXEL

WINDOW_NAME = "Bin Sequence Viewer"

# since every position for the camera gimbal has 4 frames, we skip 4 ( we read one of every 4th frame)
FRAME_SKIP = 4


# mosaic canvas dimensions 
cv2.namedWindow(
    "Panorama",
    cv2.WINDOW_NORMAL
)
cv2.resizeWindow(
    "Panorama",
    1600,
    800
)
PAN_MIN_WIDTH  = 800
PAN_MIN_HEIGHT = 400

PAN_MAX_WIDTH  = 2400
PAN_MAX_HEIGHT = 1200

class RealTimeMosaic:

    def __init__(self):


        self.ppd = 20  # pixels per degree

        self.width = 360 * self.ppd
        self.height = 180 * self.ppd

        self.canvas_sum = np.zeros(
            (self.height, self.width),
            dtype=np.float32
        )

        self.canvas_hits = np.zeros(
            (self.height, self.width),
            dtype=np.uint16
        )

    def add_frame(self, image, metadata):



        coarse_az = bytes_to_float(metadata.courseAzAngle)
        coarse_el = bytes_to_float(metadata.courseElAngle)
        fine_az = bytes_to_float(metadata.fineInnerAzAngle)
        fine_el = bytes_to_float(metadata.fineInnerElAngle)

        az = coarse_az + fine_az
        el = coarse_el + fine_el

        hfov = bytes_to_float(metadata.irHfov )
        vfov = bytes_to_float( metadata.irVfov)

        print("From within 'add_frame()': " f"AZ={az:.2f} "f"EL={el:.2f} " f"HFOV={hfov:.2f} " f"VFOV={vfov:.2f}")

        self.place_frame( image,az,el,hfov,vfov )

    def place_frame(self,image,az,el,hfov,vfov):

        frame_w = max( 1,int(hfov * self.ppd))

        frame_h = max( 1,int(vfov * self.ppd))

        scaled = cv2.resize( image,(frame_w, frame_h))

        x = int((az % 360.0) * self.ppd)

        y = int(self.height/2 + (el * self.ppd) )

        x0 = x - frame_w//2
        y0 = y - frame_h//2

        for row in range(frame_h):

            yy = y0 + row

            if yy < 0 or yy >= self.height:
                continue

            for col in range(frame_w):

                xx = (
                    x0 + col
                ) % self.width

                self.canvas_sum[yy,xx] = scaled[row,col]
                self.canvas_hits[yy,xx] = 1


    def get_display(self):

        display = self.canvas_sum / np.maximum(
            self.canvas_hits,
            1
        )

        return display.astype(np.uint8)


        
class frame_metadata:
    # these variables are metadata taken from each frame. every frame will have an instance of this class 
    frameId = bytearray([00,00,00,00])  #byte  0 1 2 3 
    turretId = bytearray([00,00,00,00])  # byte byte 4 5 6 7 
    unixTime = bytearray([00,00,00,00,00,00,00,00])  #byte 8 9 10 11 12 13 14 15 
    turretClockAtUnixRecieve = bytearray([00,00,00,00,00,00,00,00])  #byte 16 17 18 19 20 21 22 23 
    turretClockAtImageSnap = bytearray([00,00,00,00,00,00,00,00])  #byte 24 25 26 27 28 29 30 31 
    courseAzAngle = bytearray([00,00,00,00])     #byte 32 33 34 35  
    courseElAngle = bytearray([00,00,00,00])     #byte  36 37 38 39
    fineInnerAzAngle = bytearray([00,00,00,00])  #byte 40 41 42 43 
    fineInnerElAngle = bytearray([00,00,00,00])  #byte 44 45 46 47 
    mirrorElAngle = bytearray([00,00,00,00]) #byte  48 49 50 51 
    eoHfov = bytearray([00,00,00,00])    #byte  52 53 54 55 
    eoVfov = bytearray([00,00,00,00])    #byte 56 57 58 59 
    eoStatus = bytearray([00])           #byte 60
    eoShutter = bytearray([00])          #byte 61 
    eoIris   = bytearray([00])           #byte 62 
    eoGain   = bytearray([00])           #byte 63 
    irHfov = bytearray([00,00,00,00])    #byte 64 65 66 67  
    irVfov = bytearray([00,00,00,00])    #byte 68 69 70 71 
    irFpaTemp = bytearray([00,00,00,00]) #byte  72 73 74 75 
    irFpaIntegrationTime = bytearray([00,00,00,00]) #byte 76 77 78 79
    fsmInnerCounter = bytearray([00,00])#byte 80 81
    courseCounter = bytearray([00,00])  #byte 82 83
    irStatus = bytearray([00])          #byte 84 
    fsmColumnCounter = bytearray([00])  #byte 85
    turretStatus = bytearray([00])      #byte 86 
    stepStareStatus = bytearray([00])   #byte 87 
    heading = bytearray([00,00,00,00])  #byte 88 89 90 91 
    pitch = bytearray([00,00,00,00])    #byte 92 93 94 95
    roll = bytearray([00,00,00,00])          #byte 96 97 98 99  
    latitude = bytearray([00,00,00,00])      #byte 100 101 102 103   
    longtitude = bytearray([00,00,00,00])    #byte 104 105 106 107 
    altitude = bytearray([00,00,00,00])      #byte 108 109 110 111 
    velocityNorth = bytearray([00,00,00,00]) #byte 112 113 114 115 
    velocityEast = bytearray([00,00,00,00])  #byte 116 117 118 119 
    velocityDown = bytearray([00,00,00,00])  #byte 120 121 122 123 
    inputVoltage = bytearray([00,00,00,00])  #byte 124 125 126 127
    azimuthGyroRate = bytearray([00,00,00,00])          #byte 128 129 130 131 
    elevationGyroRate = bytearray([00,00,00,00])        #byte 132 133 134 135 
    rollGyroRate = bytearray([00,00,00,00])             #byte 136 137 138 139  
    azimuthGyroPosition = bytearray([00,00,00,00])      #byte 140 141 142 143 
    elevationGyroPosition = bytearray([00,00,00,00])    #byte 144 145 146 147 
    rollGyroPosition = bytearray([00,00,00,00])  #byte 148 149 150 151 
    detailedGimbalStatus = bytearray([00])       #byte 152 
    stepStareStatus2 = bytearray([00])           #byte 153 
    continousBuiltInTestStatus = bytearray([00]) #byte 154


current_metadata = frame_metadata() #instance of the class to store frame meta data 
current_metadata_hex = frame_metadata()
mosaic = RealTimeMosaic() # instance of the mosaic class 
# ------------------------------------------------------------------
# meyta data byte array, bytes 0-154 
# ------------------------------------------------------------------
# Mutable byte array                 
meta_data_array = bytearray([00,

                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,

                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,

                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,

                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,

                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,
                            
                            00, 00, 00, 00, 00, 00, 00, 00, 00, 00,

                            00,00,00,00 ])  # Represents hex 00 when initialized 





# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def play_bin_directory():

    if not os.path.isdir(DIR_PATH):
        print(f"Directory not found: {DIR_PATH}")
        return

    bin_files = sorted(
        f for f in os.listdir(DIR_PATH)
        if f.lower().endswith(".bin")
    )

    if not bin_files:
        print(f"No .bin files found in {DIR_PATH}")
        return

    # since there is 4 frame duplicates only use 1 of every 4th file 
    bin_files = bin_files[::FRAME_SKIP]


    print(f"Found {len(bin_files)} file(s)")
    print(f"Frame Size: {FRAME_SIZE:,} bytes")
    print(f"Resolution: {WIDTH} x {HEIGHT}")
    print("Press 'q' to quit")

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

    for file_name in bin_files:

        file_path = os.path.join(DIR_PATH, file_name)

        file_size = os.path.getsize(file_path)

        print("\n--------------------------------")
        print(f"Playing: {file_name}")
        print(f"File Size: {file_size:,} bytes")

        frames_in_file = file_size // FRAME_SIZE
        print(f"Frames Detected: {frames_in_file}")

        with open(file_path, "rb") as f:

            frame_index = 0

            while True:

                frame_bytes = f.read(FRAME_SIZE)

                if len(frame_bytes) != FRAME_SIZE:
                    break

                # --------------------------------------------------
                # Convert raw bytes to uint16 pixels
                # --------------------------------------------------
                frame = np.frombuffer(
                    frame_bytes,
                    dtype=PIXEL_DTYPE
                )

                expected_pixels = WIDTH * HEIGHT

                if frame.size != expected_pixels:
                    print(
                        f"Frame {frame_index}: "
                        f"Expected {expected_pixels} pixels, "
                        f"got {frame.size}"
                    )
                    break

                # --------------------------------------------------
                # Reshape to image
                # --------------------------------------------------
                frame = frame.reshape((HEIGHT, WIDTH))
                
                # --------------------------------------------------
                # Extract metadata from row 721 (last row)
                # --------------------------------------------------

                last_row_bytes = frame[-1].tobytes()

                meta_data_array[:] = last_row_bytes[:155] # 155 total bytes inclusivley (0-154) 

                sort_n_store_metadata_byte() # store values in instance of class (for raw byte value)
                sort_n_store_metadata_hex() # store values in instance of class (for hex)


                #print_decoded_meta_data_array_bytes()
                #print_organized_current_field_raw_decimal_byte()  
                print_organized_current_field_hex()              
                
                # --------------------------------------------------
                # Extract 14-bit image data
                # Bits [15:2] contain image
                # Bits [1:0] are zero
                # --------------------------------------------------
                #frame14 = frame >> 2 # uncommment to show frame with meta data 
                frame14 = frame[:-1,:] >> 2 # uncommment to show frame without meta data 
                # --------------------------------------------------
                # Convert 14-bit -> 8-bit for display
                # 16383 = max 14-bit value
                # --------------------------------------------------
                
                ## slightly darker image display 
                ###display_frame = (
                ###    frame14.astype(np.float32) * (255.0 / 16383.0)
                ###).astype(np.uint8)


                ## slightly lighter image display 
                # which stretches the contrast of each frame automatically and is often better for inspecting raw sensor data.

                display_frame = cv2.normalize(
                    frame14,
                    None,
                    0,
                    255,
                    cv2.NORM_MINMAX,
                    dtype=cv2.CV_8U
                )

                rotated_frame = cv2.rotate(display_frame, cv2.ROTATE_180)   # rotate rightside up 180

                image_only = rotated_frame
                mosaic.add_frame(
                    image_only,
                    current_metadata
                )



                cv2.imshow(WINDOW_NAME, rotated_frame) # to display raw, replace rotated w display_frame 

                show_mosaic_window(mosaic.get_display())


                key = cv2.waitKey(int(1000 / FPS)) & 0xFF

                if key == ord('q'):
                    cv2.destroyAllWindows()
                    return

                frame_index += 1

    cv2.destroyAllWindows()
    print("\nFinished playback.")





def print_decoded_meta_data_array_bytes():

    print("\n---------------- Metadata ----------------")

    # Raw decimal bytes
    print("Bytes:")
    print(list(meta_data_array))

    # Hex dump
    print("\nHex:")

    hex_string = " ".join(
        f"{b:02X}"
        for b in meta_data_array
    )

    print(hex_string)

    # Printable ASCII view
    #print("\nASCII:")

    #ascii_string = "".join(
    #    chr(b) if 32 <= b <= 126 else "."
    #    for b in meta_data_array
    #)

    #print(ascii_string)

    #print("------------------------------------------")


def sort_n_store_metadata_byte():
     
    #logic that handles sorting of meta_data_array 
    global current_metadata

    current_metadata.frameId[:] = meta_data_array[0:4]
    current_metadata.turretId[:] = meta_data_array[4:8]

    current_metadata.unixTime[:] = meta_data_array[8:16]
    current_metadata.turretClockAtUnixRecieve[:] = meta_data_array[16:24]
    current_metadata.turretClockAtImageSnap[:] = meta_data_array[24:32]

    current_metadata.courseAzAngle[:] = meta_data_array[32:36]
    current_metadata.courseElAngle[:] = meta_data_array[36:40]

    current_metadata.fineInnerAzAngle[:] = meta_data_array[40:44]
    current_metadata.fineInnerElAngle[:] = meta_data_array[44:48]

    current_metadata.mirrorElAngle[:] = meta_data_array[48:52]

    current_metadata.eoHfov[:] = meta_data_array[52:56]
    current_metadata.eoVfov[:] = meta_data_array[56:60]

    current_metadata.eoStatus[:] = meta_data_array[60:61]
    current_metadata.eoShutter[:] = meta_data_array[61:62]
    current_metadata.eoIris[:] = meta_data_array[62:63]
    current_metadata.eoGain[:] = meta_data_array[63:64]

    current_metadata.irHfov[:] = meta_data_array[64:68]
    current_metadata.irVfov[:] = meta_data_array[68:72]

    current_metadata.irFpaTemp[:] = meta_data_array[72:76]
    current_metadata.irFpaIntegrationTime[:] = meta_data_array[76:80]

    current_metadata.fsmInnerCounter[:] = meta_data_array[80:82]
    current_metadata.courseCounter[:] = meta_data_array[82:84]

    current_metadata.irStatus[:] = meta_data_array[84:85]
    current_metadata.fsmColumnCounter[:] = meta_data_array[85:86]
    current_metadata.turretStatus[:] = meta_data_array[86:87]
    current_metadata.stepStareStatus[:] = meta_data_array[87:88]

    current_metadata.heading[:] = meta_data_array[88:92]
    current_metadata.pitch[:] = meta_data_array[92:96]
    current_metadata.roll[:] = meta_data_array[96:100]

    current_metadata.latitude[:] = meta_data_array[100:104]
    current_metadata.longtitude[:] = meta_data_array[104:108]
    current_metadata.altitude[:] = meta_data_array[108:112]

    current_metadata.velocityNorth[:] = meta_data_array[112:116]
    current_metadata.velocityEast[:] = meta_data_array[116:120]
    current_metadata.velocityDown[:] = meta_data_array[120:124]

    current_metadata.inputVoltage[:] = meta_data_array[124:128]

    current_metadata.azimuthGyroRate[:] = meta_data_array[128:132]
    current_metadata.elevationGyroRate[:] = meta_data_array[132:136]
    current_metadata.rollGyroRate[:] = meta_data_array[136:140]

    current_metadata.azimuthGyroPosition[:] = meta_data_array[140:144]
    current_metadata.elevationGyroPosition[:] = meta_data_array[144:148]
    current_metadata.rollGyroPosition[:] = meta_data_array[148:152]

    current_metadata.detailedGimbalStatus[:] = meta_data_array[152:153]
    current_metadata.stepStareStatus2[:] = meta_data_array[153:154]
    current_metadata.continousBuiltInTestStatus[:] = meta_data_array[154:155]


def sort_n_store_metadata_hex():

    global current_metadata_hex

    current_metadata_hex.frameId = bytes_to_hex_list(meta_data_array[0:4])
    current_metadata_hex.turretId = bytes_to_hex_list(meta_data_array[4:8])

    current_metadata_hex.unixTime = bytes_to_hex_list(meta_data_array[8:16])
    current_metadata_hex.turretClockAtUnixRecieve = bytes_to_hex_list(meta_data_array[16:24])
    current_metadata_hex.turretClockAtImageSnap = bytes_to_hex_list(meta_data_array[24:32])

    current_metadata_hex.courseAzAngle = bytes_to_hex_list(meta_data_array[32:36])
    current_metadata_hex.courseElAngle = bytes_to_hex_list(meta_data_array[36:40])

    current_metadata_hex.fineInnerAzAngle = bytes_to_hex_list(meta_data_array[40:44])
    current_metadata_hex.fineInnerElAngle = bytes_to_hex_list(meta_data_array[44:48])

    current_metadata_hex.mirrorElAngle = bytes_to_hex_list(meta_data_array[48:52])

    current_metadata_hex.eoHfov = bytes_to_hex_list(meta_data_array[52:56])
    current_metadata_hex.eoVfov = bytes_to_hex_list(meta_data_array[56:60])

    current_metadata_hex.eoStatus = bytes_to_hex_list(meta_data_array[60:61])
    current_metadata_hex.eoShutter = bytes_to_hex_list(meta_data_array[61:62])
    current_metadata_hex.eoIris = bytes_to_hex_list(meta_data_array[62:63])
    current_metadata_hex.eoGain = bytes_to_hex_list(meta_data_array[63:64])

    current_metadata_hex.irHfov = bytes_to_hex_list(meta_data_array[64:68])
    current_metadata_hex.irVfov = bytes_to_hex_list(meta_data_array[68:72])

    current_metadata_hex.irFpaTemp = bytes_to_hex_list(meta_data_array[72:76])
    current_metadata_hex.irFpaIntegrationTime = bytes_to_hex_list(meta_data_array[76:80])

    current_metadata_hex.fsmInnerCounter = bytes_to_hex_list(meta_data_array[80:82])
    current_metadata_hex.courseCounter = bytes_to_hex_list(meta_data_array[82:84])

    current_metadata_hex.irStatus = bytes_to_hex_list(meta_data_array[84:85])
    current_metadata_hex.fsmColumnCounter = bytes_to_hex_list(meta_data_array[85:86])
    current_metadata_hex.turretStatus = bytes_to_hex_list(meta_data_array[86:87])
    current_metadata_hex.stepStareStatus = bytes_to_hex_list(meta_data_array[87:88])

    current_metadata_hex.heading = bytes_to_hex_list(meta_data_array[88:92])
    current_metadata_hex.pitch = bytes_to_hex_list(meta_data_array[92:96])
    current_metadata_hex.roll = bytes_to_hex_list(meta_data_array[96:100])

    current_metadata_hex.latitude = bytes_to_hex_list(meta_data_array[100:104])
    current_metadata_hex.longtitude = bytes_to_hex_list(meta_data_array[104:108])
    current_metadata_hex.altitude = bytes_to_hex_list(meta_data_array[108:112])

    current_metadata_hex.velocityNorth = bytes_to_hex_list(meta_data_array[112:116])
    current_metadata_hex.velocityEast = bytes_to_hex_list(meta_data_array[116:120])
    current_metadata_hex.velocityDown = bytes_to_hex_list(meta_data_array[120:124])

    current_metadata_hex.inputVoltage = bytes_to_hex_list(meta_data_array[124:128])

    current_metadata_hex.azimuthGyroRate = bytes_to_hex_list(meta_data_array[128:132])
    current_metadata_hex.elevationGyroRate = bytes_to_hex_list(meta_data_array[132:136])
    current_metadata_hex.rollGyroRate = bytes_to_hex_list(meta_data_array[136:140])

    current_metadata_hex.azimuthGyroPosition = bytes_to_hex_list(meta_data_array[140:144])
    current_metadata_hex.elevationGyroPosition = bytes_to_hex_list(meta_data_array[144:148])
    current_metadata_hex.rollGyroPosition = bytes_to_hex_list(meta_data_array[148:152])

    current_metadata_hex.detailedGimbalStatus = bytes_to_hex_list(meta_data_array[152:153])
    current_metadata_hex.stepStareStatus2 = bytes_to_hex_list(meta_data_array[153:154])
    current_metadata_hex.continousBuiltInTestStatus = bytes_to_hex_list(meta_data_array[154:155])


def print_organized_current_field_raw_decimal_byte():

    print("\n============== FRAME METADATA DECIMAL ==============")

    print("frameId:", list(current_metadata.frameId))
    print("turretId:", list(current_metadata.turretId))

    print("unixTime:", list(current_metadata.unixTime))
    print("turretClockAtUnixRecieve:", list(current_metadata.turretClockAtUnixRecieve))
    print("turretClockAtImageSnap:", list(current_metadata.turretClockAtImageSnap))

    print("courseAzAngle:", list(current_metadata.courseAzAngle))
    print("courseElAngle:", list(current_metadata.courseElAngle))

    print("fineInnerAzAngle:", list(current_metadata.fineInnerAzAngle))
    print("fineInnerElAngle:", list(current_metadata.fineInnerElAngle))

    print("mirrorElAngle:", list(current_metadata.mirrorElAngle))

    print("eoHfov:", list(current_metadata.eoHfov))
    print("eoVfov:", list(current_metadata.eoVfov))

    print("eoStatus:", list(current_metadata.eoStatus))
    print("eoShutter:", list(current_metadata.eoShutter))
    print("eoIris:", list(current_metadata.eoIris))
    print("eoGain:", list(current_metadata.eoGain))

    print("irHfov:", list(current_metadata.irHfov))
    print("irVfov:", list(current_metadata.irVfov))

    print("irFpaTemp:", list(current_metadata.irFpaTemp))
    print("irFpaIntegrationTime:", list(current_metadata.irFpaIntegrationTime))

    print("fsmInnerCounter:", list(current_metadata.fsmInnerCounter))
    print("courseCounter:", list(current_metadata.courseCounter))

    print("irStatus:", list(current_metadata.irStatus))
    print("fsmColumnCounter:", list(current_metadata.fsmColumnCounter))
    print("turretStatus:", list(current_metadata.turretStatus))
    print("stepStareStatus:", list(current_metadata.stepStareStatus))

    print("heading:", list(current_metadata.heading))
    print("pitch:", list(current_metadata.pitch))
    print("roll:", list(current_metadata.roll))

    print("latitude:", list(current_metadata.latitude))
    print("longitude:", list(current_metadata.longtitude))
    print("altitude:", list(current_metadata.altitude))

    print("velocityNorth:", list(current_metadata.velocityNorth))
    print("velocityEast:", list(current_metadata.velocityEast))
    print("velocityDown:", list(current_metadata.velocityDown))

    print("inputVoltage:", list(current_metadata.inputVoltage))

    print("azimuthGyroRate:", list(current_metadata.azimuthGyroRate))
    print("elevationGyroRate:", list(current_metadata.elevationGyroRate))
    print("rollGyroRate:", list(current_metadata.rollGyroRate))

    print("azimuthGyroPosition:", list(current_metadata.azimuthGyroPosition))
    print("elevationGyroPosition:", list(current_metadata.elevationGyroPosition))
    print("rollGyroPosition:", list(current_metadata.rollGyroPosition))

    print("detailedGimbalStatus:", list(current_metadata.detailedGimbalStatus))
    print("stepStareStatus2:", list(current_metadata.stepStareStatus2))
    print("continousBuiltInTestStatus:", list(current_metadata.continousBuiltInTestStatus))

    print("=================================================\n")


def print_organized_current_field_hex():

    print("\n============== FRAME METADATA HEX ==============")

    print("frameId:", list(current_metadata_hex.frameId))
    print("turretId:", list(current_metadata_hex.turretId))

    print("unixTime:", list(current_metadata_hex.unixTime))
    print("turretClockAtUnixRecieve:", list(current_metadata_hex.turretClockAtUnixRecieve))
    print("turretClockAtImageSnap:", list(current_metadata_hex.turretClockAtImageSnap))

    print("courseAzAngle:", list(current_metadata_hex.courseAzAngle))
    print("courseElAngle:", list(current_metadata_hex.courseElAngle))

    print("fineInnerAzAngle:", list(current_metadata_hex.fineInnerAzAngle))
    print("fineInnerElAngle:", list(current_metadata_hex.fineInnerElAngle))

    print("mirrorElAngle:", list(current_metadata_hex.mirrorElAngle))

    print("eoHfov:", list(current_metadata_hex.eoHfov))
    print("eoVfov:", list(current_metadata_hex.eoVfov))

    print("eoStatus:", list(current_metadata_hex.eoStatus))
    print("eoShutter:", list(current_metadata_hex.eoShutter))
    print("eoIris:", list(current_metadata_hex.eoIris))
    print("eoGain:", list(current_metadata_hex.eoGain))

    print("irHfov:", list(current_metadata_hex.irHfov))
    print("irVfov:", list(current_metadata_hex.irVfov))

    print("irFpaTemp:", list(current_metadata_hex.irFpaTemp))
    print("irFpaIntegrationTime:", list(current_metadata_hex.irFpaIntegrationTime))

    print("fsmInnerCounter:", list(current_metadata_hex.fsmInnerCounter))
    print("courseCounter:", list(current_metadata_hex.courseCounter))

    print("irStatus:", list(current_metadata_hex.irStatus))
    print("fsmColumnCounter:", list(current_metadata_hex.fsmColumnCounter))
    print("turretStatus:", list(current_metadata_hex.turretStatus))
    print("stepStareStatus:", list(current_metadata_hex.stepStareStatus))

    print("heading:", list(current_metadata_hex.heading))
    print("pitch:", list(current_metadata_hex.pitch))
    print("roll:", list(current_metadata_hex.roll))

    print("latitude:", list(current_metadata_hex.latitude))
    print("longitude:", list(current_metadata_hex.longtitude))
    print("altitude:", list(current_metadata_hex.altitude))

    print("velocityNorth:", list(current_metadata_hex.velocityNorth))
    print("velocityEast:", list(current_metadata_hex.velocityEast))
    print("velocityDown:", list(current_metadata_hex.velocityDown))

    print("inputVoltage:", list(current_metadata_hex.inputVoltage))

    print("azimuthGyroRate:", list(current_metadata_hex.azimuthGyroRate))
    print("elevationGyroRate:", list(current_metadata_hex.elevationGyroRate))
    print("rollGyroRate:", list(current_metadata_hex.rollGyroRate))

    print("azimuthGyroPosition:", list(current_metadata_hex.azimuthGyroPosition))
    print("elevationGyroPosition:", list(current_metadata_hex.elevationGyroPosition))
    print("rollGyroPosition:", list(current_metadata_hex.rollGyroPosition))

    print("detailedGimbalStatus:", list(current_metadata_hex.detailedGimbalStatus))
    print("stepStareStatus2:", list(current_metadata_hex.stepStareStatus2))
    print("continousBuiltInTestStatus:", list(current_metadata_hex.continousBuiltInTestStatus))

    print("================================================\n")





#helper function 

def show_mosaic_window(mosaic_image):

    h, w = mosaic_image.shape[:2]

    scale = min(
        PAN_MAX_WIDTH / w,
        PAN_MAX_HEIGHT / h,
        1.0
    )

    display_w = max(
        PAN_MIN_WIDTH,
        min(int(w * scale), PAN_MAX_WIDTH)
    )

    display_h = max(
        PAN_MIN_HEIGHT,
        min(int(h * scale), PAN_MAX_HEIGHT)
    )

    display = cv2.resize(
        mosaic_image,
        (display_w, display_h)
    )

    cv2.imshow(
        "Panorama",
        display
    )

def bytes_to_hex_list(data):
    return [f"{b:02X}" for b in data]

# bytes to float little endian
def bytes_to_float(data):
    return np.frombuffer(data, dtype='<f4')[0]


def total_az(coarse_az, fine_az):
    total_az = (coarse_az + fine_az)
    return total_az

def total_el (coarse_el,fine_el):
    total_el = (coarse_el + fine_el)
    return total_el

if __name__ == "__main__":
    play_bin_directory()