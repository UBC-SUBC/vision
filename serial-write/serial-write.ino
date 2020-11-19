#include <ArduinoJson.h>

void setup() {

}

void loop() {
    int pitch = -20;
  int yaw = -60;
  int pitchD=5;
  int yawD=5;
  Serial.begin(9600);
  DynamicJsonDocument root(1024);
  
while(1){
  if(pitch >20 || pitch <-20){
    pitchD*=-1;   
  }
  if(yaw >60 || yaw <-60){
    yawD*=-1;   
  }

  pitch+=pitchD;
  yaw += yawD;
  
  root["yaw"] = yaw;
  root["pitch"] = pitch;
  root["rpm"] = random(0,60);
  root["speed"] = random(0,5);
  root["depth"] = random(0,5);
  root["battery"] = true;
  
  serializeJson(root, Serial);
  delay(1000);
}
}
