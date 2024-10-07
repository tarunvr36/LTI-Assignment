import requests
from django.http import HttpResponse

def index(request):
    api_url = "https://canvas.instructure.com/api/v1/"
    # Authentication headers (replace with your API token)
    headers = {
        "Authorization": "Bearer 7~tYRfABEynHxxy2cryrQzeLN6DW2BaKzvKcEuB9zmRFXy2nEtBaLYXZAwecVMLcDt"
    }

    # Retrieve course information from the request
    course_id = request.POST.get("custom_course_id")
    course_name = request.POST.get("custom_course_name")

    # Check for missing course information
    if not course_id or not course_name:
        return HttpResponse("Course ID or Course Name is missing.", status=400)

    # Filter only student roles
    roles = ["student"]

    try:
        # Fetch users enrolled in the course with the role of 'student'
        user_response = requests.get(f"{api_url}courses/{course_id}/users", headers=headers,
                                     params={"enrollment_type[]": roles}, timeout=10)

        if user_response.status_code != 200:
            return HttpResponse(f"API call failed with status code: {user_response.status_code}.", status=user_response.status_code)

        users_data = user_response.json()
        user_list = [(user['id'], user['name']) for user in users_data]

        # Fetch assignments for the course
        assignments_response = requests.get(f"{api_url}courses/{course_id}/assignments", headers=headers, timeout=10)

        if assignments_response.status_code != 200:
            return HttpResponse(f"Failed to retrieve assignments with status code: {assignments_response.status_code}.", status=assignments_response.status_code)

        assignments_data = assignments_response.json()

    except requests.exceptions.Timeout:
        return HttpResponse("The request to the Canvas API timed out.", status=504)

    result = []

    # Iterate through users and their assignment submission status
    for user_id, user_name in user_list:
        user_assignments = []

        for assignment in assignments_data:
            assignment_id = assignment['id']
            submission_url = f"{api_url}courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
            submission_response = requests.get(submission_url, headers=headers)

            if submission_response.status_code == 200:
                submission_data = submission_response.json()
                print(submission_data)  # Debugging: print the full submission data
                # Adjust submission status check to handle multiple states
                submitted = submission_data.get('workflow_state') in ['submitted', 'graded']
            else:
                submitted = False

            user_assignments.append({
                'Assignment Name': assignment['name'],
                'Submission Status': submitted
            })

        result.append({
            'Student Name': user_name,
            'Assignments': user_assignments
        })

    # Prepare the response text
    response_text = f"List of Students with Their Assignment Status in Course {course_name}:\n\n"

    for user in result:
        response_text += f"Student Name: {user['Student Name']}\nAssignments:\n"
        for assignment in user['Assignments']:
            assignment_name = assignment.get('Assignment Name', 'Name not available')
            submission_status = 'Submitted' if assignment.get('Submission Status', False) else 'Not Submitted'
            response_text += f" - Assignment Name: {assignment_name}\n"
            response_text += f"   Submission Status: {submission_status}\n"
        response_text += "\n"

    return HttpResponse(response_text, content_type="text/plain")

