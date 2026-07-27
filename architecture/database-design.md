# Database Design

## Overview
The database for DataForge serves as the system of record for users, organizations, projects, pipelines, execution history, and operational events. Its purpose is to preserve the integrity of platform data while supporting reliable access, auditing, and long-term growth.

## Design Principles
- Normalization where appropriate: Organize data to reduce duplication and maintain consistency.
- Data Integrity: Preserve logical correctness across related records and lifecycle states.
- Scalability: Support growth in users, projects, workflows, and historical data.
- Auditability: Maintain sufficient records to understand who changed what and when.
- Performance: Enable efficient access to frequently used operational and user data.
- Security: Protect sensitive business and user data through controlled access and secure design boundaries.

## Core Entities

### User
- Purpose: Represents an individual user of the platform.
- Key Attributes: Identity, profile information, account status, preferences, and ownership associations.
- Relationships: A user may belong to one or more organizations, own one or more projects, and generate execution and notification records.

### Organization
- Purpose: Represents a business or team entity that groups users and resources.
- Key Attributes: Name, status, billing or subscription context, and organizational settings.
- Relationships: An organization contains users, projects, and shared assets such as pipelines and data sources.

### Project
- Purpose: Represents a logical container for related work and assets.
- Key Attributes: Name, description, ownership, status, and organizational association.
- Relationships: A project belongs to an organization and contains workspaces, pipelines, and execution records.

### Workspace
- Purpose: Represents a collaborative environment within a project for focused work.
- Key Attributes: Name, purpose, membership, and project association.
- Relationships: A workspace belongs to a project and may contain pipelines and related operational resources.

### DataSource
- Purpose: Represents an external system or service that provides input data to workflows.
- Key Attributes: Name, classification, connection metadata, ownership, and status.
- Relationships: A data source may be referenced by multiple pipelines and associated with a project or organization.

### Pipeline
- Purpose: Represents a defined workflow or processing chain.
- Key Attributes: Name, description, version, status, ownership, and project association.
- Relationships: A pipeline belongs to a project or workspace, contains pipeline nodes, and produces execution records.

### PipelineNode
- Purpose: Represents an individual step or stage within a pipeline.
- Key Attributes: Type, configuration, ordering, and logical dependencies.
- Relationships: A pipeline node belongs to a pipeline and contributes to the execution path of that pipeline.

### PipelineExecution
- Purpose: Represents a single run of a pipeline.
- Key Attributes: Run status, start time, end time, trigger source, and outcome summary.
- Relationships: A pipeline execution belongs to a pipeline and may generate logs, notifications, and audit records.

### Schedule
- Purpose: Represents a recurring or timed execution plan for a pipeline.
- Key Attributes: Frequency, timing rules, status, and association to a pipeline.
- Relationships: A schedule is linked to one pipeline and may trigger multiple executions over time.

### ExecutionLog
- Purpose: Stores detailed runtime information about pipeline execution.
- Key Attributes: Event type, timestamp, severity, and execution context.
- Relationships: An execution log belongs to a specific pipeline execution and supports observability and troubleshooting.

### Notification
- Purpose: Represents messages or alerts sent to users or teams about platform events.
- Key Attributes: Message content, channel, status, timestamp, and target audience.
- Relationships: A notification may be related to a pipeline execution, workflow event, or user action.

### APIKey
- Purpose: Represents credentials used to authenticate programmatic access or integrations.
- Key Attributes: Owner, scope, status, expiration, and associated organization or project context.
- Relationships: An API key belongs to a user or organization and is used to access platform capabilities securely.

### AuditLog
- Purpose: Records significant actions and changes made across the platform.
- Key Attributes: Actor, action, timestamp, target entity, and outcome.
- Relationships: An audit log may reference users, projects, pipelines, settings, and other entities to provide a complete change history.

## Entity Relationships
The core relationship model is centered on organizations, which own projects and shared resources. Users are associated with organizations and may participate in projects and workspaces. Pipelines and data sources are managed within projects, while pipeline executions and logs track runtime activity. Schedules define recurring execution behavior, and notifications and audit records capture operational and administrative events related to those entities.

## Indexing Strategy
Indexing should prioritize entities and relationships that are frequently queried or filtered, including:
- Users by identity, organization, and account state.
- Projects and workspaces by organization and ownership.
- Pipelines by project, status, and recent activity.
- Pipeline executions by pipeline, execution status, and time range.
- Logs by execution, severity, and timestamp.
- Notifications by recipient, status, and creation time.
- Audit logs by target entity, actor, and timestamp.

This supports responsive access to both operational dashboards and administrative views.

## Data Retention Strategy
Retention should be governed by the value and regulatory sensitivity of each data class:
- Execution logs and runtime history should be retained long enough to support monitoring, troubleshooting, and operational reporting.
- Audit records should be preserved for accountability, change tracking, and compliance-related review.
- Notifications should be retained according to relevance and user expectations, with older entries pruned or archived when appropriate.
- Historical data that is no longer active should be moved to archival storage or summarized to preserve performance while maintaining access when needed.

## Future Database Enhancements
Planned enhancements include:
- Partitioning: Improve scalability and maintenance for large historical datasets.
- Archiving: Support long-term retention of less frequently accessed records.
- Read Replicas: Improve read performance and resilience for reporting and operational workloads.
- Multi-tenancy: Strengthen logical isolation and governance for larger or more complex customer environments.
