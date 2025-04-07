import json
import neoapi
import cv2
import os#
from pathlib import Path
from time import strftime, gmtime, sleep
from utils.data_processing.mask_handler import MaskHandler
from utils.interfaces import LEDController


class CameraHandler:
    def __init__(self, config, output_path: Path):
        self.config = config
        self.camera = None
        self.mask_handler = None
        self.result = 0
        self.correction = 1
        self.exposure = config.get('exposure', 200000)  # Default to 200000 if not specified
        self.pix_per_mm = config.get('pix_per_mm', 56)
        self.part_data = []
        self.total_layers = 0
        self.coord_data = []
        self.output_path = output_path
        self.data_type = 'Camera'
        self.led_controller = LEDController()
        self.setup_camera()
        self.connect_camera()

    def setup_camera(self):
        if self.config.get('masking', False):
            cad_file = self.config['cad_file']
            with open(cad_file) as f:
                data = f.read()
            self.coord_data = json.loads(data)
            self.total_layers = len(self.coord_data)
            print(f"Total layers: {self.total_layers}")

            # Initialize MaskHandler
            image_width = self.config.get('image_width', 5472)
            image_height = self.config.get('image_height', 3648)
            self.mask_handler = MaskHandler(self.coord_data, image_width, image_height, self.pix_per_mm)
            self.mask_handler.generate_masks()

    def connect_camera(self):
        self.camera = neoapi.Cam()
        self.camera.Connect()
        if self.camera.IsConnected():
            self.camera.f.UserSetSelector.SetString('Default')
            self.camera.f.UserSetLoad.Execute()
            print("UserSetSelector:", self.camera.f.UserSetSelector.GetString())
            self.camera.f.ExposureAuto.SetString('Off')
            self.camera.f.ExposureMode.SetString('Timed')
            self.camera.f.ExposureTime.Set(self.exposure)
            print("Camera connected and configured successfully")
        else:
            raise ConnectionError("Failed to connect to the camera")

    def capture_and_save_image(self, layer):
        self.led_controller.toggle_leds(1)
        sleep(0.5)

        img = self.camera.GetImage().GetNPArray()
        timestamp = strftime("%d_%m_%y_%H_%M_%S", gmtime())

        filename = f"image_{timestamp}.bmp"
        filenamepath = self.output_path / self.data_type / filename
        filenamepath.parent.mkdir(exist_ok=True, parents=True)
        cv2.imwrite(filenamepath, img)

        self.led_controller.toggle_leds(0)
        print('Smile :)')

        if self.mask_handler:
            masked_img = self.mask_handler.apply_mask_to_image(img, layer)
            maskname = f"mask_image_{timestamp}.bmp"
            masknamepath = os.path.join(self.output_path, self.data_type, maskname)
            cv2.imwrite(masknamepath, masked_img)
            return masked_img, filenamepath
        else:
            return img, filenamepath

    def capture_image(self, layer):
        if not self.camera.IsConnected():
            raise ConnectionError("Camera is not connected")

        return self.capture_and_save_image(layer)
    def get_total_layers(self):
        return self.total_layers

    def is_correction_enabled(self):
        return self.correction == 1

# Usage example:
# config = {
#     'masking': True,
#     'cad_file': 'path/to/cad_file.txt',
#     'exposure': 200000,
#     'pix_per_mm': 56,
#     'image_width': 5472,
#     'image_height': 3648
# }
# camera_handler = CameraHandler(config, yolo_model)
# image = camera_handler.capture_image(layer=1)