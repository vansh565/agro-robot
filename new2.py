# import edge_tts
# import asyncio
# import nest_asyncio
# import requests
# import base64
# import os
# import speech_recognition as sr
# import google.generativeai as genai
# import firebase_admin
# from firebase_admin import credentials, firestore
# import socketio
# from time import time
# import subprocess
# import re

# nest_asyncio.apply()

# # ------------------ 🔊 Edge TTS ------------------
# async def edge_speak(text):
#     if not text.strip():
#         return
#     output_folder = "audio_output"
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
#     audio_file = os.path.join(output_folder, f"temp_audio_{int(time() * 1000)}.mp3")
#     communicate = edge_tts.Communicate(text=text, voice="en-US-GuyNeural")
#     await communicate.save(audio_file)
#     subprocess.Popen(["start", audio_file], shell=True)
#     await asyncio.sleep(1)

# def speak(text):
#     if not text.strip():
#         return
#     print("🤖 Assistant:", text)
#     sio.emit("assistant_reply", {"reply": text})
#     try:
#         asyncio.run(edge_speak(text))
#     except RuntimeError:
#         loop = asyncio.get_event_loop()
#         loop.run_until_complete(edge_speak(text))

# # ------------------ 🔐 Gemini + Firebase ------------------
# genai.configure(api_key="AIzaSyD2eKhcIIS33G7uuvjA3VkI93bun_aELvQ")
# cred = credentials.Certificate("serviceAccountKey.json")
# firebase_admin.initialize_app(cred)
# db = firestore.client()

# FIRESTORE_DATA = None

# # ------------------ 🌐 Socket.IO ------------------
# sio = socketio.Client()

# @sio.event
# def connect():
#     print("✅ Connected to Socket.IO server")

# @sio.event
# def disconnect():
#     print("❌ Disconnected from Socket.IO server")

# sio.connect("https://fateh-2.onrender.com/", transports=["polling", "websocket"])

# # ------------------ 🎤 Voice Recognition ------------------
# def listen_and_caption():
#     recognizer = sr.Recognizer()
#     with sr.Microphone() as source:
#         print("🎧 Listening...")
#         recognizer.adjust_for_ambient_noise(source, duration=1)
#         audio = recognizer.listen(source, timeout=10)
#     try:
#         full_text = recognizer.recognize_google(audio).lower()
#         print("🗣 You said:", full_text)
#         return full_text
#     except sr.UnknownValueError:
#         return None
#     except sr.RequestError:
#         speak("Speech recognition error.")
#         return None

# # ------------------ ⛅ Weather ------------------
# def get_city_coordinates(city):
#     geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
#     try:
#         response = requests.get(geo_url)
#         data = response.json()
#         if "results" in data:
#             lat = data["results"][0]["latitude"]
#             lon = data["results"][0]["longitude"]
#             return lat, lon
#         else:
#             speak(f"Sorry, I couldn't find coordinates for {city}.")
#             return None, None
#     except Exception as e:
#         print("Geocoding error:", e)
#         speak("Error fetching location.")
#         return None, None

# def get_weather(city):
#     lat, lon = get_city_coordinates(city)
#     if lat is None: return
#     url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation,cloudcover"
#     try:
#         res = requests.get(url).json()
#         temp = res["current"]["temperature_2m"]
#         wind = res["current"]["wind_speed_10m"]
#         rain = res["current"]["precipitation"]
#         msg = f"Temperature in {city} is {temp}°C with wind speed {wind} km/h."
#         msg += " It is raining." if rain > 0 else " No rain."
#         speak(msg)
#     except Exception as e:
#         print("Weather fetch error:", e)
#         speak("Failed to get weather.")

# # ------------------ 📸 Image Analysis ------------------
# def encode_image_to_base64(image_path):
#     try:
#         with open(image_path, "rb") as img:
#             return "data:image/jpeg;base64," + base64.b64encode(img.read()).decode("utf-8")
#     except Exception as e:
#         print(f"Encoding error for {image_path}: {e}")
#         return None

# def send_images_to_gemini(image_folder="field_images"):
#     url = "http://localhost:5000/analyze_frame"
#     headers = {"Content-Type": "application/json"}
#     images_base64 = []

#     for filename in os.listdir(image_folder):
#         if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.avif')):
#             path = os.path.join(image_folder, filename)
#             encoded = encode_image_to_base64(path)
#             if encoded:
#                 images_base64.append(encoded)

