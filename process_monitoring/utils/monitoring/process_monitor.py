import time
from utils.data_processing.gcode_parser import GCodeParser
from utils.data_processing.mask_handler import MaskHandler
from utils.monitoring.camera_handler import CameraHandler
from utils.monitoring.yolo_inference import YOLOInference
from utils.interfaces import LEDController
from utils.interfaces import GPIOManager
from datetime import datetime as dt
from pathlib import Path
import json

class ProcessMonitor:
    def __init__(self, config):
        self.config = config
        self.part_name = config.get("part_name", "unknown_part")
        self.output_path: Path = (
            Path.home() /
            config.get("output_path", ".") /
            dt.now().date().strftime("%Y-%m-%d") /
            (self.part_name + dt.now().strftime("_%H_%M"))
        )
        self.output_path.mkdir(exist_ok=True, parents=True)
        self.gcode_parser = GCodeParser()
        self.mask_handler = MaskHandler(**config['mask_handler'])
        self.camera_handler = CameraHandler(config=config['camera'], output_path=self.output_path)
        self.yolo_inference = YOLOInference(config['yolo'], output_path=self.output_path)
        self.led_controller = LEDController()
        self.gpio_manager = GPIOManager()
        self.defect_summaries = []
        self.current_layer = 0
        self.running = False


    def setup(self):
        # Initialize and setup components
        self.gcode_parser.parse_file(self.config['gcode_file'])
        self.mask_handler.generate_masks()
        # Add any other necessary setup steps

    def run(self):
        self.running = True
        while self.running:
            if self.gpio_manager.should_capture_image():
                self.process_layer()

            if self.gpio_manager.should_exit():
                print("GPIO manager says we should exit")
                self.running = False

            time.sleep(0.01)  

    def process_layer(self):
        self.led_controller.toggle_leds(True)
        image, filepath = self.camera_handler.capture_image(self.current_layer)
        self.led_controller.toggle_leds(False)

        results, plotted_img = self.yolo_inference.predict(image, filepath=filepath)
        defects, updated_layer, planarize, rework = self.yolo_inference.process_results(
            results, self.current_layer, filepath.name
        )

        self.handle_corrections(planarize, rework)
        self.current_layer = updated_layer
        self.defect_summaries.append(defects)
        # Save results, update logs, etc.

    def handle_corrections(self, planarize, rework):
        if planarize:
            self.gpio_manager.signal_planarize()
        elif rework:
            self.gpio_manager.signal_rework()

    def cleanup(self):
        # Perform any necessary cleanup
        self.led_controller.cleanup()
        self.gpio_manager.cleanup()
        with open(self.output_path / f"{self.part_name}_defects.json", "w+") as f:
            f.write(json.dumps(self.defect_summaries, indent=4))
