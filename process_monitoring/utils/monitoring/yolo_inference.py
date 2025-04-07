import torch
from ultralytics import YOLO
import cv2
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path


class YOLOInference:
    def __init__(self, config: Dict, output_path: Path):
        self.model = YOLO(config["model_path"])
        self.model.to('cuda' if torch.cuda.is_available() else 'cpu')
        self.config = config
        self.names = self.model.names
        self.correction_enabled = config.get('correction_enabled', True)
        self.remove_underextrusions = config.get('remove_underextrusions', True)

    def predict(self, image: np.ndarray, filepath: Path) -> Tuple[List, np.ndarray]:
        output_path = filepath.parent / filepath.name.replace(".bmp", "_predictions.jpeg")
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)#yolo model takes RGB input, need to adjust later
        results = self.model.predict(image, save=False, imgsz=2048, conf=0.85)
        cv2.imwrite(output_path, results[0].plot())
        return results, results[0].plot()

    def process_results(self, results, layer: int, filename: str) -> Tuple[Dict, int, bool, bool]:
        boxes = results[0].boxes.data
        num_defects = len(boxes)
        decision = ''
        planarize = False
        rework = False

        defects = self.summarize_defects(results, layer, filename, decision)

        if num_defects > 0 and self.correction_enabled:
            over_extrusions = defects['Overextrusions']
            if over_extrusions == num_defects:
                planarize = True
                decision = 'Overextrusions, planarize layer'
            elif self.remove_underextrusions:
                rework = True
                decision = 'Underextrusions, remove and reprint layer'
        else:
            decision = 'No defects' if num_defects == 0 else 'Defects found, no correction'
            layer +=1

        defects['Decision'] = decision
        return defects, layer, planarize, rework

    def summarize_defects(self, results, layer: int, filename: str, decision: str) -> Dict:
        boxes = results[0].boxes.data
        num_defects = len(boxes)
        total_defects = []
        over_extrusions = 0
        under_extrusions = 0

        for box in results[0].boxes:
            class_id = self.names[box.cls[0].item()]
            if class_id == 'Overextrusion':
                over_extrusions += 1
            else:
                under_extrusions += 1

            cords = box.xyxy[0].tolist()
            cords = [round(x) for x in cords]
            width = cords[2] - cords[0]
            height = cords[3] - cords[1]
            aspect_ratio = width / height
            area = width * height
            conf = round(box.conf[0].item(), 2)

            defect_data = {
                "Class": class_id,
                "Confidence": conf,
                "Defect coordinates": cords,
                "Box area (px)": area,
                "Box aspect ratio": aspect_ratio
            }
            total_defects.append(defect_data)

        defect_layer = {
            "Layer number": layer,
            "Number of defects": num_defects,
            "Overextrusions": over_extrusions,
            "Underextrusions": under_extrusions,
            "Notes": decision,
            "Timestamp": filename,
            "Defect data": total_defects
        }

        return defect_layer

# Usage example:
# config = {
#     'correction_enabled': True,
#     'remove_underextrusions': True
# }
# yolo_inference = YOLOInference('path/to/model.pt', config)
# results, plotted_img = yolo_inference.predict(image)
# defects, updated_layer, planarize, rework = yolo_inference.process_results(results, current_layer, filename)