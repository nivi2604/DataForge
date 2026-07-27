# API Design

## Purpose
The API layer exists to provide a consistent and secure way for clients to communicate with DataForge. It enables users, integrations, and internal services to interact with platform capabilities such as project management, pipeline operations, execution status, and notifications through a well-defined interface.

## API Design Principles
- RESTful APIs: APIs should follow resource-oriented conventions and predictable interaction patterns.
- Stateless Communication: Each request should carry the information needed to be understood independently.
- Consistent Resource Naming: Resources should be named clearly and used consistently across the platform.
- Versioning: APIs should evolve without breaking existing integrations.
- Security First: Authentication, authorization, and data protection should be built into the interface design.
- Standardized Responses: Clients should receive predictable structures for both success and failure states.
- Idempotency where applicable: Safe retries should not create duplicate side effects when appropriate.

## Base URL

/api/v1

## Authentication
Authentication should provide secure access to protected resources while supporting future extensibility. The platform should support:
- JWT Access Token: Used for short-lived access to protected endpoints.
- Refresh Token: Used to obtain new access tokens without requiring full re-authentication.
- OAuth (Future): For delegated authentication with external identity providers.
- API Keys (Future): For machine-to-machine access and integration scenarios.

## Resource Naming Convention
Resources should be represented using clear, pluralized names that reflect the domain model. Example resources include:

- /users
- /projects
- /workspaces
- /data-sources
- /pipelines
- /pipeline-executions
- /schedules
- /notifications
- /audit-logs

## Standard Request Format
Requests should be structured consistently using:
- Request Body: Used for create and update operations where payload content is required.
- Path Parameters: Used to identify a specific resource.
- Query Parameters: Used for filtering, pagination, and sorting.
- Headers: Used for authentication, content type, and optional metadata.

## Standard Response Format

Success

{
  "success": true,
  "message": "Operation completed successfully.",
  "data": {}
}

Error

{
  "success": false,
  "message": "Validation failed.",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": []
  }
}

## HTTP Status Codes
The API should use standard HTTP status codes to communicate results clearly:
- 200: Request completed successfully.
- 201: Resource created successfully.
- 204: Request completed successfully with no response body.
- 400: Bad request or invalid input.
- 401: Authentication required or invalid credentials.
- 403: Permission denied.
- 404: Resource not found.
- 409: Conflict with the current state of the resource.
- 422: Request could not be processed due to validation issues.
- 429: Too many requests.
- 500: Unexpected server error.

## Pagination
Pagination should be supported for list endpoints using query parameters such as page and pageSize. Responses should include metadata including totalItems and totalPages so clients can navigate result sets predictably.

## Filtering
Filtering should be supported through query parameters to allow clients to narrow result sets based on relevant fields such as status, owner, date range, or category.

## Sorting
Sorting should be supported through query parameters using clear direction indicators for ascending and descending order. This allows clients to present results in a consistent and predictable way.

## API Versioning
API versioning should be handled through the URL structure to preserve compatibility as the platform evolves. The current version should be exposed as:

/api/v1

## Rate Limiting
Rate limiting should be applied to protect platform availability and ensure fair usage across clients. It helps reduce abuse, prevent overload, and maintain service quality during high-volume periods.

## Error Handling
Errors should be returned in a consistent format with a clear message, error code, and supporting details. This allows clients to handle failures predictably and improves overall reliability and troubleshooting.

## Security Considerations
- HTTPS: All API traffic should be transmitted over secure channels.
- JWT Validation: Access tokens should be verified for authenticity and expiry.
- Input Validation: Requests should be validated before processing to prevent malformed or unsafe data.
- Output Sanitization: Responses should avoid exposing unintended sensitive information.
- Audit Logging: Security-relevant API activity should be recorded for review.
- Rate Limiting: Requests should be controlled to reduce abuse and protect service integrity.

## API Endpoints

### Authentication

#### POST /auth/register
- Purpose: Register a new user account.
- Authentication Required: No
- Request: Registration details such as name, email, and password.
- Response: Created account details and confirmation message.

#### POST /auth/login
- Purpose: Authenticate a user and issue an access token.
- Authentication Required: No
- Request: Email and password.
- Response: Authentication result, access token, and refresh token information.

