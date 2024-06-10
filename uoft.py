import requests
from bs4 import BeautifulSoup 
import time

#url of uofts timetable api
url = "https://api.easi.utoronto.ca/ttb/getPageableCourses"

class Course:
    def __init__(self, name, description, prereqs, exclusions, campus, type):
        self.name = name
        self.description = description
        self.prereqs = prereqs
        self.exclusions = exclusions
        self.campus = campus
        self.type = type

# Headers used when fetching data from the uoft timetable API
headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-CA,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,en-GB;q=0.6,en-US;q=0.5",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "https://ttb.utoronto.ca",
    "Referer": "https://ttb.utoronto.ca/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}

#given a list of session codes, which term to search for, and faculties to search for, this function will append the course information to a
def getCoursesDetails(sessions: list[str], a:dict, type: str, faculty: list[str]):
    pagecount = 1
    print(sessions, "consolidating course code list...", end='\r')

    #iterate through page count until no more courses are found
    while(True):
        payload = {"courseCodeAndTitleProps":{"courseCode":"",
                                            "courseTitle":"","courseSectionCode":""},
                    "departmentProps":[],
                    "campuses":[],
                    "sessions":sessions,
                    "requirementProps":[],
                    "instructor":""
                    ,"courseLevels":[],
                    "deliveryModes":[],
                    "dayPreferences":[],
                    "timePreferences":[],
                    "divisions":faculty,
                    "creditWeights":[],
                    "availableSpace":False,
                    "waitListable":False,
                    "page":pagecount,
                    "pageSize":2000,
                    "direction":"asc"}

        response = requests.post(url, headers=headers, json=payload)

        #if response is successful, parse the data
        if response.status_code == 200:
            data = response.json()

            #if no courses are found, break out of loop
            if len(data['payload']['pageableCourse']['courses']) == 0:
                break

            courses = data['payload']['pageableCourse']['courses']

            for i in courses:
                if i['code'] in a.keys() and type not in a[i['code']].type:
                    a[i['code']].type.append(type)
                elif i['code'] not in a.keys():
                    a[i['code']] = Course(i['name'], "", "", "",i['campus'], [type])
                    if i['cmCourseInfo']:
                        a[i['code']] = Course(i['name'].replace('"', "'"), 
                                              "" if i['cmCourseInfo']['description'] == None else i['cmCourseInfo']['description'].replace('"', "'").replace("\n", "\\n"),
                                              "" if i['cmCourseInfo']['prerequisitesText'] == None else i['cmCourseInfo']['prerequisitesText'].replace('"', "'").replace("\n", "\\n"), 
                                              "" if i['cmCourseInfo']['exclusionsText'] == None else i['cmCourseInfo']['exclusionsText'].replace('"', "'").replace("\n", "\\n"),
                                              i['campus'],
                                              [type])
        else:
            print(f"Request failed with status code {response.status_code}")
        pagecount+=1
    print(sessions, "finished consolidating                     ")
    return a


if __name__ == "__main__":
    start = time.time()
    # Get course information from winter, summer, and fall seperately to differentiate between terms
    a = getCoursesDetails(["20245F","20245S","20245"], {}, "Summer", ["APSC", "ARTSC", "SCAR", "ERIN"])
    a = getCoursesDetails(["20251", "20249-20251"], a, "Winter", ["APSC", "ARTSC", "SCAR", "ERIN"])
    a = getCoursesDetails(["20249", "20249-20251"], a, "Fall", ["APSC", "ARTSC", "SCAR", "ERIN"])

    #format data into a json file
    f2 = open("Courses.json", "w", encoding="utf-8")

    f2.write('{"courseList": [')
    counter = 0
    for i in a.keys():
        counter+=1
        if a[i].name == "":
            continue
        f2.write('{"courseID": "'+i+'", "courseName": "'+a[i].name+'", "courseDescription": "'+a[i].description+'", "coursePrereqs": "'+a[i].prereqs+'", "courseExclusions": "'+a[i].exclusions+'", "campus": "'+a[i].campus+'"')
        f2.write(", \"courseType\": [")

        for j in range(len(a[i].type)):
            f2.write('"'+a[i].type[j]+'"')
            if(j!=len(a[i].type)-1):
                f2.write(", ")
        f2.write("]}")
        if(counter!=len(a)):
            f2.write(",")
        f2.write("\n")

    f2.write("]}")
    f2.close()
    end = time.time()
    print("Finished in", round(end-start), "seconds")
    print("Course Information stored in Courses.json")