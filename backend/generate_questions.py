
def generate_question_paper(syllabus):
    title = f"{syllabus['courseCode']} - {syllabus['title']}"
    units = syllabus['unitTopics']
    paper = f"{title}\n\n"
    for i, unit in enumerate(units):
        paper += f"Q{i+1}. Write short notes on {unit}\n"
    return paper
