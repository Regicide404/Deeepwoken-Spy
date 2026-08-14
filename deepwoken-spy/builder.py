import os

src_dir = r"C:\Users\march\.gemini\antigravity\scratch\deepwoken-spy\src"
mqtt_file = os.path.join(src_dir, "mqttws31.min.js")
main_file = os.path.join(src_dir, "main.js")

with open(mqtt_file, "r", encoding="utf-8") as f:
    mqtt_code = f.read()

with open(main_file, "r", encoding="utf-8") as f:
    main_code = f.read()

# Prepend Paho library at the top of main.js if not already there
if "Paho.MQTT=" not in main_code:
    combined = mqtt_code + "\n\n" + main_code
    with open(main_file, "w", encoding="utf-8") as f:
        f.write(combined)
    print("Embedded Paho MQTT library at top of main.js! Total length:", len(combined))
else:
    print("Paho MQTT already embedded in main.js!")
