-- Supplemental extension to original MathEdu-Cog 100 schema.
-- Build after the original schema and 100-question database have been created.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS error_cases (
  case_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL UNIQUE REFERENCES questions(id),
  domain_code TEXT NOT NULL,
  stage TEXT NOT NULL,
  difficulty INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 5),
  split TEXT NOT NULL CHECK(split IN ('train','validation','synthetic_test')),
  title TEXT NOT NULL,
  error_tag TEXT NOT NULL,
  first_invalid_step INTEGER NOT NULL,
  provenance_id TEXT NOT NULL REFERENCES provenance(id),
  doc TEXT NOT NULL CHECK(json_valid(doc))
);
CREATE INDEX IF NOT EXISTS idx_error_cases_domain ON error_cases(domain_code,difficulty);
CREATE INDEX IF NOT EXISTS idx_error_cases_tag ON error_cases(error_tag);
CREATE INDEX IF NOT EXISTS idx_error_cases_split ON error_cases(split);
