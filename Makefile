# Makefile for the Slang specification.

#SHELL := /bin/bash

.PHONY: all clean spec watch

spec: index.html

all: spec

clean:
	rm -f index.html

index.html: index.bs *.md
	bikeshed spec

watch:
	bikeshed --die-on everything --die-when early watch