#     if not images_base64:
#         speak("No images found.")
#         return

#     data = {"images": images_base64}
#     try:
#         response = requests.post(url, json=data, headers=headers)
#         result = response.json().get("response", "No response.")
#         speak(result)
#     except:
#         speak("Error sending images to Gemini.")

# # ------------------ 🔎 Gemini Query (Farmer Context) ------------------
# def ask_gemini_with_context(query):
#     global FIRESTORE_DATA
#     plant_detected = None
#     crop_collection = "indian_crops"

#     # Try to find a matching crop name
#     try:
#         crop_docs = [doc.to_dict() for doc in db.collection(crop_collection).stream()]
#         for crop in crop_docs:
#             if crop["Crop Name"].lower() in query:
#                 plant_detected = crop
#                 break
#     except Exception as e:
#         speak("Couldn't load crop data.")
#         print("Firestore error:", e)

#     # Construct Gemini prompt
#     if plant_detected:
#         prompt = (
#             f"You are an agriculture expert. Here is data for the crop '{plant_detected['Crop Name']}':\n"
#             f"- Water Requirement: {plant_detected['Water Requirement']}\n"
#             f"- Soil Type: {plant_detected['Soil Type']}\n"
#             f"- Fertilizer: {plant_detected['Fertilizer']}\n"
#             f"- Pesticide Suggestion: {plant_detected['Pesticide Suggestion']}\n"
#             f"- Tips for Greenery: {plant_detected['Tips for Greenery']}\n"
#             f"- Eco-Friendly Pest Management: {plant_detected['Eco-Friendly Pest Management']}\n\n"
#             f"Question: {query}\nPlease provide a clear, short response."
#         )
#     else:
#         # Fallback to general knowledge base
#         if FIRESTORE_DATA is None:
#             try:
#                 FIRESTORE_DATA = [doc.to_dict() for doc in db.collection("knowledge_base").stream()]
#             except:
#                 speak("Could not load general knowledge.")
#                 return
#         prompt = (
#             f"You are a helpful farming assistant. Based on this knowledge:\n{FIRESTORE_DATA}\n\n"
#             f"Question: {query}\nRespond clearly in simple words."
#         )

#     # Call Gemini
#     try:
#         model = genai.GenerativeModel("gemini-1.5-flash")
#         res = model.generate_content(prompt)
#         speak(res.text)
#     except Exception as e:
#         print("Gemini Error:", e)
#         speak("Could not get advice.")


# # ------------------ 🚜 Main Loop ------------------
# def main_loop():
#     speak("Fuhteh bot activated for farmers. Say 'hello' or 'start' to begin.")

#     while True:
#         command = listen_and_caption()
#         if command is None:
#             continue

#         if any(kw in command for kw in ["hello", "start", "wake up"]):
#             sio.emit("robot_wakeup")
#             speak("Hello farmer! How can I help you today?")

#             while True:
#                 command = listen_and_caption()
#                 if command is None:
#                     continue
#                 if any(kw in command for kw in ["stop", "exit", "sleep"]):
#                     speak("Goodbye farmer! Say 'hello' to start again.")
#                     break
#                 elif "analyse images" in command or "condition" in command:
#                     send_images_to_gemini()
#                 elif "weather" in command or "temperature" in command:
#                     city_match = re.search(r"in ([a-zA-Z\s]+)", command)
#                     city = city_match.group(1).strip() if city_match else "Delhi"
#                     get_weather(city)
#                 else:
#                     ask_gemini_with_context(command)

# # ------------------ ▶️ Start ------------------
# if __name__ == "__main__":
#     main_loop()
import edge_tts
import asyncio
import nest_asyncio
import requests
import base64
import os
import speech_recognition as sr
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore
import socketio
from time import time
import subprocess
import re
import random

nest_asyncio.apply()

# ------------------ 🔊 Edge TTS ------------------
async def edge_speak(text):
    if not text.strip():
        return
    output_folder = "audio_output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    audio_file = os.path.join(output_folder, f"temp_audio_{int(time() * 1000)}.mp3")
    communicate = edge_tts.Communicate(text=text, voice="en-IN-PrabhatNeural")
    await communicate.save(audio_file)
    subprocess.Popen(["start", audio_file], shell=True)
    await asyncio.sleep(1)

