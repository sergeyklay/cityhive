include defaults.mk

# Extract package name from directory path
PKG_DIR := $(notdir $(CURDIR))

.PHONY: migrate
migrate:
	@echo $(CS)Running migrations for $(PKG_DIR)$(CE)
	uv run --frozen alembic --raiseerr upgrade head
	@echo $(CS)Migrations completed successfully$(CE)
	@echo
