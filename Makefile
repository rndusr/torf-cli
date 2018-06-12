MANPAGE_MD ?= doc/manpage.md
MANDIR ?= doc/man/man1
MANPAGE ?= $(MANDIR)/torf.1

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
	mkdir -p $(MANDIR)
	pandoc --standalone $(MANPAGE_MD) --to=man --output=$(MANPAGE)

release: manpage
	pyrelease CHANGELOG ./torfcli/_vars.py
