# IoT project created by Vincent Benesen and Jeremie Guerchon

> This is an automated home system which was created using multiple IoT components (arduino, Various MCUs such as Wifi, RFID, servo motor, temperature detection, etc)

# What can it do

> Using a DHT-11, the the system will actively monitor the humidity and temperature of the room and advise the user through an email when if they wish to turn on the onboard fan. This can also be automatically configurated depending on the temperature wanted.
> The user can ask the system to turn on the fan by replying to the email.
> The system can only be accessed by the use of a RFID card which is scanned by the system and will login the user to the dashboard which contains various telemetry.
> If the room is dark, the system will automatically turn on its configurated light to lit the room it is in.

# Communication

> It is possible to communicate with the system through the use of MQTT (pub/sub).
