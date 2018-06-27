all:	fxs
#	cd ../netsim && $(MAKE) all
# Include standard NCS examples build definitions and rules
include $(NCS_DIR)/src/ncs/build/include.ncs.mk

NS  = namespaces

SRC = $(wildcard yang/*.yang)
FXS = $(SRC:yang/%.yang=ncsc-out/modules/fxs/%.fxs)
DIRS = ../load-dir
fxs:	ncsc-out/.done

$(DIRS):
	mkdir -p $@

ncsc-out/.done:	$(SRC)
	$(NCSC) --ncs-compile-bundle yang \
                 --ncs-device-dir ncsc-out   \
                 --ncs-device-type netconf \
                 --yangpath yang --yangpath ../../sharedpackage/src/yang/ \
                 --ncs-skip-template --ncs-skip-statistics && \
        cp ncsc-out/modules/fxs/*.fxs ../load-dir;
	for f in `echo ../load-dir/*.fxs`; do \
           n=`basename $$f | sed 's/\.fxs//'` || exit 1; \
        done
	touch -m ncsc-out/.done

clean:
	rm -rf ncsc-out/* ncsc-out/.done ../fxs/* ../load-dir/*
#	cd ../netsim && $(MAKE) clean || true
