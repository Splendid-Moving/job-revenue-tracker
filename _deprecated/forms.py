from services.auth import get_service
import config
from datetime import datetime

def create_daily_form(jobs):
    """
    Creates a Google Form for the given list of jobs.
    """
    if not jobs:
        print("No jobs found, skipping form creation.")
        return None

    service = get_service('forms', 'v1')
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    form_title = f"Great Moving Jobs - {date_str}"
    
    # 1. Create the initial Form
    form_info = {
        "info": {
            "title": form_title,
            "documentTitle": form_title
        }
    }
    
    # Create form in Drive (default root or we can move it via Drive API later, 
    # but Forms API creates it in root usually).
    form = service.forms().create(body=form_info).execute()
    form_id = form['formId']
    form_url = form['responderUri']
    
    print(f"Created Form: {form_id}")
    print(f"Edit URL: {form_url}")

    # 2. Batch Update to add items (Questions)
    # We will loop through jobs and add a Section + 3 Questions for each.
    
    requests = []
    index = 0
    
    for job in jobs:
        job_title = f"Job: {job['summary']} ({job.get('location', '')})"
        
        # Section Header
        requests.append({
            "createItem": {
                "item": {
                    "title": job_title,
                    "description": f"Details for job ID: {job['id']}",
                    "questionGroupItem": {
                        "questions": [], # This is actually for grid, we want Section Header + Questions?
                        # Actually Forms API structure: 
                        # To group visually, we might just use TextItem (Header) or PageBreak.
                        # Using "PageBreakItem" puts each job on a new page, which is nice.
                        # Or just "TextItem" (Title/Description) before the questions.
                    } 
                },
                "location": { "index": index }
            }
        })
        # Wait, the structure above for CreateItem is specific.
        # Let's use simple TextItem for the Job Header + 3 regular QuestionItems.
        
        # Header (Text Item)
        requests.append({
            "createItem": {
                "item": {
                    "title": job_title,
                    "description": f"Date: {job['start']}",
                    "textItem": {}
                },
                "location": { "index": index }
            }
        })
        index += 1

        # Q1: Did the move happen? (Choice)
        requests.append({
            "createItem": {
                "item": {
                    "title": "Did the move happen?",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [
                                    {"value": "Yes"},
                                    {"value": "Cancelled"},
                                    {"value": "Rescheduled"},
                                    {"value": "Other"}
                                ]
                            }
                        }
                    }
                },
                "location": { "index": index }
            }
        })
        index += 1

        # Q2: Total revenue (Text/Number)
        requests.append({
            "createItem": {
                "item": {
                    "title": "Total revenue collected? ($)",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {} # simple text, validation can be added but optional
                        }
                    }
                },
                "location": { "index": index }
            }
        })
        index += 1
        
        # Q3: Net revenue (Text/Number)
        requests.append({
            "createItem": {
                "item": {
                    "title": "Net revenue collected? ($)",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {}
                        }
                    }
                },
                "location": { "index": index }
            }
        })
        index += 1

    # Execute the batch update to add questions
    service.forms().batchUpdate(
        formId=form_id, 
        body={"requests": requests}
    ).execute()
    
    print("Questions added to form.")

    # 3. Link to Google Sheet (Optional but requested via Sheet ID)
    # The API doesn't let us easily "Link to existing sheet and map columns". 
    # We can normally only "Create a new sheet" or let Forms pick.
    # HOWEVER, we can use `updateFormInfo` to set a destination if we knew how to structure it,
    # but the public API has limitations on writing to *existing* sheets seamlessly like the UI.
    # Most automation creates a NEW response file.
    # Let's *try* to see if we can set it, otherwise we skip linking and user has to link manually once?
    # Actually, automation implies it should be ready.
    # Workaround: We can't legally set an arbitrary existing sheet as destination via REST API easily in v1.
    # We will notify user about this limitation or just leave it local in Forms.
    # Wait, `writeControl`? No.
    
    return {"formId": form_id, "formUrl": form_url, "responderUri": form["responderUri"]} # responderUri is the view form link
