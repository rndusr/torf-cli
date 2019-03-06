VENV_PATH?=venv
MANPAGE ?= docs/torf.1
MANPAGE_HTML ?= docs/torf.1.html
MANPAGE_SRC ?= docs/torf.1.asciidoc

.PHONY: clean test man release

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -rf dist
	rm -rf .pytest_cache .cache
	rm -rf $(MANDIR)
	rm -rf "$(VENV_PATH)"

venv:
	python3 -m venv "$(VENV_PATH)"
	# Docutils is needed for `setup.py check -r -s`
	"$(VENV_PATH)"/bin/pip install --upgrade pytest wheel docutils
	"$(VENV_PATH)"/bin/pip install --editable .

test: venv
	. "$(VENV_PATH)"/bin/activate ; \
	"$(VENV_PATH)"/bin/pytest --exitfirst tests

man:
	asciidoctor $(MANPAGE_SRC) -o $(MANPAGE) --doctype=manpage --backend=manpage
	asciidoctor $(MANPAGE_SRC) -o $(MANPAGE_HTML) --doctype=manpage --backend=html

release: man
	pyrelease CHANGELOG ./torfcli/_vars.py
