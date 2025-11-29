PRAGMA foreign_keys = ON;

-- Main reports table
CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  age INTEGER,
  location TEXT,
  description TEXT,
  status TEXT,
  photo_filename TEXT,
  created_at TEXT
);

-- Sample data
INSERT INTO reports (name, age, location, description, status, created_at) VALUES
('Rohan', 10, 'Market Area', 'Wearing blue T-shirt, last seen near fruit market.', 'approved', '2025-01-10 10:30'),
('Ananya', 14, 'Bus Stand', 'School uniform, last seen at central bus stand.', 'pending', '2025-01-11 08:15');

-- New: comments on reports
CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_id INTEGER NOT NULL,
  author TEXT,
  text TEXT NOT NULL,
  is_helper INTEGER DEFAULT 0,
  created_at TEXT,
  FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
);

-- New: SOS events
CREATE TABLE IF NOT EXISTS sos_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  message TEXT,
  location_text TEXT,
  latitude REAL,
  longitude REAL,
  created_at TEXT
);
