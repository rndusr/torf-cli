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

test:
	python3 -m pytest --tb no tests
	python3 setup.py check -r -s >/dev/null

man:
	asciidoctor $(MANPAGE_SRC) -o $(MANPAGE) --doctype=manpage --backend=manpage
	asciidoctor $(MANPAGE_SRC) -o $(MANPAGE_HTML) --doctype=manpage --backend=html

release: manpage
	pyrelease CHANGELOG ./torfcli/_vars.py
