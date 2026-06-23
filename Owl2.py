
# ------------------------------------------------------------------
# Libraries 
# ------------------------------------------------------------------
import os 
import numpy as np
import cv2
import glob
from enum import Enum
import struct 



class PrintFormat(Enum):
    DECIMAL = 0
    HEX = 1


# ------------------------------------------------------------------
# reader class 
# ------------------------------------------------------------------

class reader:

    def parse_metadata(self, metadata_line):

        md = frame_metadata()

        md.frameId = metadata_line[0:4]
        md.turretId = metadata_line[4:8]

        md.unixTime = metadata_line[8:16]
        md.turretClockAtUnixRecieve = metadata_line[16:24]
        md.turretClockAtImageSnap = metadata_line[24:32]

        md.courseAzAngle = metadata_line[32:36]
        md.courseElAngle = metadata_line[36:40]

        md.fineInnerAzAngle = metadata_line[40:44]
        md.fineInnerElAngle = metadata_line[44:48]

        md.mirrorElAngle = metadata_line[48:52]

        md.eoHfov = metadata_line[52:56]
        md.eoVfov = metadata_line[56:60]

        md.eoStatus = metadata_line[60:61]
        md.eoShutter = metadata_line[61:62]
        md.eoIris = metadata_line[62:63]
        md.eoGain = metadata_line[63:64]

        md.irHfov = metadata_line[64:68]
        md.irVfov = metadata_line[68:72]

        md.irFpaTemp = metadata_line[72:76]
        md.irFpaIntegrationTime = metadata_line[76:80]

        md.fsmInnerCounter = metadata_line[80:82]
        md.courseCounter = metadata_line[82:84]

        md.irStatus = metadata_line[84:85]
        md.fsmColumnCounter = metadata_line[85:86]
        md.turretStatus = metadata_line[86:87]
        md.stepStareStatus = metadata_line[87:88]

        md.heading = metadata_line[88:92]
        md.pitch = metadata_line[92:96]
        md.roll = metadata_line[96:100]

        md.latitude = metadata_line[100:104]
        md.longtitude = metadata_line[104:108]
        md.altitude = metadata_line[108:112]

        md.velocityNorth = metadata_line[112:116]
        md.velocityEast = metadata_line[116:120]
        md.velocityDown = metadata_line[120:124]

        md.inputVoltage = metadata_line[124:128]

        md.azimuthGyroRate = metadata_line[128:132]
        md.elevationGyroRate = metadata_line[132:136]
        md.rollGyroRate = metadata_line[136:140]

        md.azimuthGyroPosition = metadata_line[140:144]
        md.elevationGyroPosition = metadata_line[144:148]
        md.rollGyroPosition = metadata_line[148:152]

        md.detailedGimbalStatus = metadata_line[152:153]
        md.stepStareStatus2 = metadata_line[153:154]
        md.continousBuiltInTestStatus = metadata_line[154:155]

        return md



    def print_metadata(self, md):
        """
        Print all metadata fields as hexadecimal bytes.
        """
        print("\n========== FRAME METADATA ==========")

        for field_name, value in vars(md).items():
            hex_bytes = " ".join(f"0x{b:02X}" for b in value)
            print(f"{field_name:30}: {hex_bytes}")
    
        print("====================================\n")


    def frame_stream(self,folder):

        files = sorted(glob.glob(os.path.join(folder, "*.bin")))

        for filename in files:

            frame = np.fromfile(filename, dtype=np.uint16)
            frame = frame.reshape((721,1280))

            image = frame[:720]
            metadata = self.parse_metadata(frame[720].tobytes())

            yield image, metadata

    def u32(self,b):
        return struct.unpack("<I", bytes(b))[0]

    def u16(self,b):
        return struct.unpack("<H", bytes(b))[0]

    def u8(self,b):
        return b[0]

    def f32(self,b):
        return struct.unpack("<f", bytes(b))[0]

    def u64(self,b):
        return struct.unpack("<Q", bytes(b))[0]

# ------------------------------------------------------------------
# Meta Data Class 
# ------------------------------------------------------------------

class frame_metadata:

    def __init__(self):

        self.frameId = bytearray(4)
        self.turretId = bytearray(4)

        self.unixTime = bytearray(8)
        self.turretClockAtUnixRecieve = bytearray(8)
        self.turretClockAtImageSnap = bytearray(8)

        self.courseAzAngle = bytearray(4)
        self.courseElAngle = bytearray(4)

        self.fineInnerAzAngle = bytearray(4)
        self.fineInnerElAngle = bytearray(4)

        self.mirrorElAngle = bytearray(4)

        self.eoHfov = bytearray(4)
        self.eoVfov = bytearray(4)

        self.eoStatus = bytearray(1)
        self.eoShutter = bytearray(1)
        self.eoIris = bytearray(1)
        self.eoGain = bytearray(1)

        self.irHfov = bytearray(4)
        self.irVfov = bytearray(4)

        self.irFpaTemp = bytearray(4)
        self.irFpaIntegrationTime = bytearray(4)

        self.fsmInnerCounter = bytearray(2)
        self.courseCounter = bytearray(2)

        self.irStatus = bytearray(1)
        self.fsmColumnCounter = bytearray(1)
        self.turretStatus = bytearray(1)
        self.stepStareStatus = bytearray(1)

        self.heading = bytearray(4)
        self.pitch = bytearray(4)
        self.roll = bytearray(4)

        self.latitude = bytearray(4)
        self.longtitude = bytearray(4)
        self.altitude = bytearray(4)

        self.velocityNorth = bytearray(4)
        self.velocityEast = bytearray(4)
        self.velocityDown = bytearray(4)

        self.inputVoltage = bytearray(4)

        self.azimuthGyroRate = bytearray(4)
        self.elevationGyroRate = bytearray(4)
        self.rollGyroRate = bytearray(4)

        self.azimuthGyroPosition = bytearray(4)
        self.elevationGyroPosition = bytearray(4)
        self.rollGyroPosition = bytearray(4)

        self.detailedGimbalStatus = bytearray(1)
        self.stepStareStatus2 = bytearray(1)
        self.continousBuiltInTestStatus = bytearray(1)



