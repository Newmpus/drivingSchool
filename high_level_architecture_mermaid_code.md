graph TD
    ClientLayer[Client Layer<br/>(Web Browser - Users)]
    ApplicationLayer[Application Layer<br/>(Django Web Framework)]
    Views[Views (Logic)]
    Models[Models (Data)]
    Templates[Templates (Presentation)]
    DataLayer[Data Layer<br/>(SQLite Database)]
    UserTables[User Tables]
    LessonTables[Lesson Tables]
    PaymentTables[Payment Tables]

    ClientLayer -->|HTTP/HTTPS| ApplicationLayer
    ApplicationLayer --> Views
    ApplicationLayer --> Models
    ApplicationLayer --> Templates
    Models --> DataLayer
    DataLayer --> UserTables
    DataLayer --> LessonTables
    DataLayer --> PaymentTables
