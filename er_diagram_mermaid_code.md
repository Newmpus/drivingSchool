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