#### POST /auth/logout
- Purpose: End the current authenticated session.
- Authentication Required: Yes
- Request: Session or token context.
- Response: Confirmation that the session ended successfully.

#### POST /auth/refresh
- Purpose: Refresh an access token using a valid refresh token.
- Authentication Required: No
- Request: Refresh token.
- Response: New access token details.

#### GET /auth/me
- Purpose: Retrieve the current authenticated user profile.
- Authentication Required: Yes
- Request: Authenticated session context.
- Response: Current user profile and account information.

### Users

#### GET /users
- Purpose: Retrieve a list of users within the authorized context.
- Authentication Required: Yes
- Request: Optional filters and pagination parameters.
- Response: Collection of user records with pagination metadata.

#### GET /users/{id}
- Purpose: Retrieve a specific user by identifier.
- Authentication Required: Yes
- Request: User identifier in the path.
- Response: User details for the specified record.

#### PUT /users/{id}
- Purpose: Update a user profile or account settings.
- Authentication Required: Yes
- Request: Updated user information.
- Response: Updated user record.

#### DELETE /users/{id}
- Purpose: Remove or deactivate a user account.
- Authentication Required: Yes
- Request: User identifier in the path.
- Response: Confirmation of account removal or deactivation.

### Organizations

#### GET /organizations
- Purpose: Retrieve organizations available to the current user.
- Authentication Required: Yes
- Request: Optional filters and pagination parameters.
- Response: Collection of organization records.

#### POST /organizations
- Purpose: Create a new organization.
- Authentication Required: Yes
- Request: Organization name, description, and ownership details.
- Response: Newly created organization record.

#### GET /organizations/{id}
- Purpose: Retrieve a specific organization.
- Authentication Required: Yes
- Request: Organization identifier in the path.
- Response: Organization details.

#### PUT /organizations/{id}
- Purpose: Update an existing organization.
- Authentication Required: Yes
- Request: Updated organization information.
- Response: Updated organization record.

#### DELETE /organizations/{id}
- Purpose: Delete or deactivate an organization.
- Authentication Required: Yes
- Request: Organization identifier in the path.
- Response: Confirmation of organization removal or deactivation.

### Workspaces

#### GET /workspaces
- Purpose: Retrieve workspaces available to the current user.
- Authentication Required: Yes
- Request: Optional filters and pagination parameters.
- Response: Collection of workspace records.

#### POST /workspaces
- Purpose: Create a new workspace.
- Authentication Required: Yes
- Request: Workspace name, description, and organization context.
- Response: Newly created workspace record.

#### GET /workspaces/{id}
- Purpose: Retrieve a specific workspace.
- Authentication Required: Yes
- Request: Workspace identifier in the path.
- Response: Workspace details.

#### PUT /workspaces/{id}
- Purpose: Update an existing workspace.
- Authentication Required: Yes
- Request: Updated workspace information.
- Response: Updated workspace record.

#### DELETE /workspaces/{id}
- Purpose: Delete a workspace.
- Authentication Required: Yes
- Request: Workspace identifier in the path.
- Response: Confirmation of workspace deletion.

### Projects

#### GET /projects
- Purpose: Retrieve projects available to the current user.
- Authentication Required: Yes
- Request: Optional filters and pagination parameters.
- Response: Collection of project records.

#### POST /projects
- Purpose: Create a new project.
- Authentication Required: Yes
- Request: Project name, description, and workspace context.
- Response: Newly created project record.

#### GET /projects/{id}
- Purpose: Retrieve a specific project.
- Authentication Required: Yes
- Request: Project identifier in the path.
- Response: Project details.

#### PUT /projects/{id}
- Purpose: Update an existing project.
- Authentication Required: Yes
- Request: Updated project information.
- Response: Updated project record.

#### DELETE /projects/{id}
- Purpose: Delete a project.
- Authentication Required: Yes
- Request: Project identifier in the path.
- Response: Confirmation of project deletion.

### Data Sources

#### GET /data-sources
- Purpose: Retrieve data sources available to the current project or user.
- Authentication Required: Yes
- Request: Optional filters and pagination parameters.
- Response: Collection of data source records.

