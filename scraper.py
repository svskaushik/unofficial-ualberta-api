import requests
import json
import re
from bs4 import BeautifulSoup as bs
from time import sleep, time


ROOT_URL = "https://apps.ualberta.ca"
MAIN_URL = "https://apps.ualberta.ca/catalogue"
DELAY_TIME = 2


def write_to_file(name_of_file, data):
    """
    Writes scraped data a json file.
    """
    with open(f'./data/{name_of_file}.json', 'w') as file:
        json.dump(data, file)


def get_faculties():
    """
    Returns the faculties offered at the university in the following format:
    {AR :  ['Faculty of Arts', 'https://apps.ualberta.ca/catalogue/faculty/ar'], 
    AU :  ['Augustana Faculty', 'https://apps.ualberta.ca/catalogue/faculty/au']}
    """
    catalog_page = requests.get(MAIN_URL).text
    course_soup = bs(catalog_page, 'html.parser')

    faculty_div = course_soup.find('div', {'class': 'col col-md-6 col-lg-5 offset-lg-2'})
    faculties = faculty_div.findAll('li')

    faculty_data = dict()

    for faculty in faculties:
        sleep(DELAY_TIME)

        faculty_title, faculty_link = [str(faculty.find('a').text), faculty.find('a').get('href')]
        faculty_code, faculty_name = faculty_title.split(' - ')
        faculty_link = ROOT_URL + faculty_link
        
        faculty_data[faculty_code] = {
            "faculty_name": faculty_name,
            "faculty_link": faculty_link
        }

    write_to_file('faculties', faculty_data)
    return faculty_data


def get_subjects(faculty_data):
    """
    Gets the subjects available from the different faculties.
    Key   :  Value
    WKEXP :  {'name': 'Work Experience', 
               'link': 'https://apps.ualberta.ca/catalogue/course/wkexp', 
               'faculties': ['AH', 'AR', 'BC', 'EN', 'SC']}
    """
    # ---------------------------------------------------------------------
    # Data about subjects
    # E.g. {'code', 'name', 'link', 'faculty'}
    subject_data = dict()

    for faculty_code, faculty_value in faculty_data.items():
        sleep(DELAY_TIME)
        faculty_link = faculty_data[faculty_code]["faculty_link"]
        faculty_page = requests.get(faculty_link).text
        subject_soup = bs(faculty_page, 'html.parser')
        content_div = subject_soup.find('div', {'class': 'content'})
        subject_div = content_div.find('div', {'class': 'container'})
        subject_div_list = subject_div.find('ul')
        subjects = subject_div_list.findAll('li')

        for subject in subjects:
            try:
                subject_title, subject_link = [str(subject.find('a').text), subject.find('a').get('href')]
                subject_code, subject_name = subject_title.split(' - ', 1)
                subject_link = ROOT_URL + subject_link
                subject_data[subject_code] = {}
                subject_data[subject_code]["name"] = subject_name  # Assuming you want to store the subject name
                subject_data[subject_code]['link'] = subject_link  # Assuming you want to store the full link
                subject_data[subject_code]['faculties'] = []
            except ValueError as e:
                if "not enough values to unpack" in str(e):
                    print(f"Skipping subject due to unpacking error: {subject}")
                    continue  # Skip to the next subject
            except Exception as e:
                print(f"Error processing subject: {subject}")
                print(f"Exception: {e}")

    for faculty_code, faculty_value in faculty_data.items():
        sleep(DELAY_TIME)
        faculty_link = faculty_data[faculty_code]["faculty_link"]
        faculty_page = requests.get(faculty_link).text
        subject_soup = bs(faculty_page, 'html.parser')
        content_div = subject_soup.find('div', {'class': 'content'})
        subject_div = content_div.find('div', {'class': 'container'})
        subject_div_list = subject_div.find('ul')
        subjects = subject_div_list.findAll('li')

        for subject in subjects:
            subject_title, subject_link = [str(subject.find('a').text), subject.find('a').get('href')]
            subject_code, subject_name = subject_title.split(' - ', 1)
            subject_link = ROOT_URL + subject_link
            subject_data[subject_code]["name"] = subject_name
            subject_data[subject_code]["link"] = subject_link
            subject_data[subject_code]["faculties"].append(faculty_code)

    write_to_file('subjects', subject_data)

    return subject_data


