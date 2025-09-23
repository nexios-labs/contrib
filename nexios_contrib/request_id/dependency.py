from nexios.dependencies import Depend,Context
from nexios_contrib.request_id import get_request_id_from_request

def RequestIdDepend(attribute_name: str = "request_id"):
    def _wrap(request = Context().request):
        return get_request_id_from_request(request, attribute_name)
    return Depend(_wrap)
    