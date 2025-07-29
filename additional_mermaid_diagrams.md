%% System Inputs - Data Flow Diagram
graph TD
    UserInput[User Inputs]
    RegistrationForm[Registration Form]
    PaymentUpload[Payment Proof Upload]
    LessonBooking[Lesson Booking Form]
    AdminInput[Admin Inputs]

    UserInput --> RegistrationForm
    UserInput --> PaymentUpload
    UserInput --> LessonBooking
    UserInput --> AdminInput

%% System Processes - Flowchart
flowchart TD
    Start((Start))
    Registration[User Registration]
    Validation[Validate Input]
    AccountCreation[Create Account]
    AdminApproval[Admin Approval]
    Login[User Login]
    LessonBookingProcess[Lesson Booking]
    PaymentProcessing[Payment Processing]
    Notification[Send Notifications]
    End((End))

    Start --> Registration --> Validation --> AccountCreation --> AdminApproval --> Login
    Login --> LessonBookingProcess --> PaymentProcessing --> Notification --> End

%% System Outputs - Data Flow
graph TD
    SystemOutputs[System Outputs]
    ConfirmationPages[Confirmation Pages]
    Dashboards[Dashboards]
    Reports[Reports and Analytics]

    SystemOutputs --> ConfirmationPages
    SystemOutputs --> Dashboards
    SystemOutputs --> Reports

%% Physical Design - Deployment Diagram
graph TD
    UserBrowser[User Browser]
    WebServer[Web Server (Django)]
    AppServer[Application Server (Gunicorn)]
    DatabaseServer[Database Server (PostgreSQL/SQLite)]
    CacheServer[Cache Server (Redis)]
    Storage[Storage (Local/Cloud)]

    UserBrowser --> WebServer --> AppServer --> DatabaseServer
    AppServer --> CacheServer
    AppServer --> Storage
