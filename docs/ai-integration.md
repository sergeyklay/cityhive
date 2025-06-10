# AI Integration

I'm a firm believer that anything a human doesn't have to do by hand should be automated — and that absolutely includes how we write, review and deploy code. In CityHive, AI isn't an add-on, it's woven into the very fabric of the development process:

## Cursor AI Integration

All code is composed in Cursor AI, guided by a living collection of experimental rules (found in `.cursor/rules/`). These rule files — covering everything from dependency management to project patterns — continuously evolve alongside the code, ensuring Cursor's completions stay aligned with our clean-architecture layers, type-hinting conventions and testing best practices.

## MCP (Model Context Protocol) Server

To enrich the AI's perspective, we run two [MCP](https://modelcontextprotocol.io/introduction) servers. First, [Context7 MCP Server](https://context7.com) streams curated indexes of CityHive's schemas, contracts and usage examples directly into the AI's context window. Second, our own lightweight MCP implementation (in `.cursor/postgres.py` with its `.cursor/mcp.json` manifest) provides read-only PostgreSQL access: schema inspection, query execution and data-relationship awareness — all with minimal dependencies and transparent logic. This dual setup guarantees that generated code reflects both our domain model and real database constraints without ever compromising safety.

## Code Review

Every pull request is then auto-reviewed by two LLM-powered bots. [GitHub Copilot](https://github.com/features/copilot) lays down broad-stroke suggestions — boilerplate, idioms, imports — while [CodeRabbit](https://www.coderabbit.ai/) delivers focused critiques, refactorings and policy checks. CodeRabbit's behavior is entirely driven by its code-based config (see `.coderabbit.yaml`), so tweaks can be made in-repo to refine thresholds or rules. In tandem, they elevate code quality far beyond manual review alone.

Beyond these LLM tools, CityHive leverages additional automation agents for dependency audits, test-coverage reporting, and other routine tasks. Together, they free me to focus on features and architecture instead of repetitive chores.

## Conclusion

By weaving AI rules, dynamic context servers and intelligent review bots into a single pipeline, CityHive achieves faster iteration, consistently formatted code, reliable database integrations and a continual feedback loop — all without ever leaving the IDE.

The AI integration provides a foundation for enhanced development workflows. The current setup focuses on:
- Understanding project architecture and patterns
- Providing database context for code generation
- Following established coding standards and testing practices

This creates a development environment where AI assistance is informed by the actual project structure and requirements.
