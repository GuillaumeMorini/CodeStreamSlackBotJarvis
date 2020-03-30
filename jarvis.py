#! /bin/python3
import os
import slack
import requests

@slack.RTMClient.run_on(event='message')
def jarvis(**payload):
    print("...Payload...")
    print(payload)

    data = payload['data']
    web_client = payload['web_client']
    rtm_client = payload['rtm_client']
    user_text = data.get('text', [])
    channel_id = data['channel']

    # If the override is set, then  force all communication from Jarvis to that channel
    if channelOverride != "default":
        channel_id = channelOverride

    # Catch if its a delete operation (or something that could throw a type error), then ignore the event.
    if type(user_text) == list:
        return

    # If message was generated by a bot, catch that.
    if "bot_id" in data:
        pass
    else:
        user = data['user']

##### This is the Rejection workflow follow up
    if "has been rolled back due to qa rejection." in user_text.lower():
        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"I've successfully killed QA."
        )
        return

#### This is the deny workflow
    if "dear god no" in user_text.lower():
        executionID = os.getenv('EXECUTIONID', "default")
        print ("checking env vars")

        #Check and ensure there is something in QA to deploy, otherwise go through workflow
        if "default" in executionID:
            response = "Excuse me?"
        else:
            response = "That bad? Very well. Give me 60 seconds."
            print ("passed checks")
            print ("Grabbing Bearer Token...")

            # grab bearer token
            tPayload = '{"username":"' + username + '","password":"' + password + '"}'
            print (tPayload)
            tURL = baseURL + "/csp/gateway/am/api/login"
            print (tURL)
            Hed = {'Content-Type': 'application/json'}
            r = requests.post(tURL, data=tPayload, headers=Hed, verify=False).json()
            print (r)
            bearerToken = r["cspAuthToken"]

            # Look for the TaskID to reject, via querying the executionID
            print ("searching for the ID")

            qURL = baseURL + "/codestream/api/user-operations/?$filter=executionId%20eq%20'" + executionID + "'"
            Auth = "Bearer " + bearerToken
            Head = {'Content-Type': 'application/json', 'accept':'application/json', 'Authorization':Auth}
            r = requests.get(qURL, headers=Head, verify=False).json()
            print (r)

            # Walk the response, and grab the ID from the url in the documents.
            link = list(r["documents"])[0]
            link = link.split('/')
            TaskID = link[4]

            print ("taskID is: " + TaskID)
            print ("sending POST to approve...")

            # Send the PATCH to approve of the UserOperations Task.
            url = baseURL + '/codestream/api/user-operations/' + TaskID
            payload = '{"responseMessage": "Rejected by ' + user + ' via Jarvis.","status": "Rejected"}'
            r = requests.patch(url, headers=Head, data=payload, verify=False)
            print (r)

        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=response
        )
        return

    if 'thank' in data.get('text', []).lower():

        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"My pleasure."
        )
        return

    if 'hello' in data.get('text', []).lower():

        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"Greetings, sir."
        )
        return


#### This is the approval workflow
    if 'go ahead' in user_text.lower():
        executionID = os.getenv('EXECUTIONID', "default")
        print ("checking env vars")

        #Check and ensure there is something in QA to deploy, otherwise go through workflow
        if "default" in executionID:
            response = "Excuse me?"
        else:
            response = "Understood. Give me 60 seconds."

            print ("passed checks")
            print ("Grabbing Bearer Token...")

            # grab bearer token
            tPayload = '{"username":"' + username + '","password":"' + password + '"}'
            print (tPayload)
            tURL = baseURL + "/csp/gateway/am/api/login"
            print (tURL)
            Hed = {'Content-Type': 'application/json'}
            r = requests.post(tURL, data=tPayload, headers=Hed, verify=False).json()
            print (r)
            bearerToken = r["cspAuthToken"]

            # Look for the TaskID to approve, via querying the executionID
            print ("searching for the ID")

            qURL = baseURL + "/codestream/api/user-operations/?$filter=executionId%20eq%20'" + executionID + "'"
            Auth = "Bearer " + bearerToken
            Head = {'Content-Type': 'application/json', 'accept':'application/json', 'Authorization':Auth}
            r = requests.get(qURL, headers=Head, verify=False).json()
            print (r)

            # Walk the response, and grab the ID from the url in the documents.
            link = list(r["documents"])[0]
            link = link.split('/')
            TaskID = link[4]

            print ("taskID is: " + TaskID)
            print ("sending POST to approve...")

            # Send the PATCH to approve of the UserOperations Task.
            url = baseURL + '/codestream/api/user-operations/' + TaskID
            payload = '{"responseMessage": "Approved by ' + user + ' via Jarvis.","status": "Approved"}'
            r = requests.patch(url, headers=Head, data=payload, verify=False)
            print (r)

        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=response
        )
        return
    if 'thank' in data.get('text', []).lower():

        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"My pleasure."
        )
        return
    if 'hello' in data.get('text', []).lower():

        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"Greetings, sir."
        )
        return
