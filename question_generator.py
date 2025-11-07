"""
question_generator.py

Rule-based + classical ML hybrid question paper generator.

This updated version:
- Integrates with your backend/database fetch_syllabus/get_database layout.
- Trains/saves/loads TF-IDF + RandomForest models to models/question_model_{courseCode}.pkl
- Exposes a function generate_paper_from_db(course_code, ...) to fetch course from MongoDB
  and produce a question paper using rule-based logic + optional ML-based mark prediction.
"""

import os
import re
import json
import random
import pickle
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

# Optional NLP tools
try:
    import nltk
    from nltk.corpus import wordnet as wn
    from nltk.stem import WordNetLemmatizer
    nltk_available = True
except Exception:
    nltk_available = False

# Optional ML model
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    sklearn_available = True
except Exception:
    sklearn_available = False

# Import your DB helper (adjust path if your package layout differs)
try:
    # If this file is in /backend, and your db helpers are at /backend/database
    from database.fetch_syllabus import get_syllabus
    from database.connection import get_database
except Exception:
    # Try relative import fallback for different working directories
    try:
        from backend.database.fetch_syllabus import get_syllabus  # CI setups
        from backend.database.connection import get_database
    except Exception:
        get_syllabus = None
        get_database = None


# ---------------------------
# 1) Utility & preprocessing
# ---------------------------
def normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


if nltk_available:
    lemmatizer = WordNetLemmatizer()

    def lemmatize_text(s: str) -> str:
        return ' '.join(lemmatizer.lemmatize(w) for w in s.split())
else:
    def lemmatize_text(s: str) -> str:
        return s


def expand_with_wordnet(term: str, max_synonyms: int = 2) -> List[str]:
    if not nltk_available:
        return []
    syns = set()
    words = term.split()
    if not words:
        return []
    head = words[-1]
    for syn in wn.synsets(head):
        for lemma in syn.lemmas()[:max_synonyms]:
            name = lemma.name().replace('_', ' ')
            if name != head:
                syns.add(name)
        if len(syns) >= max_synonyms:
            break
    return list(syns)[:max_synonyms]


# ---------------------------
# 2) Complexity scoring rules
# ---------------------------
COMPLEXITY_KEYWORDS = {
    'mathematical': 3,
    'analysis': 3,
    'case': 3,
    'foundation': 3,
    'simulation': 3,
    'modeling': 3,
    'project': 3,
    'synthesis': 3,
    'design problems': 3,
    'core': 2,
    'practical': 2,
    'technique': 2,
    'techniques': 2,
    'application': 2,
    'applications': 2,
    'lab': 2,
    'laboratory': 2,
    'introduction': 1,
    'overview': 1,
    'recent advances': 1,
    'history': 1,
    'definition': 1,
}


def topic_complexity_score(topic: str) -> float:
    t = normalize_text(topic)
    score = 0.0
    for kw, w in COMPLEXITY_KEYWORDS.items():
        if kw in t:
            score += w
    token_count = len(t.split())
    score += 0.1 * token_count
    return score


def score_to_mark(score: float) -> int:
    if score < 1.5:
        return 1
    elif score < 2.5:
        return 2
    elif score < 4.0:
        return 5
    elif score < 6.0:
        return 12
    else:
        return 16


# ---------------------------
# 3) Template system
# ---------------------------
def generate_mcq(topic: str) -> str:
    """
    Generate a simple rule-based MCQ for a 1-mark question.
    """
    correct = f"It refers to {topic}."
    distractors = [
        f"It is unrelated to {topic}.",
        f"It mainly involves mathematical modeling of {topic}.",
        f"It focuses on case studies of {topic}."
    ]
    random.shuffle(distractors)
    options = distractors[:3] + [correct]
    random.shuffle(options)
    mcq_text = f"Which of the following best describes {topic}?\n"
    letters = ["A", "B", "C", "D"]
    for i, opt in enumerate(options):
        mcq_text += f"  {letters[i]}) {opt}\n"
    return mcq_text.strip()


