
PRAGMA foreign_keys=ON;
CREATE TABLE provenance(id TEXT PRIMARY KEY, origin_type TEXT NOT NULL, generator_model TEXT, validation_level TEXT NOT NULL, doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE concepts(id TEXT PRIMARY KEY, label TEXT NOT NULL, domain TEXT NOT NULL, doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE concept_edges(from_concept TEXT NOT NULL REFERENCES concepts(id),to_concept TEXT NOT NULL REFERENCES concepts(id),relation TEXT NOT NULL, PRIMARY KEY(from_concept,to_concept,relation));
CREATE TABLE questions(id TEXT PRIMARY KEY, family_id TEXT NOT NULL UNIQUE, domain_code TEXT NOT NULL, domain TEXT NOT NULL, stage TEXT NOT NULL, difficulty INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 5), split TEXT NOT NULL CHECK(split IN ('train','validation','synthetic_test')), stem TEXT NOT NULL, correct_answer TEXT NOT NULL, provenance_id TEXT NOT NULL REFERENCES provenance(id), doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE INDEX idx_questions_domain ON questions(domain_code,difficulty);
CREATE INDEX idx_questions_split ON questions(split);
CREATE TABLE item_concepts(item_id TEXT NOT NULL REFERENCES questions(id),concept_id TEXT NOT NULL REFERENCES concepts(id),role TEXT NOT NULL,PRIMARY KEY(item_id,concept_id));
CREATE TABLE solutions(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),status TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE error_patterns(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),category TEXT NOT NULL,signature TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE cognitive_hypotheses(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),kind TEXT NOT NULL,label TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE diagnostic_probes(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),stem TEXT NOT NULL,correct_answer TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE student_observations(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),session_id TEXT, correctness TEXT NOT NULL,source_type TEXT NOT NULL,raw_response TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE cognitive_inferences(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),student_pseudonym TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE teaching_interventions(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),action TEXT NOT NULL,message TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE teaching_sessions(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),source_type TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE learning_outcomes(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),independent_assessment INTEGER NOT NULL,causal_attribution TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE teaching_preferences(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),choice TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE all_records(id TEXT PRIMARY KEY,record_type TEXT NOT NULL,provenance_id TEXT REFERENCES provenance(id),doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE INDEX idx_allrecords_type ON all_records(record_type);
CREATE VIEW question_summary AS SELECT q.id,q.domain_code,q.stage,q.difficulty,q.split,q.stem,q.correct_answer,
 (SELECT COUNT(*) FROM error_patterns e WHERE e.item_id=q.id) AS n_errors,
 (SELECT COUNT(*) FROM diagnostic_probes p WHERE p.item_id=q.id) AS n_probes,
 (SELECT COUNT(*) FROM student_observations o WHERE o.item_id=q.id) AS n_observations,
 (SELECT COUNT(*) FROM teaching_sessions s WHERE s.item_id=q.id) AS n_sessions
 FROM questions q;
