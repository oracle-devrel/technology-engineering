import os
from PIL import Image
import numpy as np
import cv2

def load_image(uploaded_file):
    image = Image.open(uploaded_file).convert("RGB")
    return image

def save_uploaded_image(uploaded_file, save_dir):
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, uploaded_file.name)

    with open(save_path, "wb") as f:
        f.write(uploaded_file.read())
    return save_path

def draw_detections(image, detections, box_color=(0, 255, 0), text_color=(0, 0, 0), thickness=2,
                    font_scale = 0.8, font_thickness = 2):
    """
    Draws bounding boxes and labels on the image.
    """
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    height, width = image.shape[:2]

    for det in detections:
        x1 = int(det['bbox'][0] * width)
        y1 = int(det['bbox'][1] * height)
        x2 = int(det['bbox'][2] * width)
        y2 = int(det['bbox'][3] * height)
        label = det['label']
        score = det['confidence_score']

        cv2.rectangle(image, (x1, y1), (x2, y2), box_color, thickness)

        label_text = f"{label}"
        if score is not None:
            label_text += f" {score:.2f}"

        # Add label text background
        (text_width, text_height), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX,  font_scale, font_thickness)
        cv2.rectangle(image, (x1, y1 - text_height - 4), (x1 + text_width + 2, y1), box_color, -1)
        cv2.putText(image, label_text, (x1 + 1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thickness)
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    return pil_image

def draw_masks(image, mask, alpha=0.3, color=(0, 0, 255)):
    """
    Overlays binary mask onto the image.
    """
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    if mask.dtype != np.uint8:
        mask = (mask > 0).astype(np.uint8)

    colored_mask = np.zeros_like(image, dtype=np.uint8)
    colored_mask[mask == 1] = color

    image = cv2.addWeighted(colored_mask, alpha, image, 1 - alpha, 0)

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)
    return pil_image