TEMPLATES = {
    2: [
        "Briefly explain {topic}.",
        "List two applications of {topic}.",
        "Differentiate between {topic} and a related concept."
    ],
    5: [
        "Explain in detail the concept of {topic} with an example.",
        "Discuss the importance of {topic} in practical design contexts.",
        "Describe major methods used for {topic} and their merits."
    ],
    12: [
        "Discuss {topic} thoroughly; include theory, practical applications, and an example.",
        "Critically analyze the methods related to {topic}, and propose improvements.",
        "Design a small project or practical plan that demonstrates {topic} and explain its workflow."
    ],
    16: [
        "Write an extensive essay on {topic}, including background, mathematical/technical foundations, case studies and references.",
        "Create a detailed project brief based on {topic} with step-by-step justification, expected outcomes, and evaluation metrics.",
        "Formulate a complex problem related to {topic} and provide a structured solution with diagrams and calculations where applicable."
    ]
}


def render_template(mark: int, topic: str) -> str:
    if mark == 1:
        return generate_mcq(topic)
    choices = TEMPLATES.get(mark, TEMPLATES[2])
    template = random.choice(choices)
    return template.format(topic=topic)


# ---------------------------
# 4) Question generation
# ---------------------------
def generate_questions_from_topics(unit_topics: List[str],
                                   rules_to_use: List[int] = [1, 2, 5, 12, 16],
                                   per_unit_distribution: Dict[int, int] = None,
                                   use_ml_for_marks: bool = False,
                                   vect=None, clf=None) -> List[Tuple[int, str, str]]:
    """
    Generate questions for the given list of topics.
    If use_ml_for_marks is True and vect/clf provided, try to predict marks for each topic
    and then render templates according to predicted marks. Otherwise use scoring rules.
    Returns a list of tuples (mark, topic, question_text).
    """
    if per_unit_distribution is None:
        per_unit_distribution = {1: 2, 2: 2, 5: 1}

    # prepare topics and scores
    scored = [(topic, topic_complexity_score(topic)) for topic in unit_topics]
    scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)

    # if using ML, map predicted marks
    predicted_marks = {}
    if use_ml_for_marks and sklearn_available and vect is not None and clf is not None:
        for topic, _ in scored_sorted:
            try:
                mark_pred = int(clf.predict(vect.transform([topic]))[0])
                predicted_marks[topic] = mark_pred
            except Exception:
                # fallback to score-based
                predicted_marks[topic] = score_to_mark(topic_complexity_score(topic))

    generated = []
    for mark, count in per_unit_distribution.items():
        # candidate selection strategy
        if use_ml_for_marks and predicted_marks:
            candidates = [t for t, _ in scored_sorted if predicted_marks.get(t, score_to_mark(topic_complexity_score(t))) == mark]
        else:
            if mark >= 12:
                candidates = [t for t, sc in scored_sorted if score_to_mark(sc) >= 12]
            elif mark >= 5:
                candidates = [t for t, sc in scored_sorted if score_to_mark(sc) >= 5]
            elif mark == 2:
                candidates = [t for t, sc in scored_sorted if score_to_mark(sc) >= 2]
            else:
                candidates = [t for t, sc in scored_sorted if score_to_mark(sc) <= 2]

        if not candidates:
            candidates = [t for t, _ in scored_sorted]

        chosen = []
        for _ in range(count):
            remaining = [c for c in candidates if c not in chosen]
            sel = random.choice(remaining if remaining else candidates)
            chosen.append(sel)
            question_text = render_template(mark, sel)
            generated.append((mark, sel, question_text))

    generated_sorted = sorted(generated, key=lambda x: x[0])
    return generated_sorted


