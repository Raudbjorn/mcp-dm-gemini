# Requirements Document

## Introduction

This feature creates an MCP (Model Context Protocol) tool that enables LLMs to look up information from TTRPG rulebooks and manage campaign data. The system will parse PDF rulebooks into searchable text, create vector embeddings for semantic search, and store both rulebook content and campaign data in Redis. This creates a comprehensive "side-car" assistant for Dungeon Masters and Game Runners that can quickly retrieve relevant rules, spells, monsters, and campaign information during gameplay.

## Requirements

### Requirement 1

**User Story:** As a Dungeon Master, I want to quickly look up rules, spells, and monster stats from my TTRPG rulebooks during gameplay, so that I can maintain game flow without manually searching through physical or digital books.

#### Acceptance Criteria

1. WHEN a user queries for a specific rule or game element THEN the system SHALL return relevant information from the parsed rulebook content with semantic similarity matching
2. WHEN multiple relevant results exist THEN the system SHALL rank results by relevance and return the top matches with source page references
3. IF a query matches content from multiple rulebooks THEN the system SHALL clearly identify which source each result comes from

### Requirement 2

**User Story:** As a Game Runner, I want to store and retrieve campaign-specific data (characters, NPCs, locations, plot points), so that I can maintain continuity and quickly access relevant information during sessions.

#### Acceptance Criteria

1. WHEN campaign data is stored THEN the system SHALL organize it by campaign identifier and data type (characters, NPCs, locations, etc.)
2. WHEN querying campaign data THEN the system SHALL support both exact matches and semantic search across stored content
3. WHEN updating campaign data THEN the system SHALL maintain version history and allow rollback to previous states
4. IF campaign data references rulebook content THEN the system SHALL create linkages between campaign elements and relevant rules

### Requirement 3

**User Story:** As a developer or advanced user, I want to easily add new source material to the system, so that I can expand the knowledge base without technical complexity.

#### Acceptance Criteria

1. WHEN a PDF source is provided THEN the system SHALL extract text content while preserving structure and formatting
2. WHEN processing a source THEN the system SHALL use the book's glossary/index to create meaningful content chunks and metadata
3. IF a source has already been processed THEN the system SHALL detect duplicates and offer options to update or skip
4. WHEN adding a source THEN the user SHALL be able to specify whether it is a "rulebook" or "flavor" source.

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
5. WHEN a user wants to run the application in a container THEN the system SHALL provide a Dockerfile and Docker Compose file.
6. WHEN a user wants to contribute to the project THEN the system SHALL provide a CI/CD pipeline for automated testing.

### Requirement 6

**User Story:** As a system administrator, I want the tool to efficiently handle large rulebook collections and concurrent users, so that performance remains acceptable during active gaming sessions.

#### Acceptance Criteria

1. WHEN processing large PDF files THEN the system SHALL handle memory efficiently and provide progress feedback
2. WHEN multiple users query simultaneously THEN the system SHALL maintain response times under 2 seconds for typical queries
3. WHEN storing vector embeddings THEN the system SHALL optimize for both storage efficiency and query speed
4. IF the Redis database grows large THEN the system SHALL provide maintenance tools for cleanup and optimization

### Requirement 7

**User Story:** As a user, I want the LLM to adopt a personality that is appropriate for the game system I am using, so that the interaction feels more immersive.

#### Acceptance Criteria

1. WHEN a source is imported THEN the system SHALL extract a "personality" from the text.
2. WHEN a user interacts with the LLM THEN the system SHALL use the personality of the relevant source to configure the LLM's voice and style.

### Requirement 8

**User Story:** As a player, I want to create a character for a new campaign, so that I can start playing the game.

#### Acceptance Criteria

1. WHEN a user wants to create a character THEN the system SHALL provide the character creation rules from the relevant rulebook.
2. WHEN a user wants to create a backstory for their character THEN the system SHALL generate a backstory that is consistent with the rulebook's "vibe" and any details the player provides.

### Requirement 9

**User Story:** As a Game Master, I want to generate NPCs for my campaign, so that I can quickly populate the world with interesting characters.

#### Acceptance Criteria

1. WHEN a user wants to generate an NPC THEN the system SHALL create an NPC with stats that are appropriate for the player characters' level.
2. WHEN a user wants to generate an NPC THEN the system SHALL use the rulebook's "vibe" to create a character that is consistent with the game world.

### Requirement 10

**User Story:** As a Game Master, I want to manage my game sessions, so that I can keep track of initiative, monster health, and session notes.

#### Acceptance Criteria

1. WHEN a user wants to start a new session THEN the system SHALL create a new session with an empty initiative tracker, monster list, and notes.
2. WHEN a user wants to add a note to the session THEN the system SHALL add the note to the session's notes.
3. WHEN a user wants to set the initiative order THEN the system SHALL set the initiative order for the session.
4. WHEN a user wants to add a monster to the session THEN the system SHALL add the monster to the session's monster list.
5. WHEN a user wants to update a monster's health THEN the system SHALL update the monster's health in the session's monster list.
6. WHEN a user wants to view the session data THEN the system SHALL display the session's notes, initiative order, and monster list.

### Requirement 11

**User Story:** As a user, I want to add non-rulebook source material to the system, so that I can enhance the narrative and immersive aspects of the game.

#### Acceptance Criteria

1. WHEN a user adds a new source THEN they SHALL be able to specify whether it is a "rulebook" or a "flavor" source.
2. WHEN a user generates a character backstory or an NPC THEN the system SHALL use the "flavor" sources to inform the generation process.
3. WHEN a user searches for information THEN they SHALL be able to filter the results by source type.

### Requirement 12

**User Story:** As a Game Master, I want to generate a map for a combat encounter, so that I can quickly create a visual aid for my players.

#### Acceptance Criteria

1. WHEN a user wants to generate a map THEN the system SHALL create a simple SVG map with a grid.
2. WHEN a user wants to generate a map THEN the system SHALL use the rulebook's "vibe" to influence the style of the map.
3. WHEN a user wants to generate a map THEN the system SHALL allow the user to specify the dimensions of the map.
4. WHEN a user wants to generate a map THEN the system SHALL allow the user to provide a description of the map to be generated.
