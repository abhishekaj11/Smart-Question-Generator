"""
question_generator.py

Rule-based + classical ML hybrid question paper generator.

Features:
- Generates questions per unit using rule-based templates and mark rules (1,2,5,12,16)
- 1-mark questions are MCQs
- Trains and saves a TF-IDF + RandomForest model using pickle
- Can reload model later to generate papers without retraining
"""

import re
import json
import random
import pickle
from collections import defaultdict
from typing import List, Dict, Tuple

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
    correct = f"It refers to {topic.lower()}."
    distractors = [
        f"It is unrelated to {topic.lower()}.",
        f"It mainly involves mathematical modeling of {topic.lower()}.",
        f"It focuses on case studies of {topic.lower()}."
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
                                   per_unit_distribution: Dict[int, int] = None) -> List[Tuple[int, str, str]]:
    if per_unit_distribution is None:
        per_unit_distribution = {1: 2, 2: 2, 5: 1}

    scored = [(topic, topic_complexity_score(topic)) for topic in unit_topics]
    scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)

    generated = []
    for mark, count in per_unit_distribution.items():
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
                        unit_question_config: Dict[int, Dict[int, int]] = None) -> Dict:
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
        questions = generate_questions_from_topics(topics_clean, per_unit_distribution=per_unit_dist)
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
        for i in range(examples_per_topic):
            variant = t_norm
            if i == 1:
                variant = variant + " - advanced"
            elif i == 2:
                variant = "introduction to " + variant
            texts.append(variant)
            labels.append(base_label)
    return texts, labels


def train_classical_model(texts: List[str], labels: List[int]):
    if not sklearn_available:
        raise RuntimeError("scikit-learn not available; install it first.")
    vect = TfidfVectorizer(ngram_range=(1, 2), max_features=2000)
    X = vect.fit_transform(texts)
    X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    print("\nClassification report (synthetic dataset):")
    print(classification_report(y_test, preds))
    return vect, clf


def predict_with_model(vect, clf, topic: str) -> int:
    x = vect.transform([topic])
    return int(clf.predict(x)[0])


def save_model(vect, clf, filename: str = "question_model.pkl"):
    with open(filename, "wb") as f:
        pickle.dump((vect, clf), f)
    print(f"Model saved to {filename}")


def load_model(filename: str = "question_model.pkl"):
    with open(filename, "rb") as f:
        vect, clf = pickle.load(f)
    print(f"Model loaded from {filename}")
    return vect, clf


# ---------------------------
# 6) Example run
# ---------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_saved_model", action="store_true", help="Use saved model.pkl instead of retraining")
    args = parser.parse_args()

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

    print("Generating question paper using deterministic rule-based pipeline...\n")
    paper = generate_full_paper(sample_course)
    for unit in paper['questions_by_unit']:
        print(f"\n{unit['unit_name']}:")
        for q in unit['questions']:
            print(f"  [{q['mark']} marks] {q['question']}  (topic: {q['topic']})")

    if sklearn_available:
        if args.use_saved_model:
            vect, clf = load_model("question_model.pkl")
            print("\nLoaded model from disk. Using it for prediction example...")
        else:
            print("\nTraining new model and saving to pickle...")
            texts, labels = create_synthetic_dataset_from_course(sample_course)
            vect, clf = train_classical_model(texts, labels)
            save_model(vect, clf)

        example_topic = "mathematical foundations of design studio"
        pred = predict_with_model(vect, clf, example_topic)
        print(f"Predicted mark {pred} for topic: '{example_topic}'")
    else:
        print("\nscikit-learn not available; skipping model training.")
