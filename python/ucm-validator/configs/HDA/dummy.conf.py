#
# Suppress some false-positive condition block errors
#

SUPPRESS_IF = {
  "HDA-Intel/HDA-Intel.conf@HiFi.conf: 'If'.'acp'.'Condition' - True": 1,
  "HDA-Intel/HDA-Intel.conf@HiFi.conf: 'If'.'hdmi'.'True'.'Include'.'hdmi'.'If'.'hdmi4'.'True'.'Include'.'hdmi4'.'If'.'hdmi'.'Condition' - True": 1,
  "HDA-Intel/HDA-Intel.conf@HiFi.conf: 'If'.'hdmi'.'True'.'Include'.'hdmi'.'If'.'hdmi5'.'True'.'Include'.'hdmi5'.'If'.'hdmi'.'Condition' - True": 1,
  "HDA-Intel/HDA-Intel.conf@HiFi.conf: 'If'.'hdmi'.'True'.'Include'.'hdmi'.'If'.'hdmi6'.'True'.'Include'.'hdmi5'.'If'.'hdmi'.'Condition' - True": 1,

}

def generate_config(topdir):
    return {'suppress_if': SUPPRESS_IF}
