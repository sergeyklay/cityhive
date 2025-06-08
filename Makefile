include defaults.mk

# Extract package name from directory path
PKG_DIR := $(notdir $(CURDIR))

.PHONY: test
test:
	@echo $(CS)Running all tests for package: $(PKG_DIR)$(CE)
	uv run --frozen coverage erase
	uv run --frozen coverage run -m pytest -v ./tests
	@echo

.PHONY: test-unit
test-unit:
	@echo $(CS)Running unit tests for package: $(PKG_DIR)$(CE)
	uv run --frozen coverage erase
	uv run --frozen coverage run -m pytest -v ./tests/unit
	@echo

.PHONY: test-integration
test-integration:
	@echo $(CS)Running integration tests for package: $(PKG_DIR)$(CE)
	uv run --frozen coverage run -m pytest -v ./tests/integration -m integration
	@echo

.PHONY: ccov
ccov:
	@echo $(CS)Combine coverage reports for package: $(PKG_DIR)$(CE)
	uv run --frozen coverage combine
ifneq ($(CI_ENV),1)
	uv run --frozen coverage report
	uv run --frozen coverage html
else
	uv run --frozen coverage xml
endif
	@echo

.PHONY: format
format:
	@echo $(CS)Formatting code for package: $(PKG_DIR)$(CE)
	uv run --frozen ruff check --select I --fix ./
	uv run --frozen ruff format --target-version py312 ./
	@echo

.PHONY: format-check
format-check:
	@echo $(CS)Checking formatting for package: $(PKG_DIR)$(CE)
	uv run --frozen ruff format --diff --target-version py312 ./
	@echo

.PHONY: lint
lint:
	@echo $(CS)Running linters for package: $(PKG_DIR)$(CE)
	uv run --frozen ruff check --target-version py312 ./
	@echo

.PHONY: clean
clean:
	@echo $(CS)Remove build and tests artefacts and directories$(CE)
	find ./ -name '__pycache__' -delete -o -name '*.pyc' -delete
	$(RM) -r ./.pytest_cache
	$(RM) -r ./coverage
	@echo

.PHONY: migrate
migrate:
	@echo $(CS)Running migrations for $(PKG_DIR)$(CE)
	uv run --frozen alembic --raiseerr upgrade head
	@echo $(CS)Migrations completed successfully$(CE)
	@echo
