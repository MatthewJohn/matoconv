

# Matoconv

Re-implementation of unoconv-server, to avoid unoconv conversion errors (pyuno-bridge etc.)


## Example

    curl -H 'Content-Disposition: attachment; filename="test.html"' -d'<html><body><h1>Hi</h1></body></html>' -XPOST --output - localhost:5000/convert/format/pdf


## Quickstart

### Build

    docker build . -t matoconv:latest


### Run

    docker run -p 5000:5000 matoconv:latest

Now send API requests to /convert/format/pdf or /convert/format/docx.

Example demo page API at http://localhost:5000


## Quotes

* `Matoconv is the fundamental step to error-free conversions` - John, Adobe

