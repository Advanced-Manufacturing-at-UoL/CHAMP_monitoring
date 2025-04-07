import numpy as np
import cv2

class CoordinateTransformer:
    def __init__(self, pix_per_mm, image_width, image_height):
        self.pix_per_mm = pix_per_mm
        self.image_width = image_width
        self.image_height = image_height

    def transform(self, x, y):
        x = np.asarray(x) * -self.pix_per_mm  # Flip X
        y = np.asarray(y) * self.pix_per_mm   # Y is already flipped
        x += self.image_width // 2   # Center X
        y += self.image_height // 2  # Center Y
        return x, y

class MaskGenerator:
    def __init__(self, transformer, image_width, image_height):
        self.transformer = transformer
        self.image_width = image_width
        self.image_height = image_height

    def generate_mask(self, coordinates, thickness):
        poly_mask = np.zeros((self.image_height, self.image_width), np.uint8)
        x, y = self.transformer.transform(coordinates['X'], coordinates['Y'])
        points = np.column_stack((x, y)).reshape((-1, 1, 2)).astype(np.int32)
        
        cv2.polylines(poly_mask, [points], isClosed=False, 
                      color=255, thickness=int(self.transformer.pix_per_mm * thickness))
        
        contours, _ = cv2.findContours(poly_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.drawContours(poly_mask, contours, -1, 255, cv2.FILLED)
        
        return poly_mask

class MaskApplicator:
    @staticmethod
    def apply_mask(image, mask, alpha=0.1):
        image = cv2.normalize(image, None, 0, 254, cv2.NORM_MINMAX)
        mask_bool = mask.astype(bool)
        out = image.copy()
        out[mask_bool] = cv2.addWeighted(image, alpha, mask, 1 - alpha, 0)[mask_bool]
        return image - out

class LayerMaskManager:
    def __init__(self, parsed_gcode, transformer, image_width, image_height):
        self.parsed_gcode = parsed_gcode
        self.transformer = transformer
        self.image_width = image_width
        self.image_height = image_height
        self.masks = {}

    def generate_all_masks(self, thickness=1.3):
        mask_gen = MaskGenerator(self.transformer, self.image_width, self.image_height)
        for layer, moves in self.parsed_gcode.items():
            coordinates = self._extract_coordinates_with_travel(moves)
            if coordinates['X'] and coordinates['Y']:  # Only generate mask if there are coordinates
                mask = mask_gen.generate_mask(coordinates, thickness)
                self.masks[layer] = mask

    def get_mask(self, layer):
        return self.masks.get(layer)

    def _extract_coordinates_with_travel(self, moves):
        x_coords = []
        y_coords = []
        last_travel_x = None
        last_travel_y = None

        for move in moves:
            if self._is_travel_move(move):
                last_travel_x = move.get('X', last_travel_x)
                last_travel_y = move.get('Y', last_travel_y)
            elif self._is_print_move(move):
                if last_travel_x is not None and last_travel_y is not None:
                    x_coords.append(last_travel_x)
                    y_coords.append(last_travel_y)
                    last_travel_x = None
                    last_travel_y = None
                
                x_coords.append(move.get('X', x_coords[-1] if x_coords else None))
                y_coords.append(move.get('Y', y_coords[-1] if y_coords else None))

        return {'X': x_coords, 'Y': y_coords}

    @staticmethod
    def _is_print_move(move):
        # Adjust this method based on how print moves are identified in your G-code
        return move.get('type') == 'print'

    @staticmethod
    def _is_travel_move(move):
        # Adjust this method based on how travel moves are identified in your G-code
        return move.get('type') == 'travel'

class MaskHandler:
    def __init__(self, parsed_gcode, image_width, image_height, pix_per_mm):
        self.transformer = CoordinateTransformer(pix_per_mm, image_width, image_height)
        self.mask_manager = LayerMaskManager(parsed_gcode, self.transformer, image_width, image_height)
        self.mask_applicator = MaskApplicator()

    def generate_masks(self, thickness=1.3):
        self.mask_manager.generate_all_masks(thickness)

    def apply_mask_to_image(self, image, layer, alpha=0.1):
        mask = self.mask_manager.get_mask(layer)
        if mask is None:
            return image  # Return original image if no mask for this layer
        return self.mask_applicator.apply_mask(image, mask, alpha)

# # Usage example
# def main():
#     # Assume parsed_gcode is a dictionary where keys are layer numbers
#     # and values are lists of move dictionaries with 'X' and 'Y' keys
#     parsed_gcode = {
#         1: [{'X': -10, 'Y':0}, {'X': 0, 'Y': 10},{'X': 10, 'Y': 0}, {'X': 0, 'Y': -10}, {'X': -10, 'Y': 0}],
#         2: [{'X': 0, 'Y': 0}, {'X': 15, 'Y': 15}, {'X': 30, 'Y': 0}]
#     }
    
#     image_width = 5472
#     image_height = 3648
#     pix_per_mm = 50  # Example value, adjust as needed

#     mask_handler = MaskHandler(parsed_gcode, image_width, image_height, pix_per_mm)
#     mask_handler.generate_masks()

#     # Simulating image capture for demonstration
#     captured_image = np.random.randint(0, 255, (image_height, image_width), dtype=np.uint8)

#     # Apply mask for layer 1
#     masked_image = mask_handler.apply_mask_to_image(captured_image, layer=1)

#     # Display or save the result
#     cv2.imwrite("masked_image.png", masked_image)

# if __name__ == "__main__":
#     main()