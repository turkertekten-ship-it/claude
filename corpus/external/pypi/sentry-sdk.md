---
date: 2026-08-24T13:09:36+0000
source: https://pypi.org/project/sentry-sdk/
---
[image: Sentry for Python]

Bad software is everywhere, and we're tired of it. Sentry is on a mission to help developers write better software faster, so we can get back to enjoying technology. If you want to join us
Check out our open positions.

[image: Discord] [image: X Follow] [image: PyPi page link -- version] [image: python] [image: Build Status]

# Official Sentry SDK for Python

Welcome to the official Python SDK for Sentry.

## 📦 Getting Started

### Prerequisites

You need a Sentry account and project.

### Installation

Getting Sentry into your project is straightforward. Just run this command in your terminal:

```
pip install --upgrade sentry-sdk
```

### Basic Configuration

Here's a quick configuration example to get Sentry up and running:

```
import sentry_sdk

sentry_sdk.init(
    "https://12927b5f211046b575ee51fd8b1ac34f@o1.ingest.sentry.io/1",  # Your DSN here

    # Set traces_sample_rate to 1.0 to capture 100%
    # of traces for performance monitoring.
    traces_sample_rate=1.0,

    # To disable sending user data and HTTP request/response bodies, uncomment
    # the line below. For more info visit:
    # https://docs.sentry.io/platforms/python/configuration/options/#data_collection
    # data_collection={"user_info": False, "http_bodies": []},
)
```

With this configuration, Sentry will monitor for exceptions and performance issues.

### Quick Usage Example

To generate some events that will show up in Sentry, you can log messages or capture errors:

```
import sentry_sdk
sentry_sdk.init(...)  # same as above

sentry_sdk.capture_message("Hello Sentry!")  # You'll see this in your Sentry dashboard.

raise ValueError("Oops, something went wrong!")  # This will create an error event in Sentry.
```

## 📚 Documentation

For more details on advanced usage, integrations, and customization, check out the full documentation on https://docs.sentry.io.

## 🧩 Integrations

Sentry integrates with a ton of popular Python libraries and frameworks, including FastAPI, Django, Celery, OpenAI and many, many more. Check out the full list of integrations to get the full picture.

## 🚧 Migrating Between Versions?

### From 1.x to 2.x

If you're using the older 1.x version of the SDK, now's the time to upgrade to 2.x. It includes significant upgrades and new features. Check our migration guide for assistance.

### From raven-python

Using the legacy raven-python client? It's now in maintenance mode, and we recommend migrating to the new SDK for an improved experience. Get all the details in our migration guide.

## 🙌 Want to Contribute?

We'd love your help in improving the Sentry SDK! Whether it's fixing bugs, adding features, writing new integrations, or enhancing documentation, every contribution is valuable.

For details on how to contribute, please read our contribution guide and explore the open issues.

## 🛟 Need Help?

If you encounter issues or need help setting up or configuring the SDK, don't hesitate to reach out to the Sentry Community on Discord. There is a ton of great people there ready to help!

## 🔗 Resources

Here are all resources to help you make the most of Sentry:

- Documentation - Official documentation to get started.
- Discord - Join our Discord community.
- X/Twitter - Follow us on X (Twitter) for updates.
- Stack Overflow - Questions and answers related to Sentry.

## 📃 License

The SDK is open-source and available under the MIT license. Check out the LICENSE file for more information.

## 😘 Contributors

Thanks to everyone who has helped improve the SDK!
