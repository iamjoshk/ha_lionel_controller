# Lionel Train Controller

A Home Assistant custom integration for controlling Lionel LionChief Bluetooth locomotives.

## Features

- **Speed Control**: Use a fan entity to control train speed (0-100%)
- **Direction Control**: Switch between forward and reverse
- **Sound Effects**: Control horn, bell, and announcements  
- **Lighting**: Turn train lights on/off
- **Connection Status**: Monitor Bluetooth connection status
- **HACS Compatible**: Easy installation through HACS

## Supported Controls

### Fan Entity
- **Speed**: Variable speed control from 0-100%

### Switch Entities  
- **Lights**: Control locomotive lighting
- **Horn**: Turn horn sound on/off
- **Bell**: Turn bell sound on/off
- **Direction**: Switch between forward (on) and reverse (off)

### Button Entities
- **Stop**: Emergency stop button
- **Disconnect**: Disconnect from locomotive
- **Announcements**: Various conductor announcements
  - Random, Ready to Roll, Hey There, Squeaky
  - Water and Fire, Fastest Freight, Penna Flyer

### Binary Sensor
- **Connection**: Shows Bluetooth connection status

## Installation

### HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add `https://github.com/iamjoshk/ha_lionel_controller` as an Integration
5. Install "Lionel Train Controller"
6. Restart Home Assistant

### Manual Installation
1. Copy the `custom_components/lionel_controller` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration" 
3. Search for "Lionel Train Controller"
4. Enter your locomotive's Bluetooth MAC address
5. Optionally customize the name and service UUID
6. Click Submit

### Finding Your Train's MAC Address

You can find your locomotive's MAC address by:
1. Using a Bluetooth scanner app on your phone
2. Looking in Home Assistant Developer Tools → States for bluetooth devices
3. Using the ESPHome logs if you have the reference implementation

## Protocol Details

This integration is based on reverse-engineered Lionel LionChief Bluetooth protocol:

- **Default Service UUID**: `e20a39f4-73f5-4bc4-a12f-17d1ad07a961` (may vary by model)
- **Write Characteristic**: `08590f7e-db05-467e-8757-72f6faeb13d4`
- **Notify Characteristic**: `08590f7e-db05-467e-8757-72f6faeb14d3`

## Compatibility

- Tested with Pennsylvania Flyer locomotive
- Should work with other LionChief Bluetooth locomotives
- Requires Home Assistant 2023.8.0 or later
- Requires Python bleak 0.20.0 or later

## Troubleshooting

### Connection Issues
- Ensure locomotive is powered on and in Bluetooth pairing mode
- Check that locomotive is within Bluetooth range
- Verify MAC address is correct
- Try restarting Home Assistant

### Service UUID Issues
Different locomotive models may use different service UUIDs. If the default doesn't work:
1. Use a Bluetooth scanner to find your locomotive's service UUID
2. Reconfigure the integration with the correct UUID

## Credits

- Protocol reverse engineering by [Property404](https://github.com/Property404/lionchief-controller)
- ESPHome reference implementation by [@iamjoshk](https://github.com/iamjoshk/home-assistant-collection/tree/main/ESPHome/LionelController)

## Contributing

Issues and pull requests welcome! Please see the GitHub repository for more information.
