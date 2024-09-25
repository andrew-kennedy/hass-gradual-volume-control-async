# hass-gradual-volume-control-async  [![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
 This integration provides a service to gradually change the volume of target mediaplayers over a given timespan
## Installation (with HACS)

1. Go to Home Assistant > HACS > Integrations > Click on tree dot (on top right corner) > Custom repositories \
and fill :
   * **Repository** :  `andrew-kennedy/hass-gradual-volume-control-async`
   * **Category** : `Integration` 

2. Click on `ADD`, restart HA.

## Installation (manual)
1. Download last release.
2. Unzip `grad_vol` folder into your HomeAssistant : `custom_components`
3. Restart HA

## Configuration

Add the integration via the integrations section of home assistant.

## Usage

Using a service-call, you can gradually change the volume to a target volume over a given timespan
For example: I want to have the volume gradually increase to 80% over 20 seconds.
The volume would be: 0.8
duration: 20
if the duration is not provided it will fall back to 5 seconds by default.

If there are multiple resolved entity targets, they will all have their volume's adjusted over the duration in parallel.

example:
``` YAML
service: grad_vol.set_volume
data:
  volume: <target volume [0.00; 1.00], required>
  duration: <timespan in seconds, optional>
target:
  entity_id: <entity_id, required>
``` 