def get_courses(subject_data):
    """
    Gets the courses in the different subjects of the different faculties.
    """
    course_data = dict()

    for subject_code, values in subject_data.items():
        sleep(DELAY_TIME)
        subject_url = subject_data[subject_code]["link"]
        subject_page = requests.get(subject_url).text 
        course_soup = bs(subject_page, 'html.parser')
        courses = course_soup.findAll('div', {'class': 'course first'})

        for course in courses:
            course_code, course_name = course.find('h2', {'class': 'flex-grow-1'}).text.strip().split('\n')[0].split(' - ', 1)
            course_link = ROOT_URL + course.find('a').get('href')
            course_weight = course.find('b').text[2:][:2].strip()

            # Code is a bit ugly here because there is a bit of an inconsistecy 
            # due to the nature of some courses not having some of the data
            try:
                course_fee_index = course.find('b').text[2:].split('fi')[1].split(')')[0].strip()
            except:
                course_fee_index = None
            try:
                course_schedule = courses[0].find('b').text[2:].split('fi')[1].split('(')[1].split(',')[0]
            except:
                course_schedule = None        
            try:            
                course_description = course.find('p').text.split('Prerequisite')[0]
            except:
                course_description = "There is no available course description."
            try:
                course_hrs_for_lecture = course.find('b').text[2:].split('fi')[1].split('(')[1].split(',')[1].split('-')[0].strip(' )')
            except:
                course_hrs_for_lecture = None
            try:
                course_hrs_for_seminar = course.find('b').text[2:].split('fi')[1].split('(')[1].split(',')[1].split('-')[1]
            except:
                course_hrs_for_seminar = None
            try:    
                course_hrs_for_labtime = course.find('b').text[2:].split('fi')[1].split('(')[1].split(',')[1].split('-')[2].strip(')')
            except:
                course_hrs_for_labtime = None
            try:
                course_prerequisites = course.find('p').text.split('Prerequisite')[1]
            except:
                course_prerequisites = None

            # If it is a 100 level class: Junior. Else, Senior.
            if course_code.split(' ')[1].startswith('1'):
                course_type = 'Junior'
            else:
                course_type = 'Senior'
            
            # Get rid of the spaces between courses: CMPUT 404 to CMPUT404
            course_code = course_code.replace(" ", "")

            course_data[course_code] = {
                'course_name': course_name,
                'course_link': course_link,
                'course_description': course_description,
                'course_weight': course_weight,
                'course_fee_index': course_fee_index,
                'course_schedule': course_schedule,
                'course_hrs_for_lecture': course_hrs_for_lecture,
                'course_hrs_for_seminar': course_hrs_for_seminar,
                'course_hrs_for_labtime': course_hrs_for_labtime,
                'course_prerequisites': course_prerequisites
            }

    write_to_file('courses', course_data)
    return course_data


def get_class_schedules(course_data):
    """
    Get the class schedules for a specific course in the different terms.
    """
    class_schedules = dict()

    for course_code, values in course_data.items():
        sleep(DELAY_TIME)
        course_url = course_data[course_code]["course_link"]
        course_page = requests.get(course_url).text 
        course_soup = bs(course_page, 'html.parser')
        terms = course_soup.findAll('div', {'id': 'content-nav', 'class': 'nav flex-nowrap'})
        print("------------------------------------------------------------------")
        print(f"Currently at {course_url}. ")
        print("------------------------------------------------------------------")
        class_schedules[course_code] = {}

        for term in terms:
            try:
                term_code = term.find('a', {'class': 'nav-link active'}).text.strip()
                term_code = term_code.replace(" Term ", "")  # Condensed Name: "Winter Term 2025" --> "Winter2025"
                print(f"--Currently at {term_code}.")
            except Exception as e:
                print("No terms found")
                continue

            class_schedules[course_code][term_code] = {}
            class_types = course_soup.findAll('div', {'class': 'mb-5'})
            print(f"Number of class types: {len(class_types)}")

            for class_type in class_types:
                try:
                    class_type_name = class_type.find('h3').text.strip()  # Lecture, Seminar, or Lab
                except AttributeError:  # If .text or .find('h3') fails due to NoneType
                    print("No class type name found.", class_type_name)
                    continue  # Skip to the next iteration in the loop
                class_schedules[course_code][term_code][class_type_name] = []

                offered_classes = class_type.findAll('tr', {'data-card-title': True})

                for classes in offered_classes:
                    class_info = {}

                    section_info = classes.find('td', {'data-card-title': 'Section'}).text.strip().split('\n')
                    class_code = section_info[-1].strip("()")  # Extract the class code
                    class_name = section_info[0].strip()

                    capacity = classes.find('td', {'data-card-title': 'Capacity'}).text.strip()
                    class_times = classes.find('td', {'data-card-title': 'Class times'}).text.strip()

                    date_pattern = r"(\d{4}-\d{2}-\d{2})"
                    time_pattern = r"(\d{2}:\d{2})"
                    try:
                        start_date, end_date = re.findall(date_pattern, class_times)
                    except:
                        start_date, end_date = ['NA', 'NA']
                    try:
                        start_time, end_time = re.findall(time_pattern, class_times)
                    except:
                        start_time, end_time = ['NA', 'NA']

                    days_pattern = r"\((.*?)\)"
                    try:
                        days = re.search(days_pattern, class_times).group(1)
                    except:
                        days = 'NA'

                    class_info["class_code"] = class_code
                    class_info["class_name"] = class_name
                    class_info["capacity"] = capacity
                    class_info["days"] = days
                    class_info["start_date"] = start_date
                    class_info["end_date"] = end_date
                    class_info["start_time"] = start_time
                    class_info["end_time"] = end_time
                    class_info["room"] = 'Login to view Instructor(s) and Location'  # Placeholder as room info is behind a login

                    class_schedules[course_code][term_code][class_type_name].append(class_info)

    write_to_file('class_schedules', class_schedules)


def main():
    # print("Scraping Faculties...")
    # faculty_data = get_faculties()

    faculty_data2 = {"SS": {"faculty_name": "St Stephen's College", "faculty_link": "https://apps.ualberta.ca/catalogue/faculty/ss"}}

    print("Scraping Subjects...")
    subject_data = get_subjects(faculty_data2)

    print("Scraping Courses...")
    course_data = get_courses(subject_data)

    print("Scraping Class Schedules...")
    class_schedules = get_class_schedules(course_data)
    print("Done. Check the data folder for scraped data.")

    # print(end_time - start_time)


if __name__ == "__main__":
    main()