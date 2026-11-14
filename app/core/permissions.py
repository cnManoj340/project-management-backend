"""Default roles and their permissions. Admins can edit permissions at runtime."""
ADMIN = "admin"
PROJECT_MANAGER = "project_manager"
TEAM_MEMBER = "team_member"

DEFAULT_ROLES = {
    ADMIN: {
        "description": "Full access to every resource",
        "permissions": ["*"],
    },
    PROJECT_MANAGER: {
        "description": "Creates and manages projects, tasks and assignments",
        "permissions": [
            "user:read", "project:create", "project:read", "project:update",
            "project:delete", "task:create", "task:read", "task:update",
            "task:delete", "comment:create",
        ],
    },
    TEAM_MEMBER: {
        "description": "Works on assigned tasks",
        "permissions": ["project:read", "task:read", "task:update_status", "comment:create"],
    },
}
