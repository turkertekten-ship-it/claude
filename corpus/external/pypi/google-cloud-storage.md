---
date: 2026-08-06T06:23:36+0000
source: https://pypi.org/project/google-cloud-storage/
---
[image: stable] [image: pypi] [image: versions]

Google Cloud Storage is a managed service for storing unstructured data. Cloud Storage
allows world-wide storage and retrieval of any amount of data at any time. You can use
Cloud Storage for a range of scenarios including serving website content, storing data
for archival and disaster recovery, or distributing large data objects to users via direct download.

NOTE: 3.0 Major Version Notes are available. Feedback welcome.

A comprehensive list of changes in each version may be found in the CHANGELOG.

- Product Documentation
- Client Library Documentation
- github.com/googleapis/google-cloud-python

Certain control plane and long-running operations for Cloud Storage (including Folder
and Managed Folder operations) are supported via the Storage Control Client.
The Storage Control API creates one space to perform metadata-specific, control plane,
and long-running operations apart from the Storage API.

Read more about the client libraries for Cloud APIs, including the older
Google APIs Client Libraries, in Client Libraries Explained.

## Quick Start

In order to use this library, you first need to go through the following steps.
A step-by-step guide may also be found in Get Started with Client Libraries.

1. Select or create a Cloud Platform project.
1. Enable billing for your project.
1. Enable the Google Cloud Storage API.
1. Setup Authentication.

### Installation

Install this library in a virtual environment using venv. venv is a tool that
creates isolated Python environments. These isolated environments can have separate
versions of Python packages, which allows you to isolate one project’s dependencies
from the dependencies of other projects.

With venv, it’s possible to install this library without needing system
install permissions, and without clashing with the installed system
dependencies.

### Code samples and snippets

Code samples and snippets live in the samples/ folder.

#### Supported Python Versions

Our client libraries are compatible with all current active and maintenance versions of
Python.

Python >= 3.7

#### Unsupported Python Versions

Python <= 3.6

If you are using an end-of-life
version of Python, we recommend that you update as soon as possible to an actively supported version.

#### Mac/Linux

```
python3 -m venv <your-env>
source <your-env>/bin/activate
pip install google-cloud-storage
```

#### Windows

```
py -m venv <your-env>
.\<your-env>\Scripts\activate
pip install google-cloud-storage
```

### Example Usage

```
# Imports the Google Cloud client library
from google.cloud import storage

# Instantiates a client
storage_client = storage.Client()

# The name for the new bucket
bucket_name = "my-new-bucket"

# Creates the new bucket
bucket = storage_client.create_bucket(bucket_name)

print(f"Bucket {bucket.name} created.")
```

### Tracing With OpenTelemetry

This is a PREVIEW FEATURE: Coverage and functionality are still in development and subject to change.

This library can be configured to use OpenTelemetry to generate traces on calls to Google Cloud Storage.
For information on the benefits and utility of tracing, read the Cloud Trace Overview.

To enable OpenTelemetry tracing in the Cloud Storage client, first install OpenTelemetry:

```
pip install google-cloud-storage[tracing]
```

Set the ENABLE_GCS_PYTHON_CLIENT_OTEL_TRACES environment variable to selectively opt-in tracing for the Cloud Storage client:

```
export ENABLE_GCS_PYTHON_CLIENT_OTEL_TRACES=True
```

You will also need to tell OpenTelemetry which exporter to use. An example to export traces to Google Cloud Trace can be found below.

```
# Install the Google Cloud Trace exporter and propagator, however you can use any exporter of your choice.
pip install opentelemetry-exporter-gcp-trace opentelemetry-propagator-gcp

# [Optional] Install the OpenTelemetry Requests Instrumentation to trace the underlying HTTP requests.
pip install opentelemetry-instrumentation-requests
```

```
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter()))
trace.set_tracer_provider(tracer_provider)

# Optional yet recommended to instrument the requests HTTP library
from opentelemetry.instrumentation.requests import RequestsInstrumentor
RequestsInstrumentor().instrument(tracer_provider=tracer_provider)
```

In this example, tracing data will be published to the Google Cloud Trace console.
Tracing is most effective when many libraries are instrumented to provide insight over the entire lifespan of a request.
For a list of libraries that can be instrumented, refer to the OpenTelemetry Registry.

## 3.0 Major Version Notes

### Feedback Welcome

If you experience that backwards compatibility for your application is broken
with this major version release, please let us know through the Github issues
system. While some breaks of backwards compatibility may be unavoidable due to
new features in the major version release, we will do our best to minimize
them. Thank you.

### Exception Handling

In Python Storage 3.0, the dependency google-resumable-media was integrated.
The google-resumable-media dependency included exceptions
google.resumable_media.common.InvalidResponse and
google.resumable_media.common.DataCorruption, which were often imported
directly in user application code. The replacements for these exceptions are
google.cloud.storage.exceptions.InvalidResponse and
google.cloud.storage.exceptions.DataCorruption. Please update application code
to import and use these exceptions instead.

For backwards compatibility, if google-resumable-media is installed, the new
exceptions will be defined as subclasses of the old exceptions, so applications
should continue to work without modification. This backwards compatibility
feature may be removed in a future major version update.

Some users may be using the original exception classes from the
google-resumable-media library without explicitly installing that library. So
as not to break user applications following this pattern,
google-resumable-media is still in the list of dependencies in this package’s
setup.py file. Applications which do not import directly from
google-resumable-media can safely disregard this dependency.
This backwards compatibility feature will be removed in a future major
version update. Please migrate to using the google.cloud.storage.exceptions
classes as above.

### Checksum Defaults

In Python Storage 3.0, uploads and downloads now have a default of “auto” where
applicable. “Auto” will use crc32c checksums, except for unusual cases where the
fast (C extension) crc32c implementation is not available, in which case it will
use md5 instead. Before Python Storage 3.0, the default was md5 for most
downloads and None for most uploads. Note that ranged downloads (“start” or
“end” set) still do not support any checksumming, and some features in
transfer_manager.py still support crc32c only.

Note: The method Blob.upload_from_file() requires a file in bytes mode, but
when checksum is set to None, as was the previous default, would not throw an
error if passed a file in string mode under some circumstances. With the new
defaults, it will now raise a TypeError. Please use a file opened in bytes
reading mode as required.

### Miscellaneous

- The BlobWriter class now attempts to terminate an ongoing resumable upload if
the writer exits with an exception.
- Retry behavior is now identical between media operations (uploads and
downloads) and other operations, and custom predicates are now supported for
media operations as well.
- Blob.download_as_filename() will now delete the empty file if it results in a
google.cloud.exceptions.NotFound exception (HTTP 404).
- Previously, object upload, metadata update, and delete methods had retries
disabled by default unless the generation or metageneration was specified in
the request. This has now changed so that retries are enabled by default.

### Next Steps

- Read the Google Cloud Storage Product documentation to learn
more about the product and see How-to Guides.
- Read the Client Library Documentation for Google Cloud Storage API
to see other available methods on the client.
- View this README to see the full list of Cloud
APIs that we cover.
