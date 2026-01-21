# Custom google form generation system for a moving compayn

Create an automated google form generation system, that once a day will fetch all events from this companys google calendar, fethch each event on that day (each event = one moving job), and create a google form that will include 3 questions per moving job: 

1. Did the move happen? (Yes, cancelled, rescheduled, other)
2. Total revennue collected? (nummber, in $)
3. Net revenue collected? (number, in $)

After the form is created, it will be sent to the company's email address. The form will be open for 7 days, and after that it will be deleted. After the form is subbmited, we need to update those fields in a google sheet. 