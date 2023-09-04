from fastapi import FastAPI, HTTPException, Body
import vehicle_recognition
import threading
import NI_recognition
import text_recognition

app = FastAPI()
ip_server = 'http://192.168.164.62/'

def start_server():
    print("Starting server")
    vehicle_recognition.recognition_vehicle(ip_server)


@app.on_event("startup")
async def startup_event():
    threading.Thread(target=start_server).start()

@app.post("/getInformationUser")
async def generate_information_by_user (data: dict = Body(...)):
    image_base64 = data.get("image", "")
    try:
        text_recognition.save_image(image_base64, "ni_to_recognize.jpg")
        data_user = NI_recognition.data_user_recognition()
        print("data_user", data_user)

        if data_user == "":
            raise HTTPException(status_code=404, detail="Information not found")
        
        if data_user == "Error processing image":
            raise HTTPException(status_code=500, detail="Error processing image")
        
        return {"name": data_user["name"], "ci": data_user["ci"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error processing image")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.164.12", port=8000)


# uvicorn main:app --host 192.168.164.12 --port 8000 --reload