# ------------------------------------------------------------------
# Mosaic Class 
# ------------------------------------------------------------------


class StepStareMosaic:
    def __init__(self,
                 width=3840,
                 height=2160,
                 hfov=17.46,
                 vfov=9.88):

        self.width = width
        self.height = height
        self.hfov = hfov
        self.vfov = vfov
        self.resolution_scale = 2.0

        self.canvas = np.zeros((height, width), dtype=np.uint8)
        self.weight = np.zeros((height, width), dtype=np.float32)

        # degrees per pixel (full spherical assumption)
        self.az_ppd = width / 360.0
        self.el_ppd = height / 180.0

    def compute_angles(self, md, reader):
        az_coarse = reader.f32(md.courseAzAngle)
        az_fine   = reader.f32(md.fineInnerAzAngle)

        el_coarse = reader.f32(md.courseElAngle)
        el_fine   = reader.f32(md.fineInnerElAngle)

        mirror_el = reader.f32(md.mirrorElAngle)

        az = (az_coarse + az_fine) % 360.0
        el = - (el_coarse + el_fine + mirror_el)

        # clamp elevation
        el = max(-90.0, min(90.0, el))

        return az, el

    def angle_to_pixel(self, az, el):
        x = az / 360.0 * self.width

        y = (90.0 - el) / 180.0 * self.height

        return x, y

    def add_frame(self, img, az, el, scale=1.0):

        h, w = img.shape

        img = cv2.resize(img, (int(w * scale), int(h * scale)))

        cx, cy = self.angle_to_pixel(az, el)

        # convert HFOV/VFOV into pixel size properly
        px_per_deg_x = self.width / 360.0
        px_per_deg_y = self.height / 180.0

        dx = int(self.hfov * px_per_deg_x)
        dy = int(self.vfov * px_per_deg_y)

        # center-based placement (THIS FIXES YOUR OFFSET BUG)
        x0 = int(cx - dx / 2)
        x1 = int(cx + dx / 2)
        y0 = int(cy - dy / 2)
        y1 = int(cy + dy / 2)

        # clip
        x0c, x1c = max(0, x0), min(self.width, x1)
        y0c, y1c = max(0, y0), min(self.height, y1)

        if x0c >= x1c or y0c >= y1c:
            return

        patch_w = x1c - x0c
        patch_h = y1c - y0c

        # resize image to EXACT footprint
        img_patch = cv2.resize(img, (patch_w, patch_h), interpolation=cv2.INTER_AREA)

        self.canvas[y0c:y1c, x0c:x1c] = np.maximum(
            self.canvas[y0c:y1c, x0c:x1c],
            img_patch
        )

    def get(self):
        return self.canvas

# ------------------------------------------------------------------
# configuration   
# ------------------------------------------------------------------

readerInstance = reader()
mosaic = StepStareMosaic()
# assuming uint16 pixels
WIDTH = 1280# assuming 1280 pixels
HEIGHT = 721# assuming 721 rows

folder = "bin_files"


# ------------------------------------------------------------------
# Main()  
# ------------------------------------------------------------------







for i, (image, md) in enumerate(readerInstance.frame_stream("bin_files")):

    if i % 4 != 0:
        continue

    image = cv2.rotate(image, cv2.ROTATE_180)


    # ------------------------------------------------------------------
    # Normalize 16-bit → 8-bit for display of IR image(important!)
    # ------------------------------------------------------------------
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    img_vis = clahe.apply(cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8))
    # ------------------------------------------------------------------
    # Show image
    # ------------------------------------------------------------------
    cv2.imshow("Frame", img_vis)


    readerInstance.print_metadata(md)

    # Get angles
    az, el = mosaic.compute_angles(md, readerInstance)

    # Add to mosaic
    mosaic.add_frame(img_vis, az, el, scale=0.3)

    # Display live mosaic
    cv2.imshow("360 Mosaic", mosaic.get())


    if cv2.waitKey(1) == 27:
        break

cv2.imwrite("360_stepstare.png", mosaic.get())
cv2.destroyAllWindows()



# helper functions 
def bytes_to_float(b):
    return struct.unpack('<f', bytes(b))[0]

def bytes_to_uint32(b):
    return struct.unpack('<I', bytes(b))[0]