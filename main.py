import os, sys, re

# Canvas API
import canvasapi
from canvasapi.course import Course
from canvasapi.exceptions import Unauthorized, ResourceDoesNotExist, Forbidden
from canvasapi.file import File
from canvasapi.module import Module, ModuleItem
from pathvalidate import sanitize_filename

import chromadb
import demo

API_URL = "https://arlington.instructure.com"
API_KEY = os.environ["CANVAS_API"]


# Initialize a new Canvas object
canvas = canvasapi.Canvas(API_URL, API_KEY)
user = canvas.get_current_user()
courses = user.get_favorite_courses()

print("- Available courses -")
i = 1
for course in courses:
    course: Course = course

    print(f"{i:3}| {course.name} ({course.id})")
    i += 1

selected_course = input("Select a course: ")
course = courses[int(selected_course) - 1]

reindex = (
    input("Would you like to update the database for this course? (y/N): ").lower()
    == "y"
)

db = chromadb.PersistentClient("./chroma_db")
try:
    collection_exists = db.get_collection(course.name.lower().strip().replace(" ", "_"))
except ValueError:
    collection_exists = False

if not collection_exists or reindex:
    print("Downloading course content...")
    modules = course.get_modules()

    def extract_files(text):
        text_search = re.findall("/files/(\\d+)", text, re.IGNORECASE)
        groups = set(text_search)
        return groups

    output = "./data/"
    files_downloaded = set()

    for module in modules:
        module: Module = module
        module_items = module.get_module_items()
        print(f"Module: {module.name}")
        for item in module_items:
            item: ModuleItem = item
            item_type = item.type
            print(f"{item_type} | {item}")

            item1 = {key: value for key, value in item.__dict__.items()}
            # print(item1)

            path = (
                f"{output}/"
                f"{sanitize_filename(course.name)}/"
                f"{sanitize_filename(module.name)}/"
            )
            if not os.path.exists(path):
                os.makedirs(path)

            print(f"{course.name} - " f"{module.name} - " f"{item.title} ({item_type})")

            if item_type == "File":
                file = canvas.get_file(item.content_id)
                files_downloaded.add(item.content_id)
                file.download(path + sanitize_filename(file.filename))
            elif item_type == "Page":
                page = course.get_page(item.page_url)
                with open(
                    path + sanitize_filename(item.title) + ".html",
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(page.body or "")
                files = extract_files(page.body or "")
                for file_id in files:
                    if file_id in files_downloaded:
                        continue
                    try:
                        file = course.get_file(file_id)
                        files_downloaded.add(file_id)
                        file.download(path + sanitize_filename(file.filename))
                    except ResourceDoesNotExist or Unauthorized or Forbidden:
                        pass
            elif item_type == "Assignment":
                assignment = course.get_assignment(item.content_id)
                with open(
                    path + sanitize_filename(item.title) + ".html",
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(assignment.description or "")
                files = extract_files(assignment.description or "")
                for file_id in files:
                    if file_id in files_downloaded:
                        continue
                    try:
                        file = course.get_file(file_id)
                        files_downloaded.add(file_id)
                        file.download(path + sanitize_filename(file.filename))
                    except ResourceDoesNotExist or Unauthorized or Forbidden:
                        pass

# try:
#     files = course.get_files()
#     for file in files:
#         file: File = file
#         if not file.id in files_downloaded:
#             print(f"{course.name} - {file.filename}")
#             path = (
#                 f"{output}/{sanitize_filename(course.name)}/"
#                 f"{sanitize_filename(file.filename)}"
#             )
#             file.download(path)
# except Unauthorized or Forbidden or ResourceDoesNotExist:
#     pass

if sys.argv[1] == "0":
    demo.demo(course, resume=True, reindex=reindex)
elif sys.argv[1] == "1":
    demo.demo(course, resume=False, reindex=reindex)
