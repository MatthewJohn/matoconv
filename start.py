
from matoconv import Matoconv


m = Matoconv.get_instance(create=True)
m.app.run(host='0.0.0.0', debug=True)
