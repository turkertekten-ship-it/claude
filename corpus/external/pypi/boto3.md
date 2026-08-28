[image: Package Version] [image: Python Versions] [image: License]

Boto3 is the Amazon Web Services (AWS) Software Development Kit (SDK) for
Python, which allows Python developers to write software that makes use
of services like Amazon S3 and Amazon EC2. You can find the latest, most
up to date, documentation at our doc site, including a list of
services that are supported.

Boto3 is maintained and published by Amazon Web Services.

Boto (pronounced boh-toh) was named after the fresh water dolphin native to the Amazon river. The name was chosen by the author of the original Boto library, Mitch Garnaat, as a reference to the company.

## Notices

On 2026-04-29, support for Python 3.9 ended for Boto3. This follows the
Python Software Foundation end of support
for the runtime which occurred on 2025-10-31.

For more information on deprecations, see this
blog post.

## Getting Started

Assuming that you have a supported version of Python installed, you can first
set up your environment with:

```
$ python -m venv .venv
...
$ . .venv/bin/activate
```

Then, you can install boto3 from PyPI with:

```
$ python -m pip install boto3
```

or install from source with:

```
$ git clone https://github.com/boto/boto3.git
$ cd boto3
$ python -m pip install -r requirements.txt
$ python -m pip install -e .
```

### Using Boto3

After installing boto3

Next, set up credentials (in e.g. ~/.aws/credentials):

```
[default]
aws_access_key_id = YOUR_KEY
aws_secret_access_key = YOUR_SECRET
```

Then, set up a default region (in e.g. ~/.aws/config):

```
[default]
region = us-east-1
```

Other credential configuration methods can be found here

Then, from a Python interpreter:

```
>>> import boto3
>>> s3 = boto3.resource('s3')
>>> for bucket in s3.buckets.all():
        print(bucket.name)
```

### Running Tests

You can run tests in all supported Python versions using tox. By default,
it will run all of the unit and functional tests, but you can also specify your own
pytest options. Note that this requires that you have all supported
versions of Python installed, otherwise you must pass -e or run the
pytest command directly:

```
$ tox
$ tox -- unit/test_session.py
$ tox -e py26,py33 -- integration/
```

You can also run individual tests with your default Python version:

```
$ pytest tests/unit
```

## Getting Help

We use GitHub issues for tracking bugs and feature requests and have limited
bandwidth to address them. Please use these community resources for getting
help:

- Ask a question on Stack Overflow and tag it with boto3
- Open a support ticket with AWS Support
- If it turns out that you may have found a bug, please open an issue

## Contributing

We value feedback and contributions from our community. Whether it’s a bug report, new feature, correction, or additional documentation, we welcome your issues and pull requests. Please read through this CONTRIBUTING document before submitting any issues or pull requests to ensure we have all the necessary information to effectively respond to your contribution.

## Maintenance and Support for SDK Major Versions

Boto3 was made generally available on 06/22/2015 and is currently in the full support phase of the availability life cycle.

For information about maintenance and support for SDK major versions and their underlying dependencies, see the following in the AWS SDKs and Tools Shared Configuration and Credentials Reference Guide:

- AWS SDKs and Tools Maintenance Policy
- AWS SDKs and Tools Version Support Matrix

## More Resources

- NOTICE
- Changelog
- License
