[image: Elastic logo]

# Elasticsearch Python Client

[image: PyPI Version] [image: Python Versions] [image: Conda Version] [image: Downloads]
 [image: Build Status on GitHub] [image: Buildkite Status on Buildkite] [image: Documentation Status]

The official Python client for Elasticsearch.

## Features

- Translating basic Python data types to and from JSON
- Configurable automatic discovery of cluster nodes
- Persistent connections
- Load balancing (with pluggable selection strategy) across available nodes
- Failed connection penalization (time based - failed connections won't be
retried until a timeout is reached)
- Support for TLS and HTTP authentication
- Thread safety across requests
- Pluggable architecture
- Helper functions for idiomatically using APIs together

## Installation

Download the latest version of Elasticsearch
or
sign-up
for a free trial of Elastic Cloud.

Refer to the Installation section
of the getting started documentation.

## Connecting

Refer to the Connecting section
of the getting started documentation.

## Usage

---

- Creating an index
- Indexing a document
- Getting documents
- Searching documents
- Updating documents
- Deleting documents
- Deleting an index

## Compatibility

Language clients are forward compatible: each client version works with equivalent and later minor versions of Elasticsearch without breaking.

Compatibility does not imply full feature parity. New Elasticsearch features are supported only in equivalent client versions. For example, an 8.12 client fully supports Elasticsearch 8.12 features and works with 8.13 without breaking; however, it does not support new Elasticsearch 8.13 features. An 8.13 client fully supports Elasticsearch 8.13 features.

| Elasticsearch version | elasticsearch-py branch |
| main | main |
| 9.x | 9.x |
| 9.x | 8.x |
| 8.x | 8.x |

Elasticsearch language clients are also backward compatible across minor versions — with default distributions and without guarantees.

> [!TIP]
> To upgrade to a new major version, first upgrade Elasticsearch, then upgrade the Python Elasticsearch client.

If you need to work with multiple client versions, note that older versions are also released as elasticsearch7 and elasticsearch8.

## Documentation

Documentation for the client is available on elastic.co and Read the Docs.

## Try Elasticsearch and Kibana locally

If you want to try Elasticsearch and Kibana locally, you can run the following command:

```
curl -fsSL https://elastic.co/start-local | sh
```

This will run Elasticsearch at http://localhost:9200 and Kibana at http://localhost:5601.

More information is available here.

## Contributing

See CONTRIBUTING.md

## License

This software is licensed under the Apache License 2.0. See NOTICE.
