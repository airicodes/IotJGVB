#include <WiFiUdp.h>
#include <WiFiServer.h>
#include <WiFi.h>
#include <WiFiClient.h>
#include <SPI.h>
#include <MFRC522.h>

#include <PubSubClient.h>

#include "time.h"
// The below are constants, which cannot be changed
#define LIGHT_SENSOR_PIN  32  // ESP32 pin GIOP36 (ADC0) connected to light sensor
#define LED_PIN           22  // ESP32 pin GIOP22 connected to LED
#define ANALOG_THRESHOLD  2200


//This is for the RFID
#define SS_PIN  5  // ESP32 pin GIOP5 
#define RST_PIN 27 // ESP32 pin GIOP27 
MFRC522 rfid(SS_PIN, RST_PIN);

// WiFi
const char *ssid = "vincent"; // Enter your WiFi name
const char *password = "123456789";  // Enter WiFi password

// MQTT Broker
const char *mqtt_broker = "172.20.10.8";
const char *topic = "light";
const char *topic2 = "rfid";
const char *mqtt_username = "mosquitto";
const char *mqtt_password = "";
const int mqtt_port = 1883;
const char *analogValue="";

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  // Set software serial baud to 115200;
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
  // connecting to a WiFi network
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.println("Connecting to WiFi..");
  }
  Serial.println("Connected to the WiFi network");
  //connecting to a mqtt broker
  client.setServer(mqtt_broker, mqtt_port);
  client.setCallback(callback);
  while (!client.connected()) {
      String client_id = "esp8266-client-";
      client_id += String(WiFi.macAddress());
      Serial.printf("The client %s connects to the public mqtt broker\n", client_id.c_str());
      if (client.connect(client_id.c_str(), mqtt_username, mqtt_password)) {
          Serial.println("Public emqx mqtt broker connected");
      } else {
          Serial.print("failed with state ");
          Serial.print(client.state());
          delay(2000);
      }
  }


  //This is for RFID part
   SPI.begin(); // init SPI bus
   rfid.PCD_Init(); // init MFRC522
   
  // publish and subscribe
  client.subscribe(topic);
}

void callback(char *topic, byte *payload, unsigned int length) {
//  Serial.print("Message arrived in topic: ");
//  Serial.println(topic);
//  Serial.print("Message:");
//  for (int i = 0; i < length; i++) {
//      Serial.print((char) payload[i]);
//  }
//  Serial.println();
//  Serial.println("-----------------------");
}

void loop() {
  client.loop();
  int analogValue = analogRead(LIGHT_SENSOR_PIN);
  char b[5];
  String str;
  str = String(analogValue);
  str.toCharArray(b,5);
  client.publish(topic, b); 

  String rfidValue;
 

  if (analogValue < ANALOG_THRESHOLD)
    digitalWrite(LED_PIN, HIGH); // turn on LED
  else
    digitalWrite(LED_PIN, LOW);

  //RFID part 
  if (rfid.PICC_IsNewCardPresent()) { // new tag is available
    if (rfid.PICC_ReadCardSerial()) { // NUID has been readed
      MFRC522::PICC_Type piccType = rfid.PICC_GetType(rfid.uid.sak);
      Serial.print("RFID/NFC Tag Type: ");
      Serial.println(rfid.PICC_GetTypeName(piccType));

      // print UID in Serial Monitor in the hex format
      Serial.print("UID:");
      for (int i = 0; i < rfid.uid.size; i++) {
        Serial.print(rfid.uid.uidByte[i] < 0x10 ? " 0" : " ");
        Serial.print(rfid.uid.uidByte[i], HEX);
        rfidValue.concat(String(rfid.uid.uidByte[i], HEX));
        
      }
      Serial.print(rfidValue);
      Serial.println();
      client.publish(topic2, rfidValue.c_str());
      rfid.PICC_HaltA(); // halt PICC
      rfid.PCD_StopCrypto1(); // stop encryption on PCD
    }
  }
}
