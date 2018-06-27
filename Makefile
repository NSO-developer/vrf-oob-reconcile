

SN_PACKAGES = vrf-service vrf-ned
DN_PACKAGES = vrf 
NEDS = cisco-iosxr

all: app-all

neds:
	for i in $(NEDS); do \
		$(MAKE) -C device-nodes/packages/$${i}/src all || exit 1; \
	done
app-all:
	for i in $(DN_PACKAGES); do \
		$(MAKE) -C device-nodes/packages/$${i}/src all || exit 1; \
	done
	for p in $(SN_PACKAGES); do\
		make -C service-node/packages/$$p/src all; \
	done
	./mk-init.sh

DIRS=device-nodes/nso-1 \
     device-nodes/nso-2 \
     service-node

clean: app-clean dev-clean
	for i in $(DN_PACKAGES); do \
		$(MAKE) -C device-nodes/packages/$${i}/src clean || exit 1; \
	done

app-clean:
	for i in $(DIRS); do \
		$(MAKE) -C $${i}  clean || exit 1; \
	done
	for i in $(DN_PACKAGES); do \
		$(MAKE) -C device-nodes/packages/$${i}/src clean || exit 1; \
	done
	for p in $(SN_PACKAGES); do \
		make -C service-node/packages/$$p/src clean; \
	done
	rm -rf netsim

ned-clean:
	for p in $(NEDS); do \
		make -C device-nodes/packages/$$p/src clean; \
	done

dev-clean:
	rm -rf device-nodes/nso-1/logs; \
	rm -rf device-nodes/nso-2/logs; \
	rm -rf device-nodes/nso-1/ncs-cdb; \
	rm -rf device-nodes/nso-2/ncs-cdb; \
	rm -rf device-nodes/nso-1/state; \
	rm -rf device-nodes/nso-2/state; \
	rm -rf service-node/ncs-cdb; \
	rm -rf service-node/state; \
	rm -rf service-node/logs; 

start stop:
	ncs-netsim $@
	make app-$@

app-start app-stop:
	for i in $(DIRS); do \
		$(MAKE) -C $${i}  $@ || exit 1; \
	done


reset status:
	@for i in $(DIRS); do \
		$(MAKE) -C $${i}  $@ || exit 1; \
	done


cli:
	cd service-node; make cli
cli-nso-1:
	cd device-nodes/nso-1; make cli
cli-nso-2:
	cd device-nodes/nso-2; make cli

#  LocalWords:  SN
