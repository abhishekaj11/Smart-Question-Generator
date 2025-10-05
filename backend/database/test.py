from fetch_syllabus import get_syllabus

syllabus = get_syllabus("ARCH405B")


print(syllabus["title"])       
print(syllabus["unitNames"][2]) 
print(syllabus["unitTopics"][2])