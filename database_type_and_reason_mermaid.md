graph TD
    SQLite[SQLite]
    PostgreSQL[PostgreSQL]

    SQLite -->|Used for| Development[Development Environment]
    PostgreSQL -->|Used for| Production[Production Environment]

    Development -->|Reasons| EasySetup[Easy setup, zero configuration]
    Development --> Lightweight[Lightweight, file-based]
    Development --> Fast[Fast for small-scale apps]

    Production --> Robust[Robust, secure, reliable]
    Production --> Scalable[Scalable for large data]
    Production --> AdvancedFeatures[Supports advanced features like JSONB, replication]
