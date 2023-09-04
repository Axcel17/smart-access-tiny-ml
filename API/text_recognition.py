import matplotlib.pyplot as plt
import base64
import os
import util
import cv2
import easyocr
import numpy as np


# define constants
model_cfg_path = os.path.join('.', 'model', 'cfg', 'darknet-yolov3.cfg')
model_weights_path = os.path.join('.', 'model', 'weights', 'model.weights')
class_names_path = os.path.join('.', 'model', 'class.names')

license_plates = []

# load class names
with open(class_names_path, 'r') as f:
    class_names = [j[:-1] for j in f.readlines() if len(j) > 2]
    f.close()

# load model
net = cv2.dnn.readNetFromDarknet(model_cfg_path, model_weights_path)

def save_image(image_base64, name="license_plate_to_recognize.jpg"):
    # Decodificar la cadena base64
    decoded_bytes = base64.b64decode(image_base64)

    # # # Convertir bytes a array numpy
    nparr = np.frombuffer(decoded_bytes, np.uint8)

    # # # Leer imagen con OpenCV
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # # # Guardar imagen en formato jpg
    cv2.imwrite(name, img)


def text_recognition_Darknet(name='license_plate_to_recognize.jpg'):

    try:
    
        img = cv2.imread(name)

        if img is None:
            return "Error processing image"
        
        H, W, _ = img.shape

        # convert image
        blob = cv2.dnn.blobFromImage(img, 1 / 255, (416, 416), (0, 0, 0), True)

        # get detections
        net.setInput(blob)

        detections = util.get_outputs(net)

        if len(detections) == 0:
            return "Not found license plate"

        # bboxes, class_ids, confidences
        bboxes = []
        class_ids = []
        scores = []

        for detection in detections:
            # [x1, x2, x3, x4, x5, x6, ..., x85]
            bbox = detection[:4]

            xc, yc, w, h = bbox
            bbox = [int(xc * W), int(yc * H), int(w * W), int(h * H)]

            #bbox_confidence = detection[4]

            class_id = np.argmax(detection[5:])
            score = np.amax(detection[5:])

            bboxes.append(bbox)
            class_ids.append(class_id)
            scores.append(score)

        # apply nms
        bboxes, class_ids, scores = util.NMS(bboxes, class_ids, scores)

        reader = easyocr.Reader(['en', 'es', 'fr'])
        for _ , bbox in enumerate(bboxes):
            xc, yc, w, h = bbox

            license_plate = img[int(yc - (h / 2)):int(yc + (h / 2)), int(xc - (w / 2)):int(xc + (w / 2)), :].copy()

            img = cv2.rectangle(img,
                                (int(xc - (w / 2)), int(yc - (h / 2))),
                                (int(xc + (w / 2)), int(yc + (h / 2))),
                                (0, 255, 0),
                                15)
            
            if license_plate is None or license_plate.size == 0:
                return "Not found license plate"
                    
            license_plate_gray = cv2.cvtColor(license_plate, cv2.COLOR_BGR2GRAY)
            _, license_plate_thresh = cv2.threshold(license_plate_gray, 64, 255, cv2.THRESH_BINARY_INV)

            output = reader.readtext(license_plate_thresh)

            for out in output:
                _ , text, text_score = out
                print(text, text_score)
                if text_score > 0.5:
                    return text, text_score

        return "Not found license plate"
    
    except Exception as e:
        return "Error processing image"

def recognize_license_plate_Darknet(image_base64):
    save_image(image_base64)
    return text_recognition_Darknet(image_base64)