#### This is the trigger for QA notification by Jarvis. Looks for subroutine's message on QA.
    if 'QA environment pending approval. Git Commit: ' in data.get('text', []) and botID in data['bot_id']:

        # Parse out the execID and git commit from the standard message (to be used later)
        msg = data.get('text', []).split(':')
        execID = msg[2].strip(' ')
        gitCommit = msg[1].strip('. ExecutionID')
        print ("Parsing Execution ID: " + execID)
        print ("Git Commit ID: " + gitCommit)

        #Store the execution ID and git commit for follow up approval workflow
        os.environ['EXECUTIONID'] = execID
        os.environ['GITCOMMIT'] = gitCommit

        #Inform notify channel of the QA environment and approval ask.
        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"I've deployed git commit " + gitCommit + " to QA (http://qa.fortune.local:32554/). Shall I push it to production?"
        )
        return
##### This is to notify production is fully deployed.
    if 'Production has been updated with git commit ' in data.get('text', []) and botID in data['bot_id']:
        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"https://media.giphy.com/media/10XhRDTsVm1b4A/giphy.gif"
        )
        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"That commit is officially in production (http://fortune.local:30205/index.html). Congradulations, sir."
        )
##### This is to notify user if Wavefront had to roll it back.
    if 'CRITICAL: Issue with Git Commit ' in data.get('text', []) and botID in data['bot_id']:
        gitCommit = os.getenv('GITCOMMIT', "")
        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"http://www.riffsy.com/image/fcf98f4ea523b9f847202caf731328ad-2.gif"
        )
        web_client.chat_postMessage(
            channel=channel_id,
            as_user=True,
            text=f"I had to roll back git commit " + gitCommit + " due to higher than expected CPU usage."
        )

##### This is to delete all of Jarvis's messages
    if 'clean up' in data.get('text', []):
        cmd = 'slack-cleaner --token ' + slackToken + ' --message --channel notify --user "*" --perform'
        os.system(cmd)

slackToken = os.getenv("SLACK_API_TOKEN", "default")
baseURL = os.getenv('BASE_URL_CODESTREAM', "default")
username = os.getenv('CS_USERNAME', "default")
password = os.getenv('CS_PASSWORD', "default")
channelOverride = os.getenv('JARVIS_OVERRIDE', "default")
botID = os.getenv('JARVIS_SUBROUTINE_ID', "default")

# Check that env vars are properly set
if baseURL == "default":
    print ("Please set the BASE_URL_CODESTREAM envrionment variable (ex: https://codestream_location.com)")
    exit()
if slackToken == "default":
    print ("Please set the SLACK_API_TOKEN environment variable")
    exit()
if username == "default":
    print ("Please set the CS_USERNAME environment variable")
    exit()
if password == "default":
    print ("Please set the CS_PASSWORD environment variable")
    exit()
if botID == "default":
    print ("Please set the JARVIS_SUBROUTINE_ID environment variable to the Subroutine bot's internal ID")
    exit()
if baseURL[len(baseURL)-1] == '/': #Check for trailing / and remove it
    baseURL= baseURL[:len(baseURL)-1]

rtm_client = slack.RTMClient(token=slackToken)
rtm_client.start()