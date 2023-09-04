import threading
from time import sleep
import cv2 #opencv
import urllib.request
import numpy as np
import text_recognition
from concurrent.futures import ThreadPoolExecutor
import firebase
executor = ThreadPoolExecutor(max_workers=5)
license_plates = []
accuracys = []
requests = 0
lock = threading.Lock()

def validate_url(url):
    try:
        # Open the URL
        with urllib.request.urlopen(url) as response:
            # Check if the response code is 200 (HTTP OK)
            if response.getcode() == 200:
                return True, "URL is accessible!"
            else:
                return False, f"Got HTTP response code {response.getcode()}"
    except urllib.error.HTTPError as e:
        # Return HTTP error code
        return False, f"HTTP error: {e.code} - {e.reason}"
    except urllib.error.URLError as e:
        # Return error reason
        return False, f"Failed to reach the server. Reason: {e.reason}"
    except Exception as e:
        return False, str(e)

#PROGRAMA DE CLASIFICACION DE OBJETOS PARA VIDEO EN DIRECCION IP 
def recognition_vehicle(ip):
    global requests

    url = ip+'cam-mid.jpg' #URL de la imagen
    url_sensor = ip+'status-sensor' #URL de la imagen

    valid_connection = False

    while not valid_connection:
        valid_connection, message = validate_url(url)
        if not valid_connection:
            print(message)
            sleep(1)

    winName = 'ESP32 CAMERA'
    cv2.namedWindow(winName,cv2.WINDOW_AUTOSIZE)
    #scale_percent = 80 # percent of original size    #para procesamiento de imagen

    classNames = []
    classFile = 'model-vehicle/coco.names'
    with open(classFile,'rt') as f:
        classNames = f.read().rstrip('\n').split('\n')

    configPath = 'model-vehicle/ssd_mobilenet_v3.pbtxt'
    weightsPath = 'model-vehicle/frozen_inference_graph.pb'

    net = cv2.dnn_DetectionModel(weightsPath,configPath)
    net.setInputSize(320,320)
    #et.setInputSize(480,480)
    net.setInputScale(1.0/127.5)
    net.setInputMean((127.5, 127.5, 127.5))
    net.setInputSwapRB(True)

    while(1):

        imgResponse = urllib.request.urlopen(url) #abrimos el URL
        sensorResponse = urllib.request.urlopen(url_sensor).read().decode('utf-8') #abrimos el URL

        imgNp = np.array(bytearray(imgResponse.read()),dtype=np.uint8)
        img = cv2.imdecode (imgNp,-1) #decodificamos
        
        #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #black and white
        
        classIds, confs, bbox = net.detect(img,confThreshold=0.5)

        vehicles = ["car", "truck", "bus", "motorcycle", "bicycle"]
        
        if len(classIds) != 0:

            for classId, confidence,box in zip(classIds.flatten(),confs.flatten(),bbox):
                
                if (classNames[classId-1] in vehicles):
                    name = "vehicle"
                    cv2.imwrite('license_plate_to_recognize.jpg', img)

                else:
                    name = "no-vehicle"

                if (name == "vehicle" and sensorResponse == "1" and requests < 5) :
                    requests += 1
                    future = executor.submit(text_recognition.text_recognition_Darknet)
                    future.add_done_callback(callback_future)
                    
                cv2.rectangle(img,box,color=(0,255,0),thickness = 3) #mostramos en rectangulo lo que se encuentra
                cv2.putText(img, name, (box[0]+10,box[1]+30), cv2.FONT_HERSHEY_COMPLEX, 1, (0,255,0),2)

        cv2.imshow(winName,img) # mostramos la imagen

        # #esperamos a que se presione ESC para terminar el programa
        tecla = cv2.waitKey(5) & 0xFF
        if tecla == 27:
            break
    cv2.destroyAllWindows() #cerramos las ventanas al presionar ESC


def callback_future(future):

    with lock:
        global license_plates, accuracys, requests

        if future.result() == "Not found license plate" or future.result() == "Error processing image":
            requests -= 1
            return
        
        license_plate = future.result()[0]
        accuracy = future.result()[1]

        if len(license_plate) < 5:
            requests -= 1
            return
        
        license_plates.append(license_plate)
        accuracys.append(accuracy)

        if len(license_plates) == 3:
            license_plate_correct = license_plates[np.argmax(accuracys)]

            print("License plate", license_plates)
            print("Accuracy", accuracys)

            response = firebase.send_data_to_firebase(license_plate_correct)

            if response["status"] == "success":
                print("Data sent to Firebase: ", license_plate_correct)
                license_plates, accuracys = [], []
                requests = 0
            else:
                print("Error sending data to Firebase: ", response["message"])
                license_plates, accuracys = [], []
                requests = 0

