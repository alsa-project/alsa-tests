#
# Suppress some false-positive condition block errors
#

SUPPRESS_IF = {
  "USB-Audio/Dell-WD15-Dock.conf@Dell-WD15-Dock-HiFi.conf: 'SectionDevice'.'Headphones'.'Value'.'If'.'Headphone_ctl'.'Condition' - True": 1,
  "USB-Audio/Dell-WD15-Dock.conf@Dell-WD15-Dock-HiFi.conf: 'SectionDevice'.'Line'.'Value'.'If'.'Line_ctl'.'Condition' - True": 1,
}

def generate_config(topdir):
    return {'suppress_if': SUPPRESS_IF}
