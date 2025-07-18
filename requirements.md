# Requirements Document

## Introduction

This feature creates an MCP (Model Context Protocol) tool that enables LLMs to look up information from TTRPG rulebooks and manage campaign data. The system will parse PDF rulebooks into searchable text, create vector embeddings for semantic search, and store both rulebook content and campaign data in Redis. This creates a comprehensive "side-car" assistant for Dungeon Masters and Game Runners that can quickly retrieve relevant rules, spells, monsters, and campaign information during gameplay.

## Requirements

### Requirement 1

**User Story:** As a Dungeon Master, I want to quickly look up rules, spells, and monster stats from my TTRPG rulebooks during gameplay, so that I can maintain game flow without manually searching through physical or digital books.

#### Acceptance Criteria

1. WHEN a user queries for a specific rule or game element THEN the system SHALL return relevant information from the parsed rulebook content with semantic similarity matching
2. WHEN multiple relevant results exist THEN the system SHALL rank results by relevance and return the top matches with source page references
3. WHEN tabular data (like stat blocks or spell tables) is queried THEN the system SHALL preserve and return the structured format of the original content
4. IF a query matches content from multiple rulebooks THEN the system SHALL clearly identify which source each result comes from

### Requirement 2

**User Story:** As a Game Runner, I want to store and retrieve campaign-specific data (characters, NPCs, locations, plot points), so that I can maintain continuity and quickly access relevant information during sessions.

#### Acceptance Criteria

1. WHEN campaign data is stored THEN the system SHALL organize it by campaign identifier and data type (characters, NPCs, locations, etc.)
2. WHEN querying campaign data THEN the system SHALL support both exact matches and semantic search across stored content
3. WHEN updating campaign data THEN the system SHALL maintain version history and allow rollback to previous states
4. IF campaign data references rulebook content THEN the system SHALL create linkages between campaign elements and relevant rules

### Requirement 3

**User Story:** As a developer or advanced user, I want to easily add new rulebooks to the system, so that I can expand the knowledge base without technical complexity.

#### Acceptance Criteria

1. WHEN a PDF rulebook is provided THEN the system SHALL extract text content while preserving structure and formatting
2. WHEN processing a rulebook THEN the system SHALL use the book's glossary/index to create meaningful content chunks and metadata
3. WHEN text extraction encounters tables or complex layouts THEN the system SHALL attempt to preserve the tabular structure in a searchable format
4. IF a rulebook has already been processed THEN the system SHALL detect duplicates and offer options to update or skip

### Requirement 4

**User Story:** As an LLM or AI assistant, I want to access TTRPG information through standardized MCP tools, so that I can provide accurate and contextual responses about game rules and campaign data.

#### Acceptance Criteria

1. WHEN the MCP server receives a search request THEN it SHALL return structured data including content, source, page numbers, and relevance scores
2. WHEN multiple search types are needed THEN the system SHALL support both vector similarity search and traditional keyword search
3. WHEN campaign context is relevant THEN the system SHALL cross-reference rulebook content with stored campaign data
4. IF search results are ambiguous THEN the system SHALL provide clarifying context and suggest refinement options

### Requirement 5

**User Story:** As a user sharing the tool with my gaming group, I want the system to be accessible to non-developers, so that other players and GMs can benefit from the tool without technical setup.

#### Acceptance Criteria

1. WHEN the system is deployed THEN it SHALL provide clear documentation for non-technical users to access campaign data features
2. WHEN users interact with campaign data THEN the system SHALL provide intuitive commands that don't require Redis knowledge
3. WHEN sharing campaign data THEN the system SHALL support export/import functionality for easy distribution
4. IF users need to configure the system THEN it SHALL provide sensible defaults and clear configuration options

### Requirement 6

**User Story:** As a system administrator, I want the tool to efficiently handle large rulebook collections and concurrent users, so that performance remains acceptable during active gaming sessions.

#### Acceptance Criteria

1. WHEN processing large PDF files THEN the system SHALL handle memory efficiently and provide progress feedback
2. WHEN multiple users query simultaneously THEN the system SHALL maintain response times under 2 seconds for typical queries
3. WHEN storing vector embeddings THEN the system SHALL optimize for both storage efficiency and query speed
4. IF the Redis database grows large THEN the system SHALL provide maintenance tools for cleanup and optimization