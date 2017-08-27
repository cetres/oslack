# Oslack - OpenShift Slack Alerts

Oslack is a alert system reading OpenShift cluster events and sending to slack communication platform



```shell with right oc permissions
$ oc new-app -f https://raw.githubusercontent.com/cetres/oslack/master/template.yaml \
             -p APPLICATION_NAME=<application_name> 
             -p SLACK_API_TOKEN=<slack_token> \
             -p OPENSHIFT_CONSOLE_URL=https://<openshift-host-here>:8443
$ oc start-build <application_name>
```
