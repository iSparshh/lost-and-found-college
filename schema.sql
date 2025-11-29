
PRAGMA foreign_keys = ON;

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

INSERT INTO reports (name, age, location, description, status, created_at) VALUES
('Rohan', 10, 'Market Area', 'Wearing blue T-shirt, last seen near fruit market.', 'approved', '2025-01-10 10:30'),
('Ananya', 14, 'Bus Stand', 'School uniform, last seen at central bus stand.', 'pending', '2025-01-11 08:15');
