SHELL=/bin/bash

WORKING_DIR_ := $(shell cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
WORKING_DIR = $(shell printf "%q\n" "${WORKING_DIR_}")

COLLECTION_SCOPE := mwallraf
COLLECTION_NAME := ekinops

ANSIBLE_FOLDER := ~/.ansible/collections/ansible_collections
DESTINATION_COLLECTION_FOLDER := ${ANSIBLE_FOLDER}/${COLLECTION_SCOPE}


.PHONY: init clean show test build

init:
	mkdir -p ${DESTINATION_COLLECTION_FOLDER}
	ln -s ${WORKING_DIR}/ansible_collections/${COLLECTION_SCOPE}/${COLLECTION_NAME} ${DESTINATION_COLLECTION_FOLDER}/${COLLECTION_NAME}

clean:
	rm -rf ${DESTINATION_COLLECTION_FOLDER}

test:
	cd ansible_collections/mwallraf/ekinops && ansible-test units

show:
	ls -ald ${ANSIBLE_FOLDER}/*
	@echo working dir: ${WORKING_DIR}

build:
	cd ansible_collections/mwallraf/ekinops && ansible-galaxy collection build
