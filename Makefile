rst-src:
	sphinx-apidoc -o ./docs/src ./bal
	rm ./docs/src/modules.rst

html-docs:
	sphinx-build -c docs/src/ ./docs/src ./docs/html -b html

publish: html-docs
	git checkout gh-pages
	cp -r docs/html/. .
	ls docs/html | xargs git add
	git add -u
	git commit
	git push origin gh-pages
	git checkout master
