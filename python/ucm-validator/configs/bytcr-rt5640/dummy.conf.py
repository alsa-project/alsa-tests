#
# Suppress some false-positive condition block errors
#

SUPPRESS_IF = {
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'mono'.'True'.'Include'.'mspk'.'SectionDevice'.'Speaker'.'Value'.'If'.'MonoSpkAif1'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'mono'.'True'.'Include'.'mspk'.'SectionDevice'.'Speaker'.'Value'.'If'.'MonoSpkAif2'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'hp'.'True'.'Include'.'hs'.'SectionDevice'.'Headphones'.'Value'.'If'.'HpAif1'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'hp'.'True'.'Include'.'hs'.'SectionDevice'.'Headphones'.'Value'.'If'.'HpAif2'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'dmic1'.'True'.'Include'.'dmic'.'SectionDevice'.'Mic'.'Value'.'If'.'DmicAif1'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'dmic1'.'True'.'Include'.'dmic'.'SectionDevice'.'Mic'.'Value'.'If'.'DmicAif2'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'hsmic'.'True'.'Include'.'hsmic'.'SectionDevice'.'Headset'.'Value'.'If'.'HSmicAif1'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'hsmic'.'True'.'Include'.'hsmic'.'SectionDevice'.'Headset'.'Value'.'If'.'HSmicAif2'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'spk'.'True'.'Include'.'spk'.'SectionDevice'.'Speaker'.'Value'.'If'.'SpkAif1'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'spk'.'True'.'Include'.'spk'.'SectionDevice'.'Speaker'.'Value'.'If'.'SpkAif2'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'in1'.'True'.'Include'.'mic1'.'SectionDevice'.'Mic'.'Value'.'If'.'In1Aif1'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'in1'.'True'.'Include'.'mic1'.'SectionDevice'.'Mic'.'Value'.'If'.'In1Aif2'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'in3'.'True'.'Include'.'mic3'.'SectionDevice'.'Mic'.'Value'.'If'.'In3Aif1'.'Condition' - False": 1,
    "bytcr-rt5640/bytcr-rt5640.conf@HiFi.conf: 'If'.'0'.'False'.'Include'.'long'.'If'.'in3'.'True'.'Include'.'mic3'.'SectionDevice'.'Mic'.'Value'.'If'.'In3Aif2'.'Condition' - False": 1,
}

def generate_config(topdir):
    return {'suppress_if': SUPPRESS_IF}
