import oci
import base64
import torch
import numpy as np
import cv2

class InferencePipeline:
    """
    A class used to translate text using a OCI AI Vision Service.
    """
    def __init__(self, config, sam_model=None):
        self.sam_model = sam_model
        oci_config = oci.config.from_file(config.CONFIG_FILE_PATH)
        self.client = oci.ai_vision.AIServiceVisionClient(oci_config)
        self.config = config

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read())
        #encoded_image = base64.b64encode(image_path.read())
        return encoded_image
    
    def _format_output(self, output):
        objects_list = []
        for obj in output.data.image_objects:
            vertices = obj.bounding_polygon.normalized_vertices
            x_values, y_values = [v.x for v in vertices], [v.y for v in vertices]
            min_x, max_x = min(x_values), max(x_values)
            min_y, max_y = min(y_values), max(y_values)
            objects_list.append({
                "label": obj.name,
                "confidence_score": obj.confidence,
                "bbox": [min_x, min_y, max_x, max_y]
            })
        return objects_list

    def _inference_ai_vision(self, image_path):
        encoded_image = self._encode_image(image_path)

        oci_vision_detection = self.client.analyze_image(
            analyze_image_details=oci.ai_vision.models.AnalyzeImageDetails(
                features=[
                    oci.ai_vision.models.ImageObjectDetectionFeature(
                        feature_type="OBJECT_DETECTION",
                        max_results=1000000
                    ),
                ],   
                image=oci.ai_vision.models.InlineImageDetails(
                    source="INLINE",
                    data=encoded_image.decode("utf-8")),
                compartment_id=self.config.COMPARTMENT_ID),
            )

        return oci_vision_detection

    def get_detection(self, image_path):
        oci_vision_detection = self._inference_ai_vision(image_path)
        detections = self._format_output(oci_vision_detection)
        return detections
    
    def get_detections_and_masks(self, image_path):
        img = cv2.imread(image_path)
        detections = self.get_detection(image_path)
        segmentations = []

        if self.sam_model is None:
            raise Exception("Unable to prepare segmentations, SAM model is None")
        
        segmentations = []
        with torch.inference_mode(), torch.autocast("cpu"):
            self.sam_model.set_image(img)
            for detected_object in detections:
                bounding_box = detected_object["bbox"]
                name  = detected_object["label"]
                score = detected_object["confidence_score"]

                bbox = [
                    int(bounding_box[0] * img.shape[1]),
                    int(bounding_box[1] * img.shape[0]),
                    int(bounding_box[2] * img.shape[1]),
                    int(bounding_box[3] * img.shape[0]),
                ]
                masks, scores, _ = self.sam_model.predict(box=bbox)
                best_mask, best_score = sorted(zip(masks, scores), key=lambda t: t[1])[-1]
                indices = np.nonzero(best_mask)

                segmentations.append({
                    "class": name,
                    "score": score,
                    "bounding_box": bbox,
                    "mask": best_mask,
                    "mask_indices": [[int(y), int(x)] for y, x in zip(*indices)],
                    "shape": best_mask.shape,
                })
        return detections, segmentations
