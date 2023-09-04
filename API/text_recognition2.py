import matplotlib.pyplot as plt
import base64
import cv2
import imutils
import numpy as np
import pytesseract
import text_recognition

pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"

def text_recognition_pytesseract(name='license_plate_to_recognize.jpg'):
    
    img = cv2.imread(name)
    img = cv2.resize(img, (600,400))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
    gray = cv2.bilateralFilter(gray, 13, 15, 15) 

    edged = cv2.Canny(gray, 30, 200) 
    contours = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    contours = sorted(contours, key = cv2.contourArea, reverse = True)[:10]
    screenCnt = None

    for c in contours:
        
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.018 * peri, True)
    
        if len(approx) == 4:
            screenCnt = approx
            break

    if screenCnt is None:
        detected = 0
        print ("No contour detected")
    else:
        detected = 1

    if detected == 1:
        cv2.drawContours(img, [screenCnt], -1, (0, 0, 255), 3)
    
    cv2.imwrite('newimage.jpg', img)

    mask = np.zeros(gray.shape,np.uint8)
    #new_image = cv2.drawContours(mask,[screenCnt],0,255,-1,)
    #new_image = cv2.bitwise_and(img,img,mask=mask)

    (x, y) = np.where(mask == 255)

    if len(x) >0 and  len(y) >0 :
        (topx, topy) = (np.min(x), np.min(y))
        (bottomx, bottomy) = (np.max(x), np.max(y))
        Cropped = gray[topx:bottomx+1, topy:bottomy+1]
        text = pytesseract.image_to_string(Cropped, config= r'--psm 11 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        return text
    else:
        return "No license plate found"

def recognize_license_plate_pytesseract(image_base64):

    try:
        text_recognition.save_image(image_base64)
        return text_recognition_pytesseract()
    
    except Exception as e:
        return "Error processing image"