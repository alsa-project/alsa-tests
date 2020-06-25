#
# Suppress some false-positive condition block errors
#

SUPPRESS_IF = {
  "HDA-Intel/HDA-Intel.conf@HiFi.conf: 'If'.'acp'.'Condition' - True": 1
}

def generate_config(topdir):
    return {'suppress_if': SUPPRESS_IF}