#### POST /data-sources
- Purpose: Create a new data source definition.
- Authentication Required: Yes
- Request: Data source name, type, and connection details.
- Response: Newly created data source record.

#### GET /data-sources/{id}
- Purpose: Retrieve a specific data source.
- Authentication Required: Yes
- Request: Data source identifier in the path.
- Response: Data source details.

#### PUT /data-sources/{id}
- Purpose: Update an existing data source.
- Authentication Required: Yes
- Request: Updated connection or metadata details.
- Response: Updated data source record.

#### DELETE /data-sources/{id}
- Purpose: Delete a data source.
- Authentication Required: Yes
- Request: Data source identifier in the path.
- Response: Confirmation of data source deletion.

#### POST /data-sources/{id}/test-connection
- Purpose: Validate the connectivity of a configured data source.
- Authentication Required: Yes
- Request: Data source identifier in the path.
- Response: Connection test result and status.

### Pipelines

#### GET /pipelines
- Purpose: Retrieve pipelines available to the current project or user.
- Authentication Required: Yes
- Request: Optional filters and pagination parameters.
- Response: Collection of pipeline records.

#### POST /pipelines
- Purpose: Create a new pipeline definition.
- Authentication Required: Yes
- Request: Pipeline name, description, and initial configuration.
- Response: Newly created pipeline record.

#### GET /pipelines/{id}
- Purpose: Retrieve a specific pipeline.
- Authentication Required: Yes
- Request: Pipeline identifier in the path.
- Response: Pipeline details.

#### PUT /pipelines/{id}
- Purpose: Update an existing pipeline.
- Authentication Required: Yes
- Request: Updated pipeline definition.
- Response: Updated pipeline record.

#### DELETE /pipelines/{id}
- Purpose: Delete a pipeline.
- Authentication Required: Yes
- Request: Pipeline identifier in the path.
- Response: Confirmation of pipeline deletion.

### Pipeline Executions

#### POST /pipelines/{id}/execute
- Purpose: Trigger execution of a pipeline.
- Authentication Required: Yes
- Request: Pipeline identifier in the path and optional execution parameters.
- Response: Execution initiation details and status.

#### GET /executions
- Purpose: Retrieve execution history for the authorized context.
- Authentication Required: Yes
- Request: Optional filters and pagination parameters.
- Response: Collection of execution records.

#### GET /executions/{id}
- Purpose: Retrieve a specific pipeline execution.
- Authentication Required: Yes
- Request: Execution identifier in the path.
- Response: Execution details and related status information.

#### POST /executions/{id}/cancel
- Purpose: Request cancellation of an active execution.
- Authentication Required: Yes
- Request: Execution identifier in the path.
- Response: Cancellation request result.

### Schedules

#### GET /schedules
- Purpose: Retrieve schedules for accessible pipelines.
- Authentication Required: Yes
- Request: Optional filters and pagination parameters.
- Response: Collection of schedule records.

#### POST /schedules
- Purpose: Create a new schedule.
- Authentication Required: Yes
- Request: Pipeline association and schedule definition.
- Response: Newly created schedule record.

#### PUT /schedules/{id}
- Purpose: Update an existing schedule.
- Authentication Required: Yes
- Request: Updated schedule details.
- Response: Updated schedule record.

#### DELETE /schedules/{id}
- Purpose: Remove a schedule.
- Authentication Required: Yes
- Request: Schedule identifier in the path.
- Response: Confirmation of schedule deletion.

### Notifications

#### GET /notifications
- Purpose: Retrieve notifications for the current user.
- Authentication Required: Yes
- Request: Optional filters and pagination parameters.
- Response: Collection of notification records.

#### PUT /notifications/{id}/read
- Purpose: Mark a notification as read.
- Authentication Required: Yes
- Request: Notification identifier in the path.
- Response: Updated notification status.

### Health

#### GET /health
- Purpose: Check the availability of the platform API.
- Authentication Required: No
- Request: No request body.
- Response: Service health status.

## Future Improvements
- GraphQL
- WebSockets
- Public Developer API
- SDKs
- API Gateway
