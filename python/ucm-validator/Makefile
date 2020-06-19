DBGCMD?=
V?=0
ALSA_UCM_DIR?=../../../alsa-ucm-conf/ucm2
#CONFIGS_FILTER=configs/cht-bsw-rt5672/Lenovo_Miix_2_10.txt
#CONFIGS_FILTER=configs/HDA/DualCodecs.json
#CONFIGS_FILTER=configs/SOF/dummy.json
#CONFIGS_FILTER=configs/chtmax98090/GOOGLE-Cyan.txt

all: verify configs
	@exit 0

.PHONY: verify
verify:
	./ucm.py --level $(V) all $(ALSA_UCM_DIR)

.PHONY: configs
configs:
	$(DBGCMD) ./ucm.py --level $(V) configs $(ALSA_UCM_DIR) configs $(CONFIGS_FILTER)
