from roboflow import Roboflow
import cv2
import keras_ocr
import text_recognition
import text_recognition2
import numpy as np

rf = Roboflow(api_key="gDrxh7UyVGRzYYWFuYvr")
project = rf.workspace().project("cdvl4_object_detection")
model = project.version(2).model

# keras-ocr will automatically download pretrained
# weights for the detector and recognizer.
pipeline = keras_ocr.pipeline.Pipeline()

# infer on a local image
def data_user_recognition():

    # infer on a local image
    prediction = model.predict("ni_to_recognize.jpg", confidence=40, overlap=30).json()
    predictions = prediction["predictions"]
    image = prediction["image"]

    if len(predictions) == 0:
        return

    img = cv2.imread('ni_to_recognize.jpg')
    for prediction in predictions:
        writeOnStream(prediction['x'], prediction['y'], prediction['width'], prediction['height'],prediction['class'],img)    

    # visualize your prediction
    model.predict("ni_to_recognize.jpg", confidence=40, overlap=30).save("prediction.jpg")

    images = [keras_ocr.tools.read("letters.jpg"), keras_ocr.tools.read("number.jpg")]

    results = text_recognition.text_recognition_Darknet('letters.jpg')
    print('letters:', results)

    results = text_recognition.text_recognition_Darknet('number.jpg')
    print('number:',results)

    results = text_recognition2.text_recognition_pytesseract('letters.jpg')
    print('letters:', results)

    results = text_recognition2.text_recognition_pytesseract('number.jpg')
    print('number:',results)

    # Get Predictions
    prediction_groups = pipeline.recognize(images)
    print(prediction_groups)

    text_predictions = []
    # Print the predictions
    for predictions in prediction_groups:
        for prediction in predictions:
           text_predictions.append(prediction[0])

    if len(text_predictions) == 5:
        name = text_predictions[0:4]
        name.reverse()
        return {"name": " ".join(name), "ci": text_predictions[4]}
    elif len(text_predictions) > 6:
        name = text_predictions[0:4]
        name.reverse()
        return {"name": " ".join(name), "ci": " ".join(text_predictions[4:-1])}
    else:
        return "Error processing image"

def writeOnStream(x, y, width, height, className, frame):
    crop_frame = frame[int(y - height / 2):int(y + height / 2), int(x - width / 2):int(x + width / 2)]

    dimensions = (crop_frame.shape[1]*5 , crop_frame.shape[0]*5)

    crop_frame = cv2.resize(crop_frame, dimensions)

    # # psf = np.ones((5, 5), np.float32) / 25
    # # deblurred = cv2.filter2D(crop_frame, -1, psf)

    # gray = cv2.cvtColor(crop_frame, cv2.COLOR_BGR2GRAY)
    # # equalized = cv2.equalizeHist(gray)
    # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    # cl1 = clahe.apply(gray)
    # denoised = cv2.GaussianBlur(cl1, (5, 5), 0)
    # kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    # crop_frame = cv2.filter2D(denoised, -1, kernel)

    cv2.imwrite(className+".jpg", crop_frame)

    # Draw a Rectangle around detected image
    cv2.rectangle(frame, (int(x - width / 2), int(y + height / 2)), (int(x + width / 2), int(y - height / 2)),
                (255, 0, 0), 2)

    # Draw filled box for class name
    cv2.rectangle(frame, (int(x - width / 2), int(y + height / 2)), (int(x + width / 2), int(y + height / 2) + 35),
                (255, 0, 0), cv2.FILLED)

    # Set label font + draw Text
    font = cv2.FONT_HERSHEY_DUPLEX

    cv2.putText(frame, className, (int(x - width / 2 + 6), int(y + height / 2 + 26)), font, 0.5, (255, 255, 255), 1)

