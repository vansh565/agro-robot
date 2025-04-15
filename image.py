from flask import Flask, request, jsonify
import google.generativeai as genai
import base64
from io import BytesIO
from PIL import Image
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# 🔐 Gemini API Key
genai.configure(api_key="AIzaSyB2TvHIt8HsoiKuURmb7jme5IvF1JbBXF8")  # Replace with your actual key

def read_all_farm_data():
    farm_files = ["plant_fertilizer.xlsx", "irrigation_schedule.xlsx", "pesticide_recommendations.xlsx"]
    all_items = []

    for file in farm_files:
        try:
            df = pd.read_excel(file)
            if "Item Name" in df.columns and "Details" in df.columns:
                df["Category"] = file.replace(".xlsx", "").replace("_", " ").title()
                items = df.to_dict(orient="records")
                all_items.extend(items)
            else:
                print(f"⚠️ Missing required columns in {file}")
        except Exception as e:
            print(f"❌ Error reading {file}: {e}")

    return all_items

@app.route('/analyze_frame', methods=['POST'])
def analyze_frame():
    try:
        image_list = request.json.get("images", [])
        if not image_list:
            return jsonify({"error": "No image data received"}), 400

        location = request.json.get("location", {})
        latitude = location.get("latitude")
        longitude = location.get("longitude")

        location_text = ""
        if latitude and longitude:
            location_text = f"\n\nGPS Coordinates: Latitude {latitude}, Longitude {longitude}."

        model = genai.GenerativeModel("gemini-1.5-flash")
        all_results = []

        for idx, image_data in enumerate(image_list):
            try:
                image_bytes = base64.b64decode(image_data.split(",")[1])
                image = Image.open(BytesIO(image_bytes))

                prompt = f"""
You are an expert AI agriculture advisor helping a farmer by analyzing field or any plant conditions from the image.

Tasks:
1. Identify the type of plants or crops visible.
2. Detect dryness, pest attack, discoloration, or other signs of stress.
 Recommend eco-friendly pesticides and their benefits.
3. Recommend if  pesticide, or fertilizer is needed. Mention quantity for crop benefit.
4. Analyze the soil color and surface cracks to estimate soil moisture in percentage.
5. Suggest ideal soil moisture percentage range for the detected plant to stay healthy.
6. Recommend eco-friendly pesticides too and their benefits.
7. Suggest eco-friendly ways to control pest attacks.

 give all the above ND Keep it short and simple — max 2 OR 3 lines. Speak in friendly language a farmer can easily understand. Avoid use of special characters.

{location_text}
"""

                response = model.generate_content([image, prompt])
                result = response.text if response.text else "No analysis returned."
                all_results.append(f"Image {idx+1}: {result.strip()}")

            except Exception as img_error:
                all_results.append(f"Image {idx+1}: Error analyzing image - {img_error}")

        final_response = "\n".join(all_results)
        return jsonify({"response": final_response})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/gemini', methods=['POST'])
def gemini_equipment_query():
    try:
        data = request.json
        query = data.get("query", "")

        items = read_all_farm_data()

        if not items:
            return jsonify({"response": "No farming data found to process your query."})

        equipment_list = ""
        for item in items:
            name = item.get("Item Name", "Unknown")
            details = item.get("Details", "No details")
            moisture = item.get("Ideal Moisture %", "Unknown")
            category = item.get("Category", "Unknown Data")
            equipment_list += f"- {name}: {details} (Ideal Moisture: {moisture}%) in {category}\n"

        prompt = f"""
You are an AI assistant helping farmers with agriculture advice.
The user asked: "{query}"

Here is crop and soil data from the system:
{equipment_list}

Answer the query briefly in friendly tone. Focus on practical steps farmers can take.
"""

        model = genai.GenerativeModel("gemini-2.0-pro")
        response = model.generate_content(prompt)
        result = response.text if response.text else "No response generated."

        return jsonify({"response": result})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
