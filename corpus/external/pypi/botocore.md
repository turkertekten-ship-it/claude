---
date: 2026-08-27T20:08:34+0000
source: https://pypi.org/project/botocore/
---
[image: Package Version] [image: Python Versions] [image: License]

A low-level interface to a growing number of Amazon Web Services. The
botocore package is the foundation for the
AWS CLI as well as
boto3.

Botocore is maintained and published by Amazon Web Services.

## Notices

On 2026-04-29, support for Python 3.9 ended for Botocore. This follows the
Python Software Foundation end of support
for the runtime which occurred on 2025-10-31.

For more information, see this blog post.

## Getting Started

Assuming that you have Python and virtualenv installed, set up your environment and install the required dependencies like this or you can install the library using pip:

```
$ git clone https://github.com/boto/botocore.git
$ cd botocore
$ python -m venv .venv
...
$ source .venv/bin/activate
$ python -m pip install -r requirements.txt
$ python -m pip install -e .
```

```
$ pip install botocore
```

### Using Botocore

After installing botocore

Next, set up credentials (in e.g. ~/.aws/credentials):

```
[default]
aws_access_key_id = YOUR_KEY
aws_secret_access_key = YOUR_SECRET
```

Then, set up a default region (in e.g. ~/.aws/config):

```
[default]
region=us-east-1
```

Other credentials configuration method can be found here

Then, from a Python interpreter:

```
>>> import botocore.session
>>> session = botocore.session.get_session()
>>> client = session.create_client('ec2')
>>> print(client.describe_instances())
```

## Getting Help

We use GitHub issues for tracking bugs and feature requests and have limited
bandwidth to address them. Please use these community resources for getting
help. Please note many of the same resources available for boto3 are
applicable for botocore:

- Ask a question on Stack Overflow and tag it with boto3
- Open a support ticket with AWS Support
- If it turns out that you may have found a bug, please open an issue

## Contributing

We value feedback and contributions from our community. Whether it’s a bug report, new feature, correction, or additional documentation, we welcome your issues and pull requests. Please read through this CONTRIBUTING document before submitting any issues or pull requests to ensure we have all the necessary information to effectively respond to your contribution.

## Maintenance and Support for SDK Major Versions

Botocore was made generally available on 06/22/2015 and is currently in the full support phase of the availability life cycle.

For information about maintenance and support for SDK major versions and their underlying dependencies, see the following in the AWS SDKs and Tools Reference Guide:

- AWS SDKs and Tools Maintenance Policy
- AWS SDKs and Tools Version Support Matrix

## More Resources

- NOTICE
- Changelog
- License
