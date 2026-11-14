# Database Schema (ER Diagram)

Render this with any Mermaid viewer (GitHub renders it automatically).

```mermaid
erDiagram
    ROLES ||--o{ USERS : "has"
    USERS ||--o{ PROJECTS : "owns"
    USERS ||--o{ PROJECT_MEMBERS : "joins"
    PROJECTS ||--o{ PROJECT_MEMBERS : "has"
    PROJECTS ||--o{ TASKS : "contains"
    USERS ||--o{ TASKS : "assigned / created / updated"
    TASKS ||--o{ TASK_COMMENTS : "has"
    USERS ||--o{ TASK_COMMENTS : "writes"
    USERS ||--o{ ACTIVITY_LOGS : "performs"
    PROJECTS ||--o{ ACTIVITY_LOGS : "about"
    TASKS ||--o{ ACTIVITY_LOGS : "about"

    ROLES {
        int id PK
        string name UK
        string description
        json permissions
    }
    USERS {
        int id PK
        string email UK
        string username UK
        string full_name
        string hashed_password
        bool is_active
        int role_id FK
        datetime created_at
        datetime updated_at
    }
    PROJECTS {
        int id PK
        string name
        text description
        date start_date
        date end_date
        int owner_id FK
        datetime created_at
        datetime updated_at
    }
    PROJECT_MEMBERS {
        int project_id PK, FK
        int user_id PK, FK
        datetime joined_at
    }
    TASKS {
        int id PK
        string title
        text description
        string status "todo|in_progress|review|completed"
        string priority "low|medium|high|critical"
        date due_date
        int project_id FK
        int assignee_id FK
        int created_by_id FK
        int updated_by_id FK
        datetime created_at
        datetime updated_at
    }
    TASK_COMMENTS {
        int id PK
        int task_id FK
        int user_id FK
        text content
        datetime created_at
    }
    ACTIVITY_LOGS {
        int id PK
        int user_id FK
        int project_id FK
        int task_id FK
        string entity_type
        int entity_id
        string action
        json details
        datetime created_at
    }
```

**Delete behaviour:** deleting a project cascades to its members, tasks and comments;
activity logs are kept (their `project_id` / `task_id` become NULL), so history survives.
Users are deactivated, never deleted.