def generate_full_paper(course: dict,
                        unit_question_config: Dict[int, Dict[int, int]] = None,
                        use_ml_for_marks: bool = False,
                        vect=None,
                        clf=None) -> Dict:
    """
    Generate a full paper for the given course dictionary.
    course should contain keys: courseCode, title, unitNames (list), unitTopics (list-of-lists).
    unit_question_config: optional dict mapping unit_index -> per_unit_distribution dict.
    use_ml_for_marks: whether to attempt mark prediction with vect/clf.
    """
    paper = {
        "courseCode": course.get("courseCode"),
        "title": course.get("title"),
        "questions_by_unit": []
    }

    units = course.get("unitNames", [])
    unit_topics_all = course.get("unitTopics", [])

    for i, unit_name in enumerate(units):
        topics = unit_topics_all[i] if i < len(unit_topics_all) else []
        topics_clean = []
        for t in topics:
            t_norm = normalize_text(t)
            t_norm = lemmatize_text(t_norm)
            synonyms = expand_with_wordnet(t_norm) if nltk_available else []
            topics_clean.append(t_norm)
            for s in synonyms:
                topics_clean.append(f"{t_norm} ({s})")

        per_unit_dist = unit_question_config[i] if unit_question_config and i in unit_question_config else None
        questions = generate_questions_from_topics(topics_clean,
                                                  per_unit_distribution=per_unit_dist,
                                                  use_ml_for_marks=use_ml_for_marks,
                                                  vect=vect,
                                                  clf=clf)
        paper["questions_by_unit"].append({
            "unit_index": i,
            "unit_name": unit_name,
            "questions": [{"mark": m, "topic": top, "question": q} for m, top, q in questions]
        })
    return paper


# ---------------------------
# 5) ML model + pickle I/O
# ---------------------------
def create_synthetic_dataset_from_course(course: dict, examples_per_topic: int = 3) -> Tuple[List[str], List[int]]:
    texts = []
    labels = []
    all_topics = []
    for ts in course.get("unitTopics", []):
        all_topics.extend(ts)

    for t in all_topics:
        t_norm = normalize_text(t)
        base_label = score_to_mark(topic_complexity_score(t_norm))
        # create small set of variants to enrich training
        variants = [t_norm, f"introduction to {t_norm}", f"{t_norm} advanced"]
        for variant in variants[:examples_per_topic]:
            texts.append(variant)
            labels.append(base_label)
    return texts, labels


def train_classical_model(texts: List[str], labels: List[int]):
    if not sklearn_available:
        raise RuntimeError("scikit-learn not available; install it first.")
    # ensure at least two classes exist
    unique_labels = set(labels)
    if len(unique_labels) < 2:
        # create a tiny synthetic split to ensure at least two target classes
        alt_label = max(unique_labels) + 1 if unique_labels else 1
        labels.append(alt_label)
        texts.append("placeholder example for alt class")
        unique_labels = set(labels)
    vect = TfidfVectorizer(ngram_range=(1, 2), max_features=2000)
    X = vect.fit_transform(texts)
    X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)
    try:
        preds = clf.predict(X_test)
        print("\nClassification report (synthetic dataset):")
        print(classification_report(y_test, preds))
    except Exception:
        pass
    return vect, clf


def predict_with_model(vect, clf, topic: str) -> int:
    try:
        x = vect.transform([topic])
        return int(clf.predict(x)[0])
    except Exception:
        # fallback to heuristic
        return score_to_mark(topic_complexity_score(topic))


def default_model_path(course_code: str) -> str:
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)
    safe_code = re.sub(r'[^A-Za-z0-9_\-]', '_', course_code or "default")
    return os.path.join(models_dir, f"question_model_{safe_code}.pkl")


def save_model(vect, clf, filename: str):
    with open(filename, "wb") as f:
        pickle.dump((vect, clf), f)
    print(f"Model saved to {filename}")


def load_model(filename: str):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"No model file found at: {filename}")
    with open(filename, "rb") as f:
        vect, clf = pickle.load(f)
    print(f"Model loaded from {filename}")
    return vect, clf


# ---------------------------
# 6) High-level helpers integrating MongoDB
# ---------------------------
def fetch_course_from_db(course_code: str) -> Optional[dict]:
    """
    Fetch course document from MongoDB using your fetch_syllabus helper, if available.
    The expected structure: document with keys courseCode, title, unitNames, unitTopics.
    """
    if get_syllabus:
        try:
            data = get_syllabus(course_code)
            if not data:
                print(f"[fetch_course_from_db] No document for {course_code}")
                return None
            # if your DB uses different key names, adapt here
            return data
        except Exception as e:
            print(f"[fetch_course_from_db] Error fetching syllabus: {e}")
            return None
    else:
        print("[fetch_course_from_db] get_syllabus helper not found - ensure database.fetch_syllabus exists")
        return None


