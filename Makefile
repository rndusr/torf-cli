MANPAGE_SRC ?= doc/torf.1.asciidoc
MANPAGE ?= doc/torf.1

.PHONY: clean test man release

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -rf dist
	rm -rf .pytest_cache .cache
	rm -rf $(MANDIR)

test:
	python3 -m pytest --tb no tests

man:
	asciidoctor $(MANPAGE_SRC) -o $(MANPAGE) --doctype=manpage --backend=manpage

release: manpage
	pyrelease CHANGELOG ./torfcli/_vars.py
