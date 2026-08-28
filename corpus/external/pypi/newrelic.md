---
date: 2026-08-21T00:09:40+0000
source: https://pypi.org/project/newrelic/
---
# New Relic Python Agent

[image: GitHub release] [image: image] [image: image] [image: PyPI Downloads]

[image: Tests] [image: Ruff] [image: MegaLinter] [image: codecov] [image: Secured with Trivy]

The newrelic package instruments your application for performance
monitoring and advanced performance analytics with New
Relic.

Pinpoint and solve Python application performance issues down to the
line of code. New Relic
APM is the only tool
you'll need to see everything in your Python application, from the end
user experience to server monitoring. Trace problems down to slow
database queries, slow 3rd party APIs and web services, caching layers,
and more. Monitor your app in a production environment and make sure
your app can stand a big spike in traffic by running scalability
reports.

Visit Python Application Performance Monitoring with New
Relic to learn more.

## Usage

This package supports Python 3.9+, and can be installed via pip:

```
pip install newrelic
```

(These instructions can also be found online: Python Agent Installation Guide.)

1. Generate the agent configuration file with your license
key.

```
newrelic-admin generate-config $YOUR_LICENSE_KEY newrelic.ini
``` 
1. Validate the agent configuration and test the connection to our data
collector service.

```
newrelic-admin validate-config newrelic.ini
``` 
1. Integrate the agent with your web application.

If you control how your web application or WSGI server is started,
the recommended way to integrate the agent is to use the
newrelic-admin wrapper
script.
Modify the existing startup script, prefixing the existing startup
command and options with newrelic-admin run-program.

Also, set the NEW_RELIC_CONFIG_FILE environment
variable to the name of the configuration file you created above:

```
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program $YOUR_COMMAND_OPTIONS
```

Examples:

```
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program gunicorn -c config.py test_site.wsgi
NEW_RELIC_CONFIG_FILE=newrelic.ini newrelic-admin run-program uwsgi uwsgi_config.ini
```

Alternatively, you can also manually integrate the
agent
by adding the following lines at the very top of your python WSGI
script file. (This is useful if you're using mod_wsgi.)

```
import newrelic.agent
newrelic.agent.initialize("/path/to/newrelic.ini")
``` 
1. Start or restart your Python web application or WSGI server.
1. Done! Check your application in the New Relic
UI to see the real time statistics
generated from your application.

Additional resources may be found here:

- New Relic for Python
Documentation
- New Relic for Python Release
Notes

## Support

Should you need assistance with New Relic products, you are in good
hands with several support diagnostic tools and support channels.

This troubleshooting
framework
steps you through common troubleshooting questions.

New Relic offers NRDiag, a client-side diagnostic
utility
that automatically detects common problems with New Relic agents. If
NRDiag detects a problem, it suggests troubleshooting steps. NRDiag can
also automatically attach troubleshooting data to a New Relic Support
ticket.

If the issue has been confirmed as a bug or is a Feature request, please
file a GitHub issue.

### Support Channels

- New Relic
Documentation:
Comprehensive guidance for using our platform
- New Relic
Community:
The best place to engage in troubleshooting questions
- New Relic Developer: Resources
for building a custom observability applications
- New Relic University:
A range of online training for New Relic users of every level
- New Relic Technical Support
24/7/365 ticketed support. Read more about our Technical Support
Offerings.

## Privacy

At New Relic we take your privacy and the security of your information
seriously, and are committed to protecting your information. We must
emphasize the importance of not sharing personal data in public forums,
and ask all users to scrub logs and diagnostic information for sensitive
information, whether personal, proprietary, or otherwise.

We define "Personal Data" as any information relating to an identified
or identifiable individual, including, for example, your name, phone
number, post code or zip code, Device ID, IP address and email address.

Please review New Relic's General Data Privacy
Notice for more
information.

## Contribute

We encourage your contributions to improve the New Relic Python Agent! Keep in mind that when you submit your pull request, you'll need to sign the CLA via the click-through using CLA-Assistant. You only have to sign the CLA one time per project.

If you have any questions, or to execute our corporate CLA (which is required if your contribution is on behalf of a company), drop us an email at opensource@newrelic.com.

### A note about vulnerabilities

As noted in our security policy, New Relic is committed to the privacy and security of our customers and their data. We believe that providing coordinated disclosure by security researchers and engaging with the security community are important means to achieve our security goals.

If you believe you have found a security vulnerability in this project or any of New Relic's products or websites, we welcome and greatly appreciate you reporting it to New Relic through our bug bounty program.

If you would like to contribute to this project, review these guidelines.

To all contributors, we thank you! Without your contribution, this project would not be what it is today.

## License

The New Relic Python Agent is licensed under the Apache 2.0 License. The New Relic
Python Agent also uses source code from third-party libraries. You can
find full details on which libraries are used and the terms under which
they are licensed in the third-party notices document.
