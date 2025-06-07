# Common variables and utilities for all makefiles

SHELL := $(shell which bash)

ifndef VERBOSE
MAKEFLAGS += --no-print-directory
endif

# Terminal color support detection and configuration
# Check if we're in a CI environment (GitHub Actions)
CI_ENV := $(if $(GITHUB_ACTIONS),1,$(if $(CI),1,0))

# Only use tput if we have a valid TERM and not in CI
COLORIZE := $(shell if [ -n "$$TERM" ] && [ "$$TERM" != "dumb" ] && [ "$(CI_ENV)" != "1" ]; then command -v tput >/dev/null 2>&1 && echo 1 || echo 0; else echo 0; fi)

ifeq ($(COLORIZE),1)
	# Regular colors
	BLACK        := $(shell tput setaf 0)
	RED          := $(shell tput setaf 1)
	GREEN        := $(shell tput setaf 2)
	YELLOW       := $(shell tput setaf 3)
	BLUE         := $(shell tput setaf 4)
	MAGENTA      := $(shell tput setaf 5)
	CYAN         := $(shell tput setaf 6)
	WHITE        := $(shell tput setaf 7)

	# Bold colors
	BOLD         := $(shell tput bold)
	BOLD_GREEN   := $(BOLD)$(GREEN)
	BOLD_YELLOW  := $(BOLD)$(YELLOW)
	BOLD_BLUE    := $(BOLD)$(BLUE)
	BOLD_MAGENTA := $(BOLD)$(MAGENTA)

	# Special
	RESET        := $(shell tput sgr0)

	# Composite styles for different types of content
	TITLE        := $(BOLD_BLUE)
	SECTION      := $(BOLD_MAGENTA)
	TARGET       := $(BOLD_GREEN)
	DESCRIPTION  := $(WHITE)
	EXAMPLE      := $(BOLD_YELLOW)

	CS = "${GREEN}~~~ "
	CE = " ~~~${RESET}"
else
	# No color support
	BLACK := YELLOW := RED := GREEN := BLUE := MAGENTA := CYAN := WHITE := \
	BOLD := BOLD_GREEN := BOLD_YELLOW := BOLD_BLUE := BOLD_MAGENTA := \
	RESET := TITLE := SECTION := TARGET := DESCRIPTION := EXAMPLE :=

	CS = "~~~ "
	CE = " ~~~"
endif
