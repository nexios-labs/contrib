from nexios.dependencies import Context, Depend

from nexios_contrib.request_id import get_request_id_from_request


def RequestIdDepend(attribute_name: str = "request_id"):
    def _wrap(ctx=Context()):
        return get_request_id_from_request(ctx.request, attribute_name)  # ty:ignore[invalid-argument-type]

    return Depend(_wrap)
