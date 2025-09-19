# flake8: noqa

if __import__("typing").TYPE_CHECKING:
    # import apis into api package
    from deltastream.api.dataplane.openapi_client.api.dataplane_api import DataplaneApi
    
else:
    from lazy_imports import LazyModule, as_package, load

    load(
        LazyModule(
            *as_package(__file__),
            """# import apis into api package
from deltastream.api.dataplane.openapi_client.api.dataplane_api import DataplaneApi

""",
            name=__name__,
            doc=__doc__,
        )
    )
