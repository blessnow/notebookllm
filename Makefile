.PHONY: test run smoke

test:
	pytest -q

run:
	uvicorn app.main:app --reload

smoke:
	bash scripts/smoke_test.sh
