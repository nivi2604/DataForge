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
- Attributes:
  - id
  - firstName
  - lastName
  - email
  - passwordHash
  - avatar
  - status
  - createdAt
  - updatedAt

### Organization
- Attributes:
  - id
  - name
  - description
  - ownerId
  - createdAt

### Workspace
- Attributes:
  - id
  - organizationId
  - name
  - description
  - createdAt

### Project
- Attributes:
  - id
  - workspaceId
  - name
  - description
  - status
  - createdAt

### DataSource
- Attributes:
  - id
  - projectId
  - name
  - type
  - connectionDetails
  - status
  - createdAt

### Pipeline
- Attributes:
  - id
  - projectId
  - name
  - description
  - version
  - status
  - createdAt

### PipelineNode
- Attributes:
  - id
  - pipelineId
  - type
  - configuration
  - position

### PipelineExecution
- Attributes:
  - id
  - pipelineId
  - status
  - startedAt
  - completedAt
  - duration

### Schedule
- Attributes:
  - id
  - pipelineId
  - cronExpression
  - enabled

### ExecutionLog
- Attributes:
  - id
  - executionId
  - level
  - message
  - timestamp

### Notification
- Attributes:
  - id
  - userId
  - title
  - message
  - read
  - createdAt

### APIKey
- Attributes:
  - id
  - userId
  - name
  - key
  - expiresAt

### AuditLog
- Attributes:
  - id
  - userId
  - action
  - resource
  - timestamp

## Relationships
The entities form a coherent logical model centered on organizations, workspaces, projects, and pipelines. An organization owns one or more workspaces and is associated with users through ownership and membership. Each workspace contains one or more projects, and each project contains data sources, pipelines, and related execution history. A pipeline is composed of multiple nodes and may have multiple executions, schedules, and logs. Users receive notifications, manage API access keys, and generate audit events. Pipeline executions produce execution logs, while audit records track important changes and actions across the platform.

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