def speak(text):
    if not text.strip():
        return
    print("🤖 Assistant:", text)
    sio.emit("assistant_reply", {"reply": text})
    try:
        asyncio.run(edge_speak(text))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(edge_speak(text))

# ------------------ 🔐 Gemini + Firebase ------------------
genai.configure(api_key="AIzaSyD2eKhcIIS33G7uuvjA3VkI93bun_aELvQ")
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

FIRESTORE_DATA = None

# ------------------ 🌐 Socket.IO ------------------
sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connected to Socket.IO server")

@sio.event
def disconnect():
    print("❌ Disconnected from Socket.IO server")

sio.connect("https://fateh-2.onrender.com/", transports=["polling", "websocket"])

# ------------------ 🎤 Voice Recognition ------------------
def listen_and_caption():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎧 Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source, timeout=10)
    try:
        full_text = recognizer.recognize_google(audio).lower()
        print("🗣 You said:", full_text)
        return full_text
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        speak("Speech recognition error.")
        return None

# ------------------ ⛅ Weather ------------------
def get_city_coordinates(city):
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    try:
        response = requests.get(geo_url)
        data = response.json()
        if "results" in data:
            lat = data["results"][0]["latitude"]
            lon = data["results"][0]["longitude"]
            return lat, lon
        else:
            speak(f"Sorry, I couldn't find coordinates for {city}.")
            return None, None
    except Exception as e:
        print("Geocoding error:", e)
        speak("Error fetching location.")
        return None, None

def get_weather(city):
    lat, lon = get_city_coordinates(city)
    if lat is None: return
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,precipitation,cloudcover"
    try:
        res = requests.get(url).json()
        temp = res["current"]["temperature_2m"]
        wind = res["current"]["wind_speed_10m"]
        rain = res["current"]["precipitation"]
        msg = f"Temperature in {city} is {temp}°C with wind speed {wind} km/h."
        msg += " It is raining." if rain > 0 else " No rain."
        speak(msg)
    except Exception as e:
        print("Weather fetch error:", e)
        speak("Failed to get weather.")

# ------------------ 📸 Image Analysis ------------------
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as img:
            return "data:image/jpeg;base64," + base64.b64encode(img.read()).decode("utf-8")
    except Exception as e:
        print(f"Encoding error for {image_path}: {e}")
        return None

