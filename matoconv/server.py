
import os

from matoconv import Matoconv


# Initialise server instance
m = Matoconv.get_instance()
# Run server
m.app.run(
    host=os.environ.get('LISTEN_HOST', '0.0.0.0'),
    port=os.environ.get('LISTEN_PORT', '5000'),
    debug=(os.environ.get('DEBUG', False) == 'true'),
    threaded=(os.environ.get('THREADING', 'true') == 'true')
)
