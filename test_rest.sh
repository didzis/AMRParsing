#!/bin/bash

host='localhost:5000'
if [ "$1" != "" ]; then
	host="$1"
else
	echo "usage: $0 [hostname:port]"
	echo
	echo "defaults to $host"
fi

echo
echo "Testing CAMR on $host"

echo
echo "Plaintext input, YAML output (without sentence split)"
echo

curl -X POST --header 'Content-Type: text/plain' --header 'Accept: application/yaml' -d '

I had thus learned a second fact of great importance: this was that the planet the little prince came from was scarcely any larger than a house! But that did not really surprise me much. I knew very well that in addition to the great planets -- such as the Earth, Jupiter, Mars, Venus -- to which we have given names, there are also hundreds of others, some of which are so small that one has a hard time seeing them through the telescope.

For information call the Service at (999) 111-12345 or (777) 222-87654.

' "http://$host/api/parse?fmt=yaml"

echo
echo
echo "Plaintext input, YAML output (with sentence split)"
echo

curl -X POST --header 'Content-Type: text/plain' --header 'Accept: application/yaml' -d '

I had thus learned a second fact of great importance: this was that the planet the little prince came from was scarcely any larger than a house! But that did not really surprise me much. I knew very well that in addition to the great planets -- such as the Earth, Jupiter, Mars, Venus -- to which we have given names, there are also hundreds of others, some of which are so small that one has a hard time seeing them through the telescope.

For information call the Service at (999) 111-12345 or (777) 222-87654.

' "http://$host/api/parse?fmt=yaml&ssplit=true"

echo
echo
echo "JSON input (array of objects), JSON output (without sentence split)"
echo

curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '
[
  {
    "text": "First sentence. Second sentence.",
	"some input field": "some id 1"
  },
  {
    "text": "Third sentence.",
	"some input field": "some id 2"
  }
]
' "http://$host/api/parse?pretty=true"

echo
echo
echo "JSON input (array of objects), JSON output (with sentence split)"
echo

curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '
[
  {
    "text": "First sentence. Second sentence.",
	"some input field": "some id 1"
  },
  {
    "text": "Third sentence.",
	"some input field": "some id 2"
  }
]
' "http://$host/api/parse?pretty=true&ssplit=true"

echo
echo
echo "JSON input (array of objects), YAML output (without sentence split)"
echo

curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/yaml' -d '
[
  {
    "text": "First sentence. Second sentence.",
	"some input field": "some id 1"
  },
  {
    "text": "Third sentence.",
	"some input field": "some id 2"
  }
]
' "http://$host/api/parse?fmt=yaml"

echo
echo
echo "JSON input (array of objects), YAML output (with sentence split)"
echo

curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/yaml' -d '
[
  {
    "text": "First sentence. Second sentence.",
	"some input field": "some id 1"
  },
  {
    "text": "Third sentence.",
	"some input field": "some id 2"
  }
]
' "http://$host/api/parse?fmt=yaml&ssplit=true"

echo
echo
echo "JSON input (array of strings), YAML output (without sentence split)"
echo

curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/yaml' -d '
[
  "First sentence. Second sentence.",
  "Third sentence."
]
' "http://$host/api/parse?fmt=yaml"

echo
echo
echo "JSON input (array of strings), YAML output (with sentence split)"
echo

curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/yaml' -d '
[
  "First sentence. Second sentence.",
  "Third sentence."
]
' "http://$host/api/parse?fmt=yaml&ssplit=true"

echo
echo
echo "YAML input (array of objects), YAML output (without sentence split)"
echo

curl -X POST --header 'Content-Type: application/yaml' --header 'Accept: application/yaml' -d '
- text: First sentence.
        Second sentence.
  custom field: some id 1
- text: Third sentence.
  some input field: some id 2
' "http://$host/api/parse?fmt=yaml"

echo
echo
echo "YAML input (array of objects), YAML output (with sentence split)"
echo

curl -X POST --header 'Content-Type: application/yaml' --header 'Accept: application/yaml' -d '
- text: First sentence.
        Second sentence.
  some input field: some id 1
- text: Third sentence.
  custom field: some id 2
' "http://$host/api/parse?fmt=yaml&ssplit=true"

echo
echo
echo "YAML input (array of strings), YAML output (without sentence split)"
echo

curl -X POST --header 'Content-Type: application/yaml' --header 'Accept: application/yaml' -d '
- First sentence. Second sentence.
- Third sentence.
' "http://$host/api/parse?fmt=yaml"

echo
echo
echo "YAML input (array of strings), YAML output (with sentence split)"
echo

curl -X POST --header 'Content-Type: application/yaml' --header 'Accept: application/yaml' -d '
- First sentence. Second sentence.
- Third sentence.
' "http://$host/api/parse?fmt=yaml&ssplit=true"

echo
echo
