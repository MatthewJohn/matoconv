

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


### Environment variables

* `DEBUG` - Set to 'true' to enable debug (default: disabled)
* `THREADING` - Set to 'false' to disable (defaults on)
* `LISTEN_HOST` - Host to listen on (default: 0.0.0.0)
* `LISTEN_PORT` - Port to listen on (default: 5000)
* `MAX_ATTEMPTS` - Maximum conversion attempts before failing (default: 3)
* `MAX_CONVERTERS` - Maximum simulatenous Libreoffice converisons (default: 5)
* `POOL_CONVERT_TIMEOUT` - Time to wait for available conversion worker before timing out (seconds) (default: 60)
* `RETRY_WAIT_PERIOD` - Time to wait after conversion failure before retrying (seconds) (default: 1)
* `EXECUTION_TIMEOUT` - Maximum conversion command execution time (seconds) (default: 10)


## Quotes

* `Matoconv is the fundamental step to error-free conversions` - John, Adobe

