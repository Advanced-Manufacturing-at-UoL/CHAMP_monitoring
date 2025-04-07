import yaml
import time
import digitalio as IO
import board
import logging
import neopixel_spi as neo

logger = logging.getLogger(__name__)

class GPIOManager:
    def __init__(
            self
        ):
        self.load_in = IO.DigitalInOut(board.C0) 
        self.load_in.direction = IO.Direction.INPUT
        #Laser start input
        self.laser_in = IO.DigitalInOut(board.C1)
        self.laser_in.direction = IO.Direction.INPUT
        #Save laser
        self.save_in = IO.DigitalInOut(board.C2)
        self.save_in.direction = IO.Direction.INPUT
        #spare digital input
        self.exit_in = IO.DigitalInOut(board.C3)
        self.exit_in.direction = IO.Direction.INPUT
        #Cancel output 6/rewind
        self.rewind_in = IO.DigitalInOut(board.C4)
        self.rewind_in.direction = IO.Direction.INPUT
        #take photo
        self.photo_in = IO.DigitalInOut(board.C5) 
        self.photo_in.direction = IO.Direction.INPUT
        ####################################
        #OUTPUTS FROM PYTHON (inputs Mach4)
        #spare output signal
        self.spare = IO.DigitalInOut(board.D4)
        self.spare.direction = IO.Direction.OUTPUT
        #overextrusion signal
        self.planarize = IO.DigitalInOut(board.D5)
        self.planarize.direction = IO.Direction.OUTPUT
        #underextrusion signal
        self.rework = IO.DigitalInOut(board.D6)
        self.rework.direction = IO.Direction.OUTPUT
        #loop exit
        self.continue_print = IO.DigitalInOut(board.D7)
        self.continue_print.direction = IO.Direction.OUTPUT

        #initialize output values
        logger.debug("class GpIO calling sleep for 100ms")
        time.sleep(0.1)

        self.planarize.value = 0
        self.rework.value = 0
        self.continue_print.value = 0
        self.spare.value = 0

    def should_capture_image(self) -> bool:
        return self.photo_in.value

    def should_exit(self) -> bool:
        return self.exit_in.value

    def signal_planarize(self):
        self.planarize.value = 1

    def signal_rework(self):
        self.rework.value = 1
    
    def cleanup(self):
        print("We should have some cleanup tasks here")

class LEDController:
    def __init__(self, num_pixels=24, pixel_order=neo.GRB):
        self.num_pixels = num_pixels
        self.pixel_order = pixel_order
        self.pixels = None
        self.setup_leds()

    def setup_leds(self):
        spi = board.SPI()
        self.pixels = neo.NeoPixel_SPI(
            spi, 
            self.num_pixels,
            pixel_order=self.pixel_order, 
            auto_write=True
        )
        self.pixels.fill((0, 0, 0))  # Initialize all LEDs to off

    def toggle_leds(self, state):
        if state:
            self.pixels.fill((255, 255, 255))  # Turn on all LEDs (white)
        else:
            self.pixels.fill((0, 0, 0))  # Turn off all LEDs

    def set_color(self, color):
        self.pixels.fill(color)

    def cleanup(self):
        if self.pixels:
            self.pixels.deinit()

# Usage example:
# led_controller = LEDController()
# led_controller.toggle_leds(True)  # Turn on LEDs
# led_controller.toggle_leds(False)  # Turn off LEDs
# led_controller.set_color((255, 0, 0))  # Set all LEDs to red
# led_controller.cleanup()  # Clean up when done


def load_config(path):
    with open(path) as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)