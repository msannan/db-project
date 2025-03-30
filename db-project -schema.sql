CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    FName VARCHAR(100) NOT NULL,
    LName VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    gender VARCHAR(10),
    DOB DATE
);

CREATE TABLE Creator (
    creator_id SERIAL PRIMARY KEY REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Event (
    event_id SERIAL PRIMARY KEY,
    creator_id INT REFERENCES Creator(creator_id) ON DELETE CASCADE,
    event_name VARCHAR(255) NOT NULL,
    event_place TEXT,
    event_start_date TIMESTAMP NOT NULL,
    event_end_date TIMESTAMP NOT NULL,
    deadline_enforced BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) CHECK (status IN ('Open', 'Closed', 'Cancelled'))
);

CREATE TABLE Participants (
    P_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    event_id INT REFERENCES Event(event_id) ON DELETE CASCADE
);

CREATE TABLE Eligibility_Criteria (
    criteria_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES Event(event_id) ON DELETE CASCADE,
    rule_type VARCHAR(255) NOT NULL,
    rule_value TEXT NOT NULL
);

CREATE TABLE Inputs (
    input_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES Event(event_id) ON DELETE CASCADE,
    label VARCHAR(255) NOT NULL,
    field_type VARCHAR(50) NOT NULL CHECK (field_type IN ('text', 'number', 'date', 'boolean', 'select')),
    default_value TEXT,
    validation_rules TEXT
);

CREATE TABLE Submissions (
    submission_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES Event(event_id) ON DELETE CASCADE,
    P_id INT REFERENCES Participants(P_id) ON DELETE CASCADE,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Submission_Values (
    suva_id SERIAL PRIMARY KEY,
    submission_id INT REFERENCES Submissions(submission_id) ON DELETE CASCADE,
    input_id INT REFERENCES Inputs(input_id) ON DELETE CASCADE,
    value TEXT
);

CREATE TABLE Event_Statistics (
    stat_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES Event(event_id) ON DELETE CASCADE,
    summary_type VARCHAR(255),
    public_viewable BOOLEAN DEFAULT FALSE
);

CREATE TABLE Reminders (
    reminder_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES Event(event_id) ON DELETE CASCADE,
    P_id INT REFERENCES Participants(P_id) ON DELETE CASCADE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
