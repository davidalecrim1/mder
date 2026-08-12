.PHONY: ci test lint smoke security validate-skill install-dev

# Mirrors the locally-reproducible jobs in .github/workflows/ci.yml.
ci: lint test smoke security validate-skill

install-dev:
	pip install pytest ruff bandit

test:
	pytest tests/ -q

lint:
	ruff check --select E9,F --target-version py310 mder/ scripts/ tests/ tools/

smoke:
	@set -eu; \
	mkdir -p sample; \
	printf '# Backpressure\n\nChapter 1\nBounded queues prevent overload.\n' > sample/note.md; \
	export MDER_WORKDIR="$${TMPDIR:-/tmp}/mder_smoke"; \
	python3 scripts/extract.py sample/note.md --mode text --install-missing no; \
	test -f "$$MDER_WORKDIR/full_text.txt"; \
	test -f "$$MDER_WORKDIR/metadata.json"; \
	grep -q "Backpressure" "$$MDER_WORKDIR/full_text.txt"

security:
	bandit -q -r mder scripts tools --severity-level high --confidence-level medium

validate-skill:
	python3 tools/validate_skill.py SKILL.md