def ensure_model_for_course(course_code: str, course_doc: dict, force_retrain: bool = False):
    """
    Train & save model for a course if it doesn't exist or force_retrain True.
    Returns (vect, clf) or (None, None) if training not possible.
    """
    model_file = default_model_path(course_code)
    if not force_retrain and os.path.exists(model_file):
        try:
            return load_model(model_file)
        except Exception as e:
            print(f"[ensure_model_for_course] Failed to load existing model: {e} - will retrain")

    if not sklearn_available:
        print("[ensure_model_for_course] scikit-learn not available; skipping training")
        return None, None

    texts, labels = create_synthetic_dataset_from_course(course_doc)
    if not texts or not labels:
        print("[ensure_model_for_course] No training data available from course; skipping training")
        return None, None

    try:
        vect, clf = train_classical_model(texts, labels)
        save_model(vect, clf, model_file)
        return vect, clf
    except Exception as e:
        print(f"[ensure_model_for_course] Training failed: {e}")
        return None, None


def generate_paper_from_db(course_code: str,
                           unit_question_config: Dict[int, Dict[int, int]] = None,
                           use_ml: bool = True,
                           force_retrain: bool = False) -> Optional[dict]:
    """
    Top-level function:
    - fetches course from DB
    - ensures model available (optionally)
    - generates full paper (uses ML for mark prediction if requested and model exists)
    """
    course = fetch_course_from_db(course_code)
    if not course:
        print(f"[generate_paper_from_db] Course {course_code} not found in DB")
        return None

    vect, clf = None, None
    if use_ml:
        vect, clf = ensure_model_for_course(course_code, course, force_retrain=force_retrain)
        if vect is None or clf is None:
            print("[generate_paper_from_db] Model not available, falling back to rule-based generation")

    paper = generate_full_paper(course, unit_question_config=unit_question_config, use_ml_for_marks=(vect is not None and clf is not None), vect=vect, clf=clf)
    return paper


# ---------------------------
# 7) CLI quick-run (for debugging)
# ---------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", type=str, default="ARCH405B", help="Course code to fetch from DB")
    parser.add_argument("--no-ml", action="store_true", help="Disable ML and use rule-based generation")
    parser.add_argument("--retrain", action="store_true", help="Force retrain model even if saved file exists")
    args = parser.parse_args()

    if args.no_ml:
        use_ml = False
    else:
        use_ml = True

    # If DB helper not present, fallback to sample course for local testing
    if get_syllabus:
        print(f"Attempting to fetch course {args.course} from DB...")
        paper = generate_paper_from_db(args.course, use_ml=use_ml, force_retrain=args.retrain)
        if paper:
            print(json.dumps(paper, indent=2))
        else:
            print("Could not generate paper from DB. Check logs / DB connection.")
    else:
        # sample course for local offline testing
        sample_course = {
            "courseCode": "ARCH405B",
            "title": "Fundamentals of Design Studio",
            "unitNames": [
                "Unit 1: Design Studio - Design",
                "Unit 2: Design Studio - Methods",
                "Unit 3: Design Studio - Analysis",
                "Unit 4: Design Studio - Analysis",
                "Unit 5: Design Studio - Applications",
                "Unit 6: Design Studio - Design"
            ],
            "unitTopics": [
                ["Design Studio - Laboratory Work", "Design Studio - Introduction", "Design Studio - Recent Advances"],
                ["Design Studio - Introduction", "Design Studio - Design Problems", "Design Studio - Simulation & Modeling"],
                ["Design Studio - Core Theory", "Design Studio - Project Work", "Design Studio - Case Studies"],
                ["Design Studio - Project Work", "Design Studio - Practical Techniques"],
                ["Design Studio - Laboratory Work", "Design Studio - Mathematical Foundations"],
                ["Design Studio - Design Problems", "Design Studio - Case Studies", "Design Studio - Project Work"]
            ]
        }
        print("Generating paper from sample course (no DB helper present)...")
        vect, clf = None, None
        if use_ml and sklearn_available:
            vect, clf = ensure_model_for_course(sample_course['courseCode'], sample_course, force_retrain=args.retrain)
        paper = generate_full_paper(sample_course, use_ml_for_marks=(vect is not None and clf is not None), vect=vect, clf=clf)
        print(json.dumps(paper, indent=2))
