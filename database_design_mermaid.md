erDiagram
    USER {
        INTEGER id PK "Primary Key"
        STRING username "Unique"
        STRING email "Unique"
        STRING password
        STRING first_name
        STRING last_name
        STRING phone
        STRING address
        STRING role "student, tutor, admin"
        BOOLEAN is_approved
        BOOLEAN is_invited
        STRING invitation_code
        BOOLEAN payment_verified
        STRING payment_proof
        STRING payment_status "pending, approved, rejected"
        DATETIME payment_submitted_at
        DATETIME payment_approved_at
        STRING profile_picture
    }

    LESSON {
        INTEGER id PK "Primary Key"
        DATE date
        TIME start_time
        TIME end_time
        STRING location
        DATETIME created_at
        DATETIME updated_at
    }

    NOTIFICATION {
        INTEGER id PK "Primary Key"
        STRING message
        BOOLEAN is_read
        DATETIME created_at
    }

    USER ||--o{ LESSON : "student_lessons"
    USER ||--o{ LESSON : "tutor_lessons"
    USER ||--o{ NOTIFICATION : "user_notifications"
```

```mermaid
classDiagram
    class User {
        +int id
        +string username
        +string email
        +string password
        +string first_name
        +string last_name
        +string phone
        +string address
        +string role
        +bool is_approved
        +bool is_invited
        +string invitation_code
        +bool payment_verified
        +string payment_proof
        +string payment_status
        +datetime payment_submitted_at
        +datetime payment_approved_at
        +string profile_picture
        +can_access_services()
    }

    class Lesson {
        +int id
        +date date
        +time start_time
        +time end_time
        +string location
        +datetime created_at
        +datetime updated_at
        +get_duration()
    }

    class Notification {
        +int id
        +string message
        +bool is_read
        +datetime created_at
    }

    User "1" -- "many" Lesson : student_lessons
    User "1" -- "many" Lesson : tutor_lessons
    User "1" -- "many" Notification : user_notifications