def send_images_to_gemini(image_folder="field_images"):
    url = "http://localhost:5000/analyze_frame"
    headers = {"Content-Type": "application/json"}
    images_base64 = []

    for filename in os.listdir(image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.avif')):
            path = os.path.join(image_folder, filename)
            encoded = encode_image_to_base64(path)
            if encoded:
                images_base64.append(encoded)

    if not images_base64:
        speak("No images found.")
        return

    data = {"images": images_base64}
    try:
        response = requests.post(url, json=data, headers=headers)
        result = response.json().get("response", "No response.")
        speak(result)
    except:
        speak("Error sending images to Gemini.")

# ------------------ 🔎 Gemini Query (Farmer Context) ------------------
def ask_gemini_with_context(query):
    global FIRESTORE_DATA
    plant_detected = None
    crop_collection = "indian_crops"

    try:
        crop_docs = [doc.to_dict() for doc in db.collection(crop_collection).stream()]
        for crop in crop_docs:
            if crop["Crop Name"].lower() in query:
                plant_detected = crop
                break
    except Exception as e:
        speak("Couldn't load crop data.")
        print("Firestore error:", e)

    if plant_detected:
        prompt = (
            f"You are an agriculture expert. Here is data for the crop '{plant_detected['Crop Name']}':\n"
            f"- Water Requirement: {plant_detected['Water Requirement']}\n"
            f"- Soil Type: {plant_detected['Soil Type']}\n"
            f"- Fertilizer: {plant_detected['Fertilizer']}\n"
            f"- Pesticide Suggestion: {plant_detected['Pesticide Suggestion']}\n"
            f"- Tips for Greenery: {plant_detected['Tips for Greenery']}\n"
            f"- Eco-Friendly Pest Management: {plant_detected['Eco-Friendly Pest Management']}\n\n"
            f"Question: {query}\nPlease provide a clear, short response."
        )
    else:
        if FIRESTORE_DATA is None:
            try:
                FIRESTORE_DATA = [doc.to_dict() for doc in db.collection("knowledge_base").stream()]
            except:
                speak("Could not load general knowledge.")
                return
        prompt = f"You are a helpful farming assistant. Based on this knowledge:\n{FIRESTORE_DATA}\n\nQuestion: {query}\nRespond clearly in simple words in hindi language."

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(prompt)
        speak(res.text)
    except Exception as e:
        print("Gemini Error:", e)
        speak("Could not get advice.")

# ------------------ 🌱 Crop-specific Data ------------------
def ask_crop_specific_data(query):
    crop_collection = "indian_crops"
    crop_docs = [doc.to_dict() for doc in db.collection(crop_collection).stream()]

    matched_crop = None
    for crop in crop_docs:
        if crop["Crop Name"].lower() in query:
            matched_crop = crop
            break

    if not matched_crop:
        speak("Sorry, I couldn't find crop data.")
        return

    if "soil" in query:
        speak(f"{matched_crop['Crop Name']} needs soil type: {matched_crop['Soil Type']}")
    elif "water" in query:
        speak(f"{matched_crop['Crop Name']} needs water level: {matched_crop['Water Requirement']}")
    elif "pesticide" in query:
        speak(f"Suggested pesticide for {matched_crop['Crop Name']}: {matched_crop['Pesticide Suggestion']}")
    else:
        speak(f"Here is what I found for {matched_crop['Crop Name']}: {matched_crop}")

# ------------------ 🌾 Suggest Crops by Region or Season ------------------
def suggest_crops_by_region_or_season(query):
    crop_docs = [doc.to_dict() for doc in db.collection("indian_crops").stream()]
    suggested = []

    if "summer" in query:
        suggested = [crop["Crop Name"] for crop in crop_docs if "summer" in crop.get("Season", "").lower()]
    elif "winter" in query:
        suggested = [crop["Crop Name"] for crop in crop_docs if "winter" in crop.get("Season", "").lower()]
    elif "rainy" in query or "monsoon" in query:
        suggested = [crop["Crop Name"] for crop in crop_docs if "rainy" in crop.get("Season", "").lower()]
    elif "punjab" in query:
        suggested = [crop["Crop Name"] for crop in crop_docs if "punjab" in crop.get("Region", "").lower()]
    elif "kerala" in query:
        suggested = [crop["Crop Name"] for crop in crop_docs if "kerala" in crop.get("Region", "").lower()]

    if suggested:
        speak(f"Suggested crops: {', '.join(suggested[:5])}")
    else:
        speak("No matching crops found for your region or season.")

# ------------------ 💧 Soil Moisture Sensor (Dummy) ------------------
def get_soil_moisture():
    moisture = random.randint(200, 800)  # Simulated sensor value
    if moisture < 300:
        speak(f"Soil moisture is low: {moisture}. Irrigation needed.")
    elif moisture < 600:
        speak(f"Soil moisture is optimal: {moisture}.")
    else:
        speak(f"Soil is too wet: {moisture}. Avoid overwatering.")

# ------------------ 🚜 Main Loop ------------------
def main_loop():
    speak("Vardaan bot activated for farmers. Say 'hello' or 'start' to begin.")
    while True:
        command = listen_and_caption()
        if command is None:
            continue

        if any(kw in command for kw in ["hello", "start", "wake up"]):
            sio.emit("robot_wakeup")
            speak("Hello farmer! How can I help you today?")

            while True:
                command = listen_and_caption()
                if command is None:
                    continue
                if any(kw in command for kw in ["stop", "exit", "sleep"]):
                    speak("Goodbye farmer! Say 'hello' to start again.")
                    break
                elif "analyse images" in command or "analyse" in command:
                    send_images_to_gemini()
                elif "soil for" in command or "water need for" in command or "pesticide " in command:
                    ask_crop_specific_data(command)
                elif "suggest crop" in command or "recommend crop" in command:
                    suggest_crops_by_region_or_season(command)
                elif "moisture" in command or "soil level" in command:
                    get_soil_moisture()
                elif "weather" in command or "temperature" in command:
                    city_match = re.search(r"in ([a-zA-Z\s]+)", command)
                    city = city_match.group(1).strip() if city_match else "Delhi"
                    get_weather(city)
                else:
                    ask_gemini_with_context(command)

# ------------------ ▶️ Start ------------------
if __name__ == "__main__":
    main_loop()
